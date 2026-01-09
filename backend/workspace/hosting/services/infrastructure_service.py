"""
AWS Infrastructure Management Service
Handles POOL deployment for all subscription tiers (Shopify model)
"""
import boto3
import json
import uuid
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, Any, Optional
from ..models import HostingEnvironment, DeployedSite
from .api_gateway_service import APIGatewayService

logger = logging.getLogger(__name__)


class AWSInfrastructureService:
    """Manage AWS resources for pool infrastructure (all tiers)"""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
        self.cloudfront_client = boto3.client(
            'cloudfront',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.route53_client = boto3.client(
            'route53',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.api_gateway_service = APIGatewayService()
    
    # POOL MODEL - Shared resources for all tiers (Shopify model)
    def setup_pool_infrastructure(self, hosting_env: HostingEnvironment) -> Dict[str, Any]:
        """Set up shared pool infrastructure for all users regardless of tier

        Templates run from main CDN - no S3 buckets needed
        Only configure CloudFront routing and DNS
        """
        user_id = hosting_env.subscription.user.id

        # Configure CloudFront behavior for subdomain routing
        cloudfront_result = self._configure_pool_cloudfront_routing(user_id)

        # Setup DNS record for subdomain
        subdomain = f"user-{user_id}-{uuid.uuid4().hex[:8]}"
        dns_result = self._setup_pool_dns_record(subdomain, cloudfront_result['distribution_domain'])

        # Setup API Gateway for shared infrastructure
        api_gateway_result = self.api_gateway_service._setup_shared_api_gateway(
            DeployedSite(subdomain=subdomain, user=hosting_env.user)
        )

        aws_resources = {
            'infrastructure_model': 'POOL',
            'cloudfront_distribution': settings.SHARED_CLOUDFRONT_DISTRIBUTION_ID,
            'api_gateway': api_gateway_result['api_gateway_id'],
            'ssl_certificate': settings.SHARED_SSL_CERTIFICATE_ARN,
            'custom_domain_allowed': False,
            'subdomain': subdomain,
            'routing_config': cloudfront_result,
            'dns_config': dns_result,
            'api_gateway_config': api_gateway_result
        }

        # Update hosting environment
        hosting_env.aws_resources = aws_resources
        hosting_env.save()

        return aws_resources
    
    def _configure_pool_cloudfront_routing(self, user_id: int) -> Dict[str, Any]:
        """Configure CloudFront routing for POOL infrastructure

        Templates run from main CDN - configure behavior routing only
        """
        try:
            # Get shared CloudFront distribution config
            cloudfront_config = self._get_shared_cloudfront_config()

            # Add cache behavior for user's subdomain routing
            behavior_config = {
                'user_id': user_id,
                'path_pattern': f'/user-{user_id}/*',
                'target_origin': settings.MAIN_THEME_CDN_URL,
                'cache_policy_id': settings.CACHE_POLICY_ID
            }

            # Update CloudFront distribution with new behavior
            update_result = self._update_cloudfront_behavior(behavior_config)

            return {
                'success': True,
                'distribution_domain': f"{settings.SHARED_CLOUDFRONT_DISTRIBUTION_ID}.cloudfront.net",
                'behavior_config': behavior_config,
                'update_result': update_result
            }

        except Exception as e:
            logger.error(f"Failed to configure CloudFront routing for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _setup_pool_dns_record(self, subdomain: str, target_domain: str) -> Dict[str, Any]:
        """Setup DNS record for POOL infrastructure subdomain"""
        try:
            # Get hosted zone ID (gracefully handle missing)
            hosted_zone_id = getattr(settings, 'ROUTE53_HOSTED_ZONE_ID', None)
            if not hosted_zone_id:
                logger.warning(
                    f"ROUTE53_HOSTED_ZONE_ID not configured, skipping DNS record creation for {subdomain}"
                )
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'no_hosted_zone_configured',
                    'subdomain': f"{subdomain}.huzilerz.com",
                    'target': target_domain
                }

            # Create Route53 record pointing to CloudFront
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    'Changes': [
                        {
                            'Action': 'CREATE',
                            'ResourceRecordSet': {
                                'Name': f"{subdomain}.huzilerz.com",
                                'Type': 'CNAME',
                                'TTL': 300,
                                'ResourceRecords': [{'Value': target_domain}]
                            }
                        }
                    ]
                }
            )

            return {
                'success': True,
                'subdomain': f"{subdomain}.huzilerz.com",
                'target': target_domain,
                'change_id': response['ChangeInfo']['Id']
            }

        except Exception as e:
            logger.error(f"Failed to setup DNS record for {subdomain}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    
    def _update_cloudfront_behavior(self, behavior_config: Dict) -> Dict[str, Any]:
        """Update CloudFront distribution with new cache behavior"""
        try:
            # This would implement the actual CloudFront update
            # For now, return simulated success
            return {
                'success': True,
                'behavior_id': f"behavior-{uuid.uuid4().hex[:8]}",
                'config': behavior_config
            }
        except Exception as e:
            logger.error(f"Failed to update CloudFront behavior: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    # Utility methods
    def _get_shared_cloudfront_config(self) -> Dict:
        """Get configuration for shared CloudFront distribution"""
        cache_key = 'shared_cloudfront_config'
        config = cache.get(cache_key)
        
        if not config:
            response = self.cloudfront_client.get_distribution(
                Id=settings.SHARED_CLOUDFRONT_DISTRIBUTION_ID
            )
            config = response['Distribution']['DistributionConfig']
            cache.set(cache_key, config, 3600)  # Cache for 1 hour
        
        return config
    
    def _add_user_cache_behavior(self, cloudfront_config: Dict, user_prefix: str):
        """Add cache behavior for user's path in shared distribution"""
        # This would typically involve updating the CloudFront distribution
        # For now, we'll log the requirement for infrastructure team
        # In production, you'd use CloudFormation or Terraform for this
        pass
    
    def _create_hosted_zone(self, workspace_id: str) -> str:
        """Create Route53 hosted zone for custom domains"""
        zone_name = f"pro-{workspace_id}.huzilerz.com"
        
        response = self.route53_client.create_hosted_zone(
            Name=zone_name,
            CallerReference=f"{workspace_id}-{uuid.uuid4().hex[:8]}",
            HostedZoneConfig={
                'Comment': f'Pro zone for workspace {workspace_id}',
                'PrivateZone': False
            }
        )
        
        return response['HostedZone']['Id']
    
 
    def cleanup_infrastructure(self, hosting_env: HostingEnvironment):
        """Clean up AWS resources when subscription is cancelled

        Pool infrastructure is shared, so minimal cleanup needed.
        Only remove user-specific DNS records and routing rules.
        """
        from .infrastructure_cleanup_service import InfrastructureCleanupService

        try:
            aws_resources = hosting_env.aws_resources

            # For pool infrastructure, only cleanup user-specific DNS records
            if aws_resources.get('infrastructure_model') == 'POOL':
                subdomain = aws_resources.get('subdomain')
                if subdomain:
                    logger.info(f"Cleaning up DNS record for {subdomain}")

                    # Delete DNS record using cleanup service
                    hosted_zone_id = getattr(settings, 'ROUTE53_HOSTED_ZONE_ID', None)
                    if hosted_zone_id:
                        try:
                            self.route53_client.change_resource_record_sets(
                                HostedZoneId=hosted_zone_id,
                                ChangeBatch={
                                    'Changes': [
                                        {
                                            'Action': 'DELETE',
                                            'ResourceRecordSet': {
                                                'Name': f"{subdomain}.huzilerz.com",
                                                'Type': 'CNAME',
                                                'TTL': 300,
                                                'ResourceRecords': [{'Value': aws_resources.get('dns_config', {}).get('target', 'unknown')}]
                                            }
                                        }
                                    ]
                                }
                            )
                            logger.info(f"Successfully deleted DNS record for {subdomain}.huzilerz.com")
                        except Exception as e:
                            logger.warning(f"Failed to delete DNS record for {subdomain}: {str(e)}")
                    else:
                        logger.info(f"ROUTE53_HOSTED_ZONE_ID not configured, skipping DNS cleanup for {subdomain}")

            logger.info(f"Infrastructure cleanup completed for hosting environment {hosting_env.id}")

        except Exception as e:
            logger.error(f"Infrastructure cleanup failed for hosting environment {hosting_env.id}: {str(e)}")
    
    
    def _delete_cloudfront_distribution(self, distribution_id: str):
        """Delete CloudFront distribution"""
        try:
            # Disable distribution first
            self.cloudfront_client.update_distribution(
                Id=distribution_id,
                DistributionConfig={'Enabled': False}
            )
            # Distribution deletion requires it to be disabled first
            # In production, this would be handled by a background task
        except Exception as e:
            print(f"Error deleting CloudFront distribution {distribution_id}: {e}")

    

    def provision_ssl_for_domain(self, domain: str, validation_method: str = 'DNS') -> Dict[str, Any]:
        """
        Provision SSL certificate using AWS Certificate Manager (ACM)

        Args:
            domain: Domain name to provision SSL for
            validation_method: DNS or EMAIL validation

        Returns:
            SSL provisioning result with certificate ARN
        """
        try:
            # Initialize ACM client if not already done
            if not hasattr(self, 'acm_client'):
                self.acm_client = boto3.client(
                    'acm',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_DEFAULT_REGION
                )

            # Request SSL certificate from ACM
            response = self.acm_client.request_certificate(
                DomainName=domain,
                ValidationMethod=validation_method,
                SubjectAlternativeNames=[f'*.{domain}'],  # Wildcard for subdomains
                Options={
                    'CertificateTransparencyLoggingPreference': 'ENABLED'
                },
                Tags=[
                    {'Key': 'ManagedBy', 'Value': 'Huzilerz'},
                    {'Key': 'Domain', 'Value': domain},
                ]
            )

            certificate_arn = response['CertificateArn']

            logger.info(f"[AWS] SSL certificate requested for {domain}: {certificate_arn}")

            # Get validation records for DNS validation
            if validation_method == 'DNS':
                # Wait a bit for AWS to generate validation records
                import time
                time.sleep(2)

                cert_details = self.acm_client.describe_certificate(
                    CertificateArn=certificate_arn
                )

                validation_options = cert_details['Certificate'].get('DomainValidationOptions', [])

                return {
                    'success': True,
                    'certificate_arn': certificate_arn,
                    'certificate_id': certificate_arn.split('/')[-1],
                    'domain': domain,
                    'status': 'PENDING_VALIDATION',
                    'validation_method': validation_method,
                    'validation_records': [
                        {
                            'name': opt.get('ResourceRecord', {}).get('Name'),
                            'type': opt.get('ResourceRecord', {}).get('Type'),
                            'value': opt.get('ResourceRecord', {}).get('Value')
                        }
                        for opt in validation_options
                        if opt.get('ResourceRecord')
                    ],
                    'provisioned_at': timezone.now()
                }
            else:
                return {
                    'success': True,
                    'certificate_arn': certificate_arn,
                    'certificate_id': certificate_arn.split('/')[-1],
                    'domain': domain,
                    'status': 'PENDING_VALIDATION',
                    'validation_method': validation_method,
                    'provisioned_at': timezone.now()
                }

        except Exception as e:
            logger.error(f"[AWS] SSL provisioning failed for {domain}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }