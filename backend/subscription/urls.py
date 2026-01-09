"""
Subscription URL Configuration - Hybrid REST + GraphQL

GraphQL Endpoint: /api/subscriptions/graphql
- Public Queries (no auth): plans, planDetails, trialPricing
- Authenticated Queries: billingOverview, paymentRecords, billingProfile, currentPlan, myTrial

REST Mutations: Subscription and Trial operations (webhook-driven pattern)
"""
from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from .graphql.schema import schema
from .graphql.middleware.auth import SubscriptionAuthMiddleware
from .views.subscription_views import (
    create_subscription,
    void_pending_payment,
    cancel_active_subscription,
    resume_cancelled_subscription,
    renew_subscription,
    upgrade_subscription,
    schedule_downgrade,
    reactivate_subscription,
    get_my_capabilities,
    retry_subscription_payment,
)
from .views.trial_views import (
    create_trial,
    convert_trial,
    cancel_trial,
)

app_name = 'subscription'

urlpatterns = [
    # GraphQL endpoint for all subscription queries
    # Hybrid authentication: public queries (plans, planDetails, trialPricing) + authenticated operations
    path('graphql/', csrf_exempt(GraphQLView.as_view(
        graphiql=True,
        schema=schema,
        middleware=[SubscriptionAuthMiddleware()]
    )), name='subscription-graphql'),

    # Subscription mutations (webhook-driven pattern)
    path('create/', create_subscription, name='create_subscription'),
    path('<str:subscription_id>/void/', void_pending_payment, name='void_pending_payment'),
    path('cancel/', cancel_active_subscription, name='cancel_active_subscription'),
    path('resume/', resume_cancelled_subscription, name='resume_cancelled_subscription'),
    path('renew/', renew_subscription, name='renew_subscription'),
    path('upgrade/', upgrade_subscription, name='upgrade_subscription'),
    path('schedule-downgrade/', schedule_downgrade, name='schedule_downgrade'),
    path('reactivate/', reactivate_subscription, name='reactivate_subscription'),
    path('retry-payment/', retry_subscription_payment, name='retry_subscription_payment'),

    # Capabilities endpoint (Industry Standard: Stripe/GitHub/Vercel approach)
    path('me/capabilities/', get_my_capabilities, name='get_my_capabilities'),

    # Trial mutations (webhook-driven pattern)
    path('trials/create/', create_trial, name='create_trial'),
    path('trials/convert/', convert_trial, name='convert_trial'),
    path('trials/cancel/', cancel_trial, name='cancel_trial'),
]