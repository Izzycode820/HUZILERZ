# Core Workspace Views - RESTful API endpoints

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.apps import apps

from ..serializers import WorkspaceSerializer, MembershipSerializer, RoleSerializer
from ..services.workspace_service import WorkspaceService
from ..services.membership_service import MembershipService


class WorkspaceViewSet(viewsets.ModelViewSet):
    """Workspace management API"""
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return workspaces user has access to"""
        return WorkspaceService.get_user_workspaces(self.request.user)
    
    def perform_create(self, serializer):
        """Create workspace with user as owner"""
        workspace = serializer.save(owner=self.request.user)
        WorkspaceService.setup_workspace_extensions(workspace)
    
    def perform_update(self, serializer):
        """Update workspace with permission check"""
        workspace = self.get_object()
        if not WorkspaceService.can_user_manage_workspace(workspace, self.request.user):
            raise PermissionDenied("Insufficient permissions to update workspace")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Soft delete workspace"""
        WorkspaceService.delete_workspace(instance, self.request.user)
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """Invite user to workspace"""
        workspace = self.get_object()
        email = request.data.get('email')
        role_name = request.data.get('role', 'member')
        
        if not WorkspaceService.can_user_manage_workspace(workspace, request.user):
            raise PermissionDenied("Insufficient permissions to invite members")
        
        try:
            membership = MembershipService.invite_user_to_workspace(
                workspace=workspace,
                email=email,
                role_name=role_name,
                invited_by=request.user
            )
            serializer = MembershipSerializer(membership)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MembershipViewSet(viewsets.ModelViewSet):
    """Workspace membership management API"""
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return memberships for workspaces user has access to"""
        Membership = apps.get_model('core', 'Membership')
        user_workspaces = WorkspaceService.get_user_workspaces(self.request.user)
        return Membership.objects.filter(workspace__in=user_workspaces)
    
    def perform_update(self, serializer):
        """Update membership with permission check"""
        membership = self.get_object()
        if not WorkspaceService.can_user_manage_workspace(membership.workspace, self.request.user):
            raise PermissionDenied("Insufficient permissions to update membership")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate membership"""
        membership = self.get_object()
        
        if not WorkspaceService.can_user_manage_workspace(membership.workspace, request.user):
            raise PermissionDenied("Insufficient permissions to deactivate membership")
        
        MembershipService.deactivate_membership(membership, request.user)
        return Response({'status': 'membership deactivated'})


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Role management API - Read only for now"""
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get all roles"""
        Role = apps.get_model('core', 'Role')
        return Role.objects.all()