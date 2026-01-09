"""
Authentication Serializers - Data validation layer
"""
from .auth_serializers import (
    LoginSerializer,
    RegisterSerializer, 
    RefreshTokenSerializer,
    WorkspaceSwitchSerializer,
    TokenResponseSerializer,
    UserDataSerializer,
    AuthResponseSerializer
)
from .profile_serializers import (
    ProfileSerializer,
    UpdateProfileSerializer,
    ProfileResponseSerializer
)
from .session_serializers import (
    SessionSerializer,
    RevokeSessionSerializer,
    SessionsResponseSerializer,
    SessionActionResponseSerializer
)
from .ux_serializers import (
    AuthStatusResponseSerializer,
    PromptActionResponseSerializer,
    HealthCheckResponseSerializer
)
from .mfa_serializers import (
    TOTPSetupSerializer,
    TOTPConfirmSerializer,
    MFAVerifySerializer,
    BackupCodeRegenerateSerializer,
    TOTPDeviceSerializer,
    BackupCodeSerializer,
    MFAStatusSerializer,
    TOTPSetupResponseSerializer,
    MFAVerifyResponseSerializer,
    BackupCodeResponseSerializer
)
from .oauth2_serializers import (
    OAuth2InitiateSerializer,
    OAuth2CallbackSerializer,
    OAuth2TokenRefreshSerializer,
    OAuth2ProviderSerializer,
    OAuth2InitiateResponseSerializer,
    OAuth2CallbackResponseSerializer,
    OAuth2ProvidersResponseSerializer
)
from .email_serializers import (
    EmailVerificationRequestSerializer,
    EmailVerificationConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailChangeRequestSerializer,
    EmailChangeConfirmSerializer,
    EmailVerificationResponseSerializer,
    PasswordResetResponseSerializer,
    EmailVerificationStatusSerializer
)
from .phone_serializers import (
    PhoneVerificationRequestSerializer,
    PhoneVerificationConfirmSerializer,
    PhoneChangeRequestSerializer,
    PhoneChangeConfirmSerializer,
    PhoneVerificationResponseSerializer,
    PhoneVerificationStatusSerializer,
    SMSServiceStatusSerializer
)

__all__ = [
    # Authentication serializers
    'LoginSerializer',
    'RegisterSerializer',
    'RefreshTokenSerializer',
    'WorkspaceSwitchSerializer',
    'TokenResponseSerializer',
    'UserDataSerializer',
    'AuthResponseSerializer',
    # Profile serializers
    'ProfileSerializer',
    'UpdateProfileSerializer',
    'ProfileResponseSerializer',
    # Session serializers
    'SessionSerializer',
    'RevokeSessionSerializer',
    'SessionsResponseSerializer',
    'SessionActionResponseSerializer',
    # UX serializers
    'AuthStatusResponseSerializer',
    'PromptActionResponseSerializer',
    'HealthCheckResponseSerializer',
    # MFA serializers
    'TOTPSetupSerializer',
    'TOTPConfirmSerializer',
    'MFAVerifySerializer',
    'BackupCodeRegenerateSerializer',
    'TOTPDeviceSerializer',
    'BackupCodeSerializer',
    'MFAStatusSerializer',
    'TOTPSetupResponseSerializer',
    'MFAVerifyResponseSerializer',
    'BackupCodeResponseSerializer',
    # OAuth2 serializers
    'OAuth2InitiateSerializer',
    'OAuth2CallbackSerializer', 
    'OAuth2TokenRefreshSerializer',
    'OAuth2ProviderSerializer',
    'OAuth2InitiateResponseSerializer',
    'OAuth2CallbackResponseSerializer',
    'OAuth2ProvidersResponseSerializer',
    # Email serializers
    'EmailVerificationRequestSerializer',
    'EmailVerificationConfirmSerializer',
    'PasswordResetRequestSerializer', 
    'PasswordResetConfirmSerializer',
    'EmailChangeRequestSerializer',
    'EmailChangeConfirmSerializer',
    'EmailVerificationResponseSerializer',
    'PasswordResetResponseSerializer',
    'EmailVerificationStatusSerializer',
    # Phone serializers
    'PhoneVerificationRequestSerializer',
    'PhoneVerificationConfirmSerializer',
    'PhoneChangeRequestSerializer',
    'PhoneChangeConfirmSerializer',
    'PhoneVerificationResponseSerializer',
    'PhoneVerificationStatusSerializer',
    'SMSServiceStatusSerializer',
]