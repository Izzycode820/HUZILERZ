"""
Resource Usage Monitoring Service
Monitor and enforce subscription limits in real-time
"""
import boto3
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count
from decimal import Decimal
import logging
from typing import Dict, Any, Optional, List
from ..models import HostingEnvironment, DeployedSite, ResourceUsageLog
from subscription.models import Subscription

logger = logging.getLogger(__name__)


class ResourceUsageService:
    """Monitor and enforce subscription limits in real-time"""
    
    # Subscription tier limits from README
    SUBSCRIPTION_HOSTING_TIERS = {
        'free': {
            'deployment_allowed': False,
            'storage_gb': 0,
            'bandwidth_gb': 0,
            'custom_domains': 0,
        },
        'beginning': {
            'deployment_allowed': True,
            'storage_gb': 1,
            'bandwidth_gb': 10,
            'custom_domains': 1,
        },
        'pro': {
            'deployment_allowed': True,
            'storage_gb': 5,
            'bandwidth_gb': 50,
            'custom_domains': 5,
        },
        'enterprise': {
            'deployment_allowed': True,
            'storage_gb': 25,
            'bandwidth_gb': 200,
            'custom_domains': 999999,  # "unlimited"
        }
    }
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
        self.cloudwatch_client = boto3.client(
            'cloudwatch',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
        self.logs_client = boto3.client(
            'logs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
    
    def check_upload_eligibility(self, user, file_size_bytes: int) -> Dict[str, Any]:
        """Validate if user can upload file based on current storage usage"""

        try:
            hosting_env = HostingEnvironment.objects.get(subscription__user=user)
            subscription = hosting_env.subscription
        except HostingEnvironment.DoesNotExist:
            return {
                'allowed': False,
                'reason': 'no_hosting_environment',
                'message': 'No hosting environment found'
            }

        storage_limit = hosting_env.capabilities.get('storage_gb', 0)
        current_usage = self.get_current_usage(user)

        # Convert file size to GB
        file_size_gb = file_size_bytes / (1024 * 1024 * 1024)
        total_storage_needed_gb = current_usage['storage_gb'] + file_size_gb

        # Check storage limits at upload time (CRITICAL - prevents overages)
        if total_storage_needed_gb > storage_limit:
            return {
                'allowed': False,
                'reason': 'storage_limit_exceeded',
                'message': f'Storage limit exceeded. Need {total_storage_needed_gb:.2f}GB but limit is {storage_limit}GB',
                'current_usage_gb': current_usage['storage_gb'],
                'limit_gb': storage_limit,
                'file_size_gb': file_size_gb,
                'suggested_action': 'upgrade_subscription' if subscription.plan.tier != 'enterprise' else 'contact_support'
            }

        # Check if approaching limit (warning)
        storage_usage_percent = (current_usage['storage_gb'] / storage_limit * 100) if storage_limit > 0 else 0
        warnings = []

        if storage_usage_percent > 80:
            warnings.append({
                'type': 'storage_warning',
                'message': f'Storage usage at {storage_usage_percent:.1f}% of limit',
                'usage_gb': current_usage['storage_gb'],
                'limit_gb': storage_limit
            })

        return {
            'allowed': True,
            'warnings': warnings,
            'remaining_storage_gb': storage_limit - current_usage['storage_gb'],
            'file_size_gb': file_size_gb
        }

    def check_deployment_eligibility(self, user, new_site_config: Dict) -> Dict[str, Any]:
        """Validate if user can deploy based on current usage"""

        try:
            hosting_env = HostingEnvironment.objects.get(subscription__user=user)
            subscription = hosting_env.subscription
        except HostingEnvironment.DoesNotExist:
            return {
                'eligible': False,
                'reason': 'no_hosting_environment',
                'message': 'No hosting environment found'
            }

        tier_limits = self.SUBSCRIPTION_HOSTING_TIERS[subscription.plan.tier]
        current_usage = self.get_current_usage(user)

        # Check basic deployment permission
        if not hosting_env.capabilities.get('deployment_allowed', False):
            return {
                'eligible': False,
                'reason': 'deployment_not_allowed',
                'message': 'Deployment requires a paid subscription',
                'upgrade_required': True,
                'upgrade_benefits': self.get_upgrade_benefits(subscription.plan.tier)
            }


        # Check bandwidth usage (warning if approaching limit)
        bandwidth_usage_percent = (current_usage['bandwidth_gb'] / tier_limits['bandwidth_gb']) * 100
        warnings = []

        if bandwidth_usage_percent > 80:
            warnings.append({
                'type': 'bandwidth_warning',
                'message': f'Bandwidth usage at {bandwidth_usage_percent:.1f}% of monthly limit',
                'usage_gb': current_usage['bandwidth_gb'],
                'limit_gb': tier_limits['bandwidth_gb']
            })

        return {
            'eligible': True,
            'warnings': warnings,
            'remaining_capacity': {
                'bandwidth_gb': tier_limits['bandwidth_gb'] - current_usage['bandwidth_gb']
            }
        }
    
    def get_current_usage(self, user) -> Dict[str, Any]:
        """Get current resource usage for user"""

        try:
            hosting_env = HostingEnvironment.objects.get(subscription__user=user)
        except HostingEnvironment.DoesNotExist:
            return {
                'storage_gb': 0,
                'bandwidth_gb': 0,
                'active_sites': 0,
                'custom_domains': 0
            }

        # Get active sites count
        active_sites = DeployedSite.objects.filter(
            workspace__owner=user,
            status='active'
        ).count()

        # Get custom domains count
        custom_domains = DeployedSite.objects.filter(
            workspace__owner=user,
            status='active',
            custom_domain__isnull=False
        ).count()

        # Get storage usage from AWS or cached data
        storage_gb = self._calculate_storage_usage(hosting_env)

        # Get bandwidth usage from CloudWatch or cached data
        bandwidth_gb = self._calculate_bandwidth_usage(hosting_env)

        # Update usage log
        self._log_usage_metrics(hosting_env, {
            'storage_gb': storage_gb,
            'bandwidth_gb': bandwidth_gb,
            'active_sites': active_sites,
            'custom_domains': custom_domains
        })

        return {
            'storage_gb': storage_gb,
            'bandwidth_gb': bandwidth_gb,
            'active_sites': active_sites,
            'custom_domains': custom_domains
        }
    
    def estimate_site_size(self, site_config: Dict) -> float:
        """Estimate site size in MB based on configuration"""
        
        base_size_mb = 0.5  # Base HTML, CSS, JS files
        
        # Count images and assets
        assets = site_config.get('assets', {})
        estimated_asset_size = 0
        
        for asset_key, asset_data in assets.items():
            if isinstance(asset_data, str) and asset_data.startswith('data:'):
                # Base64 encoded asset - estimate size from length
                estimated_asset_size += len(asset_data) * 0.75 / 1024 / 1024  # Convert to MB
            else:
                # Assume average asset size
                estimated_asset_size += 0.2  # 200KB per asset
        
        # Count components that might have embedded media
        components = site_config.get('content', [])
        media_components = [c for c in components if c.get('type') in ['Image', 'Video', 'Hero']]
        estimated_component_size = len(media_components) * 0.3  # 300KB per media component
        
        total_size_mb = base_size_mb + estimated_asset_size + estimated_component_size
        
        return round(total_size_mb, 2)
    
    def _calculate_storage_usage(self, hosting_env: HostingEnvironment) -> float:
        """
        Calculate storage usage from AWS S3 (pool infrastructure)
        All users have folder-based isolation in shared buckets
        """
        total_size_gb = 0

        try:
            # Get all workspaces for this user
            from ..models import WorkspaceInfrastructure
            workspaces = WorkspaceInfrastructure.objects.filter(
                pool=hosting_env,
                status='active'
            )

            # Calculate storage across all workspace folders
            for workspace_infra in workspaces:
                metadata = workspace_infra.infra_metadata or {}

                # Get workspace folder paths
                media_product_path = metadata.get('media_product_path', '')
                media_theme_path = metadata.get('media_theme_path', '')
                storage_path = metadata.get('storage_path', '')

                # Extract bucket and prefix from S3 paths
                # Format: s3://bucket-name/prefix/path/
                for s3_path in [media_product_path, media_theme_path, storage_path]:
                    if s3_path and s3_path.startswith('s3://'):
                        path_parts = s3_path.replace('s3://', '').split('/', 1)
                        if len(path_parts) == 2:
                            bucket_name, prefix = path_parts
                            folder_size = self._get_s3_folder_size(bucket_name, prefix.rstrip('/') + '/')
                            total_size_gb += folder_size

        except Exception as e:
            # Fall back to cached data if AWS call fails
            logger.error(f"Failed to calculate storage usage: {str(e)}")
            latest_log = ResourceUsageLog.objects.filter(
                hosting_environment=hosting_env
            ).order_by('-recorded_at').first()

            if latest_log:
                total_size_gb = latest_log.storage_used_gb

        return round(total_size_gb, 3)  # Return in GB with 3 decimal places
    
    def _get_s3_bucket_size(self, bucket_name: str) -> float:
        """Get total size of S3 bucket in GB"""
        try:
            total_size = 0
            paginator = self.s3_client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']

            return total_size / (1024 * 1024 * 1024)  # Convert to GB

        except Exception:
            return 0.0

    def _get_s3_folder_size(self, bucket_name: str, prefix: str) -> float:
        """Get total size of S3 folder in GB"""
        try:
            total_size = 0
            paginator = self.s3_client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']

            return total_size / (1024 * 1024 * 1024)  # Convert to GB

        except Exception:
            return 0.0
    
    def _calculate_bandwidth_usage(self, hosting_env: HostingEnvironment) -> float:
        """
        Calculate bandwidth usage from CloudWatch Logs (pool infrastructure)
        Filters by workspace paths in shared CDN distribution
        """
        try:
            # Get all workspace IDs for this user
            from ..models import WorkspaceInfrastructure
            workspaces = WorkspaceInfrastructure.objects.filter(
                pool=hosting_env,
                status='active'
            ).values_list('workspace_id', flat=True)

            if not workspaces:
                return 0.0

            # Calculate bandwidth using CloudWatch Logs Insights
            total_bytes = self._query_cloudfront_logs_for_workspaces(list(workspaces))

            # Convert bytes to GB
            return round(total_bytes / (1024 * 1024 * 1024), 3)

        except Exception as e:
            logger.error(f"Failed to calculate bandwidth usage: {str(e)}")
            # Fall back to cached data
            latest_log = ResourceUsageLog.objects.filter(
                hosting_environment=hosting_env
            ).order_by('-recorded_at').first()

            return latest_log.bandwidth_used_gb if latest_log else 0.0

    def _query_cloudfront_logs_for_workspaces(self, workspace_ids: List[str]) -> int:
        """
        Query CloudFront access logs using CloudWatch Logs Insights
        Filters by workspace paths and sums bandwidth

        CloudFront logs format: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html
        """
        try:
            # Get log group name from settings
            log_group_name = getattr(
                settings,
                'CLOUDFRONT_LOGS_GROUP',
                '/aws/cloudfront/shared-pool-distribution'
            )

            # Build query to sum bytes for workspace paths
            # CloudFront log format: cs-uri-stem contains the request path
            workspace_patterns = ' or '.join([
                f'cs-uri-stem like "/ws/{ws_id}%"' for ws_id in workspace_ids
            ])

            query = f"""
            fields @timestamp, cs-bytes
            | filter {workspace_patterns}
            | stats sum(cs-bytes) as total_bytes
            """

            # Query for current billing month
            end_time = timezone.now()
            start_time = end_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Start query
            start_query_response = self.logs_client.start_query(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp()),
                endTime=int(end_time.timestamp()),
                queryString=query
            )

            query_id = start_query_response['queryId']

            # Poll for results (timeout after 30 seconds)
            import time
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(1)

                result = self.logs_client.get_query_results(queryId=query_id)

                if result['status'] == 'Complete':
                    if result['results']:
                        # Extract total bytes from results
                        for row in result['results']:
                            for field in row:
                                if field['field'] == 'total_bytes':
                                    return int(float(field['value']))
                    return 0

                elif result['status'] == 'Failed':
                    logger.error(f"CloudWatch Logs query failed: {result.get('statistics', {})}")
                    return 0

            # Timeout reached
            logger.warning(f"CloudWatch Logs query timeout for workspaces: {workspace_ids}")
            return 0

        except Exception as e:
            logger.error(f"Failed to query CloudFront logs: {str(e)}")
            # Return 0 if query fails, caller will use cached data
            return 0
    
    def _log_usage_metrics(self, hosting_env: HostingEnvironment, metrics: Dict):
        """Log current usage metrics"""

        ResourceUsageLog.objects.create(
            hosting_environment=hosting_env,
            storage_used_gb=metrics['storage_gb'],
            bandwidth_used_gb=metrics['bandwidth_gb'],
            active_sites_count=metrics['active_sites'],
            custom_domains_count=metrics['custom_domains'],
            recorded_at=timezone.now()
        )
    
    def enforce_subscription_limits(self, user) -> Dict[str, Any]:
        """Handle subscription downgrades and limit enforcement"""
        
        try:
            hosting_env = HostingEnvironment.objects.get(subscription__user=user)
            subscription = hosting_env.subscription
        except HostingEnvironment.DoesNotExist:
            return {'success': False, 'error': 'No hosting environment found'}
        
        current_usage = self.get_current_usage(user)
        new_limits = self.SUBSCRIPTION_HOSTING_TIERS[subscription.plan.tier]
        storage_limit = hosting_env.capabilities.get('storage_gb', 0)
        
        enforcement_actions = []
        
        
        # Handle storage overages
        storage_usage_gb = current_usage['storage_gb']
        if storage_usage_gb > storage_limit:
            # First, try to compress assets and archive old versions
            compression_saved_gb = self._compress_user_assets(hosting_env)
            archive_saved_gb = self._archive_old_versions(hosting_env)

            enforcement_actions.append({
                'action': 'storage_optimization',
                'compression_saved_gb': compression_saved_gb,
                'archive_saved_gb': archive_saved_gb
            })

            # Recalculate usage after optimization
            updated_usage = self.get_current_usage(user)
            updated_storage_gb = updated_usage['storage_gb']

            # If still over limit, suspend largest sites
            if updated_storage_gb > storage_limit:
                sites_to_suspend = self._get_largest_sites_for_suspension(
                    user, updated_storage_gb - storage_limit
                )

                for site in sites_to_suspend:
                    site.status = 'suspended'
                    site.suspension_reason = 'storage_limit_exceeded'
                    site.save()

                    enforcement_actions.append({
                        'action': 'site_suspended_storage',
                        'site_url': site.primary_url,
                        'reason': 'Storage limit exceeded for current subscription tier'
                    })
        
        # Handle custom domain limits
        if current_usage['custom_domains'] > new_limits['custom_domains']:
            excess_domains_count = current_usage['custom_domains'] - new_limits['custom_domains']
            
            sites_with_custom_domains = DeployedSite.objects.filter(
                workspace__owner=user,
                status='active',
                custom_domain__isnull=False
            ).order_by('created_at')[:excess_domains_count]
            
            for site in sites_with_custom_domains:
                site.custom_domain = None
                site.save()
                
                enforcement_actions.append({
                    'action': 'custom_domain_removed',
                    'site_url': site.primary_url,
                    'reason': 'Custom domain limit exceeded for current subscription tier'
                })
        
        return {
            'success': True,
            'enforcement_actions': enforcement_actions,
            'final_usage': self.get_current_usage(user)
        }
    
    def get_upgrade_benefits(self, current_tier: str) -> List[Dict[str, Any]]:
        """Get benefits of upgrading to higher tiers"""
        
        tier_order = ['free', 'beginning', 'pro', 'enterprise']
        current_index = tier_order.index(current_tier)
        
        upgrade_options = []
        
        for i in range(current_index + 1, len(tier_order)):
            next_tier = tier_order[i]
            next_limits = self.SUBSCRIPTION_HOSTING_TIERS[next_tier]
            
            upgrade_options.append({
                'tier': next_tier,
                'benefits': {
                    'storage_gb': next_limits['storage_gb'],
                    'bandwidth_gb': next_limits['bandwidth_gb'],
                    'custom_domains': next_limits['custom_domains'],
                }
            })
        
        return upgrade_options
    
    def _compress_user_assets(self, hosting_env: HostingEnvironment) -> float:
        """Compress user assets to save storage space"""
        # This would implement asset compression logic
        # For now, return simulated savings
        return 0.1  # 100MB saved
    
    def _archive_old_versions(self, hosting_env: HostingEnvironment) -> float:
        """Archive old deployment versions"""
        # This would implement version archiving logic
        # For now, return simulated savings
        return 0.05  # 50MB saved
    
    def _get_largest_sites_for_suspension(self, user, gb_to_free: float) -> List[DeployedSite]:
        """Get largest sites that need to be suspended to free up storage"""
        
        # This would calculate site sizes and return largest ones
        # For now, return oldest sites as proxy
        sites_to_suspend = DeployedSite.objects.filter(
            workspace__owner=user,
            status='active'
        ).order_by('created_at')[:2]  # Suspend 2 oldest sites
        
        return sites_to_suspend
    
    def get_usage_analytics(self, user, days: int = 30) -> Dict[str, Any]:
        """Get usage analytics for dashboard"""
        
        try:
            hosting_env = HostingEnvironment.objects.get(subscription__user=user)
        except HostingEnvironment.DoesNotExist:
            return {}
        
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        usage_logs = ResourceUsageLog.objects.filter(
            hosting_environment=hosting_env,
            recorded_at__gte=start_date
        ).order_by('recorded_at')
        
        # Prepare time series data
        storage_history = []
        bandwidth_history = []
        sites_history = []
        
        for log in usage_logs:
            timestamp = log.recorded_at.isoformat()

            storage_history.append({
                'timestamp': timestamp,
                'value': log.storage_used_gb
            })

            bandwidth_history.append({
                'timestamp': timestamp,
                'value': log.bandwidth_used_gb
            })

            sites_history.append({
                'timestamp': timestamp,
                'value': log.active_sites_count
            })

        # Get current limits
        current_limits = self.SUBSCRIPTION_HOSTING_TIERS[hosting_env.subscription.plan.tier]

        return {
            'current_usage': self.get_current_usage(user),
            'subscription_limits': current_limits,
            'usage_history': {
                'storage_gb': storage_history,
                'bandwidth_gb': bandwidth_history,
                'active_sites': sites_history
            },
            'usage_percentages': {
                'storage': (usage_logs.last().storage_used_gb / current_limits['storage_gb'] * 100) if usage_logs.exists() and current_limits['storage_gb'] > 0 else 0,
                'bandwidth': (usage_logs.last().bandwidth_used_gb / current_limits['bandwidth_gb'] * 100) if usage_logs.exists() and current_limits['bandwidth_gb'] > 0 else 0,
            }
        }