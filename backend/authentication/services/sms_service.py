"""
Enterprise SMS Service - 2025 Security Standards
Handles SMS OTP verification using Twilio

Production Standards:
- Response time < 200ms for user-facing operations
- Retry mechanisms with exponential backoff
- Comprehensive error handling and logging
- Rate limiting to prevent abuse
- Graceful degradation when service unavailable
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from ..models import PhoneVerificationCode, SecurityEvent
from .security_service import SecurityService
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)


class SMSService:
    """
    Enterprise SMS service for authentication and verification
    
    Uses Twilio as the SMS provider with production-grade features:
    - Automatic retry on transient failures
    - Rate limiting integration
    - Comprehensive audit logging
    - Graceful error handling
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1
    
    @staticmethod
    def _get_twilio_client():
        """
        Get configured Twilio client
        
        Returns:
            Client or None: Twilio client if configured, None otherwise
        """
        if not getattr(settings, 'TWILIO_ENABLED', False):
            logger.warning("Twilio is disabled in settings")
            return None
            
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        
        if not account_sid or not auth_token:
            logger.error("Twilio credentials not configured")
            return None
        
        try:
            return Client(account_sid, auth_token)
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            return None
    
    @staticmethod
    def _get_from_number():
        """Get the Twilio phone number for sending SMS"""
        return getattr(settings, 'TWILIO_PHONE_NUMBER', '')
    
    @staticmethod
    def send_sms(phone_number, message, retry_count=0):
        """
        Send SMS message via Twilio with retry logic
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message: SMS message content
            retry_count: Current retry attempt (internal use)
            
        Returns:
            dict: Send result with success status and message SID
        """
        client = SMSService._get_twilio_client()
        from_number = SMSService._get_from_number()
        
        if not client:
            logger.error("Twilio client not available")
            return {
                'success': False,
                'message': 'SMS service not configured',
                'error_code': 'SERVICE_NOT_CONFIGURED'
            }
        
        if not from_number:
            logger.error("Twilio phone number not configured")
            return {
                'success': False,
                'message': 'SMS sender number not configured',
                'error_code': 'SENDER_NOT_CONFIGURED'
            }
        
        try:
            # Send SMS via Twilio
            twilio_message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            
            logger.info(
                f"SMS sent successfully: SID={twilio_message.sid}, "
                f"to={phone_number}, status={twilio_message.status}"
            )
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'message_sid': twilio_message.sid,
                'status': twilio_message.status
            }
            
        except TwilioRestException as e:
            # Handle specific Twilio errors
            error_code = e.code
            
            # Retryable errors (rate limits, temporary failures)
            retryable_codes = [20429, 30022, 30028]  # Rate limit, network errors
            
            if error_code in retryable_codes and retry_count < SMSService.MAX_RETRIES:
                delay = SMSService.RETRY_DELAY_SECONDS * (2 ** retry_count)
                logger.warning(
                    f"Twilio retryable error {error_code}: {e.msg}, "
                    f"retrying in {delay}s (attempt {retry_count + 1}/{SMSService.MAX_RETRIES})"
                )
                time.sleep(delay)
                return SMSService.send_sms(phone_number, message, retry_count + 1)
            
            # Non-retryable error or max retries exceeded
            logger.error(
                f"Twilio error: code={error_code}, message={e.msg}, "
                f"phone={phone_number}"
            )
            
            # Map common error codes to user-friendly messages
            error_messages = {
                21211: 'Invalid phone number format',
                21214: 'Phone number is not a valid mobile number',
                21408: 'Phone number is not reachable',
                21610: 'Phone number is unsubscribed',
                21612: 'Cannot send to this phone number',
            }
            
            return {
                'success': False,
                'message': error_messages.get(error_code, 'Failed to send SMS'),
                'error_code': str(error_code),
                'error_detail': e.msg
            }
            
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {phone_number}: {e}")
            return {
                'success': False,
                'message': 'Failed to send SMS due to unexpected error',
                'error_code': 'UNEXPECTED_ERROR',
                'error_detail': str(e)
            }
    
    @staticmethod
    def send_verification_sms(phone_number, raw_code, code_type):
        """
        Send verification OTP via SMS
        
        Args:
            phone_number: Recipient phone number
            raw_code: Plain text verification code
            code_type: Type of verification for message customization
            
        Returns:
            dict: Send result
        """
        # Get site name for branding
        site_name = getattr(settings, 'SITE_NAME', 'HustlerzCamp')
        
        # Customize message based on code type
        messages = {
            PhoneVerificationCode.PHONE_VERIFICATION: (
                f"Your {site_name} verification code is: {raw_code}. "
                f"This code expires in 10 minutes. Do not share this code."
            ),
            PhoneVerificationCode.LOGIN_VERIFICATION: (
                f"Your {site_name} login code is: {raw_code}. "
                f"If you did not request this, please ignore."
            ),
            PhoneVerificationCode.PASSWORD_RESET: (
                f"Your {site_name} password reset code is: {raw_code}. "
                f"This code expires in 10 minutes."
            ),
            PhoneVerificationCode.PHONE_CHANGE: (
                f"Your {site_name} phone change verification code is: {raw_code}. "
                f"This code expires in 10 minutes."
            ),
        }
        
        message = messages.get(code_type, f"Your verification code is: {raw_code}")
        
        return SMSService.send_sms(phone_number, message)
    
    @staticmethod
    def request_phone_verification(phone_number, code_type, user=None, request=None):
        """
        Request phone verification code with rate limiting
        
        Complete flow:
        1. Check rate limits
        2. Generate secure code
        3. Send SMS
        4. Return result
        
        Args:
            phone_number: Phone number to verify
            code_type: Type of verification code
            user: User instance (optional)
            request: HTTP request for audit
            
        Returns:
            dict: Verification request result
        """
        try:
            # Normalize phone number
            normalized_phone, country_code = PhoneVerificationCode.normalize_phone_number(phone_number)
            
            # Check rate limiting
            rate_limit_status = PhoneVerificationCode.get_rate_limit_status(
                normalized_phone, 
                code_type
            )
            
            if rate_limit_status['is_rate_limited']:
                logger.warning(
                    f"Rate limit exceeded for phone verification: {normalized_phone}, "
                    f"type: {code_type}"
                )
                return {
                    'success': False,
                    'message': 'Too many verification attempts. Please try again later.',
                    'rate_limited': True,
                    'cooldown_until': rate_limit_status['cooldown_until'].isoformat() if rate_limit_status['cooldown_until'] else None
                }
            
            # Get client info for audit
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            # Set expiration based on code type
            expires_minutes = {
                PhoneVerificationCode.PHONE_VERIFICATION: 10,
                PhoneVerificationCode.PASSWORD_RESET: 10,
                PhoneVerificationCode.PHONE_CHANGE: 10,
                PhoneVerificationCode.LOGIN_VERIFICATION: 5,
            }.get(code_type, 10)
            
            # Create verification code
            verification_code, raw_code = PhoneVerificationCode.create_verification_code(
                phone_number=normalized_phone,
                code_type=code_type,
                user=user,
                expires_minutes=expires_minutes,
                ip_address=ip_address,
                user_agent=user_agent,
                country_code=country_code
            )
            
            # Send SMS
            sms_result = SMSService.send_verification_sms(
                phone_number=normalized_phone,
                raw_code=raw_code,
                code_type=code_type
            )
            
            if sms_result['success']:
                logger.info(
                    f"Phone verification SMS sent: phone={normalized_phone}, "
                    f"type={code_type}, verification_id={verification_code.id}"
                )
                
                # Log security event
                try:
                    SecurityEvent.log_event(
                        event_type='phone_verification_sms_sent',
                        user=user,
                        description=f'Phone verification SMS sent: {code_type}',
                        risk_level=1,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            'phone': normalized_phone,
                            'code_type': code_type,
                            'verification_id': str(verification_code.id),
                            'message_sid': sms_result.get('message_sid')
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log security event: {e}")
                
                return {
                    'success': True,
                    'message': f'Verification code sent to {SMSService._mask_phone(normalized_phone)}',
                    'verification_id': str(verification_code.id),
                    'expires_in_minutes': expires_minutes,
                    'code_type': code_type
                }
            else:
                # SMS sending failed - revoke the code
                verification_code.revoke('SMS sending failed')
                
                logger.error(
                    f"Failed to send verification SMS: phone={normalized_phone}, "
                    f"error={sms_result.get('error_code')}"
                )
                
                return {
                    'success': False,
                    'message': sms_result.get('message', 'Failed to send verification SMS'),
                    'error_code': sms_result.get('error_code')
                }
                
        except Exception as e:
            logger.error(f"Phone verification request error for {phone_number}: {e}")
            return {
                'success': False,
                'message': 'Failed to process verification request',
                'error': str(e)
            }
    
    @staticmethod
    def verify_phone_code(phone_number, code_type, raw_code, request=None):
        """
        Verify phone verification code
        
        Args:
            phone_number: Phone number
            code_type: Type of verification code
            raw_code: Raw verification code
            request: HTTP request for audit
            
        Returns:
            dict: Verification result
        """
        try:
            # Normalize phone number
            normalized_phone, _ = PhoneVerificationCode.normalize_phone_number(phone_number)
            
            # Find pending verification code
            verification_code = PhoneVerificationCode.objects.filter(
                phone_number=normalized_phone,
                code_type=code_type,
                status=PhoneVerificationCode.PENDING
            ).order_by('-created_at').first()
            
            if not verification_code:
                logger.warning(
                    f"No pending verification code found: phone={normalized_phone}, "
                    f"type={code_type}"
                )
                return {
                    'success': False,
                    'message': 'No pending verification code found for this phone number'
                }
            
            # Get client info for audit
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            # Verify code
            is_valid, message = verification_code.verify_code(raw_code, ip_address, user_agent)
            
            return {
                'success': is_valid,
                'message': message,
                'verification_id': str(verification_code.id),
                'user_id': str(verification_code.user.id) if verification_code.user else None
            }
            
        except Exception as e:
            logger.error(f"Phone code verification error for {phone_number}: {e}")
            return {
                'success': False,
                'message': 'Failed to verify phone code',
                'error': str(e)
            }
    
    @staticmethod
    def get_phone_verification_status(phone_number, user=None):
        """
        Get phone verification status
        
        Args:
            phone_number: Phone number to check
            user: User instance (optional)
            
        Returns:
            dict: Verification status
        """
        try:
            normalized_phone, _ = PhoneVerificationCode.normalize_phone_number(phone_number)
            
            # Check if phone is verified (has a successful verification)
            verified = PhoneVerificationCode.objects.filter(
                phone_number=normalized_phone,
                status=PhoneVerificationCode.VERIFIED
            ).exists()
            
            # Check for pending verification
            pending = PhoneVerificationCode.objects.filter(
                phone_number=normalized_phone,
                status=PhoneVerificationCode.PENDING
            ).order_by('-created_at').first()
            
            # Get rate limit status
            rate_limit = PhoneVerificationCode.get_rate_limit_status(
                normalized_phone,
                PhoneVerificationCode.PHONE_VERIFICATION
            )
            
            return {
                'phone_verified': verified,
                'has_pending_verification': pending is not None,
                'pending_expires_at': pending.expires_at.isoformat() if pending else None,
                'rate_limit': {
                    'is_limited': rate_limit['is_rate_limited'],
                    'remaining_attempts': max(0, rate_limit['max_codes'] - rate_limit['recent_codes']),
                    'cooldown_until': rate_limit['cooldown_until'].isoformat() if rate_limit['cooldown_until'] else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting phone verification status: {e}")
            return {
                'phone_verified': False,
                'error': str(e)
            }
    
    @staticmethod
    def _mask_phone(phone_number):
        """
        Mask phone number for display (privacy)
        
        Example: +237612345678 -> +237****5678
        """
        if len(phone_number) <= 8:
            return phone_number[:3] + '****'
        return phone_number[:4] + '****' + phone_number[-4:]
    
    @staticmethod
    def cleanup_expired_codes():
        """Clean up expired verification codes"""
        try:
            expired_count = PhoneVerificationCode.cleanup_expired_codes()
            logger.info(f"Phone verification cleanup: {expired_count} codes expired")
            return {'expired_codes': expired_count}
        except Exception as e:
            logger.error(f"Phone verification cleanup error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def is_service_available():
        """
        Check if SMS service is available
        
        Used for health checks and graceful degradation.
        """
        client = SMSService._get_twilio_client()
        from_number = SMSService._get_from_number()
        
        return {
            'available': client is not None and bool(from_number),
            'configured': bool(getattr(settings, 'TWILIO_ENABLED', False)),
            'has_credentials': bool(getattr(settings, 'TWILIO_ACCOUNT_SID', ''))
        }
