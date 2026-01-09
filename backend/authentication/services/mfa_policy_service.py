"""
Enterprise MFA Policy Service - 2025 Security Standards
Handles MFA enforcement, progressive enrollment, and compliance policies
"""
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
from ..models import User, TOTPDevice, SecurityEvent
from .security_service import SecurityService
import logging

logger = logging.getLogger(__name__)


class MFAPolicyService:
    """Enterprise MFA policy management and enforcement"""
    
    # Policy configuration constants
    ENFORCEMENT_LEVELS = {
        'none': 0,
        'recommended': 1,
        'encouraged': 2,
        'required_grace': 3,
        'required_strict': 4,
    }
    
    USER_RISK_LEVELS = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4,
    }
    
    @staticmethod
    def get_user_mfa_policy(user):
        """
        Get comprehensive MFA policy for user based on multiple factors
        
        Args:
            user: User instance
            
        Returns:
            dict: MFA policy configuration
        """
        try:
            # Calculate user risk level
            risk_level = MFAPolicyService._calculate_user_risk_level(user)
            
            # Determine enforcement level
            enforcement_level = MFAPolicyService._determine_enforcement_level(user, risk_level)
            
            # Get policy details
            policy = MFAPolicyService._build_policy_response(user, enforcement_level, risk_level)
            
            return policy
            
        except Exception as e:
            logger.error(f"MFA policy error for user {user.id}: {str(e)}")
            return MFAPolicyService._get_default_policy()
    
    @staticmethod
    def _calculate_user_risk_level(user):
        """Calculate user risk level based on multiple factors"""
        risk_score = 0
        factors = []
        
        # Account privileges (highest risk factor)
        if user.is_superuser:
            risk_score += 40
            factors.append('superuser_access')
        elif user.is_staff:
            risk_score += 30
            factors.append('staff_access')
        
        # Subscription type
        if hasattr(user, 'subscription') and user.subscription:
            sub_type = user.subscription.subscription_type
            if sub_type == 'enterprise':
                risk_score += 25
                factors.append('enterprise_account')
            elif sub_type == 'business':
                risk_score += 20
                factors.append('business_account')
        
        # Account age (newer accounts are higher risk)
        if hasattr(user, 'date_joined'):
            account_age_days = (timezone.now() - user.date_joined).days
            if account_age_days < 30:
                risk_score += 15
                factors.append('new_account')
            elif account_age_days < 90:
                risk_score += 10
                factors.append('recent_account')
        
        # Recent security events
        recent_events = SecurityEvent.objects.filter(
            user=user,
            risk_level__in=['medium', 'high'],
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        if recent_events >= 5:
            risk_score += 20
            factors.append('recent_security_events')
        elif recent_events >= 2:
            risk_score += 10
            factors.append('some_security_events')
        
        # Data access patterns (simulated - would integrate with actual usage)
        # This could check workspace access, template usage, etc.
        if MFAPolicyService._has_sensitive_data_access(user):
            risk_score += 15
            factors.append('sensitive_data_access')
        
        # Determine risk level
        if risk_score >= 70:
            level = 'critical'
        elif risk_score >= 50:
            level = 'high'
        elif risk_score >= 30:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'level': level,
            'score': risk_score,
            'factors': factors,
            'calculated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def _determine_enforcement_level(user, risk_assessment):
        """Determine MFA enforcement level based on user and risk"""
        risk_level = risk_assessment['level']
        risk_score = risk_assessment['score']
        
        # Critical risk users - strict enforcement
        if risk_level == 'critical' or user.is_superuser:
            return {
                'level': 'required_strict',
                'grace_period_days': 0,
                'enforcement_date': timezone.now(),
                'reason': 'Critical access requires immediate MFA'
            }
        
        # High risk users - required with short grace
        if risk_level == 'high' or user.is_staff:
            return {
                'level': 'required_grace',
                'grace_period_days': 7,
                'enforcement_date': timezone.now() + timedelta(days=7),
                'reason': 'High-risk account requires MFA within 7 days'
            }
        
        # Enterprise/Business accounts - encouraged with longer grace
        if (hasattr(user, 'subscription') and user.subscription and 
            user.subscription.subscription_type in ['enterprise', 'business']):
            return {
                'level': 'encouraged',
                'grace_period_days': 30,
                'enforcement_date': timezone.now() + timedelta(days=30),
                'reason': 'Business accounts strongly encouraged to enable MFA'
            }
        
        # Medium risk - recommended
        if risk_level == 'medium':
            return {
                'level': 'recommended',
                'grace_period_days': None,
                'enforcement_date': None,
                'reason': 'MFA recommended for enhanced security'
            }
        
        # Low risk - optional
        return {
            'level': 'none',
            'grace_period_days': None,
            'enforcement_date': None,
            'reason': 'MFA optional for this account type'
        }
    
    @staticmethod
    def _build_policy_response(user, enforcement, risk_assessment):
        """Build comprehensive policy response"""
        # Check current MFA status
        mfa_enabled = TOTPDevice.objects.filter(
            user=user, 
            is_active=True, 
            is_confirmed=True
        ).exists()
        
        # Calculate compliance status
        compliance_status = MFAPolicyService._calculate_compliance_status(
            enforcement, mfa_enabled
        )
        
        # Generate recommendations
        recommendations = MFAPolicyService._generate_recommendations(
            user, enforcement, risk_assessment, mfa_enabled
        )
        
        # Calculate enrollment prompts
        enrollment_prompts = MFAPolicyService._calculate_enrollment_prompts(
            user, enforcement, mfa_enabled
        )
        
        return {
            'user_id': str(user.id),
            'mfa_enabled': mfa_enabled,
            'risk_assessment': risk_assessment,
            'enforcement': enforcement,
            'compliance': compliance_status,
            'recommendations': recommendations,
            'enrollment_prompts': enrollment_prompts,
            'policy_version': '2025.1',
            'calculated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def _calculate_compliance_status(enforcement, mfa_enabled):
        """Calculate compliance status"""
        level = enforcement['level']
        grace_period = enforcement.get('grace_period_days')
        enforcement_date = enforcement.get('enforcement_date')
        
        if level in ['required_strict', 'required_grace']:
            if mfa_enabled:
                return {
                    'status': 'compliant',
                    'message': 'MFA requirement satisfied',
                    'action_required': False
                }
            else:
                # Check if still in grace period
                if (level == 'required_grace' and enforcement_date and 
                    timezone.now() < enforcement_date):
                    days_remaining = (enforcement_date - timezone.now()).days
                    return {
                        'status': 'grace_period',
                        'message': f'MFA required in {days_remaining} days',
                        'action_required': True,
                        'days_remaining': days_remaining
                    }
                else:
                    return {
                        'status': 'non_compliant',
                        'message': 'MFA is required but not enabled',
                        'action_required': True
                    }
        
        elif level == 'encouraged':
            return {
                'status': 'encouraged' if not mfa_enabled else 'compliant',
                'message': 'MFA strongly encouraged' if not mfa_enabled else 'MFA enabled',
                'action_required': not mfa_enabled
            }
        
        else:
            return {
                'status': 'optional',
                'message': 'MFA is optional for this account',
                'action_required': False
            }
    
    @staticmethod
    def _generate_recommendations(user, enforcement, risk_assessment, mfa_enabled):
        """Generate personalized MFA recommendations"""
        recommendations = []
        
        if not mfa_enabled:
            # Primary recommendation - enable MFA
            priority = 'high' if enforcement['level'] in ['required_strict', 'required_grace'] else 'medium'
            recommendations.append({
                'type': 'enable_mfa',
                'priority': priority,
                'title': 'Enable Multi-Factor Authentication',
                'description': 'Secure your account with TOTP-based MFA',
                'action': 'setup_totp',
                'estimated_time': '2 minutes'
            })
            
            # Risk-based additional recommendations
            if risk_assessment['level'] in ['high', 'critical']:
                recommendations.append({
                    'type': 'security_review',
                    'priority': 'medium',
                    'title': 'Review Account Security',
                    'description': 'Your account has elevated risk factors',
                    'action': 'security_review',
                    'estimated_time': '5 minutes'
                })
        
        else:
            # Maintenance recommendations for MFA-enabled users
            recommendations.append({
                'type': 'backup_codes',
                'priority': 'low',
                'title': 'Verify Backup Codes',
                'description': 'Ensure you have secure backup codes stored',
                'action': 'check_backup_codes',
                'estimated_time': '1 minute'
            })
        
        # Additional security recommendations
        if user.is_staff or user.is_superuser:
            recommendations.append({
                'type': 'admin_security',
                'priority': 'high',
                'title': 'Administrative Security Review',
                'description': 'Review security settings for privileged account',
                'action': 'admin_security_check',
                'estimated_time': '10 minutes'
            })
        
        return recommendations
    
    @staticmethod
    def _calculate_enrollment_prompts(user, enforcement, mfa_enabled):
        """Calculate when and how to prompt for MFA enrollment"""
        if mfa_enabled:
            return {
                'should_prompt': False,
                'prompt_type': 'none',
                'message': None
            }
        
        level = enforcement['level']
        
        if level == 'required_strict':
            return {
                'should_prompt': True,
                'prompt_type': 'blocking',
                'message': 'MFA is required to continue using this account',
                'frequency': 'every_login'
            }
        
        elif level == 'required_grace':
            grace_end = enforcement.get('enforcement_date')
            if grace_end:
                days_remaining = (grace_end - timezone.now()).days
                if days_remaining <= 3:
                    prompt_type = 'urgent'
                    frequency = 'every_login'
                elif days_remaining <= 7:
                    prompt_type = 'important'
                    frequency = 'daily'
                else:
                    prompt_type = 'normal'
                    frequency = 'weekly'
                
                return {
                    'should_prompt': True,
                    'prompt_type': prompt_type,
                    'message': f'MFA will be required in {days_remaining} days',
                    'frequency': frequency,
                    'days_remaining': days_remaining
                }
        
        elif level == 'encouraged':
            return {
                'should_prompt': True,
                'prompt_type': 'gentle',
                'message': 'Enhance your account security with MFA',
                'frequency': 'weekly'
            }
        
        elif level == 'recommended':
            return {
                'should_prompt': True,
                'prompt_type': 'subtle',
                'message': 'Consider enabling MFA for better security',
                'frequency': 'monthly'
            }
        
        return {
            'should_prompt': False,
            'prompt_type': 'none',
            'message': None
        }
    
    @staticmethod
    def _has_sensitive_data_access(user):
        """Check if user has access to sensitive data (placeholder)"""
        # This would integrate with workspace/template access patterns
        # For now, simulate based on user type
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if user has enterprise subscription
        if hasattr(user, 'subscription') and user.subscription:
            return user.subscription.subscription_type in ['enterprise', 'business']
        
        return False
    
    @staticmethod
    def _get_default_policy():
        """Get default policy for error cases"""
        return {
            'mfa_enabled': False,
            'risk_assessment': {'level': 'medium', 'score': 30, 'factors': []},
            'enforcement': {
                'level': 'recommended',
                'grace_period_days': None,
                'enforcement_date': None,
                'reason': 'Default policy'
            },
            'compliance': {
                'status': 'optional',
                'message': 'MFA is optional',
                'action_required': False
            },
            'recommendations': [],
            'enrollment_prompts': {
                'should_prompt': False,
                'prompt_type': 'none',
                'message': None
            },
            'policy_version': '2025.1',
            'error': 'Unable to calculate full policy'
        }
    
    @staticmethod
    def should_block_access(user):
        """
        Determine if user access should be blocked due to MFA non-compliance
        
        Args:
            user: User instance
            
        Returns:
            tuple: (should_block: bool, reason: str)
        """
        try:
            policy = MFAPolicyService.get_user_mfa_policy(user)
            
            enforcement_level = policy['enforcement']['level']
            compliance_status = policy['compliance']['status']
            
            # Block access for required strict and non-compliant users
            if (enforcement_level == 'required_strict' and 
                compliance_status == 'non_compliant'):
                return True, "MFA is required for this account"
            
            # Block access for required grace period that has expired
            if (enforcement_level == 'required_grace' and 
                compliance_status == 'non_compliant'):
                return True, "MFA grace period has expired"
            
            return False, None
            
        except Exception as e:
            logger.error(f"MFA access check error for user {user.id}: {str(e)}")
            # Fail open for error cases (don't block access)
            return False, None
    
    @staticmethod
    def log_policy_event(user, event_type, details=None):
        """Log MFA policy-related events for audit"""
        try:
            SecurityEvent.log_event(
                event_type=f'mfa_policy_{event_type}',
                user=user,
                description=f'MFA policy event: {event_type}',
                risk_level=1,
                metadata={
                    'policy_event': event_type,
                    'details': details or {},
                    'policy_version': '2025.1'
                }
            )
        except Exception as e:
            logger.error(f"Policy event logging error: {str(e)}")
    
    @staticmethod
    def get_organization_mfa_stats():
        """Get organization-wide MFA adoption statistics (admin feature)"""
        try:
            total_users = User.objects.filter(is_active=True).count()
            mfa_enabled_users = User.objects.filter(
                totp_device__is_confirmed=True,
                totp_device__is_active=True,
                is_active=True
            ).distinct().count()
            
            # Calculate stats by risk level
            risk_stats = {}
            for user in User.objects.filter(is_active=True):
                policy = MFAPolicyService.get_user_mfa_policy(user)
                risk_level = policy['risk_assessment']['level']
                
                if risk_level not in risk_stats:
                    risk_stats[risk_level] = {'total': 0, 'mfa_enabled': 0}
                
                risk_stats[risk_level]['total'] += 1
                if policy['mfa_enabled']:
                    risk_stats[risk_level]['mfa_enabled'] += 1
            
            return {
                'total_users': total_users,
                'mfa_enabled_users': mfa_enabled_users,
                'adoption_rate': (mfa_enabled_users / total_users * 100) if total_users > 0 else 0,
                'risk_level_stats': risk_stats,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Organization MFA stats error: {str(e)}")
            return {'error': str(e)}