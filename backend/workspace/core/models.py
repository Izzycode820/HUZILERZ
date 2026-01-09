# Core Models - Bridge file for Django migration discovery
# Imports from modular structure while maintaining enterprise scalability

from .models.workspace_model import Workspace
from .models.membership_model import Membership
from .models.role_model import Role
from .models.auditlog_model import AuditLog
from .models.base_models import BaseWorkspaceExtension, TenantScopedModel
from .models.customer_model import Customer
from .models.provisioning_models import ProvisioningRecord, ProvisioningLog
from .models.notification_settings_model import WorkspaceNotificationSettings

# Re-export all models for Django discovery
__all__ = [
    'Workspace',
    'Membership',
    'Role',
    'AuditLog',
    'BaseWorkspaceExtension',
    'TenantScopedModel',
    'Customer',
    'ProvisioningRecord',
    'ProvisioningLog',
    'WorkspaceNotificationSettings',
]