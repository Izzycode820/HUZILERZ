"""
Store Profile GraphQL Mutations

Mutation for updating store profile settings.
Workspace-scoped via JWT middleware with atomic transactions.
"""

import graphene
import logging
from ..types.store_profile_types import StoreProfileType, StoreProfileInput
from workspace.store.services.store_profile_service import store_profile_service

logger = logging.getLogger(__name__)


class UpdateStoreProfile(graphene.Mutation):
    """
    Update store profile settings.
    
    Validates Cameroon phone numbers and returns proper error messages.
    Uses atomic transaction for data integrity.
    """
    
    class Arguments:
        input = StoreProfileInput(required=True)
    
    success = graphene.Boolean()
    store_profile = graphene.Field(StoreProfileType)
    message = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user
        
        if not workspace:
            logger.warning("No workspace in context for updateStoreProfile mutation")
            return UpdateStoreProfile(
                success=False,
                error="Workspace not found"
            )
        
        try:
            # Convert GraphQL input to dict, filtering None values
            update_data = {}
            for field, value in input.items():
                if value is not None:
                    update_data[field] = value
            
            # Call service layer
            result = store_profile_service.update_store_profile(
                workspace=workspace,
                update_data=update_data,
                user=user
            )
            
            return UpdateStoreProfile(
                success=result['success'],
                store_profile=result.get('profile'),
                message=result.get('message'),
                error=result.get('error')
            )
            
        except Exception as e:
            logger.error(f"Store profile update mutation failed: {str(e)}", exc_info=True)
            return UpdateStoreProfile(
                success=False,
                error=f"Store profile update failed: {str(e)}"
            )


class StoreProfileMutations(graphene.ObjectType):
    """Store profile mutations collection"""
    
    update_store_profile = UpdateStoreProfile.Field()
