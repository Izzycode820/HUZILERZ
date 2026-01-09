# Workspace Service - All workspace business logic

from django.db import transaction
from django.apps import apps
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.text import slugify
import logging

logger = logging.getLogger('workspace.core.services')


class WorkspaceService:
    """
    Core service for workspace management
    Handles workspace creation, membership, and access control
    """
    
    @staticmethod
    def create_workspace(name, workspace_type, owner, **kwargs):
        """
        Create a new workspace with owner membership and default settings
        INCLUDES SUBSCRIPTION LIMIT VALIDATION
        
        Args:
            name: Workspace name
            workspace_type: Type (store, company, enterprise)
            owner: User instance
            **kwargs: Additional workspace fields
            
        Returns:
            Workspace instance
            
        Raises:
            PermissionDenied: If subscription limits are exceeded
        """
        Workspace = apps.get_model('workspace_core', 'Workspace')
        Role = apps.get_model('workspace_core', 'Role')
        Membership = apps.get_model('workspace_core', 'Membership')
        AuditLog = apps.get_model('workspace_core', 'AuditLog')
        
        try:
            with transaction.atomic():
                # CRITICAL: Check subscription limits BEFORE creation
                WorkspaceService._validate_workspace_limits(owner)
                
                # Create workspace
                workspace_data = {
                    'name': name,
                    'type': workspace_type,
                    'owner': owner,
                    'slug': kwargs.get('slug') or slugify(name),
                    **kwargs
                }
                
                workspace = Workspace.objects.create(**workspace_data)
                
                # Get or create owner role
                owner_role, _ = Role.objects.get_or_create(
                    name='owner',
                    defaults={'permissions': Role.get_default_permissions('owner')}
                )
                
                # Create owner membership
                Membership.objects.create(
                    user=owner,
                    workspace=workspace,
                    role=owner_role,
                    is_active=True
                )
                
                # Log workspace creation
                AuditLog.log_action(
                    workspace=workspace,
                    user=owner,
                    action='create',
                    resource_type='workspace',
                    resource_id=str(workspace.id),
                    description=f"Workspace '{workspace.name}' created"
                )

                # Provision workspace capabilities (Path B: new workspace creation)
                from workspace.core.tasks.workspace_capabilities_provisioning import provision_new_workspace
                provision_new_workspace.delay(str(workspace.id))

                logger.info(f"Workspace created: {workspace.name} by {owner.email}")
                return workspace
                
        except Exception as e:
            logger.error(f"Failed to create workspace: {str(e)}")
            raise ValidationError(f"Failed to create workspace: {str(e)}")
    
    @staticmethod
    def update_workspace(workspace, user, **update_data):
        """Update workspace with permission check"""
        Membership = apps.get_model('workspace_core', 'Membership')
        AuditLog = apps.get_model('workspace_core', 'AuditLog')
        
        # Check permissions
        if not WorkspaceService.can_user_manage_workspace(workspace, user):
            raise PermissionDenied("Insufficient permissions to update workspace")
        
        try:
            with transaction.atomic():
                # Update workspace
                for field, value in update_data.items():
                    if hasattr(workspace, field):
                        setattr(workspace, field, value)
                
                workspace.save()
                
                # Log update
                AuditLog.log_action(
                    workspace=workspace,
                    user=user,
                    action='update',
                    resource_type='workspace',
                    resource_id=str(workspace.id),
                    description=f"Workspace updated",
                    metadata=update_data
                )
                
                return workspace
                
        except Exception as e:
            logger.error(f"Failed to update workspace: {str(e)}")
            raise ValidationError(f"Failed to update workspace: {str(e)}")
    
    @staticmethod
    def delete_workspace(workspace, user):
        """
        Soft delete workspace with 5-day grace period
        Creates DeProvisioningRecord and schedules infrastructure cleanup
        """
        from django.utils import timezone
        from datetime import timedelta
        from workspace.core.models import AuditLog, DeProvisioningRecord
        from workspace.core.tasks.deprovisioning_tasks import deprovision_workspace

        # Only owner can delete
        if workspace.owner != user:
            raise PermissionDenied("Only workspace owner can delete workspace")

        # Prevent double deletion
        if workspace.status == 'suspended' and workspace.deleted_at:
            raise ValidationError(
                f"Workspace already deleted on {workspace.deleted_at.strftime('%Y-%m-%d')}. "
                f"Permanent deletion scheduled for {workspace.deletion_scheduled_for.strftime('%Y-%m-%d')}."
            )

        try:
            with transaction.atomic():
                # Calculate deletion schedule (5 days grace period)
                now = timezone.now()
                scheduled_for = now + timedelta(days=5)

                # Log deletion before marking as deleted
                AuditLog.log_action(
                    workspace=workspace,
                    user=user,
                    action='delete',
                    resource_type='workspace',
                    resource_id=str(workspace.id),
                    description=f"Workspace '{workspace.name}' soft-deleted (grace period: 5 days)",
                    metadata={
                        'deleted_at': now.isoformat(),
                        'scheduled_for': scheduled_for.isoformat(),
                        'grace_period_days': 5
                    }
                )

                # Soft delete workspace
                workspace.status = 'suspended'
                workspace.deleted_at = now
                workspace.deletion_scheduled_for = scheduled_for
                workspace.save(update_fields=['status', 'deleted_at', 'deletion_scheduled_for', 'updated_at'])

                # Create deprovisioning record
                deprovisioning_record = DeProvisioningRecord.objects.create(
                    workspace=workspace,
                    status='scheduled',
                    scheduled_for=scheduled_for,
                    cleanup_metadata={
                        'created_by': user.email,
                        'workspace_name': workspace.name,
                        'workspace_type': workspace.type,
                        'owner_id': workspace.owner_id
                    }
                )

                # Queue deprovisioning task (will execute after grace period)
                # Celery ETA is used to schedule task execution
                deprovision_workspace.apply_async(
                    args=[str(workspace.id)],
                    eta=scheduled_for  # Execute at scheduled time
                )

                logger.info(
                    f"Workspace soft-deleted: {workspace.name} by {user.email}. "
                    f"Deprovisioning scheduled for {scheduled_for.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        except Exception as e:
            logger.error(f"Failed to delete workspace: {str(e)}")
            raise ValidationError(f"Failed to delete workspace: {str(e)}")

    @staticmethod
    def restore_workspace(workspace, user):
        """
        Restore soft-deleted workspace during grace period
        Cancels scheduled deprovisioning
        """
        from workspace.core.models import AuditLog, DeProvisioningRecord

        # Only owner can restore
        if workspace.owner != user:
            raise PermissionDenied("Only workspace owner can restore workspace")

        # Check if workspace is soft-deleted
        if workspace.status != 'suspended' or not workspace.deleted_at:
            raise ValidationError("Workspace is not in deleted state")

        # Check if grace period expired
        from django.utils import timezone
        if timezone.now() >= workspace.deletion_scheduled_for:
            raise ValidationError(
                "Grace period expired. Workspace deprovisioning may have started. "
                "Contact support for assistance."
            )

        try:
            with transaction.atomic():
                # Cancel deprovisioning
                try:
                    deprovisioning = workspace.deprovisioning
                    deprovisioning.mark_cancelled()
                except DeProvisioningRecord.DoesNotExist:
                    logger.warning(f"No deprovisioning record found for workspace {workspace.id}")

                # Restore workspace
                workspace.status = 'active'
                workspace.deleted_at = None
                workspace.deletion_scheduled_for = None
                workspace.save(update_fields=['status', 'deleted_at', 'deletion_scheduled_for', 'updated_at'])

                # Log restoration
                AuditLog.log_action(
                    workspace=workspace,
                    user=user,
                    action='restore',
                    resource_type='workspace',
                    resource_id=str(workspace.id),
                    description=f"Workspace '{workspace.name}' restored from deletion"
                )

                logger.info(f"Workspace restored: {workspace.name} by {user.email}")

                return workspace

        except Exception as e:
            logger.error(f"Failed to restore workspace: {str(e)}")
            raise ValidationError(f"Failed to restore workspace: {str(e)}")

    @staticmethod
    def can_user_access_workspace(workspace, user):
        """Check if user can access workspace"""
        if workspace.owner == user:
            return True
        
        Membership = apps.get_model('workspace_core', 'Membership')
        return Membership.objects.filter(
            workspace=workspace,
            user=user,
            is_active=True
        ).exists()
    
    @staticmethod
    def can_user_manage_workspace(workspace, user):
        """Check if user can manage workspace"""
        if workspace.owner == user:
            return True
        
        Membership = apps.get_model('workspace_core', 'Membership')
        membership = Membership.objects.filter(
            workspace=workspace,
            user=user,
            is_active=True
        ).first()
        
        return membership and membership.has_permission('manage_workspace')
    
    @staticmethod
    def get_user_workspaces(user):
        """Get all workspaces user has access to"""
        Workspace = apps.get_model('workspace_core', 'Workspace')
        Membership = apps.get_model('workspace_core', 'Membership')
        
        # Get owned workspaces
        owned = Workspace.objects.filter(owner=user, status='active')
        
        # Get member workspaces
        member_workspace_ids = Membership.objects.filter(
            user=user,
            is_active=True
        ).values_list('workspace_id', flat=True)
        
        member = Workspace.objects.filter(
            id__in=member_workspace_ids,
            status='active'
        ).exclude(owner=user)
        
        return owned.union(member).order_by('-created_at')
    
    
    @staticmethod
    def validate_workspace_uniqueness(name, slug, exclude_id=None):
        """Validate workspace name and slug uniqueness"""
        Workspace = apps.get_model('workspace_core', 'Workspace')
        
        queryset = Workspace.objects.all()
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if queryset.filter(slug=slug).exists():
            raise ValidationError(f"Workspace with slug '{slug}' already exists")
        
        return True
    
    @staticmethod
    def create_default_workspace_for_user(user):
        """DISABLED: Create default workspace when user registers"""
        # No longer auto-create workspaces - let users choose explicitly
        logger.info(f"Default workspace creation disabled for user: {user.email}")
        return None
    
    @staticmethod
    def setup_workspace_extensions(workspace):
        """Set up workspace type-specific extensions"""
        extension_models = {
            'store': 'workspace.store.models.StoreProfile',
            'blog': 'workspace.blog.models.BlogProfile',
            'services': 'workspace.services.models.ServicesProfile'
        }
        
        try:
            # Create workspace settings (check for existing first)
            WorkspaceSettings = apps.get_model('settings', 'WorkspaceSettings')
            if not hasattr(workspace, 'workspacesettings'):
                # Double-check to avoid duplicate key error
                if not WorkspaceSettings.objects.filter(workspace=workspace).exists():
                    WorkspaceSettings.objects.create(workspace=workspace)
            
            # Create type-specific extension
            if workspace.type in extension_models:
                model_path = extension_models[workspace.type]
                try:
                    # Parse model path correctly: workspace.store.models.StoreProfile
                    parts = model_path.split('.')
                    app_label = parts[1]  # 'store' from 'workspace.store.models.StoreProfile'
                    model_name = parts[-1]  # 'StoreProfile'
                    
                    ExtensionModel = apps.get_model(f'workspace.{app_label}', model_name)
                    
                    # Check if extension already exists
                    extension_field = workspace.type.lower() + '_profile'
                    if not hasattr(workspace, extension_field):
                        ExtensionModel.objects.create(workspace=workspace)
                except Exception as ext_error:
                    logger.warning(f"Failed to create {workspace.type} extension: {str(ext_error)}")
                    
        except Exception as e:
            logger.warning(f"Failed to create workspace extensions: {str(e)}")
    
    @staticmethod
    def _validate_workspace_limits(owner):
        """
        Validate if user can create another workspace based on subscription tier
        CRITICAL SECURITY: Prevents workspace limit bypass
        Uses CapabilityEngine for tier limits (Industry standard: Shopify/Stripe pattern)

        Args:
            owner: User instance

        Raises:
            PermissionDenied: If limits exceeded
        """
        from django.contrib.auth import get_user_model
        from subscription.services.capability_engine import CapabilityEngine

        User = get_user_model()
        Workspace = apps.get_model('workspace_core', 'Workspace')

        # Get user's subscription tier and capabilities
        try:
            subscription = owner.subscription

            # Validate subscription status
            if subscription.status not in ['active', 'grace_period']:
                raise PermissionDenied(
                    f"Cannot create workspaces with {subscription.status} subscription. "
                    f"Please renew your subscription to continue."
                )

            tier = subscription.plan.tier
            tier_name = subscription.plan.name or tier.title()
        except:
            # No subscription = free tier
            tier = 'free'
            tier_name = 'Free'

        # Get capabilities from YAML (cached)
        capabilities = CapabilityEngine.get_plan_capabilities(tier)
        max_workspaces = capabilities.get('workspace_limit', 1)

        # Count current workspaces
        current_count = Workspace.objects.filter(
            owner=owner,
            status='active'  # Only count active workspaces
        ).count()

        # Check limits (0 = unlimited)
        if max_workspaces > 0 and current_count >= max_workspaces:
            raise PermissionDenied(
                f"Workspace limit exceeded. Your {tier_name} plan allows {max_workspaces} "
                f"workspace(s), but you already have {current_count}. "
                f"Upgrade your subscription to create more workspaces."
            )

        logger.info(f"Workspace limit validation passed for {owner.email}: {current_count}/{max_workspaces or 'unlimited'}")