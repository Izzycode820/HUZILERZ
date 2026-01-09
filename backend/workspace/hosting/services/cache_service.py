"""
Workspace Cache Service
Cache isolation per workspace with GraphQL support (Shopify model)
Prevents cache collisions between workspaces
"""
import hashlib
import json
from django.core.cache import cache
from typing import Any, Optional


class WorkspaceCacheService:
    """
    Cache isolation per workspace
    GraphQL-aware caching with query fingerprinting
    """

    @staticmethod
    def get_cache_key(workspace_id: str, key: str, version: str = None) -> str:
        """
        Generate namespaced cache key with optional version hashing
        Format: ws:{workspace_id}:{hashed_key} or ws:{workspace_id}:{hashed_key}:v{version_hash}

        Version-based caching ensures that when theme content changes,
        cache keys automatically change, preventing stale data from being served.

        Args:
            workspace_id: Workspace UUID
            key: Cache key (can be GraphQL query + variables)
            version: Optional version identifier (e.g., timestamp, version ID)
                    Will be hashed to create a consistent short hash

        Returns:
            Namespaced cache key with optional version suffix

        Examples:
            >>> # Without version
            >>> get_cache_key("ws-123", "puck_data")
            'ws:ws-123:a5f3c2b1'

            >>> # With version (theme's last_edited_at timestamp)
            >>> get_cache_key("ws-123", "puck_data", "2024-01-15T10:30:00")
            'ws:ws-123:a5f3c2b1:v8d9e1f2'
        """
        # Include version in key if provided
        if version:
            # Hash version to create consistent short identifier
            version_hash = hashlib.md5(str(version).encode()).hexdigest()[:8]
            key = f"{key}:v{version_hash}"

        # Hash the final key for consistent length
        key_hash = hashlib.md5(key.encode()).hexdigest()[:12]
        return f"ws:{workspace_id}:{key_hash}"

    @staticmethod
    def get_graphql_cache_key(workspace_id: str, query: str, variables: dict = None) -> str:
        """
        Generate cache key for GraphQL query

        Args:
            workspace_id: Workspace UUID
            query: GraphQL query string
            variables: GraphQL variables dict

        Returns:
            Namespaced cache key for GraphQL operation
        """
        # Create fingerprint from query + variables
        variables_str = json.dumps(variables or {}, sort_keys=True)
        fingerprint = f"{query}::{variables_str}"

        # Hash to consistent length
        fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()[:16]

        return f"ws:{workspace_id}:gql:{fingerprint_hash}"

    @classmethod
    def get(cls, workspace_id: str, key: str, default=None, version: str = None) -> Any:
        """
        Get cached value for workspace with optional version

        Args:
            workspace_id: Workspace UUID
            key: Cache key
            default: Default value if not in cache
            version: Optional version identifier (e.g., theme's last_edited_at)

        Returns:
            Cached value or default

        Examples:
            >>> # Get without version
            >>> WorkspaceCacheService.get("ws-123", "puck_data")

            >>> # Get with version (will only match if version hash matches)
            >>> WorkspaceCacheService.get("ws-123", "puck_data", version="2024-01-15T10:30:00")
        """
        cache_key = cls.get_cache_key(workspace_id, key, version)
        return cache.get(cache_key, default)

    @classmethod
    def set(cls, workspace_id: str, key: str, value: Any, timeout: int = 300, version: str = None):
        """
        Set cached value for workspace with optional version

        Args:
            workspace_id: Workspace UUID
            key: Cache key
            value: Value to cache
            timeout: TTL in seconds (default 5 minutes)
            version: Optional version identifier (auto-invalidates when version changes)

        Examples:
            >>> # Cache puck data with theme version
            >>> from django.utils import timezone
            >>> theme_version = str(customization.last_edited_at)
            >>> WorkspaceCacheService.set(
            ...     "ws-123",
            ...     "puck_data",
            ...     puck_data,
            ...     timeout=600,
            ...     version=theme_version
            ... )
        """
        cache_key = cls.get_cache_key(workspace_id, key, version)
        cache.set(cache_key, value, timeout)

    @classmethod
    def get_graphql(cls, workspace_id: str, query: str, variables: dict = None, default=None) -> Any:
        """
        Get cached GraphQL query result

        Args:
            workspace_id: Workspace UUID
            query: GraphQL query string
            variables: GraphQL variables
            default: Default value if not cached

        Returns:
            Cached GraphQL result or default
        """
        cache_key = cls.get_graphql_cache_key(workspace_id, query, variables)
        return cache.get(cache_key, default)

    @classmethod
    def set_graphql(cls, workspace_id: str, query: str, variables: dict, result: Any, timeout: int = 300):
        """
        Cache GraphQL query result

        Args:
            workspace_id: Workspace UUID
            query: GraphQL query string
            variables: GraphQL variables
            result: Query result to cache
            timeout: TTL in seconds
        """
        cache_key = cls.get_graphql_cache_key(workspace_id, query, variables)
        cache.set(cache_key, result, timeout)

    @classmethod
    def delete(cls, workspace_id: str, key: str, version: str = None):
        """
        Delete cached value for workspace with optional version

        Args:
            workspace_id: Workspace UUID
            key: Cache key
            version: Optional version identifier to delete specific version
        """
        cache_key = cls.get_cache_key(workspace_id, key, version)
        cache.delete(cache_key)

    @classmethod
    def clear_workspace_cache(cls, workspace_id: str):
        """
        Clear all cache for workspace (emergency use)
        Use after mutations that affect multiple queries
        """
        pattern = f"ws:{workspace_id}:*"
        cache.delete_pattern(pattern)

    @classmethod
    def invalidate_graphql_by_type(cls, workspace_id: str, typename: str):
        """
        Invalidate GraphQL queries by typename
        Useful after mutations (e.g., Product created → invalidate Product queries)

        Args:
            workspace_id: Workspace UUID
            typename: GraphQL type (e.g., 'Product', 'Order')
        """
        # Pattern to match all GraphQL queries for this type
        pattern = f"ws:{workspace_id}:gql:*"

        # Note: In production, maintain a reverse index:
        # typename -> [cache_keys] for efficient invalidation
        # For now, we clear all GraphQL cache for workspace
        cache.delete_pattern(pattern)
