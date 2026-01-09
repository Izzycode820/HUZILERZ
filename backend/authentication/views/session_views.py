"""
Session Management Views - Active sessions and revocation
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from authentication.models import RefreshToken
from authentication.services import TokenService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_sessions(request):
    """Get user's active sessions"""
    try:
        user = request.user
        
        # Get active refresh tokens
        active_tokens = RefreshToken.objects.filter(
            user=user,
            is_active=True
        ).order_by('-last_used')
        
        sessions = []
        for token in active_tokens:
            sessions.append({
                'id': str(token.id),
                'device_name': token.device_name,
                'ip_address': token.ip_address,
                'last_used': token.last_used,
                'created_at': token.created_at,
                'is_current': token.id == request.COOKIES.get('refresh_token_id')
            })
        
        return Response({
            'success': True,
            'sessions': sessions
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Active sessions error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch active sessions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_session(request):
    """Revoke a specific session"""
    try:
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'success': False,
                'error': 'Session ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Revoke the session
        success = TokenService.revoke_refresh_token(session_id)
        
        if success:
            return Response({
                'success': True,
                'message': 'Session revoked successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Session not found or already revoked'
            }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Session revoke error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to revoke session'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)