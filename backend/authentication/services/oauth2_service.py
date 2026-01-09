"""
Enterprise OAuth2 Service - 2025 Security Standards
Implements OAuth2 with mandatory PKCE, Authorization Code Flow, and modern security practices
Supports Google, GitHub, and other OAuth2 providers
"""
import secrets
import hashlib
import base64
import urllib.parse
import requests
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from ..models import SecurityEvent
from .token_service import TokenService
from .security_service import SecurityService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class OAuth2Service:
    """Modern OAuth2 service following 2025 security standards"""
    
    # OAuth2 Provider configurations
    PROVIDERS = {
        'google': {
            'authorization_endpoint': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_endpoint': 'https://oauth2.googleapis.com/token',
            'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scopes': ['openid', 'email', 'profile'],
            'client_id_setting': 'GOOGLE_OAUTH2_CLIENT_ID',
            'client_secret_setting': 'GOOGLE_OAUTH2_CLIENT_SECRET',
        },
        'apple': {
            'authorization_endpoint': 'https://appleid.apple.com/auth/authorize',
            'token_endpoint': 'https://appleid.apple.com/auth/token',
            'userinfo_endpoint': None,  # Apple doesn't have a userinfo endpoint
            'scopes': ['name', 'email'],
            'client_id_setting': 'APPLE_OAUTH2_CLIENT_ID',
            'client_secret_setting': 'APPLE_OAUTH2_CLIENT_SECRET',  # Actually a JWT key
            'key_id_setting': 'APPLE_OAUTH2_KEY_ID',
            'team_id_setting': 'APPLE_OAUTH2_TEAM_ID',
            'private_key_setting': 'APPLE_OAUTH2_PRIVATE_KEY',
        }
    }
    
    @staticmethod
    def generate_pkce_pair():
        """
        Generate PKCE code verifier and challenge following 2025 standards
        
        Returns:
            tuple: (code_verifier, code_challenge)
        """
        # Generate cryptographically secure code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(96)
        ).decode('utf-8').rstrip('=')  # Remove padding for URL safety
        
        # Generate SHA256 code challenge (mandatory in 2025 standards)
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    @staticmethod
    def generate_authorization_url(provider, redirect_uri, state=None):
        """
        Generate OAuth2 authorization URL with PKCE
        
        Args:
            provider: OAuth2 provider ('google', 'github', etc.)
            redirect_uri: Callback URL
            state: Optional state parameter for CSRF protection
            
        Returns:
            dict: Authorization URL and PKCE parameters
        """
        try:
            if provider not in OAuth2Service.PROVIDERS:
                raise ValueError(f"Unsupported OAuth2 provider: {provider}")
            
            provider_config = OAuth2Service.PROVIDERS[provider]
            
            # Get client configuration
            client_id = getattr(settings, provider_config['client_id_setting'], None)
            if not client_id:
                raise ValueError(f"Missing client ID for {provider}")
            
            # Generate PKCE pair
            code_verifier, code_challenge = OAuth2Service.generate_pkce_pair()
            
            # Generate state for CSRF protection if not provided
            if not state:
                state = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
            
            # Build authorization parameters
            auth_params = {
                'response_type': 'code',  # Authorization code flow only
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'scope': ' '.join(provider_config['scopes']),
                'state': state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',  # Mandatory SHA256
            }
            
            # Provider-specific parameters
            if provider == 'google':
                auth_params.update({
                    'access_type': 'offline',
                    'prompt': 'consent',
                    'include_granted_scopes': 'true',
                })
            elif provider == 'apple':
                auth_params.update({
                    'response_mode': 'form_post',  # Apple requirement
                    'nonce': secrets.token_urlsafe(32),  # Apple requirement for security
                })
            
            # Build authorization URL
            authorization_url = f"{provider_config['authorization_endpoint']}?{urllib.parse.urlencode(auth_params)}"
            
            return {
                'success': True,
                'authorization_url': authorization_url,
                'code_verifier': code_verifier,
                'state': state,
                'provider': provider,
                'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat(),
            }
            
        except Exception as e:
            logger.error(f"OAuth2 authorization URL generation error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def exchange_authorization_code(provider, code, code_verifier, redirect_uri, state=None):
        """
        Exchange authorization code for access token using PKCE
        
        Args:
            provider: OAuth2 provider
            code: Authorization code from callback
            code_verifier: PKCE code verifier
            redirect_uri: Original redirect URI
            state: State parameter for validation
            
        Returns:
            dict: Token exchange result
        """
        try:
            if provider not in OAuth2Service.PROVIDERS:
                raise ValueError(f"Unsupported OAuth2 provider: {provider}")
            
            provider_config = OAuth2Service.PROVIDERS[provider]
            
            # Get client configuration
            client_id = getattr(settings, provider_config['client_id_setting'], None)
            client_secret = getattr(settings, provider_config['client_secret_setting'], None)
            
            if not client_id or not client_secret:
                raise ValueError(f"Missing client credentials for {provider}")
            
            # Prepare token request
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'code_verifier': code_verifier,  # PKCE verification
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': f'HustlerzCamp-OAuth2-Client/1.0',
            }
            
            # Exchange code for token
            response = requests.post(
                provider_config['token_endpoint'],
                data=token_data,
                headers=headers,
                timeout=30
            )
            
            if not response.ok:
                logger.error(f"OAuth2 token exchange failed for {provider}: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Token exchange failed: {response.status_code}'
                }
            
            token_response = response.json()
            
            # Validate required fields
            if 'access_token' not in token_response:
                return {
                    'success': False,
                    'error': 'Invalid token response: missing access_token'
                }
            
            return {
                'success': True,
                'access_token': token_response['access_token'],
                'token_type': token_response.get('token_type', 'Bearer'),
                'refresh_token': token_response.get('refresh_token'),
                'expires_in': token_response.get('expires_in'),
                'scope': token_response.get('scope'),
                'provider': provider
            }
            
        except requests.RequestException as e:
            logger.error(f"OAuth2 token exchange network error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': f'Network error during token exchange: {str(e)}'
            }
        except Exception as e:
            logger.error(f"OAuth2 token exchange error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_user_info(provider, access_token):
        """
        Fetch user information from OAuth2 provider
        
        Args:
            provider: OAuth2 provider
            access_token: Valid access token
            
        Returns:
            dict: User information
        """
        try:
            if provider not in OAuth2Service.PROVIDERS:
                raise ValueError(f"Unsupported OAuth2 provider: {provider}")
            
            provider_config = OAuth2Service.PROVIDERS[provider]
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'User-Agent': f'HustlerzCamp-OAuth2-Client/1.0',
            }
            
            # Fetch user info
            response = requests.get(
                provider_config['userinfo_endpoint'],
                headers=headers,
                timeout=30
            )
            
            if not response.ok:
                return {
                    'success': False,
                    'error': f'Failed to fetch user info: {response.status_code}'
                }
            
            user_info = response.json()
            
            # Provider-specific user info processing
            if provider == 'google':
                processed_info = OAuth2Service._process_google_user_info(user_info)
            elif provider == 'apple':
                # Apple provides user info in the token response, not via API
                processed_info = OAuth2Service._process_apple_user_info(user_info, access_token)
            else:
                processed_info = user_info
            
            return {
                'success': True,
                'user_info': processed_info,
                'provider': provider
            }
            
        except requests.RequestException as e:
            logger.error(f"OAuth2 user info network error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': f'Network error fetching user info: {str(e)}'
            }
        except Exception as e:
            logger.error(f"OAuth2 user info error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _process_apple_user_info(user_info, access_token):
        """Process Apple user info from token response"""
        import jwt
        
        try:
            # Apple provides user info in the ID token (JWT)
            # For now, we'll extract what we can from the access token or user_info
            # In a full implementation, you'd decode the ID token
            
            # Apple typically provides minimal user info for privacy
            return {
                'id': user_info.get('sub'),
                'email': user_info.get('email'),
                'email_verified': user_info.get('email_verified', True),  # Apple emails are verified
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'full_name': f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip(),
                'provider_id': user_info.get('sub'),
                'is_private_email': user_info.get('is_private_email', False),
                'real_user_status': user_info.get('real_user_status', 0),
                'raw_data': user_info
            }
            
        except Exception as e:
            logger.error(f"Apple user info processing error: {str(e)}")
            return {
                'id': None,
                'email': None,
                'email_verified': False,
                'first_name': '',
                'last_name': '',
                'full_name': '',
                'provider_id': None,
                'raw_data': user_info
            }
    
    @staticmethod
    def _process_google_user_info(user_info):
        """Process Google user info into standard format"""
        return {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'email_verified': user_info.get('verified_email', False),
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
            'full_name': user_info.get('name', ''),
            'picture': user_info.get('picture'),
            'locale': user_info.get('locale'),
            'provider_id': user_info.get('id'),
            'raw_data': user_info
        }
    
    
    @staticmethod
    def create_or_update_user(provider, user_info, request=None):
        """
        Create or update user from OAuth2 provider data
        
        Args:
            provider: OAuth2 provider name
            user_info: Processed user information
            request: HTTP request for audit logging
            
        Returns:
            dict: User creation/update result
        """
        try:
            email = user_info.get('email')
            provider_id = user_info.get('provider_id')
            
            if not email:
                return {
                    'success': False,
                    'error': 'No email provided by OAuth2 provider'
                }
            
            if not user_info.get('email_verified', False):
                return {
                    'success': False,
                    'error': 'Email not verified by OAuth2 provider'
                }
            
            # Check if user exists
            user = None
            created = False
            
            try:
                user = User.objects.get(email=email)
                # Update existing user
                OAuth2Service._update_user_from_oauth2(user, provider, user_info)
            except User.DoesNotExist:
                # Create new user
                user = OAuth2Service._create_user_from_oauth2(provider, user_info)
                created = True
            
            # Log OAuth2 authentication event
            ip_address = SecurityService.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            SecurityEvent.log_event(
                event_type='oauth2_authentication',
                user=user,
                description=f'OAuth2 authentication via {provider}',
                risk_level=1,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'provider': provider,
                    'user_created': created,
                    'provider_id': provider_id,
                    'email_verified': user_info.get('email_verified', False)
                }
            )
            
            # Generate JWT tokens
            tokens = TokenService.generate_tokens_for_user(user)
            
            return {
                'success': True,
                'user': user,
                'created': created,
                'tokens': tokens,
                'provider': provider
            }
            
        except Exception as e:
            logger.error(f"OAuth2 user creation error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _create_user_from_oauth2(provider, user_info):
        """Create new user from OAuth2 data"""
        # Generate username from email or provider data
        base_username = user_info.get('username') or user_info['email'].split('@')[0]
        username = OAuth2Service._generate_unique_username(base_username)
        
        user = User.objects.create_user(
            username=username,
            email=user_info['email'],
            first_name=user_info.get('first_name', ''),
            last_name=user_info.get('last_name', ''),
            is_active=True,
        )
        
        # Set OAuth2-specific fields if available
        if hasattr(user, 'profile'):
            user.profile.oauth2_provider = provider
            user.profile.oauth2_provider_id = user_info.get('provider_id')
            user.profile.avatar_url = user_info.get('picture')
            user.profile.save()
        
        return user
    
    @staticmethod
    def _update_user_from_oauth2(user, provider, user_info):
        """Update existing user with OAuth2 data"""
        # Update basic info if not set
        if not user.first_name and user_info.get('first_name'):
            user.first_name = user_info['first_name']
        
        if not user.last_name and user_info.get('last_name'):
            user.last_name = user_info['last_name']
        
        user.save()
        
        # Update profile if available
        if hasattr(user, 'profile'):
            if not user.profile.avatar_url and user_info.get('picture'):
                user.profile.avatar_url = user_info['picture']
                user.profile.save()
    
    @staticmethod
    def _generate_unique_username(base_username):
        """Generate unique username"""
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username
    
    @staticmethod
    def refresh_oauth2_token(provider, refresh_token):
        """
        Refresh OAuth2 access token
        
        Args:
            provider: OAuth2 provider
            refresh_token: Valid refresh token
            
        Returns:
            dict: Token refresh result
        """
        try:
            if provider not in OAuth2Service.PROVIDERS:
                raise ValueError(f"Unsupported OAuth2 provider: {provider}")
            
            provider_config = OAuth2Service.PROVIDERS[provider]
            client_id = getattr(settings, provider_config['client_id_setting'], None)
            client_secret = getattr(settings, provider_config['client_secret_setting'], None)
            
            if not client_id or not client_secret:
                raise ValueError(f"Missing client credentials for {provider}")
            
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret,
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            response = requests.post(
                provider_config['token_endpoint'],
                data=token_data,
                headers=headers,
                timeout=30
            )
            
            if not response.ok:
                return {
                    'success': False,
                    'error': f'Token refresh failed: {response.status_code}'
                }
            
            token_response = response.json()
            
            return {
                'success': True,
                'access_token': token_response['access_token'],
                'token_type': token_response.get('token_type', 'Bearer'),
                'refresh_token': token_response.get('refresh_token', refresh_token),
                'expires_in': token_response.get('expires_in'),
                'provider': provider
            }
            
        except Exception as e:
            logger.error(f"OAuth2 token refresh error for {provider}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }