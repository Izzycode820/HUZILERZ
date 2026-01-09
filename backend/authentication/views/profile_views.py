"""
User Profile Views - Profile management endpoints
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get current user profile"""
    try:
        user = request.user
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar': user.avatar,
                'bio': user.bio,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified,
                'two_factor_enabled': user.two_factor_enabled,
                'preferred_auth_method': user.preferred_auth_method,
                'security_notifications': user.security_notifications,
                'created_at': user.created_at,
                'last_login': user.last_login,
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    try:
        user = request.user
        data = request.data
        
        # Updateable fields
        updateable_fields = [
            'first_name', 'last_name', 'username', 'bio', 
            'avatar', 'preferred_auth_method', 'security_notifications'
        ]
        
        updated_fields = []
        
        for field in updateable_fields:
            if field in data:
                if field == 'username':
                    # Ensure username uniqueness
                    new_username = data[field].strip()
                    if new_username != user.username and User.objects.filter(username=new_username).exists():
                        return Response({
                            'success': False,
                            'error': 'Username is already taken'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                setattr(user, field, data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.save(update_fields=updated_fields)
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar': user.avatar,
                'bio': user.bio,
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)