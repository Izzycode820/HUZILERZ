"""
SEO Management GraphQL Input Types - For Mutations

Input types used by SEO management mutations
Follows pattern from domain_inputs.py
"""

import graphene


class UpdateStorefrontSEOInput(graphene.InputObjectType):
    """
    Input for updating storefront SEO settings

    Used by updateStorefrontSEO mutation
    """
    workspace_id = graphene.ID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    seo_keywords = graphene.String()
    seo_image_url = graphene.String()
