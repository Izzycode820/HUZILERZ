"""
Enterprise Email Service - 2025 Security Standards
Handles email OTP verification, password reset, and email-based authentication
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from ..models import EmailVerificationCode, PasswordResetToken, SecurityEvent
from .security_service import SecurityService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailService:
    """Enterprise email service for authentication and verification"""
    
    @staticmethod
    def send_verification_email(email, code_type, verification_code, raw_code, request=None):
        """
        Send email verification code to user
        
        Args:
            email: Recipient email address
            code_type: Type of verification (account_verification, login_verification, etc.)
            verification_code: EmailVerificationCode instance
            raw_code: Plain text verification code
            request: HTTP request for context
            
        Returns:
            dict: Email sending result
        """
        try:
            # Get email template and subject based on code type
            template_info = EmailService._get_email_template_info(code_type)
            
            # Prepare email context
            context = {
                'code': raw_code,
                'email': email,
                'expires_minutes': int((verification_code.expires_at - verification_code.created_at).total_seconds() / 60),
                'code_type_display': verification_code.get_code_type_display(),
                'site_name': getattr(settings, 'SITE_NAME', 'HustlerzCamp'),
                'site_url': getattr(settings, 'SITE_URL', 'https://hustlerz.camp'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@hustlerz.camp'),
                'verification_id': str(verification_code.id),
            }
            
            # Render email templates
            html_message = render_to_string(template_info['html_template'], context)
            plain_message = render_to_string(template_info['text_template'], context)
            
            # Send email
            send_mail(
                subject=template_info['subject'],
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hustlerz.camp'),
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log email sent event
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            SecurityEvent.log_event(
                event_type='verification_email_sent',
                user=verification_code.user,
                description=f'Verification email sent: {code_type}',
                risk_level=1,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'email': email,
                    'code_type': code_type,
                    'verification_id': str(verification_code.id)
                }
            )
            
            return {
                'success': True,
                'message': f'Verification code sent to {email}',
                'verification_id': str(verification_code.id)
            }
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to send verification email',
                'error': str(e)
            }
    
    @staticmethod
    def send_password_reset_email(user, reset_token, raw_token, request=None):
        """
        Send password reset email to user
        
        Args:
            user: User instance
            reset_token: PasswordResetToken instance
            raw_token: Plain text reset token
            request: HTTP request for context
            
        Returns:
            dict: Email sending result
        """
        try:
            # Prepare reset URL
            reset_url = f"{getattr(settings, 'FRONTEND_URL', 'https://hustlerz.camp')}/reset-password?token={raw_token}"
            
            # Email context
            context = {
                'user': user,
                'reset_url': reset_url,
                'token': raw_token,
                'expires_hours': int((reset_token.expires_at - reset_token.created_at).total_seconds() / 3600),
                'site_name': getattr(settings, 'SITE_NAME', 'HustlerzCamp'),
                'site_url': getattr(settings, 'SITE_URL', 'https://hustlerz.camp'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@hustlerz.camp'),
                'reset_id': str(reset_token.id),
            }
            
            # Render email templates
            html_message = render_to_string('emails/password_reset.html', context)
            plain_message = render_to_string('emails/password_reset.txt', context)
            
            # Send email
            send_mail(
                subject=f'{context["site_name"]} - Password Reset Request',
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hustlerz.camp'),
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log email sent event
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            SecurityEvent.log_event(
                event_type='password_reset_email_sent',
                user=user,
                description='Password reset email sent',
                risk_level='medium',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'reset_id': str(reset_token.id),
                    'email': user.email
                }
            )
            
            return {
                'success': True,
                'message': f'Password reset instructions sent to {user.email}',
                'reset_id': str(reset_token.id)
            }
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to send password reset email',
                'error': str(e)
            }
    
    @staticmethod
    def send_password_changed_notification(user, request=None):
        """
        Send notification when password is successfully changed
        
        Args:
            user: User instance
            request: HTTP request for context
            
        Returns:
            dict: Email sending result
        """
        try:
            # Get client information
            ip_address = SecurityService.get_client_ip(request) if request else 'Unknown'
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown') if request else 'Unknown'
            
            # Email context
            context = {
                'user': user,
                'change_time': user.date_joined,  # This would be the actual change time
                'ip_address': ip_address,
                'user_agent': user_agent,
                'site_name': getattr(settings, 'SITE_NAME', 'HustlerzCamp'),
                'site_url': getattr(settings, 'SITE_URL', 'https://hustlerz.camp'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@hustlerz.camp'),
            }
            
            # Render email templates
            html_message = render_to_string('emails/password_changed.html', context)
            plain_message = render_to_string('emails/password_changed.txt', context)
            
            # Send email
            send_mail(
                subject=f'{context["site_name"]} - Password Changed Successfully',
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hustlerz.camp'),
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return {
                'success': True,
                'message': f'Password change notification sent to {user.email}'
            }
            
        except Exception as e:
            logger.error(f"Failed to send password changed notification to {user.email}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to send password change notification',
                'error': str(e)
            }
    
    @staticmethod
    def request_email_verification(email, code_type, user=None, request=None):
        """
        Request email verification code with rate limiting
        
        Args:
            email: Email address to verify
            code_type: Type of verification code
            user: User instance (optional)
            request: HTTP request for audit
            
        Returns:
            dict: Verification request result
        """
        try:
            # Check rate limiting
            rate_limit_status = EmailVerificationCode.get_user_rate_limit_status(email, code_type)
            
            if rate_limit_status['is_rate_limited']:
                return {
                    'success': False,
                    'message': 'Too many verification attempts. Please try again later.',
                    'rate_limited': True,
                    'cooldown_until': rate_limit_status['cooldown_until'].isoformat()
                }
            
            # Get client info for audit
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            # Set expiration based on code type
            expires_minutes = {
                EmailVerificationCode.ACCOUNT_VERIFICATION: 30,
                EmailVerificationCode.PASSWORD_RESET: 15,
                EmailVerificationCode.EMAIL_CHANGE: 15,
                EmailVerificationCode.LOGIN_VERIFICATION: 10,
            }.get(code_type, 10)
            
            # Create verification code
            verification_code, raw_code = EmailVerificationCode.create_verification_code(
                email=email,
                code_type=code_type,
                user=user,
                expires_minutes=expires_minutes,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Send verification email
            email_result = EmailService.send_verification_email(
                email=email,
                code_type=code_type,
                verification_code=verification_code,
                raw_code=raw_code,
                request=request
            )
            
            if email_result['success']:
                return {
                    'success': True,
                    'message': f'Verification code sent to {email}',
                    'verification_id': str(verification_code.id),
                    'expires_in_minutes': expires_minutes,
                    'code_type': code_type
                }
            else:
                # If email sending failed, revoke the code
                verification_code.revoke('Email sending failed')
                return email_result
            
        except Exception as e:
            logger.error(f"Email verification request error for {email}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to process verification request',
                'error': str(e)
            }
    
    @staticmethod
    def verify_email_code(email, code_type, raw_code, request=None):
        """
        Verify email verification code
        
        Args:
            email: Email address
            code_type: Type of verification code
            raw_code: Raw verification code
            request: HTTP request for audit
            
        Returns:
            dict: Verification result
        """
        try:
            # Find pending verification code
            verification_code = EmailVerificationCode.objects.filter(
                email=email,
                code_type=code_type,
                status=EmailVerificationCode.PENDING
            ).order_by('-created_at').first()
            
            if not verification_code:
                return {
                    'success': False,
                    'message': 'No pending verification code found for this email'
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
            logger.error(f"Email code verification error for {email}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to verify email code',
                'error': str(e)
            }
    
    @staticmethod
    def request_password_reset(email, request=None):
        """
        Request password reset for user
        
        Args:
            email: User email address
            request: HTTP request for audit
            
        Returns:
            dict: Password reset request result
        """
        try:
            # Find user by email
            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                # For security, don't reveal if email exists
                return {
                    'success': True,
                    'message': 'If an account with this email exists, password reset instructions will be sent.'
                }
            
            # Check rate limiting for password reset requests
            rate_limit_status = EmailVerificationCode.get_user_rate_limit_status(
                email, EmailVerificationCode.PASSWORD_RESET, time_window_minutes=60
            )
            
            if rate_limit_status['is_rate_limited']:
                return {
                    'success': False,
                    'message': 'Too many password reset attempts. Please try again later.',
                    'rate_limited': True
                }
            
            # Get client info for audit
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            # Create password reset token
            reset_token, raw_token = PasswordResetToken.create_reset_token(
                user=user,
                expires_hours=24,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Send reset email
            email_result = EmailService.send_password_reset_email(
                user=user,
                reset_token=reset_token,
                raw_token=raw_token,
                request=request
            )
            
            if email_result['success']:
                return {
                    'success': True,
                    'message': 'Password reset instructions sent to your email address.',
                    'reset_id': str(reset_token.id)
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to send password reset email. Please try again.'
                }
            
        except Exception as e:
            logger.error(f"Password reset request error for {email}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to process password reset request',
                'error': str(e)
            }
    
    @staticmethod
    def reset_password_with_token(token, new_password, request=None):
        """
        Reset user password using reset token
        
        Args:
            token: Password reset token (raw token string)
            new_password: New password
            request: HTTP request for audit
            
        Returns:
            dict: Password reset result
        """
        try:
            # Get client info for audit
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            # Find valid reset tokens (not used, not expired)
            # We need to iterate through them since we can't query by raw token
            valid_tokens = PasswordResetToken.objects.filter(
                is_used=False,
                expires_at__gt=timezone.now(),
                token_hash__isnull=False
            ).select_related('user').order_by('-created_at')[:20]  # Limit to prevent abuse
            
            reset_token = None
            for candidate_token in valid_tokens:
                is_valid, message = candidate_token.verify_token(token, ip_address, user_agent)
                if is_valid:
                    reset_token = candidate_token
                    break
            
            if not reset_token:
                # Log failed attempt - no matching token found
                logger.warning(
                    f"Password reset token verification failed - no matching token, "
                    f"IP: {ip_address}"
                )
                return {
                    'success': False,
                    'message': 'Invalid or expired reset token'
                }
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            # Mark token as used
            reset_token.mark_used(ip_address, user_agent)
            
            # Send confirmation email
            EmailService.send_password_changed_notification(user, request)
            
            # Log successful password reset
            SecurityEvent.log_event(
                event_type='password_reset_completed',
                user=user,
                description='Password successfully reset using email token',
                risk_level='medium',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'reset_token_id': str(reset_token.id)
                }
            )
            
            return {
                'success': True,
                'message': 'Password reset successfully. You can now login with your new password.',
                'user_id': str(user.id)
            }
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to reset password',
                'error': str(e)
            }
    
    @staticmethod
    def _get_email_template_info(code_type):
        """Get email template information based on code type"""
        templates = {
            EmailVerificationCode.ACCOUNT_VERIFICATION: {
                'subject': 'Verify Your Account - HustlerzCamp',
                'html_template': 'emails/account_verification.html',
                'text_template': 'emails/account_verification.txt',
            },
            EmailVerificationCode.LOGIN_VERIFICATION: {
                'subject': 'Login Verification Code - HustlerzCamp',
                'html_template': 'emails/login_verification.html',
                'text_template': 'emails/login_verification.txt',
            },
            EmailVerificationCode.EMAIL_CHANGE: {
                'subject': 'Verify New Email Address - HustlerzCamp',
                'html_template': 'emails/email_change_verification.html',
                'text_template': 'emails/email_change_verification.txt',
            },
            EmailVerificationCode.PASSWORD_RESET: {
                'subject': 'Password Reset Code - HustlerzCamp',
                'html_template': 'emails/password_reset_code.html',
                'text_template': 'emails/password_reset_code.txt',
            }
        }
        
        return templates.get(code_type, templates[EmailVerificationCode.ACCOUNT_VERIFICATION])
    
    @staticmethod
    def cleanup_expired_codes_and_tokens():
        """Clean up expired verification codes and reset tokens"""
        try:
            # Cleanup expired verification codes
            expired_codes = EmailVerificationCode.cleanup_expired_codes()
            
            # Cleanup expired password reset tokens
            expired_tokens = PasswordResetToken.cleanup_expired_tokens()
            
            logger.info(f"Email cleanup: {expired_codes} codes, {expired_tokens} tokens expired")
            
            return {
                'expired_codes': expired_codes,
                'expired_tokens': expired_tokens
            }
            
        except Exception as e:
            logger.error(f"Email cleanup error: {str(e)}")
            return {'error': str(e)}