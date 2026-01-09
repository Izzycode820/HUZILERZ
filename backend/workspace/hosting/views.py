"""
Internal Health Endpoints for Hosting System (Critical fix #10)

Provides token-protected health checks for internal monitoring.
These endpoints are not publicly accessible and require X-Internal-Token header.
"""

import logging
import json
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])  # Token validation handled by middleware
def internal_health_check(request):
    """
    Internal health check endpoint for hosting system

    Protected by InternalTokenMiddleware - requires X-Internal-Token header.
    Returns detailed health status of hosting components.

    Path: GET /api/workspaces/hosting/internal/health/
    Header: X-Internal-Token: <token from settings.INTERNAL_HEALTH_TOKEN>

    Returns:
        200 OK with detailed health status
        403 Forbidden if token missing/invalid (middleware handles)
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'workspace-hosting',
        'version': '1.0.0',
        'components': {}
    }

    # Check database connectivity
    db_status = 'healthy'
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError as e:
        db_status = 'unhealthy'
        db_error = str(e)
        health_status['status'] = 'degraded'

    health_status['components']['database'] = {
        'status': db_status,
        'type': 'postgresql',
        'error': db_error
    }

    # Check Redis cache connectivity
    cache_status = 'healthy'
    cache_error = None
    try:
        cache.set('health_check', 'test', timeout=1)
        if cache.get('health_check') != 'test':
            cache_status = 'degraded'
            cache_error = 'Cache write/read mismatch'
    except Exception as e:
        cache_status = 'unhealthy'
        cache_error = str(e)
        health_status['status'] = 'degraded'

    health_status['components']['redis_cache'] = {
        'status': cache_status,
        'type': 'redis',
        'error': cache_error
    }

    # Check CDN connectivity (if configured)
    cdn_status = 'healthy'
    cdn_error = None
    if hasattr(settings, 'CDN_ENABLED') and settings.CDN_ENABLED:
        # In production, we might ping CDN endpoints
        # For now, just report configuration
        cdn_status = 'configured'
    else:
        cdn_status = 'not_configured'

    health_status['components']['cdn'] = {
        'status': cdn_status,
        'configured': getattr(settings, 'CDN_ENABLED', False)
    }

    # Check provisioning queue (Celery)
    celery_status = 'healthy'
    try:
        # Try to import celery app to check worker connectivity
        from celery import current_app
        celery_status = 'available'
    except Exception as e:
        celery_status = 'unavailable'
        health_status['status'] = 'degraded'

    health_status['components']['celery'] = {
        'status': celery_status,
        'type': 'task_queue'
    }

    # Add system metrics
    from workspace.hosting.models import (
        WorkspaceInfrastructure, DeployedSite, CustomDomain
    )

    health_status['metrics'] = {
        'total_workspace_infrastructure': WorkspaceInfrastructure.objects.count(),
        'active_workspace_infrastructure': WorkspaceInfrastructure.objects.filter(status='active').count(),
        'total_deployed_sites': DeployedSite.objects.count(),
        'active_deployed_sites': DeployedSite.objects.filter(status='active').count(),
        'total_custom_domains': CustomDomain.objects.count(),
        'verified_custom_domains': CustomDomain.objects.filter(status='verified').count(),
        'timestamp': timezone.now().isoformat()
    }

    # Determine overall status
    unhealthy_components = [
        comp for comp, data in health_status['components'].items()
        if data.get('status') in ['unhealthy', 'failed']
    ]

    degraded_components = [
        comp for comp, data in health_status['components'].items()
        if data.get('status') in ['degraded', 'unavailable']
    ]

    if unhealthy_components:
        health_status['status'] = 'unhealthy'
        health_status['unhealthy_components'] = unhealthy_components
    elif degraded_components:
        health_status['status'] = 'degraded'
        health_status['degraded_components'] = degraded_components

    logger.info(f"Internal health check completed: {health_status['status']}")

    return Response(health_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def simple_health_check(request):
    """
    Simple public health check for load balancers and external monitoring

    This endpoint is public (no authentication required) and provides
    minimal health information for infrastructure checks.

    Path: GET /api/workspaces/hosting/health/

    Returns:
        200 OK with basic health status
    """
    try:
        # Minimal database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return Response({
            'status': 'healthy',
            'service': 'workspace-hosting',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            'status': 'unhealthy',
            'service': 'workspace-hosting',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)


# Storefront Password Protection Views (Concern #2)

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest, HttpResponseNotFound


@require_http_methods(["POST"])
@csrf_exempt  # CSRF handled by middleware for storefront domains
def unlock_storefront(request):
    """
    Handle storefront password submission

    POST /storefront/unlock/
    Form data:
        - site_id: UUID of DeployedSite
        - password: Plain text password
        - next: URL to redirect to after unlock (default: /)

    Returns:
        Redirect to 'next' URL on success
        Redirect back with error on failure

    Security:
        - Password validated using constant-time comparison
        - Session-based (password not stored in session)
        - Rate limiting handled by existing middleware
    """
    from workspace.hosting.models import DeployedSite

    # Extract form data
    site_id = request.POST.get('site_id')
    password = request.POST.get('password', '').strip()
    next_url = request.POST.get('next', '/')

    # Validation: Required fields
    if not site_id or not password:
        logger.warning(
            f"Storefront unlock failed: Missing site_id or password from IP {_get_client_ip(request)}"
        )
        request.session['password_error'] = "Please enter a password"
        return redirect(next_url)

    # Get DeployedSite from form
    try:
        site_from_form = DeployedSite.objects.get(id=site_id)
    except DeployedSite.DoesNotExist:
        logger.error(f"Storefront unlock failed: Invalid site_id {site_id}")
        request.session['password_error'] = "Invalid site"
        return redirect(next_url)

    # CRITICAL: Validate site_id matches hostname (prevent form tampering)
    # Resolve site from request hostname and compare with form site_id
    site_from_hostname = _resolve_site_from_hostname(request)

    # DEBUG OVERRIDE: Allow localhost to bypass hostname check (for dev mode)
    if not site_from_hostname and settings.DEBUG and 'localhost' in request.get_host():
        logger.debug(f"DEV mode: Bypassing hostname check for localhost unlock (Site {site_from_form.subdomain})")
        site_from_hostname = site_from_form

    if not site_from_hostname:
        logger.error(f"Storefront unlock failed: Could not resolve site from hostname {request.get_host()}")
        request.session['password_error'] = "Invalid request"
        return redirect(next_url)

    if site_from_form.id != site_from_hostname.id:
        logger.warning(
            f"Storefront unlock failed: Site ID mismatch - "
            f"Form submitted site_id {site_from_form.id} but hostname resolves to {site_from_hostname.id}. "
            f"Possible form tampering from IP {_get_client_ip(request)}"
        )
        request.session['password_error'] = "Invalid request"
        return redirect(next_url)

    # Use validated site from hostname
    site = site_from_hostname

    # Validate password (constant-time comparison)
    if not site.check_password(password):
        logger.warning(
            f"Storefront unlock failed: Wrong password for site {site.id} ({site.subdomain}) "
            f"from IP {_get_client_ip(request)}"
        )
        request.session['password_error'] = "Incorrect password"
        return redirect(next_url)

    # Password correct → Set session
    session_key = f"storefront_access_{site.id}"
    request.session[session_key] = True
    request.session.set_expiry(86400)  # 24 hours

    logger.info(
        f"Storefront unlocked: site {site.id} ({site.subdomain}) "
        f"from IP {_get_client_ip(request)}"
    )

    # Clear any error messages
    request.session.pop('password_error', None)

    # Redirect to requested URL
    return redirect(next_url)


def _get_client_ip(request):
    """Helper to get client IP for logging"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _resolve_site_from_hostname(request):
    """
    Resolve DeployedSite from request hostname

    This is the TRUSTED source - hostname cannot be tampered by client.
    Used for security validation in password unlock.

    Args:
        request: Django HTTP request

    Returns:
        DeployedSite or None
    """
    from workspace.hosting.models import DeployedSite

    hostname = request.get_host().split(':')[0]  # Remove port if present

    # Try subdomain match first (e.g., mikes-store.huzilerz.com)
    try:
        subdomain = hostname.replace('.huzilerz.com', '')
        return DeployedSite.objects.select_related('workspace').get(subdomain=subdomain)
    except DeployedSite.DoesNotExist:
        pass

    # Try custom domain match
    try:
        return DeployedSite.objects.select_related('workspace').get(
            custom_domains__domain=hostname,
            custom_domains__status='active'
        )
    except DeployedSite.DoesNotExist:
        pass

    return None


