# Core Workspace Views - Workspace management API endpoints

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from workspace.core.models import Workspace
from workspace.core.serializers.core_serializers import WorkspaceSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_workspaces(request):
    """
    List all user's accessible workspaces (owned + member)
    
    Returns workspaces where user is:
        1. Owner (created the workspace)
        2. Active member (invited as staff)
    
    Response includes role to distinguish owner vs staff for frontend
    """
    try:
        from django.db.models import Q, Case, When, Value, CharField
        from workspace.core.models import Membership
        
        # Get owned workspaces
        owned_workspaces = Workspace.objects.filter(
            owner=request.user,
            status__in=['active', 'suspended', 'suspended_by_plan']
        )
        
        # Get member workspaces (where user is staff)
        member_workspace_ids = Membership.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('workspace_id', flat=True)
        
        member_workspaces = Workspace.objects.filter(
            id__in=member_workspace_ids,
            status__in=['active', 'suspended', 'suspended_by_plan']
        ).exclude(owner=request.user)  # Avoid duplicates
        
        # Combine queries efficiently
        all_workspaces = (owned_workspaces | member_workspaces).distinct().annotate(
            user_role=Case(
                When(owner=request.user, then=Value('owner')),
                default=Value('staff'),
                output_field=CharField()
            )
        ).order_by('-user_role', 'status', '-updated_at')  # Owners first, then staff
        
        # Serialize workspace data with request context for permissions
        serializer = WorkspaceSerializer(all_workspaces, many=True, context={'request': request})
        
        # Add role to each workspace in response
        workspaces_data = serializer.data
        for idx, workspace in enumerate(all_workspaces):
            workspaces_data[idx]['role'] = workspace.user_role

        return Response({
            'success': True,
            'workspaces': workspaces_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing workspaces for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to list workspaces',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_workspace(request):
    """Create a new workspace"""
    try:
        serializer = WorkspaceSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Set owner to current user
            workspace = serializer.save(owner=request.user)
            
            return Response({
                'success': True,
                'workspace': WorkspaceSerializer(workspace, context={'request': request}).data,
                'message': 'Workspace created successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating workspace for user {request.user.id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create workspace',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_workspace(request, workspace_id):
    """Get specific workspace details"""
    try:
        # Get workspace by ID and validate ownership
        workspace = Workspace.objects.filter(
            id=workspace_id,
            owner=request.user,
            status='active'
        ).first()
        
        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize workspace data with request context for permissions
        serializer = WorkspaceSerializer(workspace, context={'request': request})
        
        return Response({
            'success': True,
            'workspace': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get workspace',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_workspace(request, workspace_id):
    """
    Update workspace (partial update)

    Allowed fields: name, description
    Forbidden fields: owner, type, status, subscription_tier

    Security:
    - Only owner or users with manage_workspace permission
    - Cannot change owner (prevents hijacking)
    - Cannot change type (data integrity)
    - Cannot change status (use delete endpoint)
    """
    try:
        from workspace.core.services.workspace_service import WorkspaceService
        from django.core.exceptions import PermissionDenied, ValidationError

        # Get workspace and validate access
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

        # Security: Check if user can manage workspace
        if not WorkspaceService.can_user_manage_workspace(workspace, request.user):
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': 'You do not have permission to update this workspace'
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate: Only allow specific fields to be updated
        ALLOWED_FIELDS = {'name', 'description'}
        FORBIDDEN_FIELDS = {'owner', 'type', 'status', 'subscription_tier', 'id', 'created_at', 'updated_at', 'slug'}

        request_fields = set(request.data.keys())
        forbidden_attempt = request_fields & FORBIDDEN_FIELDS

        if forbidden_attempt:
            return Response({
                'success': False,
                'error': 'Invalid fields',
                'detail': f"Cannot update fields: {', '.join(forbidden_attempt)}. These fields are read-only or require separate endpoints.",
                'allowed_fields': list(ALLOWED_FIELDS)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract only allowed fields
        update_data = {k: v for k, v in request.data.items() if k in ALLOWED_FIELDS}

        if not update_data:
            return Response({
                'success': False,
                'error': 'No valid fields to update',
                'detail': 'Please provide at least one field to update: name or description',
                'allowed_fields': list(ALLOWED_FIELDS)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate name if provided
        if 'name' in update_data:
            name = update_data['name'].strip()
            if not name:
                return Response({
                    'success': False,
                    'error': 'Invalid name',
                    'detail': 'Workspace name cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)
            if len(name) > 255:
                return Response({
                    'success': False,
                    'error': 'Invalid name',
                    'detail': 'Workspace name cannot exceed 255 characters'
                }, status=status.HTTP_400_BAD_REQUEST)
            update_data['name'] = name

        # Update workspace using service layer
        try:
            updated_workspace = WorkspaceService.update_workspace(
                workspace=workspace,
                user=request.user,
                **update_data
            )

            # Serialize updated workspace
            serializer = WorkspaceSerializer(updated_workspace, context={'request': request})

            return Response({
                'success': True,
                'workspace': serializer.data,
                'message': 'Workspace updated successfully'
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': str(e)
            }, status=status.HTTP_403_FORBIDDEN)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error updating workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update workspace',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_workspace(request, workspace_id):
    """
    Soft delete workspace (set status to suspended)

    Security:
    - ONLY workspace owner can delete
    - Audit log created before deletion
    - Cannot delete if has active deployments (future feature)

    Cascade behavior:
    - Memberships: Filtered by workspace status (inactive)
    - Content: Filtered by workspace status (inactive)
    - Settings: Preserved for restoration
    - Audit logs: Never deleted (compliance)
    """
    try:
        from workspace.core.services.workspace_service import WorkspaceService
        from django.core.exceptions import PermissionDenied, ValidationError

        # Get workspace
        workspace = Workspace.objects.filter(
            id=workspace_id,
            status='active'
        ).first()

        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found or already deleted'
            }, status=status.HTTP_404_NOT_FOUND)

        # Security: ONLY owner can delete
        if workspace.owner != request.user:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': 'Only the workspace owner can delete the workspace'
            }, status=status.HTTP_403_FORBIDDEN)

        # Delete workspace using service layer
        try:
            WorkspaceService.delete_workspace(
                workspace=workspace,
                user=request.user
            )

            # Reload workspace to get updated deletion fields
            workspace.refresh_from_db()
            serializer = WorkspaceSerializer(workspace, context={'request': request})

            return Response({
                'success': True,
                'message': 'Workspace deleted successfully. You have 5 days to restore it.',
                'workspace': serializer.data
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': str(e)
            }, status=status.HTTP_403_FORBIDDEN)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error deleting workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete workspace',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_workspace(request, workspace_id):
    """
    Restore soft-deleted workspace during grace period

    Security:
    - ONLY workspace owner can restore
    - Only during 5-day grace period
    - Cancels scheduled deprovisioning

    Returns restored workspace with status='active'
    """
    try:
        from workspace.core.services.workspace_service import WorkspaceService
        from django.core.exceptions import PermissionDenied, ValidationError

        # Get workspace (including suspended ones)
        workspace = Workspace.objects.filter(id=workspace_id).first()

        if not workspace:
            return Response({
                'success': False,
                'error': 'Workspace not found',
                'detail': 'Workspace not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Security: ONLY owner can restore
        if workspace.owner != request.user:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': 'Only the workspace owner can restore the workspace'
            }, status=status.HTTP_403_FORBIDDEN)

        # Restore workspace using service layer
        try:
            restored_workspace = WorkspaceService.restore_workspace(
                workspace=workspace,
                user=request.user
            )

            # Serialize restored workspace
            serializer = WorkspaceSerializer(restored_workspace, context={'request': request})

            return Response({
                'success': True,
                'message': 'Workspace restored successfully.',
                'workspace': serializer.data
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': 'Permission denied',
                'detail': str(e)
            }, status=status.HTTP_403_FORBIDDEN)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': 'Validation error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error restoring workspace {workspace_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to restore workspace',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)