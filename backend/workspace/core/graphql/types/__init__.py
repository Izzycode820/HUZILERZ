"""
Shared GraphQL types for workspace core

Export all types for easy importing by sub-apps:
- from workspace.core.graphql.types import CustomerType
"""

from .customer_types import (
    CustomerType,
    CustomerInfoInput,
)

__all__ = [
    'CustomerType',
    'CustomerInfoInput',
]
