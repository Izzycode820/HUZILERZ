"""
Enterprise MFA Service Layer - 2025 Security Standards
Handles TOTP devices, backup codes, and MFA enforcement policies
"""
import io
import base64
import pyotp
import qrcode
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from ..models import User, TOTPDevice, BackupCode, SecurityEvent
from .security_service import SecurityService
import logging

logger = logging.getLogger(__name__)


class MFAService:
    """Enterprise MFA service with comprehensive security features"""
    
    @staticmethod
    def setup_totp_device(user, device_name="Authenticator App", force_reset=False):
        """
        Set up TOTP device for user with QR code generation
        
        Args:
            user: User instance
            device_name: Human-readable device name
            force_reset: Force reset existing device
            
        Returns:
            dict: Contains device info, QR code, and setup instructions
        """
        try:
            # Check for existing device
            existing_device = TOTPDevice.objects.filter(user=user).first()
            
            if existing_device and not force_reset:
                if existing_device.is_confirmed:
                    return {
                        'success': False,
                        'message': 'TOTP device already configured',
                        'device_status': 'active'
                    }
                else:
                    # Use existing unconfirmed device
                    device = existing_device
            else:
                # Create new device (or replace existing)
                if existing_device:
                    existing_device.delete()
                
                # Generate secure secret
                secret_key = TOTPDevice.generate_secure_secret()
                
                device = TOTPDevice.objects.create(
                    user=user,
                    name=device_name,
                    secret_key=secret_key,
                    account_name=user.email,
                    is_active=True,
                    is_confirmed=False
                )
            
            # Generate QR code
            qr_code_url = device.generate_qr_code_url()
            qr_img = qrcode.make(qr_code_url, box_size=10, border=4)
            
            # Convert QR code to base64 for API response
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Log security event
            SecurityEvent.log_event(
                event_type='totp_setup_initiated',
                user=user,
                description=f'TOTP device setup initiated: {device_name}',
                risk_level=1,
                metadata={
                    'device_id': str(device.id),
                    'device_name': device_name,
                    'force_reset': force_reset
                }
            )
            
            return {
                'success': True,
                'device_id': str(device.id),
                'device_name': device.name,
                'qr_code_url': qr_code_url,
                'qr_code_base64': f"data:image/png;base64,{qr_code_base64}",
                'manual_entry_key': device.secret_key,
                'issuer': device.issuer_name,
                'account_name': device.account_name,
                'setup_instructions': {
                    'step1': 'Install an authenticator app (Google Authenticator, Authy, etc.)',
                    'step2': 'Scan the QR code or manually enter the setup key',
                    'step3': 'Enter the 6-digit code from your app to confirm setup'
                }
            }
            
        except Exception as e:
            logger.error(f"TOTP setup error for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to setup TOTP device',
                'error': str(e)
            }
    
    @staticmethod
    def confirm_totp_device(user, token, ip_address=None):
        """
        Confirm TOTP device setup by verifying token
        
        Args:
            user: User instance
            token: 6-digit TOTP token
            ip_address: Client IP for audit
            
        Returns:
            dict: Confirmation result with backup codes
        """
        try:
            device = TOTPDevice.objects.filter(user=user, is_confirmed=False).first()
            
            if not device:
                return {
                    'success': False,
                    'message': 'No pending TOTP device setup found'
                }
            
            # Verify token
            is_valid, message = device.verify_token(token, ip_address)
            
            if is_valid:
                # Confirm device
                device.is_confirmed = True
                device.activated_at = timezone.now()
                device.save(update_fields=['is_confirmed', 'activated_at'])
                
                # Generate backup codes
                backup_codes, raw_codes = BackupCode.generate_codes_for_user(user, count=10)
                
                # Log security event
                SecurityEvent.log_event(
                    event_type='totp_device_confirmed',
                    user=user,
                    description=f'TOTP device confirmed and activated: {device.name}',
                    risk_level=1,
                    ip_address=ip_address,
                    metadata={
                        'device_id': str(device.id),
                        'backup_codes_generated': len(raw_codes)
                    }
                )
                
                return {
                    'success': True,
                    'message': 'TOTP device confirmed successfully',
                    'device_confirmed': True,
                    'backup_codes': raw_codes,
                    'backup_codes_info': {
                        'count': len(raw_codes),
                        'expiration_days': 90,
                        'single_use': True,
                        'storage_warning': 'Store these codes securely. Each can only be used once.'
                    }
                }
            else:
                return {
                    'success': False,
                    'message': message,
                    'device_confirmed': False
                }
                
        except Exception as e:
            logger.error(f"TOTP confirmation error for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to confirm TOTP device',
                'error': str(e)
            }
    
    @staticmethod
    def verify_mfa_token(user, token, ip_address=None, user_agent=""):
        """
        Verify MFA token (TOTP or backup code)
        
        Args:
            user: User instance
            token: TOTP token or backup code
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            dict: Verification result
        """
        try:
            # First try TOTP verification
            totp_device = TOTPDevice.objects.filter(
                user=user, 
                is_active=True, 
                is_confirmed=True
            ).first()
            
            if totp_device:
                is_valid, message = totp_device.verify_token(token, ip_address)
                if is_valid:
                    return {
                        'success': True,
                        'method': 'totp',
                        'message': 'TOTP token verified successfully'
                    }
            
            # Try backup code verification
            backup_codes = BackupCode.objects.filter(
                user=user,
                status=BackupCode.UNUSED
            ).order_by('-created_at')
            
            for backup_code in backup_codes:
                is_valid, message = backup_code.verify_code(token, ip_address, user_agent)
                if is_valid:
                    return {
                        'success': True,
                        'method': 'backup_code',
                        'message': 'Backup code verified successfully',
                        'remaining_codes': BackupCode.objects.filter(
                            user=user, 
                            status=BackupCode.UNUSED
                        ).count()
                    }
            
            # Log failed MFA attempt
            SecurityEvent.log_event(
                event_type='mfa_verification_failed',
                user=user,
                description='Failed MFA token verification',
                risk_level='medium',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'token_length': len(token)}
            )
            
            return {
                'success': False,
                'message': 'Invalid MFA token',
                'method': None
            }
            
        except Exception as e:
            logger.error(f"MFA verification error for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'MFA verification failed',
                'error': str(e)
            }
    
    @staticmethod
    def regenerate_backup_codes(user, ip_address=None, user_agent=""):
        """
        Regenerate backup codes for user
        
        Args:
            user: User instance
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            dict: New backup codes
        """
        try:
            # Check if user has confirmed TOTP device
            if not TOTPDevice.objects.filter(
                user=user, 
                is_confirmed=True, 
                is_active=True
            ).exists():
                return {
                    'success': False,
                    'message': 'TOTP device must be configured first'
                }
            
            # Generate new backup codes
            backup_codes, raw_codes = BackupCode.generate_codes_for_user(user, count=10)
            
            # Log security event
            SecurityEvent.log_event(
                event_type='backup_codes_regenerated',
                user=user,
                description='Backup codes regenerated',
                risk_level=1,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'codes_generated': len(raw_codes)}
            )
            
            return {
                'success': True,
                'backup_codes': raw_codes,
                'codes_generated': len(raw_codes),
                'expiration_days': 90,
                'message': 'New backup codes generated successfully'
            }
            
        except Exception as e:
            logger.error(f"Backup code regeneration error for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to regenerate backup codes',
                'error': str(e)
            }
    
    @staticmethod
    def get_mfa_status(user):
        """
        Get comprehensive MFA status for user
        
        Args:
            user: User instance
            
        Returns:
            dict: MFA status and configuration
        """
        try:
            totp_device = TOTPDevice.objects.filter(user=user).first()
            
            # Get backup codes stats
            backup_codes_stats = {
                'total': BackupCode.objects.filter(user=user).count(),
                'unused': BackupCode.objects.filter(user=user, status=BackupCode.UNUSED).count(),
                'used': BackupCode.objects.filter(user=user, status=BackupCode.USED).count(),
                'expired': BackupCode.objects.filter(user=user, status=BackupCode.EXPIRED).count(),
            }
            
            # MFA enforcement check
            enforcement_policy = MFAService._get_mfa_enforcement_policy(user)
            
            status = {
                'mfa_enabled': bool(totp_device and totp_device.is_confirmed),
                'totp_device': None,
                'backup_codes': backup_codes_stats,
                'enforcement': enforcement_policy,
                'security_score': MFAService._calculate_mfa_security_score(user)
            }
            
            if totp_device:
                status['totp_device'] = {
                    'id': str(totp_device.id),
                    'name': totp_device.name,
                    'is_active': totp_device.is_active,
                    'is_confirmed': totp_device.is_confirmed,
                    'is_locked': totp_device.is_locked,
                    'created_at': totp_device.created_at.isoformat(),
                    'last_used': totp_device.last_used.isoformat() if totp_device.last_used else None,
                    'failure_count': totp_device.failure_count,
                    'total_verifications': totp_device.total_verifications,
                    'lockout_until': totp_device.lockout_until.isoformat() if totp_device.lockout_until else None
                }
            
            return status
            
        except Exception as e:
            logger.error(f"MFA status error for user {user.id}: {str(e)}")
            return {
                'mfa_enabled': False,
                'error': str(e)
            }
    
    @staticmethod
    def disable_mfa(user, confirmation_token, ip_address=None, user_agent=""):
        """
        Disable MFA for user with security confirmation
        
        Args:
            user: User instance
            confirmation_token: Current MFA token for confirmation
            ip_address: Client IP for audit
            user_agent: Client user agent
            
        Returns:
            dict: Disable result
        """
        try:
            # Verify current MFA token first
            verification_result = MFAService.verify_mfa_token(
                user, confirmation_token, ip_address, user_agent
            )
            
            if not verification_result['success']:
                return {
                    'success': False,
                    'message': 'Current MFA token required to disable MFA'
                }
            
            # Disable TOTP device
            totp_device = TOTPDevice.objects.filter(user=user).first()
            if totp_device:
                totp_device.is_active = False
                totp_device.is_confirmed = False
                totp_device.save()
            
            # Revoke all backup codes
            BackupCode.objects.filter(
                user=user, 
                status=BackupCode.UNUSED
            ).update(
                status=BackupCode.REVOKED,
                revoked_at=timezone.now(),
                revoked_reason="MFA disabled by user"
            )
            
            # Log critical security event
            SecurityEvent.log_event(
                event_type='mfa_disabled',
                user=user,
                description='MFA disabled by user request',
                risk_level='high',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'verification_method': verification_result['method']}
            )
            
            return {
                'success': True,
                'message': 'MFA disabled successfully',
                'security_warning': 'Your account security has been reduced. Consider re-enabling MFA.'
            }
            
        except Exception as e:
            logger.error(f"MFA disable error for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to disable MFA',
                'error': str(e)
            }
    
    @staticmethod
    def _get_mfa_enforcement_policy(user):
        """Get MFA enforcement policy for user"""
        # Enterprise accounts require MFA
        if hasattr(user, 'subscription') and user.subscription:
            if user.subscription.subscription_type in ['enterprise', 'business']:
                return {
                    'required': True,
                    'reason': 'Enterprise subscription requires MFA',
                    'grace_period_days': 7
                }
        
        # High-value accounts (based on activity/data)
        if user.is_staff or user.is_superuser:
            return {
                'required': True,
                'reason': 'Administrative accounts require MFA',
                'grace_period_days': 0
            }
        
        return {
            'required': False,
            'reason': 'MFA recommended for enhanced security',
            'grace_period_days': None
        }
    
    @staticmethod
    def _calculate_mfa_security_score(user):
        """Calculate MFA security score (0-100)"""
        score = 0
        
        # Base score for having MFA
        totp_device = TOTPDevice.objects.filter(user=user, is_confirmed=True).first()
        if totp_device:
            score += 60
            
            # Bonus for recent usage
            if totp_device.last_used and totp_device.last_used >= timezone.now() - timezone.timedelta(days=30):
                score += 10
            
            # Penalty for failures
            if totp_device.failure_count > 0:
                score -= min(totp_device.failure_count, 10)
        
        # Backup codes coverage
        unused_codes = BackupCode.objects.filter(user=user, status=BackupCode.UNUSED).count()
        if unused_codes >= 8:
            score += 20
        elif unused_codes >= 5:
            score += 10
        
        # Account age and activity bonus
        if hasattr(user, 'date_joined'):
            account_age_days = (timezone.now() - user.date_joined).days
            if account_age_days > 90:
                score += 10
        
        return min(max(score, 0), 100)  # Clamp between 0-100
    
    @staticmethod
    def cleanup_expired_devices():
        """Cleanup expired MFA devices and codes"""
        try:
            # Cleanup expired backup codes
            expired_count = BackupCode.cleanup_expired_codes()
            
            # Unlock devices past lockout period
            unlocked_count = 0
            locked_devices = TOTPDevice.objects.filter(
                is_locked=True,
                lockout_until__lt=timezone.now()
            )
            
            for device in locked_devices:
                if device.unlock_device():
                    unlocked_count += 1
            
            logger.info(f"MFA cleanup: {expired_count} codes expired, {unlocked_count} devices unlocked")
            
            return {
                'expired_codes': expired_count,
                'unlocked_devices': unlocked_count
            }
            
        except Exception as e:
            logger.error(f"MFA cleanup error: {str(e)}")
            return {'error': str(e)}