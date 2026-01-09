# Backend Requirements for Puck Data API

## Overview
The theme needs to fetch user's customized puck.data.json from the backend without JWT authentication (public storefront access).

---

## Required Backend Implementation

### 1. GraphQL Schema Addition
**File:** `backend/workspace/theme/schema.py` (or storefront schema)

```python
import graphene
from graphene_django import DjangoObjectType

class PuckDataResponse(graphene.ObjectType):
    """Response type for public puck data query"""
    success = graphene.Boolean()
    message = graphene.String()
    data = graphene.JSONString()  # The puck.data.json content

class Query(graphene.ObjectType):
    public_puck_data = graphene.Field(PuckDataResponse)

    def resolve_public_puck_data(self, info):
        """
        Public endpoint to fetch puck data for storefront
        Uses X-Store-Hostname header for tenant identification
        No JWT authentication required
        """
        try:
            # Extract hostname from request headers
            request = info.context
            hostname = request.META.get('HTTP_X_STORE_HOSTNAME', '')

            if not hostname:
                return PuckDataResponse(
                    success=False,
                    message="Missing X-Store-Hostname header",
                    data=None
                )

            # Extract subdomain from hostname
            # Example: johns-shop.huzilerz.com → johns-shop
            # Example (dev): johns-shop → johns-shop
            if '.huzilerz.com' in hostname:
                subdomain = hostname.replace('.huzilerz.com', '')
            else:
                # Dev mode: hostname is the subdomain directly
                subdomain = hostname

            # Look up DeployedSite by subdomain
            from workspace.hosting.models import DeployedSite

            deployed_site = DeployedSite.objects.select_related(
                'customization',
                'workspace'
            ).get(
                subdomain=subdomain,
                status='active'  # Only active sites
            )

            # Get puck data from customization
            if deployed_site.customization and deployed_site.customization.puck_data:
                puck_data = deployed_site.customization.puck_data
            else:
                # Fallback to default theme puck data
                puck_data = get_default_puck_data_for_theme(deployed_site.template.slug)

            return PuckDataResponse(
                success=True,
                message="Puck data retrieved successfully",
                data=puck_data
            )

        except DeployedSite.DoesNotExist:
            return PuckDataResponse(
                success=False,
                message=f"No active site found for subdomain: {subdomain}",
                data=None
            )
        except Exception as e:
            return PuckDataResponse(
                success=False,
                message=f"Error fetching puck data: {str(e)}",
                data=None
            )


def get_default_puck_data_for_theme(theme_slug):
    """
    Fallback function to get default puck data if customization doesn't exist
    """
    # Read from themes/{theme_slug}/puck.data.json
    import json
    import os

    default_path = f"themes/{theme_slug}/v1.0.0/puck.data.json"

    if os.path.exists(default_path):
        with open(default_path, 'r') as f:
            return json.load(f)

    # Ultimate fallback
    return {
        "content": [],
        "root": {}
    }
```

---

### 2. Endpoint Configuration
**File:** `backend/workspace/theme/urls.py` or similar

Ensure the schema is exposed at a public endpoint:
```python
# Example endpoint
# POST /api/themes/storefront/graphql/
# Headers: { 'X-Store-Hostname': 'johns-shop.huzilerz.com' }
```

---

### 3. CORS Configuration
**File:** `backend/config/settings.py`

Ensure theme domain can access the API:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3001',  # Dev
    'https://sneakers.cdn.com',  # Production CDN
    # ... other theme CDN URLs
]

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'x-store-hostname',  # IMPORTANT!
]
```

---

### 4. Middleware (Already Exists)
**File:** `backend/workspace/storefront/middleware.py`

✅ Already implemented - validates X-Store-Hostname and sets workspace context

---

## Data Structure

### Request (from theme):
```graphql
query GetPuckData {
  publicPuckData {
    success
    message
    data
  }
}
```

### Response (from backend):
```json
{
  "data": {
    "publicPuckData": {
      "success": true,
      "message": "Puck data retrieved successfully",
      "data": {
        "content": [
          {
            "type": "SaleBannerSection",
            "props": {
              "headline": "Sale!",
              "description": "Best deals"
            }
          },
          {
            "type": "HeroSection",
            "props": {
              "headline": "Welcome",
              "description": "Shop now"
            }
          }
        ],
        "root": {
          "pageTitle": "My Store",
          "backgroundColor": "bg-white"
        }
      }
    }
  }
}
```

---

## Testing

### Dev Testing:
```bash
# Start backend
python manage.py runserver

# Test query
curl -X POST http://localhost:8000/api/themes/storefront/graphql/ \
  -H "Content-Type: application/json" \
  -H "X-Store-Hostname: demo-store" \
  -d '{"query": "query { publicPuckData { success message data } }"}'
```

### Production Testing:
```bash
curl -X POST https://api.huzilerz.com/api/themes/storefront/graphql/ \
  -H "Content-Type: application/json" \
  -H "X-Store-Hostname: johns-shop.huzilerz.com" \
  -d '{"query": "query { publicPuckData { success message data } }"}'
```

---

## Security Notes

1. ✅ **Public endpoint** - No JWT required (storefront is public)
2. ✅ **Tenant isolation** - X-Store-Hostname ensures data scoping
3. ✅ **Read-only** - Only returns data, no mutations
4. ⚠️ **Rate limiting** - Consider adding rate limits per IP/subdomain
5. ✅ **Only active sites** - Filter ensures only published sites are accessible
