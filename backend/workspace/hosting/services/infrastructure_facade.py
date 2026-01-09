"""
Infrastructure Facade - Seamless Dev/Prod Switching
Provides unified interface for DNS, SSL, CDN operations
Routes to mock or real AWS based on INFRASTRUCTURE_MODE setting
"""
import logging
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class InfrastructureFacade:
    """
    Factory pattern for infrastructure operations
    Returns appropriate service based on INFRASTRUCTURE_MODE

    Usage:
        facade = InfrastructureFacade.get_service()
        result = facade.setup_dns_record(subdomain='mystore', target='cdn.example.com')
    """

    _mock_service = None
    _aws_service = None

    @classmethod
    def get_service(cls):
        """
        Get appropriate infrastructure service based on mode

        Returns:
            MockInfrastructureService or AWSInfrastructureService
        """
        mode = getattr(settings, 'INFRASTRUCTURE_MODE', 'mock')

        if mode == 'mock':
            return cls._get_mock_service()
        else:
            return cls._get_aws_service()

    @classmethod
    def _get_mock_service(cls):
        """Lazy-load mock service (singleton)"""
        if cls._mock_service is None:
            from .mock_aws_service import MockAWSService
            cls._mock_service = MockAWSService()
            logger.info("Using MockAWSService (dev mode)")
        return cls._mock_service

    @classmethod
    def _get_aws_service(cls):
        """Lazy-load AWS service (singleton)"""
        if cls._aws_service is None:
            from .infrastructure_service import AWSInfrastructureService
            cls._aws_service = AWSInfrastructureService()
            logger.info("Using AWSInfrastructureService (production mode)")
        return cls._aws_service

    @classmethod
    def get_mode(cls) -> str:
        """Get current infrastructure mode"""
        return getattr(settings, 'INFRASTRUCTURE_MODE', 'mock')

    @classmethod
    def is_mock_mode(cls) -> bool:
        """Check if running in mock mode"""
        return cls.get_mode() == 'mock'

    @classmethod
    def provision_ssl(cls, domain: str) -> Dict[str, Any]:
        """
        Provision SSL certificate for a domain
        Routes to mock or AWS based on mode

        Args:
            domain: Domain name to provision SSL for

        Returns:
            SSL provisioning result
        """
        service = cls.get_service()
        return service.provision_ssl_for_domain(domain)
