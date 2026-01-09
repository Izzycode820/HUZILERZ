"""
DataLoaders for Bulk Operations

Prevents N+1 queries when resolving bulk operations in GraphQL
Follows GraphQL architecture standards for performance optimization
"""

from promise import Promise
from promise.dataloader import DataLoader
from workspace.store.models.bulk_operation import BulkOperation


class BulkOperationLoader(DataLoader):
    """DataLoader for BulkOperation objects to prevent N+1 queries"""

    def batch_load_fn(self, bulk_operation_ids):
        """Batch load bulk operations by IDs"""
        bulk_operations = BulkOperation.objects.filter(id__in=bulk_operation_ids)
        bulk_operation_dict = {str(op.id): op for op in bulk_operations}

        return Promise.resolve([
            bulk_operation_dict.get(str(op_id)) for op_id in bulk_operation_ids
        ])


class BulkOperationByWorkspaceLoader(DataLoader):
    """DataLoader for bulk operations by workspace ID"""

    def batch_load_fn(self, workspace_ids):
        """Batch load bulk operations by workspace IDs"""
        bulk_operations = BulkOperation.objects.filter(workspace_id__in=workspace_ids)

        # Group by workspace ID
        workspace_operations = {}
        for op in bulk_operations:
            workspace_id = str(op.workspace_id)
            if workspace_id not in workspace_operations:
                workspace_operations[workspace_id] = []
            workspace_operations[workspace_id].append(op)

        return Promise.resolve([
            workspace_operations.get(str(workspace_id), []) for workspace_id in workspace_ids
        ])


class BulkOperationByUserLoader(DataLoader):
    """DataLoader for bulk operations by user ID"""

    def batch_load_fn(self, user_ids):
        """Batch load bulk operations by user IDs"""
        bulk_operations = BulkOperation.objects.filter(user_id__in=user_ids)

        # Group by user ID
        user_operations = {}
        for op in bulk_operations:
            user_id = str(op.user_id)
            if user_id not in user_operations:
                user_operations[user_id] = []
            user_operations[user_id].append(op)

        return Promise.resolve([
            user_operations.get(str(user_id), []) for user_id in user_ids
        ])


def get_bulk_operation_loader(info):
    """Get or create bulk operation loader from context"""
    if not hasattr(info.context, 'bulk_operation_loader'):
        info.context.bulk_operation_loader = BulkOperationLoader()
    return info.context.bulk_operation_loader


def get_bulk_operation_by_workspace_loader(info):
    """Get or create bulk operation by workspace loader from context"""
    if not hasattr(info.context, 'bulk_operation_by_workspace_loader'):
        info.context.bulk_operation_by_workspace_loader = BulkOperationByWorkspaceLoader()
    return info.context.bulk_operation_by_workspace_loader


def get_bulk_operation_by_user_loader(info):
    """Get or create bulk operation by user loader from context"""
    if not hasattr(info.context, 'bulk_operation_by_user_loader'):
        info.context.bulk_operation_by_user_loader = BulkOperationByUserLoader()
    return info.context.bulk_operation_by_user_loader