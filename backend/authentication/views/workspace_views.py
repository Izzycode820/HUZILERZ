"""
Workspace Authentication Views - Workspace switching
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from authentication.services import AuthenticationService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_workspace(request):
    """
    Switch user's active workspace context (Industry Standard: Shopify/Stripe/Linear)

    v3.0 - Header-Based Workspace Context:
    - NO JWT regeneration (workspace sent via X-Workspace-Id header per-request)
    - Backend validates user has access to workspace
    - Returns workspace details + membership (role, permissions)
    - Frontend updates Zustand + sends header on next request

    Body:
    {
        "workspace_id": "uuid-of-workspace"
    }

    Response:
    {
        "success": true,
        "workspace": {
            "id": "...",
            "name": "...",
            "type": "store",
            "status": "active",
            "owner_id": "...",
            "created_at": "..."
        },
        "membership": {
            "role": "owner",
            "permissions": ["read", "write", "delete", "invite", "admin"],
            "joined_at": "..."
        }
    }
    """
    try:
        data = request.data
        workspace_id = data.get('workspace_id')

        if not workspace_id:
            return Response({
                'success': False,
                'error': 'workspace_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # v3.0 - Validate access and return workspace details (NO tokens)
        result = AuthenticationService.switch_workspace(
            request.user,
            workspace_id,
            request
        )

        if result['success']:
            # Return workspace details + membership (NO tokens)
            response_data = {
                'success': True,
                'workspace': result['workspace'],
                'membership': result['membership'],
                'message': 'Workspace switched successfully'
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_403_FORBIDDEN if 'Access denied' in result['error'] else status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Workspace switch error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Workspace switch failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_workspace(request):
    """
    Leave current workspace context (Industry Standard: Stateless)

    v3.0 - Header-Based Workspace Context:
    - NO JWT regeneration (workspace sent via X-Workspace-Id header)
    - Backend logs the event for audit trail
    - Frontend clears workspace from Zustand
    - Frontend stops sending X-Workspace-Id header on next request

    This endpoint exists purely for logging/audit purposes
    """
    try:
        # v3.0 - No refresh token needed, just log the event
        result = AuthenticationService.leave_workspace(
            request.user,
            request
        )

        if result['success']:
            response_data = {
                'success': True,
                'message': result['message']
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Leave workspace error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Leave workspace failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)