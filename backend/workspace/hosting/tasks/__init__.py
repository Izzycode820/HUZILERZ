"""
Hosting Tasks Package
Celery background tasks for hosting operations
"""

from .domain_tasks import (
    auto_verify_domains,
    provision_ssl_certificates,
    check_domain_health,
    cleanup_failed_domains,
    process_domain_purchase,
    process_domain_renewal,
    send_renewal_warnings,
    handle_expired_domains,
)
from .deployment_tasks import (
    apply_theme_deployment,
    rollback_deployment,
    health_check_deployment,
    provision_storefront_password_async,
)
from .usage_sync import (
    sync_bandwidth_usage,
    sync_storage_usage,
    sync_site_counts,
    enforce_limits_on_overage,
    reset_monthly_bandwidth,
)
from .hosting_capabilities import (
    update_hosting_capabilities,
    provision_new_hosting_capabilities,
)
from .hosting_environment_tasks import (
    provision_hosting_environment,
    update_hosting_environment_capabilities,
)
from .cache_invalidation_tasks import (
    invalidate_workspace_cache_async,
    warm_cache_async,
    invalidate_on_content_change,
)
from .reconciliation_tasks import (
    reconcile_hosting_capabilities,
    reconcile_workspace_capabilities,
    reconcile_all_capabilities,
)

__all__ = [
    # Domain verification & SSL
    'auto_verify_domains',
    'provision_ssl_certificates',
    'check_domain_health',
    'cleanup_failed_domains',
    # Domain purchase & renewal
    'process_domain_purchase',
    'process_domain_renewal',
    'send_renewal_warnings',
    'handle_expired_domains',
    # Deployment
    'apply_theme_deployment',
    'rollback_deployment',
    'health_check_deployment',
    'provision_storefront_password_async',
    # Usage synchronization
    'sync_bandwidth_usage',
    'sync_storage_usage',
    'sync_site_counts',
    'enforce_limits_on_overage',
    'reset_monthly_bandwidth',
    # Capability provisioning (entitlements)
    'update_hosting_capabilities',
    'provision_new_hosting_capabilities',
    # Hosting environment provisioning (user-level hosting account)
    'provision_hosting_environment',
    'update_hosting_environment_capabilities',
    # Cache invalidation & warming
    'invalidate_workspace_cache_async',
    'warm_cache_async',
    'invalidate_on_content_change',
    # Capability reconciliation (detects and fixes drift)
    'reconcile_hosting_capabilities',
    'reconcile_workspace_capabilities',
    'reconcile_all_capabilities',
]
