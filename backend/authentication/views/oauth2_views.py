"""
Enterprise OAuth2 Views - 2025 Security Standards
Handles Google, GitHub OAuth2 authentication with PKCE
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from ..services import OAuth2Service, SecurityService
from ..serializers.oauth2_serializers import (
    OAuth2InitiateSerializer, OAuth2CallbackSerializer
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_oauth2_flow(request):
    """
    Initiate OAuth2 authorization flow with PKCE
    POST /api/auth/oauth2/initiate/
    
    Body:
    {
        "provider": "google" | "apple",
        "redirect_uri": "https://yourdomain.com/auth/callback",
        "state": "optional-csrf-token"
    }
    """
    serializer = OAuth2InitiateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    provider = serializer.validated_data['provider']
    redirect_uri = serializer.validated_data['redirect_uri']
    state = serializer.validated_data.get('state')
    
    # Generate OAuth2 authorization URL with PKCE
    result = OAuth2Service.generate_authorization_url(
        provider=provider,
        redirect_uri=redirect_uri,
        state=state
    )
    
    if not result['success']:
        return Response({
            'success': False,
            'message': 'Failed to generate OAuth2 authorization URL',
            'error': result['error']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Store PKCE parameters in cache (10 minute expiry)
    cache_key = f"oauth2_pkce_{result['state']}"
    cache_data = {
        'code_verifier': result['code_verifier'],
        'provider': provider,
        'redirect_uri': redirect_uri,
        'initiated_at': result['expires_at']
    }
    cache.set(cache_key, cache_data, 600)  # 10 minutes
    
    return Response({
        'success': True,
        'data': {
            'authorization_url': result['authorization_url'],
            'state': result['state'],
            'provider': provider,
            'expires_in_minutes': 10
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def handle_oauth2_callback(request):
    """
    Handle OAuth2 callback and complete authentication
    POST /api/auth/oauth2/callback/
    
    Body:
    {
        "code": "authorization_code",
        "state": "state_parameter",
        "error": "optional_error_code",
        "error_description": "optional_error_description"
    }
    """
    serializer = OAuth2CallbackSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check for OAuth2 errors
    if serializer.validated_data.get('error'):
        error_code = serializer.validated_data['error']
        error_description = serializer.validated_data.get('error_description', 'OAuth2 authentication failed')
        
        logger.warning(f"OAuth2 callback error: {error_code} - {error_description}")
        return Response({
            'success': False,
            'message': f'OAuth2 authentication failed: {error_description}',
            'error_code': error_code
        }, status=status.HTTP_400_BAD_REQUEST)
    
    code = serializer.validated_data['code']
    state = serializer.validated_data['state']
    
    # Retrieve PKCE parameters from cache
    cache_key = f"oauth2_pkce_{state}"
    cache_data = cache.get(cache_key)
    
    if not cache_data:
        return Response({
            'success': False,
            'message': 'Invalid or expired OAuth2 state parameter',
            'error_code': 'invalid_state'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Extract cached data
    code_verifier = cache_data['code_verifier']
    provider = cache_data['provider']
    redirect_uri = cache_data['redirect_uri']
    
    # Clear cache entry (one-time use)
    cache.delete(cache_key)
    
    try:
        # Exchange authorization code for access token
        token_result = OAuth2Service.exchange_authorization_code(
            provider=provider,
            code=code,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            state=state
        )
        
        if not token_result['success']:
            return Response({
                'success': False,
                'message': 'Failed to exchange authorization code for token',
                'error': token_result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch user information from provider
        user_info_result = OAuth2Service.get_user_info(
            provider=provider,
            access_token=token_result['access_token']
        )
        
        if not user_info_result['success']:
            return Response({
                'success': False,
                'message': 'Failed to fetch user information from provider',
                'error': user_info_result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update user
        user_result = OAuth2Service.create_or_update_user(
            provider=provider,
            user_info=user_info_result['user_info'],
            request=request
        )
        
        if not user_result['success']:
            return Response({
                'success': False,
                'message': 'Failed to create or update user account',
                'error': user_result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = user_result['user']
        tokens = user_result['tokens']
        
        return Response({
            'success': True,
            'message': f'Successfully authenticated via {provider}',
            'data': {
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_new_user': user_result['created']
                },
                'tokens': {
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'token_type': 'Bearer',
                    'expires_in': tokens['expires_in']
                },
                'provider': provider,
                'oauth2_tokens': {
                    'access_token': token_result['access_token'],
                    'refresh_token': token_result.get('refresh_token'),
                    'expires_in': token_result.get('expires_in')
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"OAuth2 callback processing error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal error processing OAuth2 callback',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_oauth2_providers(request):
    """
    Get list of available OAuth2 providers with their configurations
    GET /api/auth/oauth2/providers/
    """
    try:
        providers_info = []
        
        for provider_name, config in OAuth2Service.PROVIDERS.items():
            # Check if provider is configured
            client_id = getattr(settings, config['client_id_setting'], None)
            
            provider_info = {
                'name': provider_name,
                'display_name': provider_name.title(),
                'scopes': config['scopes'],
                'configured': bool(client_id),
            }
            
            # Add provider-specific display info
            if provider_name == 'google':
                provider_info.update({
                    'display_name': 'Google',
                    'icon': 'google',
                    'color': '#4285f4',
                    'description': 'Sign in with your Google account'
                })
            elif provider_name == 'apple':
                provider_info.update({
                    'display_name': 'Apple',
                    'icon': 'apple',
                    'color': '#000000',
                    'description': 'Sign in with your Apple ID'
                })
            
            providers_info.append(provider_info)
        
        return Response({
            'success': True,
            'data': {
                'providers': providers_info,
                'security_features': [
                    'PKCE (Proof Key for Code Exchange)',
                    'SHA256 code challenge',
                    'State parameter CSRF protection',
                    'Authorization code flow only',
                    'Secure token storage',
                    'Email verification required'
                ]
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"OAuth2 providers info error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to retrieve OAuth2 providers information',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_oauth2_token(request):
    """
    Refresh OAuth2 access token
    POST /api/auth/oauth2/refresh/
    
    Body:
    {
        "provider": "google" | "apple", 
        "refresh_token": "oauth2_refresh_token"
    }
    """
    try:
        provider = request.data.get('provider')
        refresh_token = request.data.get('refresh_token')
        
        if not provider or not refresh_token:
            return Response({
                'success': False,
                'message': 'Provider and refresh_token are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if provider not in OAuth2Service.PROVIDERS:
            return Response({
                'success': False,
                'message': f'Unsupported provider: {provider}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Refresh token
        result = OAuth2Service.refresh_oauth2_token(provider, refresh_token)
        
        if not result['success']:
            return Response({
                'success': False,
                'message': 'Failed to refresh OAuth2 token',
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': {
                'access_token': result['access_token'],
                'token_type': result['token_type'],
                'expires_in': result['expires_in'],
                'refresh_token': result['refresh_token'],
                'provider': provider
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"OAuth2 token refresh error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to refresh OAuth2 token',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Development/Testing endpoints (remove in production)
@api_view(['GET'])
@permission_classes([AllowAny])
def test_oauth2_configuration(request):
    """
    Test OAuth2 provider configurations (development only)
    GET /api/auth/oauth2/test-config/
    """
    if not settings.DEBUG:
        return Response({
            'success': False,
            'message': 'Test endpoints only available in development'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        config_status = {}
        
        for provider_name, config in OAuth2Service.PROVIDERS.items():
            client_id = getattr(settings, config['client_id_setting'], None)
            client_secret = getattr(settings, config['client_secret_setting'], None)
            
            config_status[provider_name] = {
                'client_id_configured': bool(client_id),
                'client_secret_configured': bool(client_secret),
                'required_settings': [
                    config['client_id_setting'],
                    config['client_secret_setting']
                ],
                'endpoints': {
                    'authorization': config['authorization_endpoint'],
                    'token': config['token_endpoint'],
                    'userinfo': config['userinfo_endpoint']
                },
                'scopes': config['scopes']
            }
        
        return Response({
            'success': True,
            'data': {
                'providers': config_status,
                'environment': 'development',
                'debug_mode': settings.DEBUG
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"OAuth2 config test error: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to test OAuth2 configuration',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)