"""
Storefront Password GraphQL Input Types - For Mutations

Input types used by password protection mutations
Follows pattern from domain_inputs.py
"""

import graphene


class SetStorefrontPasswordInput(graphene.InputObjectType):
    """
    Input for setting/updating storefront password

    Used by setStorefrontPassword mutation
    """
    workspace_id = graphene.ID(required=True)
    password = graphene.String()
    enabled = graphene.Boolean()
    description = graphene.String()
