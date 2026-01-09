"""
Fapshi Gateway Configuration Management
Handles environment switching and credential management
"""
from django.conf import settings
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FapshiConfig:
    """Centralized Fapshi configuration management"""
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment (sandbox or live)"""
        return 'sandbox' if getattr(settings, 'FAPSHI_USE_SANDBOX', True) else 'live'
    
    @staticmethod
    def get_credentials() -> Dict[str, str]:
        """Get environment-specific credentials"""
        environment = FapshiConfig.get_environment()
        
        if environment == 'sandbox':
            return {
                'api_user': getattr(settings, 'FAPSHI_SANDBOX_API_USER', ''),
                'api_key': getattr(settings, 'FAPSHI_SANDBOX_API_KEY', ''), 
                'base_url': getattr(settings, 'FAPSHI_SANDBOX_BASE_URL', 'https://sandbox.api.fapshi.com/v1'),
                'environment': 'sandbox'
            }
        else:
            return {
                'api_user': getattr(settings, 'FAPSHI_LIVE_API_USER', ''),
                'api_key': getattr(settings, 'FAPSHI_LIVE_API_KEY', ''),
                'base_url': getattr(settings, 'FAPSHI_LIVE_BASE_URL', 'https://api.fapshi.com/v1'),
                'environment': 'live'
            }
    
    @staticmethod
    def get_webhook_url() -> Optional[str]:
        """Get appropriate webhook URL for current environment"""
        environment = FapshiConfig.get_environment()

        if environment == 'sandbox':
            return getattr(settings, 'FAPSHI_WEBHOOK_URL_LOCAL', None)
        else:
            return getattr(settings, 'FAPSHI_WEBHOOK_URL_PRODUCTION', None)
    
    @staticmethod
    def is_configured() -> bool:
        """Check if Fapshi is properly configured"""
        try:
            credentials = FapshiConfig.get_credentials()
            webhook_url = FapshiConfig.get_webhook_url()
            
            return bool(
                credentials.get('api_user') and 
                credentials.get('api_key') and 
                webhook_url
            )
        except Exception as e:
            logger.error(f"Configuration check failed: {str(e)}")
            return False
    
    @staticmethod
    def get_timeout_settings() -> Dict[str, int]:
        """Get timeout settings for API requests"""
        return {
            'request_timeout': getattr(settings, 'FAPSHI_REQUEST_TIMEOUT', 30),
            'max_retries': getattr(settings, 'FAPSHI_MAX_RETRIES', 3),
            'retry_delay': getattr(settings, 'FAPSHI_RETRY_DELAY', 2)
        }
    
    @staticmethod
    def get_debug_mode() -> bool:
        """Check if debug mode is enabled for payment gateway"""
        return getattr(settings, 'FAPSHI_DEBUG_MODE', False)
    
    @staticmethod
    def log_configuration_status() -> None:
        """Log current configuration status (without exposing secrets)"""
        credentials = FapshiConfig.get_credentials()
        webhook_url = FapshiConfig.get_webhook_url()
        
        logger.info(f"Fapshi Configuration Status:")
        logger.info(f"  Environment: {credentials.get('environment')}")
        logger.info(f"  Base URL: {credentials.get('base_url')}")
        logger.info(f"  API User: {'✓' if credentials.get('api_user') else '✗'}")
        logger.info(f"  API Key: {'✓' if credentials.get('api_key') else '✗'}")
        logger.info(f"  Webhook URL: {'✓' if webhook_url else '✗'}")
        logger.info(f"  Is Configured: {'✓' if FapshiConfig.is_configured() else '✗'}")


def get_required_settings() -> Dict[str, str]:
    """
    Get list of required Django settings for Fapshi integration
    Useful for deployment validation
    """
    environment = FapshiConfig.get_environment()
    
    if environment == 'sandbox':
        return {
            'FAPSHI_SANDBOX_API_USER': 'Fapshi sandbox API user ID',
            'FAPSHI_SANDBOX_API_KEY': 'Fapshi sandbox API key',
            'FAPSHI_WEBHOOK_URL_SANDBOX': 'Webhook URL for sandbox environment',
            'FAPSHI_SANDBOX_BASE_URL': 'Fapshi sandbox base URL (optional)'
        }
    else:
        return {
            'FAPSHI_LIVE_API_USER': 'Fapshi live API user ID', 
            'FAPSHI_LIVE_API_KEY': 'Fapshi live API key',
            'FAPSHI_WEBHOOK_URL_LIVE': 'Webhook URL for live environment',
            'FAPSHI_LIVE_BASE_URL': 'Fapshi live base URL (optional)'
        }


def validate_configuration() -> Dict[str, str]:
    """
    Validate configuration and return any missing settings
    Returns empty dict if all settings are present
    """
    required_settings = get_required_settings()
    missing_settings = {}
    
    for setting_name, description in required_settings.items():
        if not getattr(settings, setting_name, None):
            missing_settings[setting_name] = description
    
    return missing_settings