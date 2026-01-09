"""
GraphQL queries for payment methods (public storefront)
Returns enabled payment methods for workspace checkout

Pattern follows store_settings_queries.py for consistency
"""

import graphene
import logging

from payments.models import MerchantPaymentMethod
from workspace.storefront.graphql.types.payment_types import AvailablePaymentMethodType

logger = logging.getLogger(__name__)

# Display names for providers
PROVIDER_DISPLAY_NAMES = {
    'fapshi': 'Mobile Money (MTN/Orange)',
    'mtn': 'MTN Mobile Money',
    'orange': 'Orange Money',
}

PROVIDER_DESCRIPTIONS = {
    'fapshi': 'Pay with MTN MoMo or Orange Money via Fapshi',
    'mtn': 'Pay directly with MTN Mobile Money',
    'orange': 'Pay directly with Orange Money',
}


class PaymentQueries(graphene.ObjectType):
    """
    Payment method queries for storefront checkout

    Domain-based workspace identification via middleware
    Returns enabled payment methods for customer selection
    """

    available_payment_methods = graphene.List(
        AvailablePaymentMethodType,
        description="Get available payment methods for checkout"
    )

    def resolve_available_payment_methods(self, info):
        """
        Get enabled payment methods for current workspace

        Performance: Single query, cacheable
        Security: Workspace scoping via middleware, public fields only
        """
        try:
            workspace = info.context.workspace

            if not workspace:
                logger.warning("No workspace in context for available_payment_methods query")
                return []

            # Get enabled payment methods for this workspace
            methods = MerchantPaymentMethod.objects.filter(
                workspace_id=str(workspace.id),
                enabled=True
            ).order_by('-last_used_at')

            result = []
            for method in methods:
                result.append(AvailablePaymentMethodType(
                    provider=method.provider_name,
                    display_name=PROVIDER_DISPLAY_NAMES.get(
                        method.provider_name,
                        method.provider_name.title()
                    ),
                    checkout_url=method.checkout_url,
                    description=PROVIDER_DESCRIPTIONS.get(
                        method.provider_name,
                        f'Pay with {method.provider_name.title()}'
                    )
                ))

            return result

        except Exception as e:
            logger.error(
                f"Failed to get payment methods: {str(e)}",
                exc_info=True
            )
            return []
