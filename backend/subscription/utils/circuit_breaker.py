"""
Circuit breaker pattern implementation for payment gateway resilience
Prevents cascade failures and provides graceful degradation
"""
import time
import threading
from enum import Enum
from typing import Callable, Any, Optional, Dict
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for payment gateway operations
    Implements the circuit breaker pattern to prevent cascade failures
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Unique name for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open state
            expected_exception: Exception type to count as failure
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.lock = threading.Lock()
        
        # Cache keys for persistence across requests
        self.state_key = f"circuit_breaker:{name}:state"
        self.failure_count_key = f"circuit_breaker:{name}:failures"
        self.last_failure_time_key = f"circuit_breaker:{name}:last_failure"
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: When circuit is open
        """
        with self.lock:
            state = self._get_state()
            
            if state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._set_state(CircuitBreakerState.HALF_OPEN)
                    logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
                else:
                    self._log_blocked_request()
                    raise CircuitBreakerError(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Will retry after {self.recovery_timeout} seconds."
                    )
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise e
    
    def _get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state"""
        state_value = cache.get(self.state_key, CircuitBreakerState.CLOSED.value)
        return CircuitBreakerState(state_value)
    
    def _set_state(self, state: CircuitBreakerState):
        """Set circuit breaker state"""
        cache.set(self.state_key, state.value, timeout=3600)  # 1 hour
        logger.info(f"Circuit breaker {self.name} state changed to {state.value}")
    
    def _get_failure_count(self) -> int:
        """Get current failure count"""
        return cache.get(self.failure_count_key, 0)
    
    def _increment_failure_count(self):
        """Increment failure count"""
        count = self._get_failure_count() + 1
        cache.set(self.failure_count_key, count, timeout=3600)
        cache.set(self.last_failure_time_key, time.time(), timeout=3600)
        return count
    
    def _reset_failure_count(self):
        """Reset failure count to zero"""
        cache.delete(self.failure_count_key)
        cache.delete(self.last_failure_time_key)
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        last_failure_time = cache.get(self.last_failure_time_key, 0)
        return (time.time() - last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        state = self._get_state()
        
        if state == CircuitBreakerState.HALF_OPEN:
            self._set_state(CircuitBreakerState.CLOSED)
            logger.info(f"Circuit breaker {self.name} recovered - moving to CLOSED")
        
        self._reset_failure_count()
    
    def _on_failure(self):
        """Handle failed operation"""
        failure_count = self._increment_failure_count()
        state = self._get_state()
        
        logger.warning(f"Circuit breaker {self.name} failure {failure_count}/{self.failure_threshold}")
        
        if failure_count >= self.failure_threshold and state != CircuitBreakerState.OPEN:
            self._set_state(CircuitBreakerState.OPEN)
            logger.error(
                f"Circuit breaker {self.name} OPENED after {failure_count} failures. "
                f"Will attempt recovery in {self.recovery_timeout} seconds."
            )
    
    def _log_blocked_request(self):
        """Log blocked request for monitoring"""
        logger.warning(f"Request blocked by circuit breaker {self.name}")
        
        # Increment blocked requests counter for monitoring
        blocked_key = f"circuit_breaker:{self.name}:blocked_requests"
        current_count = cache.get(blocked_key, 0)
        cache.set(blocked_key, current_count + 1, timeout=3600)
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring"""
        state = self._get_state()
        failure_count = self._get_failure_count()
        last_failure_time = cache.get(self.last_failure_time_key, 0)
        blocked_requests = cache.get(f"circuit_breaker:{self.name}:blocked_requests", 0)
        
        return {
            'name': self.name,
            'state': state.value,
            'failure_count': failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': last_failure_time,
            'recovery_timeout': self.recovery_timeout,
            'blocked_requests_1h': blocked_requests,
            'healthy': state == CircuitBreakerState.CLOSED
        }
    
    def force_open(self):
        """Force circuit breaker to open state (for testing/maintenance)"""
        self._set_state(CircuitBreakerState.OPEN)
        logger.warning(f"Circuit breaker {self.name} manually opened")
    
    def force_close(self):
        """Force circuit breaker to closed state"""
        self._set_state(CircuitBreakerState.CLOSED)
        self._reset_failure_count()
        logger.info(f"Circuit breaker {self.name} manually closed")


# Pre-configured circuit breakers for common operations
class PaymentCircuitBreakers:
    """Collection of circuit breakers for payment operations"""
    
    # Fapshi API circuit breaker
    fapshi_api = CircuitBreaker(
        name="fapshi_api",
        failure_threshold=3,  # Open after 3 failures
        recovery_timeout=30,   # Try recovery after 30 seconds
        expected_exception=Exception
    )
    
    # Payment processing circuit breaker
    payment_processing = CircuitBreaker(
        name="payment_processing",
        failure_threshold=5,   # More lenient for payment processing
        recovery_timeout=60,   # Longer recovery time
        expected_exception=Exception
    )
    
    # Webhook processing circuit breaker
    webhook_processing = CircuitBreaker(
        name="webhook_processing",
        failure_threshold=10,  # High threshold for webhooks
        recovery_timeout=30,
        expected_exception=Exception
    )
    
    @classmethod
    def get_all_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {
            'fapshi_api': cls.fapshi_api.get_status(),
            'payment_processing': cls.payment_processing.get_status(),
            'webhook_processing': cls.webhook_processing.get_status()
        }


def circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator for applying circuit breaker to functions
    
    Usage:
        @circuit_breaker(PaymentCircuitBreakers.fapshi_api)
        def call_fapshi_api():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    """
    Decorator that provides fallback when circuit breaker is open
    
    Usage:
        @with_fallback(lambda: {'error': 'Service unavailable'})
        @circuit_breaker(PaymentCircuitBreakers.fapshi_api)
        def risky_operation():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CircuitBreakerError:
                logger.info(f"Circuit breaker open, using fallback for {func.__name__}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator