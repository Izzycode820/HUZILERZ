# Hosting Module - Django Admin Interface Guide

Complete administration interface for managing infrastructure, deployments, and monitoring.

## Overview

The hosting admin interface provides comprehensive tools for:
- Resource quota and usage monitoring
- Infrastructure provisioning management
- Deployment tracking and rollback
- Custom domain management
- Performance metrics and alerting
- Cache management

## Admin Models

### 1. HostingEnvironment
**Purpose:** Manage user hosting quotas and resource usage

**Key Features:**
- Visual progress bars for storage and bandwidth usage
- Color-coded status badges (active, suspended, grace period)
- Usage summary with percentages
- Resource limit synchronization
- CSV export for usage reports

**Custom Actions:**
- Sync limits from subscription
- Reset usage counters (DANGEROUS - use carefully)
- Export usage as CSV

**Filters:**
- Status (active, suspended, etc.)
- Subscription tier (free, starter, professional, etc.)
- Resource usage level (low, medium, high, critical)
- Last usage sync date

**Use Cases:**
- Monitor users approaching quota limits
- Identify resource abuse
- Audit subscription upgrades/downgrades
- Generate billing reports

### 2. WorkspaceInfrastructure
**Purpose:** Track infrastructure provisioning lifecycle

**Key Features:**
- Provisioning status tracking (created → provisioned → active)
- Subdomain change management with limits
- Infrastructure metadata visualization
- Preview URL access
- Cache invalidation tools

**Custom Actions:**
- Mark as active
- Mark as suspended
- Invalidate tenant cache

**Filters:**
- Provisioning status
- Assignment date
- Activation date

**Use Cases:**
- Debug provisioning failures
- Track infrastructure assignments
- Manage subdomain changes
- Force cache refresh

### 3. DeployedSite
**Purpose:** Manage deployed sites and their runtime configuration

**Key Features:**
- Live site URL links
- Template and customization tracking
- Deployment status monitoring
- Health check triggers
- CSV export for sites

**Custom Actions:**
- Mark as active
- Suspend sites
- Trigger health check
- Export as CSV

**Inline Views:**
- DeploymentAudit history (last 10)

**Use Cases:**
- Monitor site status
- Troubleshoot deployment issues
- Access live sites quickly
- Bulk status updates

### 4. DeploymentAudit
**Purpose:** Track deployment history with rollback capability

**Key Features:**
- Complete deployment lifecycle tracking
- Duration calculation
- Rollback detection
- Error message capture
- Metadata storage for debugging

**Custom Actions:**
- Export audit log as CSV

**Filters:**
- Status (initiated, in_progress, completed, failed, rolled_back)
- Date ranges

**Use Cases:**
- Debug failed deployments
- Analyze deployment performance
- Track rollback frequency
- Audit user actions

### 5. CustomDomain
**Purpose:** Manage custom domains and SSL certificates

**Key Features:**
- Domain verification status
- SSL certificate tracking
- DNS records display
- Expiration monitoring

**Custom Actions:**
- Verify domain
- Enable SSL
- Disable SSL

**Filters:**
- Status (pending, active, failed, expired)
- SSL enabled/disabled
- Verification date

**Use Cases:**
- Verify domain ownership
- Monitor SSL certificate expiration
- Troubleshoot DNS issues
- Bulk SSL management

### 6. DomainPurchase & DomainRenewal
**Purpose:** Track domain purchases and renewals

**Key Features:**
- Purchase status tracking
- Price monitoring
- Transaction ID storage
- Expiration tracking

**Filters:**
- Status
- Purchase/renewal dates

**Use Cases:**
- Audit domain transactions
- Monitor renewal schedules
- Financial reporting

### 7. SubdomainHistory
**Purpose:** Track subdomain changes over time

**Key Features:**
- Change history with timestamps
- Active/inactive status
- Changed by user tracking
- Change reason capture

**Use Cases:**
- Audit subdomain changes
- Enforce change limits
- Resolve subdomain conflicts

### 8. ResourceUsageLog
**Purpose:** Historical usage tracking

**Key Features:**
- Time-series usage data
- Storage and bandwidth tracking
- Request count monitoring
- Response time metrics

**Custom Actions:**
- Export logs as CSV

**Use Cases:**
- Usage trend analysis
- Performance monitoring
- Capacity planning

### 9. DeploymentLog
**Purpose:** Detailed deployment action logging

**Key Features:**
- Action type tracking
- Status monitoring
- User attribution
- Detailed metadata

**Use Cases:**
- Deployment troubleshooting
- Audit trail
- Performance analysis

### 10. SitePerformanceMetrics
**Purpose:** Site performance monitoring

**Key Features:**
- Uptime percentage
- Response time tracking
- Request count monitoring
- Bandwidth usage per site

**Use Cases:**
- Performance optimization
- SLA monitoring
- Capacity planning

## Custom Admin Views

### Metrics Dashboard
**Access:** Admin sidebar → Hosting Management → Metrics

**Features:**
- Real-time infrastructure metrics
- Success/failure rates for provisioning and deployments
- Time-window selection (minute, hour, day)
- Active alerts display
- Auto-refresh every 30 seconds

**Metrics Displayed:**
- Provisioning success rate
- Deployment success rate
- Rollback count
- Average operation duration
- Alert thresholds

