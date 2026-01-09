"""
Payments App URL Configuration
Main URL patterns for payments system
"""
from django.urls import path, include
from . import views

app_name = 'payments'

urlpatterns = [
    # Webhook endpoints
    path('webhooks/', include('payments.webhooks.urls')),

    # Payment status (frontend polling)
    path('status/<uuid:payment_intent_id>/', views.payment_status, name='payment_status'),

    # Payment retry
    path('retry/', views.retry_payment, name='retry_payment'),

    # Platform-level payment methods (NO workspace required - for subscriptions, domains, etc.)
    path('platform-methods/', views.platform_payment_methods, name='platform_payment_methods'),

    # Merchant payment method management (Shopify-style payment settings for storefronts)
    path('methods/', views.list_payment_methods, name='list_payment_methods'),
    path('methods/add/', views.add_payment_method, name='add_payment_method'),
    path('methods/available/', views.available_payment_methods, name='available_payment_methods'),
    path('methods/<uuid:method_id>/toggle/', views.toggle_payment_method, name='toggle_payment_method'),

    # Note: No /create/ endpoint - services call PaymentService internally
]
