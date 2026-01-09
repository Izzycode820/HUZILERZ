"""
Workspace Rate Limiting Middleware
GraphQL-aware rate limiting per workspace based on subscription tier
Prevents noisy neighbor problem in shared pool infrastructure
"""
import redis
import time
import json
from django.conf import settings
from django.http import JsonResponse
from typing import Tuple, Optional


class WorkspaceRateLimitMiddleware:
    """
    Rate limit per workspace based on subscription tier
    Works with GraphQL queries
    """

    # Rate limits per tier (requests per minute)
    TIER_LIMITS = {
        'free': 60,          # 1 req/sec
        'beginning': 300,    # 5 req/sec
        'pro': 1200,         # 20 req/sec
        'enterprise': 6000,  # 100 req/sec
    }

    # GraphQL operation costs (heavier queries cost more)
    OPERATION_COSTS = {
        'query': 1,
        'mutation': 2,
        'subscription': 3,
    }

    def __init__(self, get_response):
        self.get_response = get_response

        # Connect to Redis
        redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
        redis_port = getattr(settings, 'REDIS_PORT', 6379)

        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )

    def __call__(self, request):
        # Extract workspace_id from request
        workspace_id = self.get_workspace_id(request)

        if workspace_id:
            # Check rate limit
            allowed, remaining, retry_after = self.check_rate_limit(workspace_id, request)

            if not allowed:
                return JsonResponse({
                    'errors': [{
                        'message': 'Rate limit exceeded. Please upgrade your plan for higher limits.',
                        'extensions': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'retry_after': retry_after
                        }
                    }]
                }, status=429)

            # Add rate limit headers
            response = self.get_response(request)
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Limit'] = str(self.get_limit(getattr(request, 'user', None)))
            return response

        return self.get_response(request)

    def check_rate_limit(self, workspace_id: str, request) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit

        Returns:
            (allowed: bool, remaining: int, retry_after: int)
        """
        # Get user's tier and limit
        limit = self.get_limit(request.user)

        # Calculate cost for GraphQL operations
        cost = self.get_request_cost(request)

        # Redis sliding window rate limit
        window = 60  # 1 minute window
        current_time = int(time.time())
        window_key = f"ratelimit:ws:{workspace_id}:{current_time // window}"

        # Increment counter by cost
        count = self.redis_client.incrby(window_key, cost)

        # Set expiry on first request
        if count == cost:
            self.redis_client.expire(window_key, window * 2)  # Keep for 2 windows

        allowed = count <= limit
        remaining = max(0, limit - count)
        retry_after = window  # Seconds until limit resets

        return (allowed, remaining, retry_after)

    def get_request_cost(self, request) -> int:
        """
        Calculate cost of request
        GraphQL mutations cost more than queries
        """
        # Check if GraphQL request
        if request.path.endswith('/graphql') or 'graphql' in request.path.lower():
            try:
                # Parse GraphQL operation type
                if request.method == 'POST':
                    body = json.loads(request.body.decode('utf-8'))
                    query = body.get('query', '')

                    # Detect operation type
                    query_lower = query.strip().lower()
                    if query_lower.startswith('mutation'):
                        return self.OPERATION_COSTS['mutation']
                    elif query_lower.startswith('subscription'):
                        return self.OPERATION_COSTS['subscription']
                    else:
                        return self.OPERATION_COSTS['query']
            except:
                pass

        # Default cost
        return 1

    def get_workspace_id(self, request) -> Optional[str]:
        """
        Extract workspace_id from request

        Supports:
        - GraphQL variables: {"workspaceId": "..."}
        - Header: X-Workspace-ID
        - Path: /api/workspaces/{workspace_id}/...
        """
        # Check GraphQL variables
        if request.method == 'POST' and ('graphql' in request.path.lower()):
            try:
                body = json.loads(request.body.decode('utf-8'))
                variables = body.get('variables', {})
                workspace_id = variables.get('workspaceId') or variables.get('workspace_id')
                if workspace_id:
                    return workspace_id
            except:
                pass

        # Check header
        workspace_id = request.META.get('HTTP_X_WORKSPACE_ID')
        if workspace_id:
            return workspace_id

        # Check path
        if '/workspaces/' in request.path:
            parts = request.path.split('/workspaces/')
            if len(parts) > 1:
                return parts[1].split('/')[0]

        return None

    def get_limit(self, user) -> int:
        """Get rate limit for user based on subscription tier"""
        if user is None or not user.is_authenticated:
            return self.TIER_LIMITS['free']

        try:
            tier = user.subscription.plan.tier
            return self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
        except:
            return self.TIER_LIMITS['free']
