"""
Authentication API Views - Core auth endpoints
"""
import re
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
from authentication.services import AuthenticationService, SessionService
from authentication.models import SecurityEvent

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user and return JWT tokens
    
    Body:
    {
        "email": "user@example.com",
        "password": "password123",
        "remember_me": true
    }
    """
    from authentication.serializers import LoginSerializer
    
    try:
        # Use serializer for validation
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Return first error message
            first_error = next(iter(serializer.errors.values()))[0]
            return Response({
                'success': False,
                'error': str(first_error)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated data
        validated_data = serializer.validated_data
        email = validated_data['email']
        password = validated_data['password']
        remember_me = validated_data.get('remember_me', False)
        
        # Authenticate user
        result = AuthenticationService.authenticate_user(email, password, request)
        
        if result['success']:
            # Convert guest session if exists
            SessionService.convert_session_to_authenticated(
                request, 
                User.objects.get(id=result['user']['id']),
                'login'
            )
            
            # Prepare secure response - minimal user data + structured tokens
            response_data = {
                'success': True,
                'user': {
                    'id': result['user']['id'],
                    'first_name': result['user']['first_name'],
                    'last_name': result['user']['last_name'],
                    'username': result['user'].get('username', ''),
                    'email': result['user'].get('email', ''),
                    'phone_number': result['user'].get('phone_number'),
                    'email_verified': result['user'].get('email_verified', False),
                    'phone_verified': result['user'].get('phone_verified', False),
                    'two_factor_enabled': result['user'].get('two_factor_enabled', False),
                },
                'tokens': {
                    'access_token': result['tokens']['access_token'],
                    'token_type': result['tokens']['token_type'],
                    'expires_in': result['tokens']['access_expires_in'],
                },
                'message': 'Login successful'
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            # Set refresh token as httpOnly cookie - always persistent for better UX
            response.set_cookie(
                'refresh_token',
                result['tokens']['refresh_token'],
                max_age=result['tokens']['refresh_expires_in'],  # Always set max_age
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            # Set refresh token ID for logout
            response.set_cookie(
                'refresh_token_id',
                result['tokens']['refresh_token_id'],
                max_age=result['tokens']['refresh_expires_in'],  # Always set max_age
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            return response
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred during login'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register new user account
    
    Body:
    {
        "email": "user@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+237612345678", // optional
        "username": "johndoe" // optional
    }
    """
    from authentication.serializers import RegisterSerializer
    
    try:
        # Use serializer for validation
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Return first error message
            first_error = next(iter(serializer.errors.values()))[0]
            return Response({
                'success': False,
                'error': str(first_error),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated data
        validated_data = serializer.validated_data
        
        # Build user_data dict for service
        user_data = {
            'email': validated_data['email'],
            'password': validated_data['password'],
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'phone_number': validated_data.get('phone_number', ''),
        }
        
        # Register user
        result = AuthenticationService.register_user(user_data, request)
        
        if result['success']:
            # Convert guest session if exists
            SessionService.convert_session_to_authenticated(
                request,
                User.objects.get(id=result['user']['id']),
                'registration'
            )
            
            # Prepare secure response - minimal user data + structured tokens
            response_data = {
                'success': True,
                'user': {
                    'id': result['user']['id'],
                    'first_name': result['user']['first_name'],
                    'last_name': result['user']['last_name'],
                    'username': result['user'].get('username', ''),
                    'email': result['user'].get('email', ''),
                    'phone_number': result['user'].get('phone_number'),
                    'email_verified': result['user'].get('email_verified', False),
                    'phone_verified': result['user'].get('phone_verified', False),
                    'two_factor_enabled': result['user'].get('two_factor_enabled', False),
                },
                'tokens': {
                    'access_token': result['tokens']['access_token'],
                    'token_type': result['tokens']['token_type'],
                    'expires_in': result['tokens']['access_expires_in'],
                },
                'message': 'Account created successfully! Welcome to HustlerzCamp!'
            }
            
            response = Response(response_data, status=status.HTTP_201_CREATED)
            
            # Set refresh token as httpOnly cookie
            response.set_cookie(
                'refresh_token',
                result['tokens']['refresh_token'],
                max_age=result['tokens']['refresh_expires_in'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            response.set_cookie(
                'refresh_token_id',
                result['tokens']['refresh_token_id'],
                max_age=result['tokens']['refresh_expires_in'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            return response
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'success': False,
            'error': 'An error occurred during registration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token
    """
    try:
        # Debug: Log refresh attempt
        logger.info(f"🔄 REFRESH: Refresh token request from {request.META.get('REMOTE_ADDR')}")

        # Get refresh token from cookie
        refresh_token_string = request.COOKIES.get('refresh_token')
        refresh_token_id = request.COOKIES.get('refresh_token_id')

        logger.info(f"🍪 REFRESH: Has refresh_token cookie: {bool(refresh_token_string)}")
        logger.info(f"🍪 REFRESH: Has refresh_token_id cookie: {bool(refresh_token_id)}")
        logger.info(f"🍪 REFRESH: All cookies: {list(request.COOKIES.keys())}")

        if not refresh_token_string:
            logger.warning("❌ REFRESH: No refresh token found in cookies")
            return Response({
                'success': False,
                'error': 'Refresh token not found',
                'code': 'NO_REFRESH_TOKEN'
            }, status=status.HTTP_401_UNAUTHORIZED)

        logger.info("🔄 REFRESH: Calling AuthenticationService.refresh_token")
        # v3.0 - Simple refresh (NO workspace parameter)
        # Refresh tokens extend sessions, they don't change authorization scope
        result = AuthenticationService.refresh_token(
            refresh_token_string,
            request
        )
        
        if result['success']:
            response_data = {
                'success': True,
                'tokens': {
                    'access_token': result['tokens']['access_token'],
                    'token_type': result['tokens']['token_type'],
                    'expires_in': result['tokens']['access_expires_in'],
                },
                'user': result['user']
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            # Set new refresh token cookie
            response.set_cookie(
                'refresh_token',
                result['tokens']['refresh_token'],
                max_age=result['tokens']['refresh_expires_in'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            response.set_cookie(
                'refresh_token_id',
                result['tokens']['refresh_token_id'],
                max_age=result['tokens']['refresh_expires_in'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            return response
        else:
            # Clear cookies on failed refresh
            response = Response({
                'success': False,
                'error': result['error'],
                'code': 'REFRESH_FAILED'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
            response.delete_cookie('refresh_token')
            response.delete_cookie('refresh_token_id')
            
            return response
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Token refresh failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user and revoke tokens"""
    try:
        # Get token info
        refresh_token_id = request.COOKIES.get('refresh_token_id')
        access_token_jti = getattr(request, 'jwt_payload', {}).get('jti')
        
        # Logout user
        AuthenticationService.logout_user(refresh_token_id, access_token_jti)
        
        # Log security event
        SecurityEvent.log_event(
            'logout',
            user=request.user,
            description="User logged out",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        response = Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
        # Clear cookies
        response.delete_cookie('refresh_token')
        response.delete_cookie('refresh_token_id')
        
        return response
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)