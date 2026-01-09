"""
Security utilities for payment processing
Handles signature verification, data masking, and secure operations
"""
import hashlib
import hmac
import secrets
import re
from typing import Optional, Tuple
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PaymentSecurityManager:
    """Manages security operations for payment processing"""
    
    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret_key: str) -> bool:
        """
        Verify webhook signature from payment gateway
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            secret_key: Secret key for verification
            
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    @staticmethod
    def generate_payment_signature(
        payment_reference: str, 
        amount: int, 
        user_id: int, 
        timestamp: str
    ) -> str:
        """
        Generate secure payment signature for verification
        
        Args:
            payment_reference: Payment reference ID
            amount: Payment amount in FCFA
            user_id: User ID
            timestamp: Timestamp string
            
        Returns:
            Generated signature
        """
        secret_key = getattr(settings, 'SUBSCRIPTION_PAYMENT_SECRET', 'change-in-production')
        
        data = f"{payment_reference}|{amount}|{user_id}|{timestamp}"
        
        signature = hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_payment_signature(
        payment_reference: str,
        amount: int,
        user_id: int,
        timestamp: str,
        signature: str
    ) -> bool:
        """
        Verify payment signature to prevent tampering
        
        Returns:
            True if signature is valid
        """
        expected_signature = PaymentSecurityManager.generate_payment_signature(
            payment_reference, amount, user_id, timestamp
        )
        
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def generate_secure_payment_reference() -> str:
        """Generate cryptographically secure payment reference"""
        return f"HUZILERZ_{secrets.token_hex(8).upper()}"
    
    @staticmethod
    def mask_phone_number(phone_number: str) -> str:
        """
        Mask phone number for secure display
        
        Args:
            phone_number: Phone number to mask
            
        Returns:
            Masked phone number
        """
        if not phone_number or len(phone_number) < 4:
            return "****"
        
        if len(phone_number) <= 8:
            return f"{phone_number[:2]}****{phone_number[-2:]}"
        else:
            return f"{phone_number[:3]}****{phone_number[-3:]}"
    
    @staticmethod
    def mask_payment_reference(payment_reference: str) -> str:
        """
        Mask payment reference for secure display
        
        Args:
            payment_reference: Payment reference to mask
            
        Returns:
            Masked payment reference
        """
        if not payment_reference or len(payment_reference) < 8:
            return "****"
        
        return f"{payment_reference[:4]}****{payment_reference[-4:]}"
    
    @staticmethod
    def mask_email_address(email: str) -> str:
        """
        Mask email address for secure display
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email address
        """
        if not email or '@' not in email:
            return "****"
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 3:
            masked_local = local[0] + '*' * (len(local) - 1)
        else:
            masked_local = local[:2] + '*' * (len(local) - 4) + local[-2:]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def sanitize_user_input(input_data: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            input_data: Raw user input
            
        Returns:
            Sanitized input
        """
        if not input_data:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', str(input_data))
        
        # Remove SQL injection patterns
        sql_patterns = [
            r'(\bunion\b|\bselect\b|\binsert\b|\bdelete\b|\bupdate\b|\bdrop\b)',
            r'(--|#|\/\*|\*\/)',
            r'(\bor\b|\band\b)\s+\d+\s*=\s*\d+'
        ]
        
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_amount_security(amount: float, min_amount: float = 100, max_amount: float = 5000000) -> Tuple[bool, str]:
        """
        Validate payment amount for security

        Args:
            amount: Payment amount to validate
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount (5M FCFA)

        Returns:
            (is_valid, error_message)
        """
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return False, "Invalid amount format"

        if amount < min_amount:
            return False, f"Amount below minimum ({min_amount} FCFA)"

        if amount > max_amount:
            return False, f"Amount exceeds maximum ({max_amount} FCFA)"

        # Security: Check for negative or zero amounts
        if amount <= 0:
            return False, "Payment amount must be positive"


        return True, ""

    @staticmethod
    def validate_payment_input(payment_data: dict) -> Tuple[bool, str, dict]:
        """
        Comprehensive payment input validation

        Args:
            payment_data: Dictionary containing payment information

        Returns:
            (is_valid, error_message, validated_data)
        """
        validated_data = {}

        # Required fields validation
        required_fields = ['phone_number', 'amount', 'payment_method']
        for field in required_fields:
            if field not in payment_data:
                return False, f"Required field missing: {field}", {}

        # Validate phone number
        phone_number = payment_data.get('phone_number')
        if not phone_number or not isinstance(phone_number, str):
            return False, "Phone number is required", {}

        # Clean phone number
        phone = re.sub(r'[^\d+]', '', phone_number.strip())

        # Remove country code if present
        if phone.startswith('+237'):
            phone = phone[4:]
        elif phone.startswith('237'):
            phone = phone[3:]

        # Validate length
        if len(phone) != 9:
            return False, "Phone number must be 9 digits", {}

        validated_data['phone_number'] = f"+237{phone}"

        # Validate payment method
        payment_method = payment_data.get('payment_method', '').strip().lower()
        allowed_methods = ['mtn_momo', 'orange_money', 'fapshi']

        if payment_method not in allowed_methods:
            return False, f"Invalid payment method. Allowed: {', '.join(allowed_methods)}", {}

        validated_data['payment_method'] = payment_method

        # Validate payment amount
        amount = payment_data.get('amount')
        is_valid, error_msg = PaymentSecurityManager.validate_amount_security(amount)
        if not is_valid:
            return False, error_msg, {}

        validated_data['amount'] = float(amount)

        # Optional fields validation
        if 'reference' in payment_data:
            reference = payment_data['reference'].strip()
            if len(reference) > 100:
                return False, "Reference code too long (max 100 characters)", {}
            if not re.match(r'^[a-zA-Z0-9_-]+$', reference):
                return False, "Reference code contains invalid characters", {}
            validated_data['reference'] = reference

        if 'description' in payment_data:
            description = PaymentSecurityManager.sanitize_user_input(payment_data['description'])
            if len(description) > 255:
                return False, "Description too long (max 255 characters)", {}
            validated_data['description'] = description

        return True, "", validated_data
    
    @staticmethod
    def generate_webhook_secret() -> str:
        """Generate secure webhook secret"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
        """
        Hash sensitive data for secure storage
        
        Args:
            data: Data to hash
            salt: Optional salt (generates one if not provided)
            
        Returns:
            Hashed data
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        hash_object = hashlib.pbkdf2_hmac('sha256', 
                                         data.encode('utf-8'), 
                                         salt.encode('utf-8'), 
                                         100000)  # 100k iterations
        
        return f"{salt}${hash_object.hex()}"
    
    @staticmethod
    def verify_hashed_data(data: str, hashed_data: str) -> bool:
        """
        Verify data against its hash
        
        Args:
            data: Original data
            hashed_data: Hashed data to verify against
            
        Returns:
            True if data matches hash
        """
        try:
            if '$' not in hashed_data:
                return False
            
            salt, hash_hex = hashed_data.split('$', 1)
            
            new_hash = hashlib.pbkdf2_hmac('sha256',
                                          data.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
            
            return hmac.compare_digest(hash_hex, new_hash.hex())
        
        except Exception as e:
            logger.error(f"Hash verification failed: {str(e)}")
            return False


class SecurityAuditLogger:
    """Handles security event logging for payment operations"""
    
    @staticmethod
    def log_payment_attempt(user, amount: float, phone_number: str, success: bool):
        """Log payment attempt for security monitoring"""
        masked_phone = PaymentSecurityManager.mask_phone_number(phone_number)
        
        logger.info(
            f"PAYMENT_ATTEMPT: User={user.id} Amount={amount} "
            f"Phone={masked_phone} Success={success}"
        )
    
    @staticmethod
    def log_webhook_received(payload_size: int, signature_valid: bool, source_ip: str):
        """Log webhook reception for security monitoring"""
        logger.info(
            f"WEBHOOK_RECEIVED: Size={payload_size}b "
            f"SignatureValid={signature_valid} Source={source_ip}"
        )
    
    @staticmethod
    def log_security_violation(violation_type: str, user, details: str):
        """Log security violations"""
        user_info = f"User={user.id}" if user else "Anonymous"
        
        logger.warning(
            f"SECURITY_VIOLATION: Type={violation_type} "
            f"{user_info} Details={details}"
        )
    
    @staticmethod
    def log_fraud_attempt(user, risk_score: int, risk_factors: list):
        """Log potential fraud attempts"""
        logger.warning(
            f"FRAUD_ATTEMPT: User={user.id} RiskScore={risk_score} "
            f"Factors={','.join(risk_factors)}"
        )


def get_security_headers() -> dict:
    """Get security headers for API responses"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }