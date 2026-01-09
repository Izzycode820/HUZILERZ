"""
Fapshi API Client
Low-level API client with proper retry logic and error handling
"""
import requests
import time
import random
from typing import Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from .config import FapshiConfig

logger = logging.getLogger(__name__)

class FapshiApiClient:
    """
    Low-level Fapshi API client with retry logic and proper error handling
    Implements 2025 best practices for HTTP retries with exponential backoff
    """
    
    def __init__(self):
        self.config = FapshiConfig.get_credentials()
        self.timeout_settings = FapshiConfig.get_timeout_settings()
        self.debug_mode = FapshiConfig.get_debug_mode()
        
        # Create session with retry configuration
        self.session = self._create_session()
        
        if self.debug_mode:
            self._log_configuration()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry configuration"""
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.timeout_settings['max_retries'],
            backoff_factor=1.0,  # Start with 1 second
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=['GET', 'POST'],  # Methods to retry
            raise_on_status=False  # Don't raise on HTTP errors, handle manually
        )
        
        # Mount adapters with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            'Content-Type': 'application/json',
            'apiuser': self.config['api_user'],
            'apikey': self.config['api_key'],
            'User-Agent': 'HUZILERZ-Subscription/1.0'
        }
    
    def _add_jitter(self, delay: float) -> float:
        """Add jitter to prevent thundering herd problem"""
        jitter = delay * 0.1 * random.uniform(-1, 1)  # ±10% jitter
        return max(0.1, delay + jitter)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to Fapshi API with comprehensive error handling
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request payload for POST requests
            
        Returns:
            Dict with response data or error information
        """
        url = f"{self.config['base_url']}{endpoint}"
        headers = self._get_headers()
        
        if self.debug_mode:
            logger.debug(f"Fapshi API {method} {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Payload: {data}")
        
        try:
            # Make request with timeout
            if method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    headers=headers, 
                    timeout=self.timeout_settings['request_timeout']
                )
            else:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout_settings['request_timeout']
                )
            
            # Log response details
            logger.info(f"Fapshi API response: {response.status_code}")
            
            if self.debug_mode:
                logger.debug(f"Response body: {response.text}")
            
            # Handle different response status codes
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            error_msg = "Payment gateway request timeout"
            logger.error(f"Fapshi API timeout: {url}")
            return self._create_error_response('timeout', error_msg)
        
        except requests.exceptions.ConnectionError:
            error_msg = "Unable to connect to payment gateway"
            logger.error(f"Fapshi API connection error: {url}")
            return self._create_error_response('connection_error', error_msg)
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Payment gateway request failed: {str(e)}"
            logger.error(f"Fapshi API request error: {str(e)}")
            return self._create_error_response('request_error', error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected payment gateway error: {str(e)}"
            logger.error(f"Fapshi API unexpected error: {str(e)}")
            return self._create_error_response('unexpected_error', error_msg)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response based on status code"""
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data,
                    'status_code': response.status_code
                }
            except ValueError:
                return self._create_error_response(
                    'invalid_json', 
                    'Invalid response format from payment gateway'
                )
        
        elif response.status_code == 401:
            logger.error("Fapshi API authentication failed")
            return self._create_error_response(
                'authentication_failed',
                'Payment gateway authentication failed. Please check credentials.'
            )
        
        elif response.status_code == 429:
            logger.warning("Fapshi API rate limit exceeded")
            return self._create_error_response(
                'rate_limit_exceeded',
                'Too many requests to payment gateway. Please try again later.'
            )
        
        elif response.status_code in [500, 502, 503, 504]:
            logger.error(f"Fapshi API server error: {response.status_code}")
            return self._create_error_response(
                'server_error',
                f'Payment gateway server error ({response.status_code}). Please try again.'
            )
        
        else:
            logger.error(f"Fapshi API unexpected status: {response.status_code}")
            try:
                error_detail = response.json() if response.content else {}
                logger.error(f"Fapshi error details: {error_detail}")
            except ValueError:
                error_detail = {'message': response.text}
                logger.error(f"Fapshi error text: {response.text}")

            return self._create_error_response(
                'http_error',
                f'Payment gateway error ({response.status_code})',
                error_detail
            )
    
    def _create_error_response(self, error_type: str, message: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error_type': error_type,
            'message': message,
            'details': details or {},
            'retryable': error_type in ['timeout', 'connection_error', 'server_error', 'rate_limit_exceeded']
        }
    
    def _log_configuration(self) -> None:
        """Log configuration for debugging"""
        logger.debug("Fapshi API Client Configuration:")
        logger.debug(f"  Environment: {self.config['environment']}")
        logger.debug(f"  Base URL: {self.config['base_url']}")
        logger.debug(f"  API User: {self.config['api_user']}")
        logger.debug(f"  Request Timeout: {self.timeout_settings['request_timeout']}s")
        logger.debug(f"  Max Retries: {self.timeout_settings['max_retries']}")
    
    # Public API methods
    
    def initiate_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate payment via Fapshi API
        
        Args:
            payment_data: Payment information including amount, phone, etc.
            
        Returns:
            Dict with payment initiation result
        """
        logger.info(f"Initiating Fapshi payment for amount: {payment_data.get('amount')} FCFA")
        
        # Validate required fields
        required_fields = ['amount', 'phone', 'medium', 'name', 'email', 'externalId']
        missing_fields = [field for field in required_fields if not payment_data.get(field)]
        
        if missing_fields:
            return self._create_error_response(
                'validation_error',
                f'Missing required fields: {", ".join(missing_fields)}'
            )
        
        # Make API request
        result = self._make_request('POST', '/direct-pay', payment_data)

        if result['success']:
            logger.info(f"Payment initiated successfully: {payment_data.get('externalId')}")
            # Transform response to match expected format
            api_data = result['data']
            return {
                'success': True,
                'data': {
                    'transactionId': api_data.get('transactionId') or api_data.get('transId'),
                    'link': api_data.get('link') or api_data.get('payment_link'),
                    'status': api_data.get('status', 'PENDING'),
                    'message': api_data.get('message', 'Payment initiated successfully'),
                    'amount': payment_data.get('amount'),
                    'externalId': payment_data.get('externalId')
                },
                'message': 'Payment initiated successfully'
            }
        else:
            logger.error(f"Payment initiation failed: {result.get('message')}")
            return {
                'success': False,
                'message': result.get('message', 'Payment initiation failed'),
                'error_type': result.get('error_type', 'gateway_error')
            }
    
    def check_payment_status(self, transaction_ref: str) -> Dict[str, Any]:
        """
        Check payment status via Fapshi API
        
        Args:
            transaction_ref: External transaction reference
            
        Returns:
            Dict with payment status information
        """
        logger.info(f"Checking Fapshi payment status: {transaction_ref}")
        
        if not transaction_ref:
            return self._create_error_response(
                'validation_error',
                'Transaction reference is required'
            )
        
        result = self._make_request('GET', f'/payment-status/{transaction_ref}')

        if result['success']:
            api_data = result['data']
            payment_status = api_data.get('status', 'unknown')
            logger.info(f"Payment status retrieved: {transaction_ref} -> {payment_status}")

            return {
                'success': True,
                'data': {
                    'status': payment_status,
                    'transactionId': api_data.get('transactionId') or api_data.get('transId'),
                    'amount': api_data.get('amount'),
                    'externalId': transaction_ref,
                    'completedAt': api_data.get('completedAt') or api_data.get('completed_at'),
                    'message': api_data.get('message', 'Status retrieved successfully')
                },
                'message': 'Status retrieved successfully'
            }
        else:
            logger.error(f"Payment status check failed: {result.get('message')}")
            return {
                'success': False,
                'message': result.get('message', 'Status check failed'),
                'error_type': result.get('error_type', 'gateway_error')
            }
    
    def close_session(self):
        """Close the requests session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()