**Use Cases:**
- Monitor system health
- Identify performance degradation
- Track deployment success rates
- Respond to alerts

### Cache Management
**Access:** Admin sidebar → Hosting Management → Cache Management

**Features:**
- Warm cache for all workspaces
- Invalidate specific workspace cache
- Cache statistics and TTL information
- Best practices guide

**Actions:**
- Warm All Caches: Pre-populate cache after system restart
- Invalidate Workspace: Force refresh for specific workspace

**TTL Settings:**
- Hostname lookups: 1 hour
- Workspace data: 30 minutes
- Custom domains: 2 hours

**Use Cases:**
- System maintenance
- Cache troubleshooting
- Performance optimization
- After deployments

## Advanced Features

### Bulk Operations
All model admins support bulk operations through action dropdowns:
- Status updates (activate, suspend)
- Health checks
- Cache invalidation
- CSV exports

### Color-Coded Visualizations
- Green: Healthy/Active
- Blue: In Progress/Pending
- Orange: Warning/Grace Period
- Red: Critical/Failed
- Gray: Inactive/Unknown

### Search and Filters
Every model includes:
- Full-text search on relevant fields
- Status filters
- Date range filters
- Custom filters (tier, usage level, etc.)

### Data Export
CSV export available for:
- Hosting environments (usage data)
- Deployed sites (site list)
- Deployment audits (deployment history)
- Resource usage logs (time-series data)

## Admin Permissions

Recommended permission setup:
- **Super Admin:** Full access to all models and actions
- **Operations Team:** Read-only + health checks + cache management
- **Support Team:** Read-only access for troubleshooting
- **Billing Team:** HostingEnvironment read-only for usage reports

## Monitoring and Alerts

### Alert Thresholds
Automatic alerts trigger when:
- Provision success rate < 80% (high severity)
- Deployment success rate < 90% (high severity)
- Average provision time > 60s (medium severity)
- Rollback rate > 10% (medium severity)

### Alert Response
When alerts appear:
1. Check metrics dashboard for details
2. Review recent DeploymentAudit entries
3. Check infrastructure status in WorkspaceInfrastructure
4. Verify system logs for errors
5. Consider cache invalidation if routing issues

## Common Admin Tasks

### Monitor System Health
1. Navigate to Metrics Dashboard
2. Check current hour metrics
3. Review active alerts
4. Investigate failures if any

### Troubleshoot Deployment Failure
1. Find workspace in WorkspaceInfrastructure
2. Check provisioning status
3. Review DeployedSite status
4. Check DeploymentAudit for error details
5. Trigger health check if needed

### Handle Resource Overuse
1. Navigate to HostingEnvironment
2. Filter by "Critical" resource usage
3. Review user's subscription tier
4. Contact user or suspend if necessary
5. Reset usage counters after resolution

### Domain Verification Issues
1. Find domain in CustomDomain
2. Check verification token
3. Review DNS records
4. Use "Verify domain" action
5. Monitor status change

### Cache Performance Issues
1. Navigate to Cache Management
2. Check cache hit rates (should be > 90%)
3. Warm cache if low hit rate
4. Invalidate specific workspaces if stale data
5. Review TTL settings

### Bulk Site Suspension
1. Navigate to DeployedSite
2. Use filters to identify sites
3. Select sites with checkboxes
4. Choose "Suspend sites" action
5. Confirm bulk operation

## Best Practices

### Daily Operations
- Check metrics dashboard for system health
- Review overnight deployment failures
- Monitor resource usage trends
- Verify SSL certificate expirations

### Weekly Tasks
- Export usage reports for billing
- Review deployment success rates
- Analyze performance trends
- Clear old audit logs if needed

### Monthly Maintenance
- Review alert thresholds
- Optimize cache TTLs based on usage
- Audit subdomain changes
- Generate capacity planning reports

### Performance Optimization
- Keep cache warm after deployments
- Monitor cache hit rates
- Optimize query performance for large datasets
- Use filters to limit result sets

## Troubleshooting Guide

### Slow Admin Interface
- Use filters to reduce result sets
- Export large datasets to CSV for analysis
- Check database query performance
- Review cache backend performance

### Missing Data
- Check model relationships
- Verify provisioning completed
- Review task queue status
- Check for database constraints

### Inconsistent State
- Compare WorkspaceInfrastructure with DeployedSite
- Check HostingEnvironment quota sync
- Review ProvisioningLog for failures
- Use health check actions

## API Integration

The admin interface integrates with:
- **MetricsService:** Real-time metrics and alerts
- **TenantLookupCache:** Hostname resolution caching
- **Celery Tasks:** Async operations (health checks, verification)
- **InfrastructureFacade:** Mock/AWS service switching

## Security Considerations

- Admin access requires staff permissions
- Sensitive actions (reset usage) are marked as DANGEROUS
- All actions are logged with user attribution
- CSV exports respect permissions
- Health checks run in background tasks

## Future Enhancements

Potential additions:
- Real-time monitoring graphs
- Advanced analytics dashboard
- Automated alert notifications (email, Slack)
- Custom report builder
- Workspace migration tools
- Bulk provisioning operations

## Support

For issues or questions:
1. Check deployment logs in DeploymentAudit
2. Review infrastructure status
3. Verify metrics dashboard for system-wide issues
4. Check cache management for performance problems
5. Review this guide for common solutions
