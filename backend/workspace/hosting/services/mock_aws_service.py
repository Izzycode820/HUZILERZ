"""
Mock AWS Infrastructure Service
Simulates AWS services for local development and testing

Provides realistic mock responses for:
- API Gateway
- CloudFront
- Route53
- SSL Certificate Management
- DNS Routing

Switch to real AWS by setting USE_MOCK_AWS = False in settings
"""

import uuid
import logging
from typing import Dict, Any, List
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MockAWSService:
    """
    Mock AWS service that simulates real AWS infrastructure

    Provides realistic responses for all AWS services used in hosting infrastructure
    Can be switched to real AWS by changing USE_MOCK_AWS setting
    """

    def __init__(self):
        self.mock_resources = {
            'api_gateways': {},
            'cloudfront_distributions': {},
            'route53_zones': {},
            'ssl_certificates': {},
            'dns_records': {}
        }
        self.mock_data_dir = getattr(settings, 'MOCK_AWS_DATA_DIR', './mock_aws_data')

    # API Gateway Mock Methods
    def create_api_gateway(self, name: str, description: str = "", tier: str = "shared") -> Dict[str, Any]:
        """
        Mock API Gateway creation (pool infrastructure only)

        Args:
            name: Gateway name
            description: Gateway description
            tier: Legacy parameter (ignored, all use shared infrastructure)

        Returns:
            Mock API Gateway configuration
        """
        gateway_id = f"mock-api-{uuid.uuid4().hex[:8]}"

        # All sites use shared pool infrastructure
        base_url = "https://shared-api.huzilerz.com"
        rate_limit_note = "enforced_at_application_level"

        gateway_config = {
            'id': gateway_id,
            'name': name,
            'description': description,
            'base_url': base_url,
            'endpoint_url': f"{base_url}/production",
            'created_at': timezone.now(),
            'status': 'ACTIVE',
            'tier': 'shared',
            'rate_limit': rate_limit_note,
            'resources': {
                'rest_api_id': gateway_id,
                'deployment_id': f"deploy-{uuid.uuid4().hex[:8]}",
                'stage_name': 'production'
            }
        }

        self.mock_resources['api_gateways'][gateway_id] = gateway_config
        logger.info(f"Created mock API Gateway: {gateway_id} (shared pool infrastructure)")

        return gateway_config

    def configure_api_gateway_domain(self, gateway_id: str, domain_name: str) -> Dict[str, Any]:
        """
        Mock custom domain configuration for API Gateway

        Args:
            gateway_id: API Gateway ID
            domain_name: Custom domain to configure

        Returns:
            Domain configuration result
        """
        if gateway_id not in self.mock_resources['api_gateways']:
            return {
                'success': False,
                'error': f"API Gateway {gateway_id} not found"
            }

        domain_config = {
            'domain_name': domain_name,
            'api_gateway_id': gateway_id,
            'certificate_status': 'ISSUED',
            'dns_target': f"d{uuid.uuid4().hex[:12]}.cloudfront.net",
            'status': 'AVAILABLE',
            'configured_at': timezone.now()
        }

        # Store domain configuration
        if 'custom_domains' not in self.mock_resources['api_gateways'][gateway_id]:
            self.mock_resources['api_gateways'][gateway_id]['custom_domains'] = []

        self.mock_resources['api_gateways'][gateway_id]['custom_domains'].append(domain_config)

        logger.info(f"Configured custom domain {domain_name} for API Gateway {gateway_id}")

        return {
            'success': True,
            'domain_config': domain_config
        }

    # CloudFront Mock Methods
    def create_cloudfront_distribution(self, origin_domain: str, distribution_name: str,
                                     tier: str = "shared") -> Dict[str, Any]:
        """
        Mock CloudFront distribution creation

        Args:
            origin_domain: Origin domain (main CDN)
            distribution_name: Distribution name
            tier: Infrastructure tier

        Returns:
            Mock CloudFront configuration
        """
        distribution_id = f"mock-cf-{uuid.uuid4().hex[:8]}"
        domain_name = f"{distribution_id}.cloudfront.net"

        # Configure based on tier
        if tier == 'shared':
            price_class = 'PriceClass_100'
            features = ['basic_caching']
        elif tier == 'dedicated':
            price_class = 'PriceClass_All'
            features = ['advanced_caching', 'custom_ssl']
        elif tier == 'isolated':
            price_class = 'PriceClass_All'
            features = ['enterprise_caching', 'waf', 'real_time_logs', 'custom_ssl']
        else:
            price_class = 'PriceClass_100'
            features = ['basic_caching']

        distribution_config = {
            'id': distribution_id,
            'domain_name': domain_name,
            'origin_domain': origin_domain,
            'name': distribution_name,
            'status': 'Deployed',
            'enabled': True,
            'price_class': price_class,
            'features': features,
            'created_at': timezone.now(),
            'last_modified': timezone.now(),
            'cache_behaviors': [],
            'custom_origins': [
                {
                    'id': f'origin-{uuid.uuid4().hex[:8]}',
                    'domain_name': origin_domain,
                    'protocol_policy': 'https-only'
                }
            ]
        }

        self.mock_resources['cloudfront_distributions'][distribution_id] = distribution_config
        logger.info(f"Created mock CloudFront distribution: {distribution_id} for tier {tier}")

        return distribution_config

    def add_cache_behavior(self, distribution_id: str, path_pattern: str,
                          target_origin: str, user_id: str = None) -> Dict[str, Any]:
        """
        Mock cache behavior addition for path-based routing

        Args:
            distribution_id: CloudFront distribution ID
            path_pattern: Path pattern to match
            target_origin: Target origin URL
            user_id: Optional user ID for tracking

        Returns:
            Cache behavior configuration
        """
        if distribution_id not in self.mock_resources['cloudfront_distributions']:
            return {
                'success': False,
                'error': f"CloudFront distribution {distribution_id} not found"
            }

        behavior_id = f"behavior-{uuid.uuid4().hex[:8]}"
        behavior_config = {
            'id': behavior_id,
            'path_pattern': path_pattern,
            'target_origin': target_origin,
            'user_id': user_id,
            'viewer_protocol_policy': 'redirect-to-https',
            'allowed_methods': ['GET', 'HEAD', 'OPTIONS'],
            'cached_methods': ['GET', 'HEAD'],
            'forward_headers': ['Authorization', 'X-Workspace-Id'],
            'query_string_forwarding': True,
            'created_at': timezone.now()
        }

        self.mock_resources['cloudfront_distributions'][distribution_id]['cache_behaviors'].append(behavior_config)

        logger.info(f"Added cache behavior {behavior_id} for path {path_pattern}")

        return {
            'success': True,
            'behavior_config': behavior_config
        }

    # Route53 Mock Methods
    def create_hosted_zone(self, domain_name: str, description: str = "") -> Dict[str, Any]:
        """
        Mock Route53 hosted zone creation

        Args:
            domain_name: Domain name for the hosted zone
            description: Zone description

        Returns:
            Mock hosted zone configuration
        """
        zone_id = f"mock-zone-{uuid.uuid4().hex[:8]}"

        zone_config = {
            'id': zone_id,
            'name': domain_name,
            'description': description,
            'record_count': 0,
            'created_at': timezone.now(),
            'name_servers': [
                f'ns-{i}.awsdns-{j}.com' for i, j in zip(range(1, 5), ['01', '02', '03', '04'])
            ]
        }

        self.mock_resources['route53_zones'][zone_id] = zone_config
        logger.info(f"Created mock Route53 hosted zone: {zone_id} for {domain_name}")

        return zone_config

    def create_dns_record(self, zone_id: str, record_name: str, record_type: str,
                         record_value: str, ttl: int = 300) -> Dict[str, Any]:
        """
        Mock DNS record creation

        Args:
            zone_id: Hosted zone ID
            record_name: Record name (subdomain)
            record_type: Record type (A, CNAME, etc.)
            record_value: Record value
            ttl: TTL in seconds

        Returns:
            DNS record configuration
        """
        if zone_id not in self.mock_resources['route53_zones']:
            return {
                'success': False,
                'error': f"Hosted zone {zone_id} not found"
            }

        record_id = f"record-{uuid.uuid4().hex[:8]}"
        record_config = {
            'id': record_id,
            'name': record_name,
            'type': record_type,
            'value': record_value,
            'ttl': ttl,
            'created_at': timezone.now(),
            'status': 'INSYNC'
        }

        # Store record
        if 'records' not in self.mock_resources['route53_zones'][zone_id]:
            self.mock_resources['route53_zones'][zone_id]['records'] = []

        self.mock_resources['route53_zones'][zone_id]['records'].append(record_config)
        self.mock_resources['route53_zones'][zone_id]['record_count'] += 1

        logger.info(f"Created DNS record {record_name} -> {record_value}")

        return {
            'success': True,
            'record_config': record_config
        }

    # SSL Certificate Mock Methods
    def request_ssl_certificate(self, domain_name: str, validation_method: str = "DNS") -> Dict[str, Any]:
        """
        Mock SSL certificate request

        Args:
            domain_name: Domain name for certificate
            validation_method: Validation method (DNS or EMAIL)

        Returns:
            SSL certificate configuration
        """
        certificate_id = f"mock-cert-{uuid.uuid4().hex[:8]}"

        certificate_config = {
            'id': certificate_id,
            'domain_name': domain_name,
            'status': 'PENDING_VALIDATION',
            'validation_method': validation_method,
            'requested_at': timezone.now(),
            'expires_at': timezone.now() + timedelta(days=365),
            'validation_records': [
                {
                    'name': f'_acme-challenge.{domain_name}',
                    'type': 'TXT',
                    'value': f'validation-{uuid.uuid4().hex[:16]}'
                }
            ]
        }

        self.mock_resources['ssl_certificates'][certificate_id] = certificate_config
        logger.info(f"Requested mock SSL certificate for {domain_name}")

        return certificate_config

    def validate_ssl_certificate(self, certificate_id: str) -> Dict[str, Any]:
        """
        Mock SSL certificate validation

        Args:
            certificate_id: Certificate ID to validate

        Returns:
            Validation result
        """
        if certificate_id not in self.mock_resources['ssl_certificates']:
            return {
                'success': False,
                'error': f"SSL certificate {certificate_id} not found"
            }

        # Simulate validation process
        certificate = self.mock_resources['ssl_certificates'][certificate_id]
        certificate['status'] = 'ISSUED'
        certificate['validated_at'] = timezone.now()

        logger.info(f"Validated SSL certificate {certificate_id}")

        return {
            'success': True,
            'certificate': certificate
        }

    # Infrastructure Setup Methods
    def setup_infrastructure_for_site(self, deployed_site, infrastructure_tier: str = 'POOL') -> Dict[str, Any]:
        """
        Complete mock infrastructure setup for a deployed site (pool infrastructure)

        Args:
            deployed_site: DeployedSite instance
            infrastructure_tier: Legacy parameter (ignored, all use POOL)

        Returns:
            Complete infrastructure configuration
        """
        site_name = deployed_site.site_name
        subdomain = deployed_site.subdomain
        custom_domain = deployed_site.custom_domain
        workspace_id = str(deployed_site.workspace.id)

        infrastructure_config = {
            'site_name': site_name,
            'subdomain': subdomain,
            'custom_domain': custom_domain,
            'infrastructure_tier': 'POOL',
            'workspace_id': workspace_id,
            'setup_timestamp': timezone.now(),
            'resources': {}
        }

        # Setup shared API Gateway
        api_gateway = self.create_api_gateway(
            f"shared-pool-gateway",
            "Shared API Gateway for all workspaces",
            "shared"
        )
        infrastructure_config['resources']['api_gateway'] = api_gateway

        # Setup shared CloudFront distribution
        cloudfront = self.create_cloudfront_distribution(
            origin_domain=settings.MAIN_THEME_CDN_DOMAIN,
            distribution_name="shared-pool-distribution",
            tier="shared"
        )
        infrastructure_config['resources']['cloudfront'] = cloudfront

        # Create subdomain DNS record (all tiers get subdomains)
        dns_record = self.create_dns_record(
            zone_id='shared-hosted-zone',
            record_name=f"{subdomain}.huzilerz.com",
            record_type="CNAME",
            record_value=cloudfront['domain_name']
        )
        infrastructure_config['resources']['dns_record'] = dns_record

        # Setup SSL if custom domain
        if custom_domain:
            ssl_cert = self.request_ssl_certificate(custom_domain)
            infrastructure_config['resources']['ssl_certificate'] = ssl_cert

            # Configure custom domain for API Gateway
            domain_config = self.configure_api_gateway_domain(api_gateway['id'], custom_domain)
            infrastructure_config['resources']['custom_domain'] = domain_config

        logger.info(f"Completed mock infrastructure setup for {site_name} (pool infrastructure, workspace: {workspace_id})")

        return infrastructure_config

    # Resource Management Methods
    def get_resource_status(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Get status of a mock AWS resource

        Args:
            resource_type: Type of resource (api_gateway, cloudfront, etc.)
            resource_id: Resource ID

        Returns:
            Resource status information
        """
        if resource_type not in self.mock_resources:
            return {
                'success': False,
                'error': f"Resource type {resource_type} not found"
            }

        if resource_id not in self.mock_resources[resource_type]:
            return {
                'success': False,
                'error': f"Resource {resource_id} not found in {resource_type}"
            }

        resource = self.mock_resources[resource_type][resource_id]

        return {
            'success': True,
            'resource': resource,
            'status': resource.get('status', 'ACTIVE'),
            'created_at': resource.get('created_at'),
            'last_modified': resource.get('last_modified', resource.get('created_at'))
        }

    def delete_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Delete a mock AWS resource

        Args:
            resource_type: Type of resource
            resource_id: Resource ID to delete

        Returns:
            Deletion result
        """
        if resource_type not in self.mock_resources:
            return {
                'success': False,
                'error': f"Resource type {resource_type} not found"
            }

        if resource_id not in self.mock_resources[resource_type]:
            return {
                'success': False,
                'error': f"Resource {resource_id} not found in {resource_type}"
            }

        # Remove resource
        del self.mock_resources[resource_type][resource_id]

        logger.info(f"Deleted mock resource {resource_id} from {resource_type}")

        return {
            'success': True,
            'message': f"Resource {resource_id} deleted successfully"
        }

    def list_resources(self, resource_type: str = None) -> Dict[str, Any]:
        """
        List mock AWS resources

        Args:
            resource_type: Optional resource type to filter

        Returns:
            List of resources
        """
        if resource_type:
            if resource_type not in self.mock_resources:
                return {
                    'success': False,
                    'error': f"Resource type {resource_type} not found"
                }
            resources = self.mock_resources[resource_type]
        else:
            resources = self.mock_resources

        return {
            'success': True,
            'resources': resources,
            'total_count': sum(len(resources) for resources in self.mock_resources.values())
        }

    # ==================== Deployment Service Compatibility Methods ====================

    def setup_dns_record(self, subdomain: str, target: str) -> Dict[str, Any]:
        """
        Setup DNS record (wrapper for create_dns_record)
        Used by deployment_service.py
        """
        # Create a temporary hosted zone if needed
        zone_id = self._get_or_create_hosted_zone('huzilerz.com')

        return self.create_dns_record(
            zone_id=zone_id,
            record_name=subdomain,
            record_type='CNAME',
            record_value=target
        )

    def configure_custom_domain(self, domain: str, target: str) -> Dict[str, Any]:
        """
        Configure custom domain (combines SSL + DNS)
        Used by deployment_service.py
        """
        # Request SSL certificate
        ssl_result = self.request_ssl_certificate(domain)

        if ssl_result:
            # Create DNS record
            zone_id = self._get_or_create_hosted_zone(domain)
            dns_result = self.create_dns_record(
                zone_id=zone_id,
                record_name=domain,
                record_type='CNAME',
                record_value=target
            )

            return {
                'success': dns_result.get('success', True),
                'ssl_certificate': ssl_result,
                'dns_record': dns_result.get('record_config'),
                'domain': domain
            }

        return {'success': False, 'error': 'SSL provisioning failed'}

    def invalidate_cache(self, distribution_id: str, paths: List[str]) -> Dict[str, Any]:
        """
        Invalidate CloudFront cache
        Used by deployment_service.py
        """
        invalidation_id = f"inv-{uuid.uuid4().hex[:8]}"

        logger.info(f"Mock cache invalidation for distribution {distribution_id}: {paths}")

        return {
            'success': True,
            'invalidation_id': invalidation_id,
            'distribution_id': distribution_id,
            'paths': paths,
            'status': 'Completed'
        }

    def configure_pool_cloudfront(self, user_id: int, slug: str, behavior_config: Dict) -> Dict[str, Any]:
        """
        Configure CloudFront for POOL tier (wrapper)
        Used by deployment_service.py
        """
        distribution = self.create_cloudfront_distribution(
            origin_domain=getattr(settings, 'MAIN_THEME_CDN_DOMAIN', 'cdn.huzilerz.com'),
            distribution_name=f"pool-{slug}",
            tier='shared'
        )

        # Add cache behavior
        if behavior_config:
            self.add_cache_behavior(
                distribution_id=distribution['id'],
                path_pattern=f"/{slug}/*",
                target_origin=distribution['origin_domain'],
                user_id=str(user_id)
            )

        return {
            'success': True,
            'distribution_id': distribution['id'],
            'distribution_domain': distribution['domain_name']
        }


    def _get_or_create_hosted_zone(self, domain: str) -> str:
        """Helper to get or create hosted zone"""
        # Check if zone exists
        for zone_id, zone in self.mock_resources['route53_zones'].items():
            if zone['name'] == domain:
                return zone_id

        # Create new zone
        zone = self.create_hosted_zone(domain)
        return zone['id']

    def provision_ssl_for_domain(self, domain: str) -> Dict[str, Any]:
        """
        Complete SSL provisioning for a domain (dev mode)
        Simulates Let's Encrypt/ACM certificate provisioning

        Args:
            domain: Domain name to provision SSL for

        Returns:
            SSL provisioning result with certificate details
        """
        try:
            # Request certificate
            cert_result = self.request_ssl_certificate(domain, validation_method='DNS')

            if not cert_result:
                return {
                    'success': False,
                    'error': 'Failed to request SSL certificate'
                }

            certificate_id = cert_result['id']

            # Auto-validate in mock mode (simulate DNS validation)
            validation_result = self.validate_ssl_certificate(certificate_id)

            if validation_result.get('success'):
                logger.info(f"[MOCK] SSL certificate provisioned for {domain}: {certificate_id}")

                return {
                    'success': True,
                    'certificate_id': certificate_id,
                    'certificate_arn': f"arn:aws:acm:mock-region:123456789:certificate/{certificate_id}",
                    'domain': domain,
                    'status': 'ISSUED',
                    'validation_method': 'DNS',
                    'expires_at': cert_result['expires_at'],
                    'provisioned_at': timezone.now()
                }
            else:
                return {
                    'success': False,
                    'error': 'Certificate validation failed'
                }

        except Exception as e:
            logger.error(f"[MOCK] SSL provisioning failed for {domain}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }