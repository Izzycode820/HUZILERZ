"""
Core Workspace Data Export Service
Workspace-agnostic foundation for data synchronization
Implements 4 core principles: Scalable, Secure, Maintainable, Best Practices
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger('workspace.core.data_export')


class BaseWorkspaceDataExporter(ABC):
    """
    Abstract base class for workspace-specific data exporters

    Each workspace type (store, blog, service) implements this interface
    with their own business logic while maintaining consistent API
    """

    @abstractmethod
    def export_data(self, workspace_id: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export workspace data for template consumption

        Args:
            workspace_id: UUID of the workspace
            filters: Optional filters for data export

        Returns:
            Dict containing exported data structure
        """
        pass

    @abstractmethod
    def get_storefront_data(self, workspace_id: str) -> Dict[str, Any]:
        """
        Export filtered data for customer-facing sites (Shopify Storefront API pattern)

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dict containing customer-safe data only
        """
        pass

    @abstractmethod
    def get_admin_data(self, workspace_id: str, user) -> Dict[str, Any]:
        """
        Export full data for workspace management (Shopify Admin API pattern)

        Args:
            workspace_id: UUID of the workspace
            user: User requesting the data (for permission checks)

        Returns:
            Dict containing full admin data
        """
        pass

    @abstractmethod
    def get_template_variables(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get data formatted for template variable replacement

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dict with template variable mappings
        """
        pass

    @abstractmethod
    def validate_export_permissions(self, workspace_id: str, user, export_type: str) -> bool:
        """
        Validate user permissions for data export

        Args:
            workspace_id: UUID of the workspace
            user: User requesting export
            export_type: Type of export (admin, storefront, template)

        Returns:
            Boolean indicating permission status
        """
        pass


class WorkspaceDataExportService:
    """
    Central service for workspace data export coordination
    Routes requests to appropriate workspace-specific exporters
    """

    # Registry of workspace type exporters
    _exporters: Dict[str, BaseWorkspaceDataExporter] = {}

    @classmethod
    def register_exporter(cls, workspace_type: str, exporter: BaseWorkspaceDataExporter):
        """
        Register a workspace-specific exporter

        Args:
            workspace_type: Type of workspace (store, blog, service)
            exporter: Exporter instance implementing BaseWorkspaceDataExporter
        """
        cls._exporters[workspace_type] = exporter
        logger.info(f"Registered exporter for workspace type: {workspace_type}")

    @classmethod
    def get_exporter(cls, workspace_type: str) -> BaseWorkspaceDataExporter:
        """
        Get exporter for specific workspace type

        Args:
            workspace_type: Type of workspace

        Returns:
            Workspace-specific exporter instance

        Raises:
            ValueError: If workspace type not supported
        """
        if workspace_type not in cls._exporters:
            raise ValueError(f"No exporter registered for workspace type: {workspace_type}")

        return cls._exporters[workspace_type]

    def export_for_template(self, workspace_id: str, template_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Export workspace data for template consumption

        Args:
            workspace_id: UUID of the workspace
            template_type: Optional template type for filtering

        Returns:
            Dict containing template-ready data

        Raises:
            ValidationError: If workspace not found or invalid
        """
        try:
            workspace = self._get_workspace(workspace_id)
            exporter = self.get_exporter(workspace.type)

            # Get template-specific data
            template_data = exporter.get_template_variables(workspace_id)

            # Add metadata
            template_data['_metadata'] = {
                'workspace_id': workspace_id,
                'workspace_type': workspace.type,
                'workspace_name': workspace.name,
                'exported_at': timezone.now().isoformat(),
                'template_type': template_type
            }

            logger.info(f"Exported template data for workspace {workspace_id}")
            return template_data

        except Exception as e:
            logger.error(f"Failed to export template data for workspace {workspace_id}: {str(e)}")
            raise ValidationError(f"Data export failed: {str(e)}")

    def export_for_storefront(self, workspace_id: str, site_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Export customer-facing data (Shopify Storefront API pattern)

        Args:
            workspace_id: UUID of the workspace
            site_id: Optional site ID for site-specific filtering

        Returns:
            Dict containing customer-safe data
        """
        try:
            workspace = self._get_workspace(workspace_id)
            exporter = self.get_exporter(workspace.type)

            # Get storefront data (filtered for customers)
            storefront_data = exporter.get_storefront_data(workspace_id)

            # Add site-specific metadata if provided
            if site_id:
                storefront_data['_site'] = {
                    'site_id': site_id,
                    'last_sync': timezone.now().isoformat()
                }

            return storefront_data

        except Exception as e:
            logger.error(f"Failed to export storefront data for workspace {workspace_id}: {str(e)}")
            raise ValidationError(f"Storefront export failed: {str(e)}")

    def export_for_admin(self, workspace_id: str, user, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export full workspace data for admin management (Shopify Admin API pattern)

        Args:
            workspace_id: UUID of the workspace
            user: User requesting the data
            filters: Optional filters for data export

        Returns:
            Dict containing full admin data

        Raises:
            PermissionDenied: If user lacks permissions
        """
        try:
            workspace = self._get_workspace(workspace_id)
            exporter = self.get_exporter(workspace.type)

            # Validate permissions
            if not exporter.validate_export_permissions(workspace_id, user, 'admin'):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Insufficient permissions for admin data export")

            # Get full admin data
            admin_data = exporter.get_admin_data(workspace_id, user)

            return admin_data

        except Exception as e:
            logger.error(f"Failed to export admin data for workspace {workspace_id}: {str(e)}")
            raise

    def get_supported_workspace_types(self) -> List[str]:
        """
        Get list of supported workspace types

        Returns:
            List of workspace type strings
        """
        return list(self._exporters.keys())

    def _get_workspace(self, workspace_id: str):
        """
        Get workspace instance with validation

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Workspace instance

        Raises:
            ValidationError: If workspace not found
        """
        try:
            Workspace = apps.get_model('core', 'Workspace')
            return Workspace.objects.get(id=workspace_id, status='active')
        except Workspace.DoesNotExist:
            raise ValidationError(f"Workspace {workspace_id} not found or inactive")


# Singleton instance for global use
workspace_data_export_service = WorkspaceDataExportService()


class WorkspaceDataSyncEvent:
    """
    Event class for workspace data synchronization
    Used to standardize sync events across different workspace types
    """

    def __init__(
        self,
        workspace_id: str,
        event_type: str,
        data: Dict[str, Any],
        affected_models: List[str],
        user_id: Optional[str] = None
    ):
        self.workspace_id = workspace_id
        self.event_type = event_type
        self.data = data
        self.affected_models = affected_models
        self.user_id = user_id
        self.timestamp = timezone.now()
        self.event_id = self._generate_event_id()

    def _generate_event_id(self) -> str:
        """Generate unique event ID for tracking"""
        import uuid
        return f"{self.workspace_id}-{self.event_type}-{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'workspace_id': self.workspace_id,
            'event_type': self.event_type,
            'data': self.data,
            'affected_models': self.affected_models,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat()
        }


class WorkspaceDataChangeDetector:
    """
    Utility class for detecting workspace data changes
    Used by signal handlers to determine what sync events to trigger
    """

    @staticmethod
    def detect_changes(model_instance, previous_data: Optional[Dict] = None) -> List[str]:
        """
        Detect what fields have changed in a model instance

        Args:
            model_instance: Django model instance
            previous_data: Previous field values (if available)

        Returns:
            List of changed field names
        """
        if not previous_data:
            # New instance - all fields are "changed"
            return [field.name for field in model_instance._meta.fields]

        changed_fields = []
        for field in model_instance._meta.fields:
            field_name = field.name
            current_value = getattr(model_instance, field_name)
            previous_value = previous_data.get(field_name)

            if current_value != previous_value:
                changed_fields.append(field_name)

        return changed_fields

    @staticmethod
    def should_trigger_sync(changed_fields: List[str], sync_fields: List[str]) -> bool:
        """
        Determine if changes should trigger site synchronization

        Args:
            changed_fields: List of changed field names
            sync_fields: List of fields that trigger sync when changed

        Returns:
            Boolean indicating if sync should be triggered
        """
        return bool(set(changed_fields) & set(sync_fields))