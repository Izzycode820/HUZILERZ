"""
Authentication URL Configuration for HustlerzCamp
Modern RESTful API endpoints with enterprise MFA support
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('refresh/', views.refresh_token, name='refresh_token'),

    # Workspace context management (OAuth2 token rotation pattern)
    path('workspace-switch/', views.switch_workspace, name='switch_workspace'),
    path('workspace-leave/', views.leave_workspace, name='leave_workspace'),

    # Profile management
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Session management
    path('sessions/', views.active_sessions, name='active_sessions'),
    path('sessions/revoke/', views.revoke_session, name='revoke_session'),
    
    # Multi-Factor Authentication (MFA) endpoints
    path('mfa/status/', views.mfa_status, name='mfa_status'),
    path('mfa/totp/setup/', views.setup_totp, name='setup_totp'),
    path('mfa/totp/confirm/', views.confirm_totp, name='confirm_totp'),
    path('mfa/totp/unlock/', views.unlock_totp_device, name='unlock_totp_device'),
    path('mfa/verify/', views.verify_mfa, name='verify_mfa'),
    path('mfa/disable/', views.disable_mfa, name='disable_mfa'),
    path('mfa/backup-codes/status/', views.backup_codes_status, name='backup_codes_status'),
    path('mfa/backup-codes/regenerate/', views.regenerate_backup_codes, name='regenerate_backup_codes'),
    path('mfa/security/report/', views.mfa_security_report, name='mfa_security_report'),
    
    # MFA Policy & Compliance endpoints
    path('mfa/policy/', views.get_mfa_policy, name='get_mfa_policy'),
    path('mfa/policy/check-access/', views.check_access_compliance, name='check_access_compliance'),
    path('mfa/policy/acknowledge-prompt/', views.acknowledge_mfa_prompt, name='acknowledge_mfa_prompt'),
    path('mfa/policy/enrollment-guidance/', views.get_enrollment_guidance, name='get_enrollment_guidance'),
    path('mfa/policy/risk-assessment/', views.get_risk_assessment, name='get_risk_assessment'),
    path('mfa/policy/organization-stats/', views.get_organization_mfa_stats, name='get_organization_mfa_stats'),
    path('mfa/policy/compliance-report/', views.get_compliance_report, name='get_compliance_report'),
    path('mfa/policy/settings/', views.update_policy_settings, name='update_policy_settings'),
    
    # OAuth2 Social Authentication endpoints
    path('oauth2/providers/', views.get_oauth2_providers, name='get_oauth2_providers'),
    path('oauth2/initiate/', views.initiate_oauth2_flow, name='initiate_oauth2_flow'),
    path('oauth2/callback/', views.handle_oauth2_callback, name='handle_oauth2_callback'),
    path('oauth2/refresh/', views.refresh_oauth2_token, name='refresh_oauth2_token'),
    path('oauth2/test-config/', views.test_oauth2_configuration, name='test_oauth2_configuration'),
    
    # Email-based Authentication endpoints
    path('email/verify-request/', views.request_email_verification, name='request_email_verification'),
    path('email/verify-confirm/', views.verify_email_code, name='verify_email_code'),
    path('email/resend/', views.resend_verification_code, name='resend_verification_code'),
    path('email/status/', views.get_email_verification_status, name='get_email_verification_status'),
    path('email/change-request/', views.request_email_change, name='request_email_change'),
    path('email/change-confirm/', views.confirm_email_change, name='confirm_email_change'),
    path('email/cleanup/', views.cleanup_expired_verifications, name='cleanup_expired_verifications'),
    
    # Password Reset endpoints
    path('password/reset-request/', views.request_password_reset, name='request_password_reset'),
    path('password/reset-confirm/', views.confirm_password_reset, name='confirm_password_reset'),
    
    # Phone-based Authentication endpoints
    path('phone/verify-request/', views.request_phone_verification, name='request_phone_verification'),
    path('phone/verify-confirm/', views.verify_phone_code_view, name='verify_phone_code'),
    path('phone/resend/', views.resend_phone_verification, name='resend_phone_verification'),
    path('phone/status/', views.get_phone_verification_status, name='get_phone_verification_status'),
    path('phone/change-request/', views.request_phone_change, name='request_phone_change'),
    path('phone/change-confirm/', views.confirm_phone_change, name='confirm_phone_change'),
    path('phone/service-status/', views.check_sms_service_status, name='check_sms_service_status'),
    
    # Smart authentication UX
    path('status/', views.check_auth_status, name='check_auth_status'),
    path('prompt/shown/', views.mark_auth_prompt_shown, name='mark_auth_prompt_shown'),
    path('prompt/dismiss/', views.dismiss_auth_prompt, name='dismiss_auth_prompt'),
    
    # System
    path('health/', views.health_check, name='health_check'),
    
    # Security Monitoring endpoints
    path('security/dashboard/', views.security_dashboard, name='security_dashboard'),
    path('security/events/', views.user_security_events, name='user_security_events'),
    path('security/sessions/', views.security_active_sessions, name='security_active_sessions'),
    path('security/sessions/revoke/', views.security_revoke_session, name='security_revoke_session'),
    path('security/report/', views.security_report, name='security_report'),
    path('security/health-check/', views.security_health_check, name='security_health_check'),
    
    # Admin Security endpoints
    path('admin/security/overview/', views.admin_security_overview, name='admin_security_overview'),
    path('admin/security/alerts/', views.security_alerts, name='security_alerts'),
    path('admin/security/alerts/<uuid:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
]