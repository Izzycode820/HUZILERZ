from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from .graphql.schema import schema as storefront_schema
from .views import StorefrontGraphQLView

app_name = 'storefront'

# Rate limit GraphQL endpoint
# Uses custom view that injects tenant context from StoreIdentificationMiddleware
graphql_view = csrf_exempt(
    ratelimit(key='ip', rate='100/m', method='POST')(
        StorefrontGraphQLView.as_view(
            graphiql=True,  # Enable GraphiQL in dev only
            schema=storefront_schema  # Explicitly use Storefront schema
        )
    )
)

urlpatterns = [
    # Single GraphQL endpoint (replaces all REST endpoints)
    path('graphql/', graphql_view, name='graphql'),
]
