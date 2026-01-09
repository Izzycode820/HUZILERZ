# Customer Authentication Service - Phone-first authentication
# Optimized for Cameroon market (MTN, Orange Mobile Money)

from typing import Dict, Optional, Any
from uuid import UUID, uuid4
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from workspace.core.models.customer_model import Customer, CustomerService
import logging
import secrets
import string

logger = logging.getLogger('workspace.storefront.customer_auth')


class CustomerAuthService:
    """
    Customer authentication service with phone-first approach

    Performance: < 100ms authentication operations
    Scalability: Phone-based customer identification
    Reliability: OTP verification with fallbacks
    Security: Phone verification and secure sessions

    Cameroon Market Optimizations:
    - MTN/Orange phone number support
    - SMS/WhatsApp OTP delivery
    - Mobile Money integration ready
    - French/English language support
    """

    # OTP configuration
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_OTP_ATTEMPTS = 3
    OTP_CACHE_PREFIX = 'customer_otp_'
    SESSION_CACHE_PREFIX = 'customer_session_'

    @staticmethod
    def signup_with_password(
        workspace_id: str,
        phone: str,
        password: str,
        name: str,
        email: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Direct customer signup with password

        Security: Password hashing with Django's make_password
        Cameroon Market: Phone-first with secure password
        Analytics: Tracks customer_created if session_id provided

        Args:
            workspace_id: Workspace UUID
            phone: Customer phone number
            password: Customer password (will be hashed)
            name: Customer full name
            email: Optional email address
            city: Optional city
            region: Optional region
            session_id: Optional session ID for analytics tracking
        """
        try:
            # Normalize phone number
            normalized_phone = CustomerService.normalize_phone(phone)

            # Check if customer already exists
            existing_customer = Customer.objects.filter(
                workspace_id=workspace_id,
                phone=normalized_phone,
                is_active=True
            ).first()

            if existing_customer:
                return {
                    'success': False,
                    'error': 'Customer already exists with this phone number',
                    'suggestion': 'Use login instead'
                }

            # Validate password strength
            if len(password) < 6:
                return {
                    'success': False,
                    'error': 'Password must be at least 6 characters'
                }

            # Hash password
            hashed_password = make_password(password)

            # Create customer
            with transaction.atomic():
                from workspace.core.models import Workspace
                workspace = Workspace.objects.get(id=workspace_id)

                customer = Customer.objects.create(
                    workspace=workspace,
                    phone=normalized_phone,
                    name=name,
                    email=email or '',
                    password=hashed_password,
                    customer_type='individual',
                    city=city or '',
                    region=region or '',
                    sms_notifications=True,
                    whatsapp_notifications=True
                )

                # Mark as verified (no OTP needed with password)
                customer.mark_verified()

            # Track analytics event (graceful failure - never blocks signup)
            if session_id:
                CustomerAuthService._track_customer_created(customer, session_id)

            # Create session
            session_token = CustomerAuthService._create_session(customer)

            logger.info(
                "Customer signup completed",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer.id,
                    'phone': normalized_phone
                }
            )

            return {
                'success': True,
                'customer': CustomerAuthService._format_customer_for_auth(customer),
                'session_token': session_token,
                'message': 'Account created successfully'
            }

        except Exception as e:
            logger.error(
                "Signup failed",
                extra={
                    'workspace_id': workspace_id,
                    'phone': phone,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Signup failed. Please try again.'
            }

    @staticmethod
    def verify_signup_otp(
        workspace_id: str,
        phone: str,
        otp: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify OTP and create customer account

        Cameroon Market: Phone verification for account creation
        Security: OTP validation with attempt limits
        Analytics: Tracks customer_created if session_id provided

        Args:
            workspace_id: Workspace UUID
            phone: Customer phone number
            otp: OTP code to verify
            session_id: Optional session ID for analytics tracking
        """
        try:
            normalized_phone = CustomerService.normalize_phone(phone)
            otp_key = f"{CustomerAuthService.OTP_CACHE_PREFIX}{workspace_id}_{normalized_phone}"

            # Get OTP data from cache
            otp_data = cache.get(otp_key)
            if not otp_data:
                return {
                    'success': False,
                    'error': 'Verification code expired or not found'
                }

            # Check attempt limit
            if otp_data['attempts'] >= CustomerAuthService.MAX_OTP_ATTEMPTS:
                cache.delete(otp_key)
                return {
                    'success': False,
                    'error': 'Too many failed attempts. Please request a new code.'
                }

            # Verify OTP
            if otp_data['otp'] != otp:
                otp_data['attempts'] += 1
                cache.set(otp_key, otp_data, CustomerAuthService.OTP_EXPIRY_MINUTES * 60)

                return {
                    'success': False,
                    'error': 'Invalid verification code',
                    'attempts_remaining': CustomerAuthService.MAX_OTP_ATTEMPTS - otp_data['attempts']
                }

            # OTP verified, create customer
            with transaction.atomic():
                # Get workspace object
                from workspace.core.models import Workspace
                workspace = Workspace.objects.get(id=workspace_id)

                customer, created = CustomerService.get_or_create_customer_by_phone(
                    workspace=workspace,
                    phone=normalized_phone,
                    name=otp_data['name'],
                    email=otp_data.get('email'),
                    customer_type='individual',
                    sms_notifications=True,
                    whatsapp_notifications=True
                )

                # Mark as verified
                customer.mark_verified()

            # Clear OTP cache
            cache.delete(otp_key)

            # Track analytics event (graceful failure - never blocks signup)
            if session_id:
                CustomerAuthService._track_customer_created(customer, session_id)

            # Create session
            session_token = CustomerAuthService._create_session(customer)

            logger.info(
                "Customer signup completed",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer.id,
                    'phone': normalized_phone
                }
            )

            return {
                'success': True,
                'customer': CustomerAuthService._format_customer_for_auth(customer),
                'session_token': session_token,
                'message': 'Account created successfully'
            }

        except Exception as e:
            logger.error(
                "Signup OTP verification failed",
                extra={
                    'workspace_id': workspace_id,
                    'phone': phone,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Verification failed'
            }

    @staticmethod
    def login_with_password(workspace_id: str, phone: str, password: str) -> Dict[str, Any]:
        """
        Direct customer login with password

        Security: Password verification with check_password
        Cameroon Market: Phone-first authentication
        """
        try:
            normalized_phone = CustomerService.normalize_phone(phone)

            # Find customer
            customer = Customer.objects.filter(
                workspace_id=workspace_id,
                phone=normalized_phone,
                is_active=True
            ).first()

            if not customer:
                return {
                    'success': False,
                    'error': 'Invalid phone number or password'
                }

            # Verify password
            if not check_password(password, customer.password):
                logger.warning(
                    "Failed login attempt",
                    extra={
                        'workspace_id': workspace_id,
                        'phone': normalized_phone
                    }
                )
                return {
                    'success': False,
                    'error': 'Invalid phone number or password'
                }

            # Create session
            session_token = CustomerAuthService._create_session(customer)

            logger.info(
                "Customer login successful",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer.id,
                    'phone': normalized_phone
                }
            )

            return {
                'success': True,
                'customer': CustomerAuthService._format_customer_for_auth(customer),
                'session_token': session_token,
                'message': 'Login successful'
            }

        except Exception as e:
            logger.error(
                "Login failed",
                extra={
                    'workspace_id': workspace_id,
                    'phone': phone,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Login failed. Please try again.'
            }

    @staticmethod
    def verify_login_otp(
        workspace_id: str,
        phone: str,
        otp: str
    ) -> Dict[str, Any]:
        """
        Verify login OTP and create session

        Cameroon Market: Secure phone-based authentication
        """
        try:
            normalized_phone = CustomerService.normalize_phone(phone)
            otp_key = f"{CustomerAuthService.OTP_CACHE_PREFIX}{workspace_id}_{normalized_phone}"

            # Get OTP data from cache
            otp_data = cache.get(otp_key)
            if not otp_data:
                return {
                    'success': False,
                    'error': 'Verification code expired or not found'
                }

            # Check attempt limit
            if otp_data['attempts'] >= CustomerAuthService.MAX_OTP_ATTEMPTS:
                cache.delete(otp_key)
                return {
                    'success': False,
                    'error': 'Too many failed attempts. Please request a new code.'
                }

            # Verify OTP
            if otp_data['otp'] != otp:
                otp_data['attempts'] += 1
                cache.set(otp_key, otp_data, CustomerAuthService.OTP_EXPIRY_MINUTES * 60)

                return {
                    'success': False,
                    'error': 'Invalid verification code',
                    'attempts_remaining': CustomerAuthService.MAX_OTP_ATTEMPTS - otp_data['attempts']
                }

            # Get customer
            customer = Customer.objects.get(
                id=otp_data['customer_id'],
                workspace_id=workspace_id,
                is_active=True
            )

            # Clear OTP cache
            cache.delete(otp_key)

            # Create session
            session_token = CustomerAuthService._create_session(customer)

            logger.info(
                "Customer login successful",
                extra={
                    'workspace_id': workspace_id,
                    'customer_id': customer.id,
                    'phone': normalized_phone
                }
            )

            return {
                'success': True,
                'customer': CustomerAuthService._format_customer_for_auth(customer),
                'session_token': session_token,
                'message': 'Login successful'
            }

        except Exception as e:
            logger.error(
                "Login OTP verification failed",
                extra={
                    'workspace_id': workspace_id,
                    'phone': phone,
                    'error': str(e)
                },
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Login failed'
            }

    @staticmethod
    def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
        """Validate customer session token"""
        try:
            session_key = f"{CustomerAuthService.SESSION_CACHE_PREFIX}{session_token}"
            session_data = cache.get(session_key)

            if not session_data:
                return None

            # Check if session is expired
            if timezone.now().timestamp() > session_data['expires_at']:
                cache.delete(session_key)
                return None

            # Get customer
            customer = Customer.objects.filter(
                id=session_data['customer_id'],
                is_active=True
            ).first()

            if not customer:
                cache.delete(session_key)
                return None

            # Extend session
            session_data['expires_at'] = timezone.now().timestamp() + (24 * 60 * 60)  # 24 hours
            cache.set(session_key, session_data, 24 * 60 * 60)

            return {
                'customer': CustomerAuthService._format_customer_for_auth(customer),
                'session_data': session_data
            }

        except Exception as e:
            logger.error(
                "Session validation failed",
                extra={'session_token': session_token, 'error': str(e)},
                exc_info=True
            )
            return None

    @staticmethod
    def logout(session_token: str) -> bool:
        """Logout customer by invalidating session"""
        try:
            session_key = f"{CustomerAuthService.SESSION_CACHE_PREFIX}{session_token}"
            cache.delete(session_key)
            return True
        except Exception as e:
            logger.error(
                "Logout failed",
                extra={'session_token': session_token, 'error': str(e)},
                exc_info=True
            )
            return False

    @staticmethod
    def initiate_password_reset(workspace_id: str, phone: str) -> Dict[str, Any]:
        """Initiate password reset for email-based customers"""
        try:
            normalized_phone = CustomerService.normalize_phone(phone)

            customer = Customer.objects.filter(
                workspace_id=workspace_id,
                phone=normalized_phone,
                is_active=True,
                has_email=True
            ).first()

            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found or no email associated'
                }

            # Generate reset token
            reset_token = CustomerAuthService._generate_reset_token()
            reset_key = f"password_reset_{workspace_id}_{normalized_phone}"

            # Store reset token
            reset_data = {
                'token': reset_token,
                'customer_id': str(customer.id),
                'created_at': timezone.now().isoformat()
            }
            cache.set(reset_key, reset_data, 30 * 60)  # 30 minutes

            # Send reset email (in production, integrate with email service)
            # For now, return token for testing

            return {
                'success': True,
                'message': 'Password reset instructions sent',
                'reset_token': reset_token  # Remove in production
            }

        except Exception as e:
            logger.error(
                "Password reset initiation failed",
                extra={'workspace_id': workspace_id, 'phone': phone, 'error': str(e)},
                exc_info=True
            )
            return {
                'success': False,
                'error': 'Password reset failed'
            }

    # Helper methods

    @staticmethod
    def _generate_otp() -> str:
        """Generate numeric OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(CustomerAuthService.OTP_LENGTH))

    @staticmethod
    def _generate_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def _send_otp(phone: str, otp: str) -> bool:
        """
        Send OTP via SMS or WhatsApp

        Cameroon Market: Integrate with local SMS/WhatsApp providers
        In production, implement actual SMS/WhatsApp integration
        """
        try:
            # TODO: Integrate with SMS/WhatsApp service
            # For now, log the OTP for testing
            logger.info(
                "OTP generated",
                extra={'phone': phone, 'otp': otp}
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send OTP",
                extra={'phone': phone, 'error': str(e)},
                exc_info=True
            )
            return False

    @staticmethod
    def _create_session(customer: Customer) -> str:
        """Create customer session"""
        session_token = secrets.token_urlsafe(32)
        session_key = f"{CustomerAuthService.SESSION_CACHE_PREFIX}{session_token}"

        session_data = {
            'customer_id': str(customer.id),
            'workspace_id': str(customer.workspace_id),
            'phone': customer.phone,
            'created_at': timezone.now().isoformat(),
            'expires_at': timezone.now().timestamp() + (24 * 60 * 60)  # 24 hours
        }

        cache.set(session_key, session_data, 24 * 60 * 60)
        return session_token

    @staticmethod
    def _format_customer_for_auth(customer: Customer) -> Dict[str, Any]:
        """Format customer data for authentication responses"""
        return {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'customer_type': customer.customer_type,
            'is_verified': customer.is_verified,
            'total_orders': customer.total_orders,
            'total_spent': float(customer.total_spent),
            'first_order_at': customer.first_order_at.isoformat() if customer.first_order_at else None,
            'last_order_at': customer.last_order_at.isoformat() if customer.last_order_at else None
        }

    @staticmethod
    def _track_customer_created(customer: Customer, session_id: str):
        """
        Track customer_created analytics event (internal helper)

        Reliability: Never raises exceptions - graceful failure
        Performance: Non-blocking, logs errors only

        Args:
            customer: Customer instance
            session_id: Session ID (string or UUID)
        """
        try:
            from workspace.analytics.services.event_tracking_service import EventTrackingService

            # Convert session_id to UUID if string (validate format)
            try:
                if isinstance(session_id, str):
                    session_uuid = UUID(session_id)
                else:
                    session_uuid = session_id
            except (ValueError, AttributeError) as e:
                logger.warning(
                    "Invalid session_id format for analytics",
                    extra={'session_id': session_id, 'error': str(e)}
                )
                return

            # Initialize tracker
            tracker = EventTrackingService(customer.workspace)

            # Track event (PRO tier - gated inside EventTrackingService)
            tracker.track_customer_created(
                session_id=session_uuid,
                customer_id=customer.id,
                is_first_order=False
            )

        except Exception as e:
            # Log but never crash signup
            logger.warning(
                "Analytics tracking failed for customer_created",
                extra={
                    'customer_id': str(customer.id),
                    'session_id': session_id,
                    'error': str(e)
                }
            )


# Global instance for easy access
customer_auth_service = CustomerAuthService()