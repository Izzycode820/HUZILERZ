# Member Management Views - Workspace member CRUD API endpoints

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from workspace.core.models import Workspace
from workspace.core.serializers import MembershipSerializer
from workspace.core.services import MembershipService
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_members(request, workspace_id):
    """
    List all workspace members

    GET /api/workspaces/<workspace_id>/members/

    Security: Requires workspace member access
    Returns: List of active members with roles and permissions
    """
    try:
        # Get workspace
        workspace = Workspace.objects.filter(
            id=workspace_id,
            status='active'
        ).first()

        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get members using service layer (includes permission check)
        try:
            memberships = MembershipService.get_workspace_members(workspace, request.user)

            # Serialize membership data
            serializer = MembershipSerializer(memberships, many=True)

            return Response({
                'success': True,
                'members': serializer.data,
                'total': len(serializer.data)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': str(e)
            }, status=status.HTTP_403_FORBIDDEN)

    except Exception as e:
        logger.error(f"Error listing members for workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to list members',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_member(request, workspace_id):
    """
    Invite user to workspace

    POST /api/workspaces/<workspace_id>/members/invite/

    Body:
    {
        "email": "user@example.com",
        "role": "editor"  // Optional, defaults to "viewer"
    }

    Security: Requires admin or owner permissions
    Rate Limit: Once per email per workspace per 20 minutes
    """
    try:
        # Get workspace
        workspace = Workspace.objects.filter(
            id=workspace_id,
            status='active'
        ).first()

        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get request data
        email = request.data.get('email')
        role_name = request.data.get('role', 'viewer')

        if not email:
            return Response({
                'success': False,
                'error': 'email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Invite user using service layer
        try:
            membership = MembershipService.invite_user(
                workspace=workspace,
                inviter=request.user,
                email=email,
                role_name=role_name
            )

            # Serialize membership data
            serializer = MembershipSerializer(membership)

            return Response({
                'success': True,
                'message': f"Invitation sent to {email}",
                'membership': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            error_msg = str(e)

            # Determine appropriate status code
            if 'Rate limit' in error_msg:
                return Response({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'detail': error_msg
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif 'Insufficient permissions' in error_msg or 'Only workspace owner' in error_msg:
                return Response({
                    'success': False,
                    'error': 'Permission denied',
                    'detail': error_msg
                }, status=status.HTTP_403_FORBIDDEN)
            elif 'not found' in error_msg.lower() or 'already a member' in error_msg.lower():
                return Response({
                    'success': False,
                    'error': 'Invalid request',
                    'detail': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to invite member',
                    'detail': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error inviting member to workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to invite member',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_member(request, workspace_id, user_id):
    """
    Remove member from workspace

    DELETE /api/workspaces/<workspace_id>/members/<user_id>/

    Security: Requires admin or owner permissions
    Note: Cannot remove workspace owner or self
    """
    try:
        # Get workspace
        workspace = Workspace.objects.filter(
            id=workspace_id,
            status='active'
        ).first()

        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get user to remove
        try:
            user_to_remove = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found',
                'detail': f'User with ID {user_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Cannot remove self
        if request.user == user_to_remove:
            return Response({
                'success': False,
                'error': 'Cannot remove self',
                'detail': 'Use a separate "leave workspace" endpoint to remove yourself'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Remove user using service layer
        try:
            MembershipService.remove_user(
                workspace=workspace,
                remover=request.user,
                user_to_remove=user_to_remove
            )

            return Response({
                'success': True,
                'message': 'Member removed successfully',
                'removed_user': {
                    'user_email': user_to_remove.email,
                    'user_id': user_to_remove.id
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = str(e)

            if 'Insufficient permissions' in error_msg:
                return Response({
                    'success': False,
                    'error': 'Permission denied',
                    'detail': error_msg
                }, status=status.HTTP_403_FORBIDDEN)
            elif 'Cannot remove workspace owner' in error_msg or 'not a member' in error_msg:
                return Response({
                    'success': False,
                    'error': 'Invalid request',
                    'detail': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to remove member',
                    'detail': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error removing member {user_id} from workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to remove member',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def change_member_role(request, workspace_id, user_id):
    """
    Change member's role in workspace

    PATCH /api/workspaces/<workspace_id>/members/<user_id>/role/

    Body:
    {
        "role": "admin"
    }

    Security: Prevents privilege escalation
    - Only owner can assign admin role
    - Cannot change own role
    - Cannot change workspace owner role
    - Admin can only assign editor or viewer roles
    """
    try:
        # Get workspace
        workspace = Workspace.objects.filter(
            id=workspace_id,
            status='active'
        ).first()

        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get user whose role is being changed
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found',
                'detail': f'User with ID {user_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get new role from request
        new_role_name = request.data.get('role')

        if not new_role_name:
            return Response({
                'success': False,
                'error': 'role is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Change role using service layer
        try:
            membership = MembershipService.change_user_role(
                workspace=workspace,
                changer=request.user,
                user=user,
                new_role_name=new_role_name
            )

            # Serialize updated membership
            serializer = MembershipSerializer(membership)

            return Response({
                'success': True,
                'message': 'Role changed successfully',
                'membership': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = str(e)

            if 'Insufficient permissions' in error_msg or 'Only workspace owner' in error_msg:
                return Response({
                    'success': False,
                    'error': 'Permission denied',
                    'detail': error_msg
                }, status=status.HTTP_403_FORBIDDEN)
            elif ('Cannot change' in error_msg or 'not found' in error_msg.lower() or
                  'not a member' in error_msg or 'Cannot assign owner' in error_msg):
                return Response({
                    'success': False,
                    'error': 'Invalid request',
                    'detail': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to change role',
                    'detail': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error changing role for user {user_id} in workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to change role',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
