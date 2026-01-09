"""
Theme GraphQL Input Types

Input types for theme management mutations
All mutations require authentication + workspace scoping
"""

import graphene
from graphene.types import JSONString


class UpdateThemeCustomizationInput(graphene.InputObjectType):
    """
    Input for updating theme customization

    Updates user's puck data and config from Puck editor
    Both fields optional - update only what changed
    """
    puck_data = JSONString(
        description="User's customized Puck data (page layout)"
    )
    puck_config = JSONString(
        description="User's customized Puck config (component settings)"
    )