# SEO-Optimized Storefront Serving (Phase 4: SEO Implementation)

@require_http_methods(["GET"])
def serve_storefront(request):
    """
    Serve storefront with server-side SEO meta tag injection

    Strategy:
    - Inject SEO meta tags server-side (Google/bots see real HTML)
    - Load React theme from CDN (SPA hydration)
    - Version-based cache busting
    - Bot detection for dynamic rendering

    Security:
    - Site resolved from hostname (trusted source)
    - Password protection handled by middleware
    - XSS protection via Django template escaping

    Args:
        request: Django HTTP request

    Returns:
        HttpResponse: Rendered HTML with SEO tags
    """
    from workspace.hosting.services.seo_service import SEOService

    # Resolve site from hostname (trusted source)
    # Resolve site (Middleware might have already resolved it)
    site = getattr(request, 'site', None)
    if not site:
        # Fallback to resolving from hostname (if middleware was bypassed or failed)
        site = _resolve_site_from_hostname(request)
    
    if not site:
        logger.warning(f"Storefront not found for hostname: {request.get_host()}")
        try:
            return render(request, 'store_not_found.html', status=404)
        except Exception as e:
            # Fallback if template fails
            logger.error(f"Failed to render 404 template: {e}")
            return HttpResponseNotFound("<h1>Store Not Found</h1>")

    # Check if site is active (handle suspended/preview states)
    site_active = site.status == 'active'
    if not site_active and site.status == 'suspended':
        logger.info(f"Suspended site accessed: {site.id} ({site.subdomain})")
        return render(request, 'suspended.html', {
            'site_name': site.site_name,
            'reason': 'billing'  # TODO: Get actual suspension reason
        })

    # Generate SEO meta tags
    meta = SEOService.generate_meta_tags(site, request)

    # Generate structured data (JSON-LD)
    structured_data_dict = SEOService.generate_structured_data(site)
    structured_data_json = json.dumps(structured_data_dict, indent=2)

    # Get theme CDN URL with version hash
    theme_cdn_url = SEOService.get_theme_cdn_url(site)
    theme_version = theme_cdn_url.split('/')[-2] if '/' in theme_cdn_url else 'default'

    # Build API endpoints
    api_endpoint = f"{request.scheme}://{request.get_host()}/api"
    graphql_endpoint = f"{request.scheme}://{request.get_host()}/graphql"

    # Get primary custom domain (if any)
    primary_domain = site.custom_domains.filter(
        is_primary=True,
        status='verified'
    ).first()
    custom_domain_str = primary_domain.domain if primary_domain else None

    # Prepare template context
    context = {
        # SEO data
        'meta': meta,
        'structured_data': structured_data_json,

        # Site config
        'site_id': str(site.id),
        'subdomain': site.subdomain,
        'custom_domain': custom_domain_str,
        'site_active': site_active,

        # Theme loading
        'theme_cdn_url': theme_cdn_url,
        'theme_version': theme_version,

        # API endpoints
        'api_endpoint': api_endpoint,
        'graphql_endpoint': graphql_endpoint,

        # Analytics (future)
        'analytics_enabled': False  # TODO: Implement analytics
    }

    # Log bot detection for monitoring
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if SEOService.is_bot_request(user_agent):
        logger.info(
            f"Bot serving storefront: {site.subdomain} | "
            f"UA: {user_agent[:100]}"
        )

    # Render template with SEO injection
    return render(request, 'storefront_wrapper.html', context)