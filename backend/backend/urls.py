"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('authentication.urls')),

    # Theme system (platform-level)
    path('api/themes/', include('theme.urls')),

    # Modern workspace-scoped endpoints (SaaS best practice)
    path('api/workspaces/', include('workspace.urls')),

    # Subscription & Billing system
    path('api/subscriptions/', include('subscription.urls')),

    # Payments system (multi-provider: Fapshi, MTN, Orange, Flutterwave)
    path('api/payments/', include('payments.urls')),

    # Notifications system (user-level + workspace-scoped)
    path('api/notifications/', include('notifications.urls')),

    # Storefront GraphQL (domain-based, workspace identified by hostname)
    path('api/', include('workspace.storefront.urls')),

    # API documentation
    path('api/', include('rest_framework.urls')),
]

# Storefront serving (Phase 4: SEO Implementation)
# IMPORTANT: This must come AFTER all API routes
# Serves storefront HTML with SEO meta tags for all non-API paths on storefront domains
# Middleware (StorefrontPasswordMiddleware, SEOBotMiddleware) handles password gating and bot detection
from workspace.hosting.views import serve_storefront

urlpatterns += [
    # Catchall route for storefront pages (must be last)
    # Matches: /, /collections/shoes, /products/123, etc.
    # Does NOT match /api/*, /admin/*, /theme-media/*, etc. (already matched above)
    re_path(r'^(?!api/|admin/|static/|media/|theme-media/).*$', serve_storefront, name='storefront'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if hasattr(settings, 'MEDIA_URL'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Serve theme media files (preview images, screenshots, etc.)
    if hasattr(settings, 'THEMES_MEDIA_URL') and hasattr(settings, 'THEMES_ROOT'):
        urlpatterns += static(settings.THEMES_MEDIA_URL, document_root=settings.THEMES_ROOT)
