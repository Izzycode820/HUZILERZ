"""
Infrastructure Cleanup Service
Handles AWS resource cleanup when workspaces are deleted
Production-safe with idempotency and comprehensive error handling
"""
import boto3
import logging
from typing import Dict, List, Any
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class InfrastructureCleanupService:
    """
    Service for cleaning up workspace infrastructure resources
    All methods are idempotent and safe to retry
    """

    def __init__(self):
        """Initialize AWS clients only in AWS mode"""
        self.mode = settings.INFRASTRUCTURE_MODE

        if self.mode == 'aws':
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_DEFAULT_REGION
            )
            self.route53_client = boto3.client(
                'route53',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            self.cloudfront_client = boto3.client(
                'cloudfront',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

    @classmethod
    def cleanup_s3_workspace_files(cls, workspace) -> Dict[str, Any]:
        """
        Cleanup S3 files for workspace
        Deletes files in workspace-specific folders: products/, themes/, storage/

        Args:
            workspace: Workspace instance

        Returns:
            Cleanup result with files deleted and storage freed
        """
        service = cls()

        if service.mode == 'mock':
            logger.info(f"[Mock] S3 cleanup for workspace {workspace.id}")
            return {
                'success': True,
                'mode': 'mock',
                'files_deleted': 0,
                'storage_freed_gb': 0
            }

        try:
            # Get infrastructure metadata
            infrastructure = workspace.infrastructure
            metadata = infrastructure.infra_metadata

            # Extract S3 paths
            s3_paths = [
                metadata.get('media_product_path'),
                metadata.get('media_theme_path'),
                metadata.get('storage_path'),
            ]

            total_files = 0
            total_size_bytes = 0

            for s3_path in s3_paths:
                if not s3_path:
                    continue

                # Parse S3 path: s3://bucket-name/prefix/
                if not s3_path.startswith('s3://'):
                    logger.warning(f"Invalid S3 path format: {s3_path}")
                    continue

                parts = s3_path[5:].split('/', 1)
                if len(parts) != 2:
                    logger.warning(f"Cannot parse S3 path: {s3_path}")
                    continue

                bucket_name = parts[0]
                prefix = parts[1]

                logger.info(f"Cleaning up S3 path: s3://{bucket_name}/{prefix}")

                # Delete files with pagination
                result = service._delete_s3_prefix(bucket_name, prefix)
                total_files += result['files_deleted']
                total_size_bytes += result['bytes_deleted']

            storage_freed_gb = total_size_bytes / (1024 ** 3)  # Convert to GB

            logger.info(
                f"S3 cleanup completed for workspace {workspace.id}: "
                f"{total_files} files deleted, {storage_freed_gb:.2f} GB freed"
            )

            return {
                'success': True,
                'files_deleted': total_files,
                'storage_freed_gb': round(storage_freed_gb, 2),
                'workspace_id': str(workspace.id)
            }

        except Exception as e:
            logger.error(f"S3 cleanup failed for workspace {workspace.id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'workspace_id': str(workspace.id)
            }

    def _delete_s3_prefix(self, bucket_name: str, prefix: str) -> Dict[str, int]:
        """
        Delete all objects under S3 prefix (recursive)
        Uses pagination for large folders

        Args:
            bucket_name: S3 bucket name
            prefix: Prefix/folder to delete

        Returns:
            Dict with files_deleted and bytes_deleted counts
        """
        files_deleted = 0
        bytes_deleted = 0

        try:
            # List and delete objects with pagination
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            for page in pages:
                if 'Contents' not in page:
                    continue

                # Collect objects to delete (max 1000 per batch)
                objects_to_delete = []
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
                    bytes_deleted += obj['Size']

                    # Delete in batches of 1000 (AWS limit)
                    if len(objects_to_delete) >= 1000:
                        self._delete_s3_batch(bucket_name, objects_to_delete)
                        files_deleted += len(objects_to_delete)
                        objects_to_delete = []

                # Delete remaining objects
                if objects_to_delete:
                    self._delete_s3_batch(bucket_name, objects_to_delete)
                    files_deleted += len(objects_to_delete)

            logger.info(f"Deleted {files_deleted} files from s3://{bucket_name}/{prefix}")

        except Exception as e:
            logger.error(f"Failed to delete S3 prefix s3://{bucket_name}/{prefix}: {str(e)}")
            raise

        return {
            'files_deleted': files_deleted,
            'bytes_deleted': bytes_deleted
        }

    def _delete_s3_batch(self, bucket_name: str, objects: List[Dict]):
        """
        Delete batch of S3 objects (max 1000)
        Idempotent - safe to retry
        """
        try:
            response = self.s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects, 'Quiet': True}
            )

            # Check for errors
            if 'Errors' in response and response['Errors']:
                for error in response['Errors']:
                    logger.error(
                        f"Failed to delete S3 object {error['Key']}: "
                        f"{error['Code']} - {error['Message']}"
                    )

        except Exception as e:
            logger.error(f"S3 batch delete failed for bucket {bucket_name}: {str(e)}")
            raise

    @classmethod
    def cleanup_dns_records(cls, workspace) -> Dict[str, Any]:
        """
        Cleanup DNS records for workspace
        Removes Route53 records for custom domains and subdomains

        Args:
            workspace: Workspace instance

        Returns:
            Cleanup result with records deleted count
        """
        service = cls()

        if service.mode == 'mock':
            logger.info(f"[Mock] DNS cleanup for workspace {workspace.id}")
            return {
                'success': True,
                'mode': 'mock',
                'records_deleted': 0
            }

        try:
            records_deleted = 0

            # Get infrastructure subdomain
            try:
                infrastructure = workspace.infrastructure
                subdomain = infrastructure.subdomain

                # Remove subdomain DNS record (CNAME)
                result = service._delete_route53_record(
                    subdomain,
                    'CNAME'
                )
                if result['success']:
                    records_deleted += 1

            except Exception as e:
                logger.warning(f"Failed to cleanup subdomain DNS for workspace {workspace.id}: {e}")

            # Cleanup custom domain DNS records
            try:
                custom_domains = workspace.custom_domains.all()
                for domain in custom_domains:
                    # Remove domain CNAME record
                    result = service._delete_route53_record(
                        domain.domain,
                        'CNAME'
                    )
                    if result['success']:
                        records_deleted += 1

                    # Remove verification TXT record
                    result = service._delete_route53_record(
                        f"_huzilerz-verify.{domain.domain}",
                        'TXT'
                    )
                    if result['success']:
                        records_deleted += 1

            except Exception as e:
                logger.warning(f"Failed to cleanup custom domain DNS for workspace {workspace.id}: {e}")

            logger.info(
                f"DNS cleanup completed for workspace {workspace.id}: "
                f"{records_deleted} records deleted"
            )

            return {
                'success': True,
                'records_deleted': records_deleted,
                'workspace_id': str(workspace.id)
            }

        except Exception as e:
            logger.error(f"DNS cleanup failed for workspace {workspace.id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'workspace_id': str(workspace.id)
            }

    def _delete_route53_record(self, record_name: str, record_type: str) -> Dict[str, Any]:
        """
        Delete Route53 DNS record
        Idempotent - safe to retry even if record doesn't exist

        Args:
            record_name: DNS record name (e.g., 'mystore.huzilerz.com')
            record_type: Record type ('CNAME', 'TXT', 'A', etc.)

        Returns:
            Deletion result
        """
        try:
            # Get hosted zone ID from settings (gracefully handle missing)
            hosted_zone_id = getattr(settings, 'ROUTE53_HOSTED_ZONE_ID', None)
            if not hosted_zone_id:
                logger.warning(
                    f"ROUTE53_HOSTED_ZONE_ID not configured, skipping DNS record deletion for {record_name}"
                )
                return {'success': True, 'skipped': True, 'reason': 'no_hosted_zone_configured'}

            # First, check if record exists
            try:
                response = self.route53_client.list_resource_record_sets(
                    HostedZoneId=hosted_zone_id,
                    StartRecordName=record_name,
                    StartRecordType=record_type,
                    MaxItems='1'
                )

                # Check if record exists
                record_exists = False
                resource_records = []

                for record_set in response.get('ResourceRecordSets', []):
                    if record_set['Name'].rstrip('.') == record_name and record_set['Type'] == record_type:
                        record_exists = True
                        resource_records = record_set.get('ResourceRecords', [])
                        break

                if not record_exists:
                    logger.info(f"DNS record {record_name} ({record_type}) not found, skipping")
                    return {'success': True, 'skipped': True}

            except Exception as e:
                logger.warning(f"Failed to check if DNS record exists: {e}")
                return {'success': False, 'error': str(e)}

            # Delete the record
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    'Changes': [
                        {
                            'Action': 'DELETE',
                            'ResourceRecordSet': {
                                'Name': record_name,
                                'Type': record_type,
                                'TTL': 300,
                                'ResourceRecords': resource_records
                            }
                        }
                    ]
                }
            )

            logger.info(f"Deleted DNS record: {record_name} ({record_type})")

            return {
                'success': True,
                'change_id': response['ChangeInfo']['Id'],
                'record_name': record_name,
                'record_type': record_type
            }

        except self.route53_client.exceptions.InvalidChangeBatch as e:
            # Record might not exist or already deleted
            logger.info(f"DNS record {record_name} ({record_type}) not found or already deleted")
            return {'success': True, 'skipped': True}

        except Exception as e:
            logger.error(f"Failed to delete DNS record {record_name} ({record_type}): {str(e)}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def cleanup_cloudfront_cache(cls, workspace) -> Dict[str, Any]:
        """
        Invalidate CloudFront cache for workspace
        This is called by CDN cache service, but included here for completeness

        Args:
            workspace: Workspace instance

        Returns:
            Invalidation result
        """
        from .cdn_cache_service import CDNCacheService

        try:
            result = CDNCacheService.invalidate_workspace_cache(
                workspace_id=str(workspace.id)
            )

            return {
                'success': result.get('success', False),
                'workspace_id': str(workspace.id),
                'invalidation_result': result
            }

        except Exception as e:
            logger.error(f"CloudFront cache invalidation failed for workspace {workspace.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'workspace_id': str(workspace.id)
            }

    @classmethod
    def cleanup_hosting_environment(cls, hosting_env) -> Dict[str, Any]:
        """
        Cleanup HostingEnvironment resources when subscription is cancelled
        Pool infrastructure is shared, so minimal cleanup needed

        Args:
            hosting_env: HostingEnvironment instance

        Returns:
            Cleanup result
        """
        service = cls()

        if service.mode == 'mock':
            logger.info(f"[Mock] Hosting environment cleanup for user {hosting_env.user_id}")
            return {
                'success': True,
                'mode': 'mock'
            }

        try:
            aws_resources = hosting_env.aws_resources

            # For pool infrastructure, only cleanup user-specific DNS records
            if aws_resources.get('infrastructure_model') == 'POOL':
                subdomain = aws_resources.get('subdomain')
                if subdomain:
                    service._delete_route53_record(
                        f"{subdomain}.huzilerz.com",
                        'CNAME'
                    )
                    logger.info(f"Cleaned up DNS record for subdomain: {subdomain}")

            logger.info(f"Hosting environment cleanup completed for user {hosting_env.user_id}")

            return {
                'success': True,
                'user_id': hosting_env.user_id,
                'infrastructure_model': aws_resources.get('infrastructure_model')
            }

        except Exception as e:
            logger.error(
                f"Hosting environment cleanup failed for user {hosting_env.user_id}: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'error': str(e),
                'user_id': hosting_env.user_id
            }
