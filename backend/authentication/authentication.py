"""
JWT Authentication for Django REST Framework
"""
from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from . import services
import jwt

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for DRF
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using JWT token and set workspace context
        """
        # Skip authentication for registration and login endpoints
        path = request.path_info
        if path in ['/api/auth/register/', '/api/auth/login/', '/api/auth/refresh/']:
            return None
            
        auth_header = authentication.get_authorization_header(request)
        
        if not auth_header:
            return None
        
        auth_parts = auth_header.split()
        
        if len(auth_parts) != 2 or auth_parts[0].lower() != b'bearer':
            return None
        
        token = auth_parts[1].decode('utf-8')
        
        try:
            # Verify the token using our TokenService
            payload = services.TokenService.verify_access_token(token)
            user_id = payload.get('user_id')
            
            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token payload')
            
            # Get the user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed('User not found')
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account is disabled')
            
            # Add workspace context to request if present in token
            workspace_id = payload.get('workspace_id')
            if workspace_id:
                request.workspace_id = workspace_id
                request.workspace_type = payload.get('workspace_type')
                request.workspace_permissions = payload.get('workspace_permissions', [])
                request.workspace_role = payload.get('workspace_role')
            
            return (user, token)
            
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        """
        Return the WWW-Authenticate header value
        """
        return 'Bearer'