"""
Core Authentication Service
"""
import jwt
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from user_agents import parse
from authentication.models import SecurityEvent
from .token_service import TokenService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationService:
    """Core authentication service"""
    
    @staticmethod
    def authenticate_user(email, password, request=None):
        """Authenticate user with email and password"""
        try:
            # Get device and IP info
            device_info = AuthenticationService._extract_device_info(request) if request else {}
            ip_address = AuthenticationService._get_client_ip(request) if request else None
            
            # Attempt authentication
            user = authenticate(username=email, password=password)
            
            if not user:
                # Try to find user by email (in case username is different)
                try:
                    user_obj = User.objects.get(email=email)
                    if check_password(password, user_obj.password):
                        user = user_obj
                except User.DoesNotExist:
                    pass
            
            if user:
                if not user.is_active:
                    SecurityEvent.log_event(
                        'login_failed',
                        user=user,
                        description=f"Login attempt for inactive account: {email}",
                        risk_level='medium',
                        ip_address=ip_address,
                        user_agent=device_info.get('user_agent', '')
                    )
                    raise Exception("Account is disabled")
                
                # Update user login info
                user.last_login = timezone.now()
                user.last_login_ip = ip_address
                user.save(update_fields=['last_login', 'last_login_ip'])
                
                # Generate tokens (NO workspace context)
                tokens = TokenService.generate_token_pair(user, device_info=device_info, ip_address=ip_address)
                
                # Log successful login
                SecurityEvent.log_event(
                    'login_success',
                    user=user,
                    description=f"Successful login for {email}",
                    ip_address=ip_address,
                    user_agent=device_info.get('user_agent', '')
                )
                
                return {
                    'success': True,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'avatar': user.avatar,
                        'phone_number': user.phone_number,
                        'email_verified': user.email_verified,
                        'phone_verified': user.phone_verified,
                        'two_factor_enabled': user.two_factor_enabled,
                    },
                    'tokens': tokens,
                }
            else:
                # Log failed login
                SecurityEvent.log_event(
                    'login_failed',
                    description=f"Failed login attempt for {email}",
                    risk_level=1,
                    ip_address=ip_address,
                    user_agent=device_info.get('user_agent', '')
                )
                
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def register_user(user_data, request=None):
        """Register a new user"""
        try:
            # Extract data
            email = user_data.get('email')
            password = user_data.get('password')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            phone_number = user_data.get('phone_number', '')
            
            # Auto-generate username from first and last name, fallback to email
            if first_name and last_name:
                username = f"{first_name.lower()}{last_name.lower()}"
            else:
                username = email.split('@')[0]
            
            # Check if user exists
            if User.objects.filter(email=email).exists():
                return {
                    'success': False,
                    'error': 'User with this email already exists'
                }
            
            # Ensure username is unique
            original_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Create user
            user = User.objects.create(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number if phone_number else None,
                password=make_password(password),
                is_active=True,
            )
            
            # Get device and IP info
            device_info = AuthenticationService._extract_device_info(request) if request else {}
            ip_address = AuthenticationService._get_client_ip(request) if request else None
            
            # Generate tokens (NO workspace context)
            tokens = TokenService.generate_token_pair(user, device_info=device_info, ip_address=ip_address)
            
            # Log registration
            SecurityEvent.log_event(
                'login_success',
                user=user,
                description=f"New user registration: {email}",
                ip_address=ip_address,
                user_agent=device_info.get('user_agent', '')
            )
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'avatar': user.avatar,
                    'phone_number': user.phone_number,
                    'email_verified': user.email_verified,
                    'phone_verified': user.phone_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                },
                'tokens': tokens,
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Registration error: {str(e)}")
            logger.error(f"Registration traceback: {traceback.format_exc()}")
            print(f"DEBUG Registration error: {str(e)}")
            print(f"DEBUG Registration traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }
    
    @staticmethod
    def refresh_token(refresh_token_string, request=None):
        """
        Refresh access token using refresh token (Industry Standard: OAuth2)

        SIMPLE refresh - NO workspace logic (workspace sent via X-Workspace-Id header)
        Refresh tokens extend sessions, they don't change authorization scope

        Args:
            refresh_token_string: The refresh token from cookie
            request: Django request object

        Returns:
            New access token (identity only)
        """
        try:
            # Verify refresh token
            refresh_token = TokenService.verify_refresh_token(refresh_token_string)

            # Get device info
            device_info = AuthenticationService._extract_device_info(request) if request else {}
            ip_address = AuthenticationService._get_client_ip(request) if request else None

            # Generate new token pair (rotating refresh tokens) - NO WORKSPACE
            tokens = TokenService.generate_token_pair(
                refresh_token.user,
                device_info=device_info,
                ip_address=ip_address
            )

            # Revoke old refresh token (OAuth2 refresh token rotation best practice)
            refresh_token.revoke()

            # Log token refresh
            SecurityEvent.log_event(
                'token_refresh',
                user=refresh_token.user,
                description="Token refreshed successfully",
                ip_address=ip_address,
                user_agent=device_info.get('user_agent', '')
            )

            return {
                'success': True,
                'tokens': tokens,
                'user': {
                    'id': refresh_token.user.id,
                    'email': refresh_token.user.email,
                    'username': refresh_token.user.username,
                    'first_name': refresh_token.user.first_name,
                    'last_name': refresh_token.user.last_name,
                    'avatar': refresh_token.user.avatar,
                    'email_verified': refresh_token.user.email_verified,
                }
            }

        except jwt.InvalidTokenError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return {
                'success': False,
                'error': 'Token refresh failed'
            }
    
    @staticmethod
    def logout_user(refresh_token_id, access_token_jti=None):
        """Logout user by revoking tokens"""
        try:
            # Revoke refresh token
            if refresh_token_id:
                TokenService.revoke_refresh_token(refresh_token_id)
            
            # Blacklist access token
            if access_token_jti:
                TokenService.blacklist_token(access_token_jti)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': 'Logout failed'}

    @staticmethod
    def switch_workspace(user, workspace_id, request=None):
        """
        Validate workspace access and return workspace details (Industry Standard)

        NO JWT generation - workspace context sent via X-Workspace-Id header
        This endpoint validates access (including subscription/compliance gating)
        and returns workspace info for UI/routing

        Args:
            user: User instance
            workspace_id: Workspace ID to switch to
            request: Django request object

        Returns:
            Workspace details + membership info (NO tokens)
            OR structured error if workspace is restricted/noncompliant
        """
        try:
            from workspace.core.models import Workspace, Membership
            from subscription.services.gating import check_workspace_access

            # Get workspace - include suspended_by_plan status for proper error messaging
            try:
                workspace = Workspace.objects.select_related('owner').get(
                    id=workspace_id,
                    status__in=['active', 'suspended_by_plan']
                )
            except Workspace.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Workspace not found or inactive',
                    'error_code': 'WORKSPACE_NOT_FOUND'
                }

            # GATING CHECK: Verify subscription/compliance allows access to this workspace
            # This check applies to owners only - staff see membership errors instead
            if workspace.owner == user:
                allowed, error_data = check_workspace_access(user, workspace)
                if not allowed:
                    return {'success': False, **error_data}

            # Determine user's role and permissions in this workspace
            membership = None
            if workspace.owner == user:
                # User is owner
                role = 'owner'
                permissions = ['read', 'write', 'delete', 'invite', 'admin']
            else:
                # Check membership
                try:
                    membership = Membership.objects.get(
                        workspace=workspace,
                        user=user,
                        is_active=True
                    )
                    role = membership.role
                    permissions = membership.permissions or ['read']
                except Membership.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Access denied to this workspace',
                        'error_code': 'ACCESS_DENIED'
                    }

            # Get device info for logging
            device_info = AuthenticationService._extract_device_info(request) if request else {}
            ip_address = AuthenticationService._get_client_ip(request) if request else None

            # Log workspace switch
            try:
                SecurityEvent.log_event(
                    'workspace_switch',
                    user=user,
                    description=f"Switched to workspace: {workspace.name}",
                    ip_address=ip_address,
                    user_agent=device_info.get('user_agent', '') if isinstance(device_info, dict) else ''
                )
            except Exception:
                # Skip logging if SecurityEvent is not available
                pass

            return {
                'success': True,
                'workspace': {
                    'id': str(workspace.id),
                    'name': workspace.name,
                    'type': workspace.type,
                    'status': workspace.status,
                    'owner_id': str(workspace.owner.id),
                    'created_at': workspace.created_at.isoformat() if hasattr(workspace, 'created_at') else None,
                    'restricted_mode': getattr(workspace, 'restricted_mode', False),
                },
                'membership': {
                    'role': role,
                    'permissions': permissions,
                    'joined_at': membership.created_at.isoformat() if membership and hasattr(membership, 'created_at') else None,
                }
            }

        except Exception as e:
            import traceback
            logger.error(f"Workspace switch error: {str(e)}")
            logger.error(f"Workspace switch traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Workspace switch failed: {str(e)}'
            }

    @staticmethod
    def leave_workspace(user, request=None):
        """
        Leave current workspace context (Industry Standard)

        NO JWT logic needed - frontend just stops sending X-Workspace-Id header
        This endpoint exists purely for logging/audit purposes

        Args:
            user: User instance
            request: Django request object

        Returns:
            Success confirmation (no tokens needed)
        """
        try:
            # Get device info for logging
            device_info = AuthenticationService._extract_device_info(request) if request else {}
            ip_address = AuthenticationService._get_client_ip(request) if request else None

            # Log workspace leave event (audit trail)
            try:
                SecurityEvent.log_event(
                    'workspace_leave',
                    user=user,
                    description="Left workspace context",
                    ip_address=ip_address,
                    user_agent=device_info.get('user_agent', '') if isinstance(device_info, dict) else ''
                )
            except Exception:
                # Skip logging if SecurityEvent is not available
                pass

            return {
                'success': True,
                'message': 'Left workspace successfully - frontend should stop sending X-Workspace-Id header'
            }

        except Exception as e:
            import traceback
            logger.error(f"Leave workspace error: {str(e)}")
            logger.error(f"Leave workspace traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Leave workspace failed: {str(e)}'
            }

    @staticmethod
    def _extract_device_info(request):
        """Extract device information from request"""
        if not request:
            return {}
        
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_string)
        
        return {
            'user_agent': user_agent_string,
            'device_name': f"{user_agent.browser.family} on {user_agent.os.family}",
            'browser': user_agent.browser.family,
            'os': user_agent.os.family,
            'device_type': 'mobile' if user_agent.is_mobile else 'tablet' if user_agent.is_tablet else 'desktop'
        }
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip