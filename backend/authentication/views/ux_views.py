"""
User Experience Views - Authentication prompts and UX flows
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from authentication.services import SessionService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_status(request):
    """Check if user should be prompted to authenticate"""
    try:
        # For authenticated users
        if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'show_prompt': False,
                'user': {
                    'id': request.user.id,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                }
            })
        
        # For guest users
        should_prompt = SessionService.should_prompt_authentication(request)
        session = getattr(request, 'user_session', None)
        
        context = 'general'
        if session:
            if session.page_views >= 10:
                context = 'engaged_browsing'
            elif session.actions_count >= 5:
                context = 'active_user'
        
        return Response({
            'authenticated': False,
            'show_prompt': should_prompt,
            'context': context,
            'prompt_dismissed_count': session.auth_prompt_dismissed_count if session else 0
        })
    
    except Exception as e:
        logger.error(f"Auth status check error: {str(e)}")
        return Response({
            'authenticated': False,
            'show_prompt': False,
            'context': 'general'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def mark_auth_prompt_shown(request):
    """Mark that authentication prompt was shown to user"""
    try:
        SessionService.mark_auth_prompt_shown(request)
        
        return Response({
            'success': True,
            'message': 'Prompt marked as shown'
        })
    
    except Exception as e:
        logger.error(f"Mark prompt shown error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to mark prompt as shown'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def dismiss_auth_prompt(request):
    """Mark that authentication prompt was dismissed by user"""
    try:
        session = getattr(request, 'user_session', None)
        if session:
            session.dismiss_auth_prompt()
        
        return Response({
            'success': True,
            'message': 'Prompt dismissed'
        })
    
    except Exception as e:
        logger.error(f"Dismiss prompt error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to dismiss prompt'
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check for authentication system"""
    return Response({
        'status': 'healthy',
        'service': 'authentication',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat()
    })