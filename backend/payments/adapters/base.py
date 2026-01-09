"""
Base Payment Adapter Interface
All payment providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PaymentResult:
    """
    Standardized result from payment adapter operations
    Ensures consistent return format across all providers
    """
    success: bool
    mode: Optional[str] = None  # 'redirect' | 'widget' | 'ussd' | 'hosted' | 'qr'
    provider_intent_id: Optional[str] = None  # Provider's transaction ID
    redirect_url: Optional[str] = None  # For redirect-based flows
    client_token: Optional[str] = None  # For client-side widget flows
    qr_code: Optional[str] = None  # For QR code payments
    instructions: Optional[str] = None  # User instructions (e.g., USSD code to dial)
    status: Optional[str] = None  # 'pending' | 'success' | 'failed' | 'cancelled'
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retryable: bool = False  # Can this operation be retried?
    metadata: Dict[str, Any] = None  # Additional provider-specific data

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RefundResult:
    """Standardized result from refund operations"""
    success: bool
    provider_refund_id: Optional[str] = None
    status: Optional[str] = None  # 'pending' | 'success' | 'failed'
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebhookEvent:
    """Standardized webhook event after parsing"""
    provider_event_id: str  # Unique ID from provider
    provider_intent_id: str  # Maps to PaymentIntent.provider_intent_id
    status: str  # 'success' | 'failed' | 'pending' | 'cancelled'
    amount: Optional[int] = None  # In smallest currency unit
    currency: Optional[str] = None
    timestamp: Optional[str] = None
    raw_payload: Dict[str, Any] = None  # Original webhook data
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.raw_payload is None:
            self.raw_payload = {}
        if self.metadata is None:
            self.metadata = {}


class BasePaymentAdapter(ABC):
    """
    Abstract base class for all payment provider adapters

    Each provider (Fapshi, MTN, Orange, Flutterwave, etc.) must implement this interface
    This ensures consistent behavior across all providers and makes adding new providers easy
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with provider-specific configuration

        Args:
            config: Decrypted configuration from MerchantPaymentMethod.config_encrypted
        """
        self.config = config
        self.provider_name = self.get_provider_name()

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Return provider name (e.g., 'fapshi', 'mtn', 'orange')
        Must be unique across all providers
        """
        pass

    @abstractmethod
    def create_payment(self, payment_intent) -> PaymentResult:
        """
        Initiate payment with provider

        Args:
            payment_intent: PaymentIntent model instance

        Returns:
            PaymentResult with provider response

        This method should:
        1. Call provider API to create payment
        2. Return mode (redirect/ussd/widget) and necessary client data
        3. Handle provider errors gracefully
        4. Be fast (< 5 seconds) - offload to webhooks if provider is slow
        """
        pass

    @abstractmethod
    def confirm_payment(self, provider_intent_id: str) -> PaymentResult:
        """
        Check payment status with provider (polling)
        Used for reconciliation and status checks

        Args:
            provider_intent_id: Provider's transaction ID

        Returns:
            PaymentResult with current status
        """
        pass

    @abstractmethod
    def refund_payment(self, provider_intent_id: str, amount: int, reason: str = '') -> RefundResult:
        """
        Initiate refund with provider

        Args:
            provider_intent_id: Provider's transaction ID
            amount: Amount to refund (in smallest currency unit)
            reason: Refund reason

        Returns:
            RefundResult with refund status
        """
        pass

    @abstractmethod
    def parse_webhook(self, raw_payload: Dict[str, Any], headers: Dict[str, str]) -> WebhookEvent:
        """
        Parse and validate webhook payload from provider

        Args:
            raw_payload: Raw webhook JSON payload
            headers: HTTP headers from webhook request

        Returns:
            WebhookEvent with standardized data

        Raises:
            ValueError: If webhook signature is invalid or payload is malformed
        """
        pass

    @abstractmethod
    def verify_webhook_signature(self, raw_payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        Verify webhook signature to ensure it came from provider

        Args:
            raw_payload: Raw webhook JSON payload
            headers: HTTP headers (contains signature)

        Returns:
            True if signature is valid, False otherwise

        Security critical: ALWAYS verify signatures in production
        """
        pass

    @abstractmethod
    def test_credentials(self) -> Dict[str, Any]:
        """
        Test provider credentials with a small API call
        Used during merchant setup to verify config

        Returns:
            Dict with test result: {'success': bool, 'message': str}
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return provider capabilities metadata

        Returns:
            Dict with provider capabilities:
            {
                'payment_modes': ['redirect', 'ussd', 'widget'],
                'supported_currencies': ['XAF', 'USD'],
                'supports_refunds': True,
                'supports_partial_refunds': False,
                'min_amount': 100,  # in smallest currency unit
                'max_amount': 10000000,
                'countries': ['CM'],  # ISO country codes
            }
        """
        pass

    # Optional helper methods (providers can override)

    def supports_currency(self, currency: str) -> bool:
        """Check if provider supports given currency"""
        capabilities = self.get_capabilities()
        return currency in capabilities.get('supported_currencies', [])

    def supports_refunds(self) -> bool:
        """Check if provider supports refunds"""
        capabilities = self.get_capabilities()
        return capabilities.get('supports_refunds', False)

    def validate_amount(self, amount: int, currency: str) -> bool:
        """Validate amount is within provider limits"""
        capabilities = self.get_capabilities()
        min_amount = capabilities.get('min_amount', 0)
        max_amount = capabilities.get('max_amount', float('inf'))
        return min_amount <= amount <= max_amount

    def __repr__(self):
        return f"<{self.__class__.__name__} provider={self.provider_name}>"
