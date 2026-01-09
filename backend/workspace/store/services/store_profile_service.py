"""
Store Profile Service - Store Settings Management

Service layer for StoreProfile CRUD operations.
Follows location_service.py patterns with atomic transactions and comprehensive error handling.

Performance: < 50ms response time for operations
Reliability: Atomic transactions with rollback on failure
Security: Workspace scoping ensures tenant isolation
"""

import logging
from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from workspace.store.models import StoreProfile

logger = logging.getLogger('workspace.store.profile')


class StoreProfileService:
    """
    Service for managing store profile settings.
    
    All operations are workspace-scoped for multi-tenant security.
    Atomic transactions ensure data integrity.
    """
    
    @staticmethod
    def get_store_profile(workspace) -> Dict[str, Any]:
        """
        Get store profile for workspace.
        
        Returns:
            dict with 'success', 'profile' or 'error'
        """
        try:
            profile = StoreProfile.objects.get(workspace=workspace)
            return {
                'success': True,
                'profile': profile
            }
        except StoreProfile.DoesNotExist:
            logger.warning(f"Store profile not found for workspace {workspace.id}")
            return {
                'success': False,
                'error': 'Store profile not found'
            }
        except Exception as e:
            logger.error(f"Failed to get store profile: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to get store profile: {str(e)}'
            }
    
    @staticmethod
    def update_store_profile(
        workspace,
        update_data: Dict[str, Any],
        user=None
    ) -> Dict[str, Any]:
        """
        Update store profile settings.
        
        Atomic transaction with proper locking to prevent race conditions.
        Validates all fields including Cameroon phone format.
        
        Args:
            workspace: Workspace instance
            update_data: Dict of fields to update
            user: Optional user for audit (unused currently)
        
        Returns:
            dict with 'success', 'profile', 'message' or 'error'
        """
        try:
            with transaction.atomic():
                # Get profile with lock to prevent concurrent updates
                profile = StoreProfile.objects.select_for_update().get(
                    workspace=workspace
                )
                
                # Define allowed fields for update
                allowed_fields = {
                    'store_name', 'store_description', 'store_email',
                    'support_email', 'phone_number', 'whatsapp_number',
                    'timezone'
                }
                
                # Update only allowed fields
                for field, value in update_data.items():
                    if field in allowed_fields and value is not None:
                        setattr(profile, field, value)
                
                # Validate and save (full_clean called in save)
                profile.save()
                
                logger.info(f"Store profile updated for workspace {workspace.id}")
                
                return {
                    'success': True,
                    'profile': profile,
                    'message': 'Store settings updated successfully'
                }
                
        except StoreProfile.DoesNotExist:
            logger.warning(f"Store profile not found for workspace {workspace.id}")
            return {
                'success': False,
                'error': 'Store profile not found'
            }
        except ValidationError as e:
            logger.warning(f"Store profile validation failed: {str(e)}")
            # Extract validation error messages
            if hasattr(e, 'message_dict'):
                error_messages = []
                for field, messages in e.message_dict.items():
                    error_messages.extend(messages)
                error_str = '; '.join(error_messages)
            else:
                error_str = str(e)
            return {
                'success': False,
                'error': error_str
            }
        except Exception as e:
            logger.error(f"Store profile update failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Store profile update failed: {str(e)}'
            }
    
    @staticmethod
    def create_for_workspace(workspace) -> Dict[str, Any]:
        """
        Create store profile during workspace provisioning.
        Idempotent - uses get_or_create.
        
        Args:
            workspace: Workspace instance
        
        Returns:
            dict with 'success', 'profile', 'created' or 'error'
        """
        try:
            profile, created = StoreProfile.get_or_create_for_workspace(workspace)
            
            logger.info(
                f"Store profile {'created' if created else 'retrieved'} "
                f"for workspace {workspace.id}"
            )
            
            return {
                'success': True,
                'profile': profile,
                'created': created
            }
        except Exception as e:
            logger.error(f"Store profile creation failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Store profile creation failed: {str(e)}'
            }


# Global instance for easy import
store_profile_service = StoreProfileService()
