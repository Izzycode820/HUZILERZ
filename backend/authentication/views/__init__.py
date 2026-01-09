"""
Authentication Views - Modular view layer
"""
from .auth_views import login, register, refresh_token, logout
from .workspace_views import switch_workspace, leave_workspace
from .profile_views import profile, update_profile
from .session_views import active_sessions, revoke_session
from .ux_views import (
    check_auth_status, 
    mark_auth_prompt_shown, 
    dismiss_auth_prompt, 
    health_check
)
from .mfa_views import (
    setup_totp,
    confirm_totp,
    verify_mfa,
    mfa_status,
    regenerate_backup_codes,
    disable_mfa,
    backup_codes_status,
    unlock_totp_device,
    mfa_security_report
)
from .mfa_policy_views import (
    get_mfa_policy,
    check_access_compliance,
    acknowledge_mfa_prompt,
    get_enrollment_guidance,
    get_risk_assessment,
    get_organization_mfa_stats,
    get_compliance_report,
    update_policy_settings
)
from .oauth2_views import (
    initiate_oauth2_flow,
    handle_oauth2_callback,
    get_oauth2_providers,
    refresh_oauth2_token,
    test_oauth2_configuration
)
from .email_views import (
    request_email_verification,
    verify_email_code,
    request_password_reset,
    confirm_password_reset,
    request_email_change,
    confirm_email_change,
    get_email_verification_status,
    resend_verification_code,
    cleanup_expired_verifications
)
from .phone_views import (
    request_phone_verification,
    verify_phone_code as verify_phone_code_view,
    get_phone_verification_status,
    request_phone_change,
    confirm_phone_change,
    resend_phone_verification,
    check_sms_service_status
)
from .security_views import (
    security_dashboard,
    user_security_events,
    active_sessions as security_active_sessions,
    revoke_session as security_revoke_session,
    security_report,
    admin_security_overview,
    security_alerts,
    resolve_alert,
    security_health_check
)

__all__ = [
    # Authentication views
    'login',
    'register', 
    'refresh_token',
    'logout',
    # Workspace views
    'switch_workspace',
    'leave_workspace',
    # Profile views
    'profile',
    'update_profile',
    # Session views
    'active_sessions',
    'revoke_session',
    # UX views
    'check_auth_status',
    'mark_auth_prompt_shown',
    'dismiss_auth_prompt',
    'health_check',
    # MFA views
    'setup_totp',
    'confirm_totp',
    'verify_mfa',
    'mfa_status',
    'regenerate_backup_codes',
    'disable_mfa',
    'backup_codes_status',
    'unlock_totp_device',
    'mfa_security_report',
    # MFA Policy views
    'get_mfa_policy',
    'check_access_compliance',
    'acknowledge_mfa_prompt',
    'get_enrollment_guidance',
    'get_risk_assessment',
    'get_organization_mfa_stats',
    'get_compliance_report',
    'update_policy_settings',
    # OAuth2 views
    'initiate_oauth2_flow',
    'handle_oauth2_callback',
    'get_oauth2_providers',
    'refresh_oauth2_token',
    'test_oauth2_configuration',
    # Email views
    'request_email_verification',
    'verify_email_code',
    'request_password_reset',
    'confirm_password_reset',
    'request_email_change',
    'confirm_email_change',
    'get_email_verification_status',
    'resend_verification_code',
    'cleanup_expired_verifications',
    # Phone views
    'request_phone_verification',
    'verify_phone_code_view',
    'get_phone_verification_status',
    'request_phone_change',
    'confirm_phone_change',
    'resend_phone_verification',
    'check_sms_service_status',
    # Security views
    'security_dashboard',
    'user_security_events',
    'security_active_sessions',
    'security_revoke_session',
    'security_report',
    'admin_security_overview',
    'security_alerts',
    'resolve_alert',
    'security_health_check',
]