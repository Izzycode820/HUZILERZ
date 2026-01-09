"""
Webhook URL Patterns
Defines webhook endpoints for all payment providers
"""
from django.urls import path
from . import views

app_name = 'payment_webhooks'

urlpatterns = [
    # Provider-specific webhook endpoints
    path('fapshi/', views.fapshi_webhook, name='fapshi'),
    path('mtn/', views.mtn_webhook, name='mtn'),
    path('orange/', views.orange_webhook, name='orange'),
    path('flutterwave/', views.flutterwave_webhook, name='flutterwave'),

    # Generic webhook endpoint (can handle any provider via URL param)
    path('<str:provider_name>/', views.GenericWebhookView.as_view(), name='generic'),

    # Utility endpoints
    path('status/', views.webhook_status, name='status'),
    path('test/', views.test_webhook, name='test'),
    path('logs/<uuid:payment_intent_id>/', views.webhook_logs, name='logs'),
]
