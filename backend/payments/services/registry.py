"""
Payment Provider Registry
Central registry for all payment adapters
Enables dynamic provider selection and management
"""
import logging
from typing import Dict, Type, Optional, List
from ..adapters.base import BasePaymentAdapter

logger = logging.getLogger(__name__)


class PaymentProviderRegistry:
    """
    Global registry for payment provider adapters

    Usage:
        # Register providers at startup
        registry.register('fapshi', FapshiAdapter)
        registry.register('mtn', MtnAdapter)

        # Get adapter instance
        adapter = registry.get_adapter('fapshi', config)

        # List all providers
        providers = registry.list_providers()
    """

    def __init__(self):
        self._adapters: Dict[str, Type[BasePaymentAdapter]] = {}
        self._capabilities_cache: Dict[str, Dict] = {}  # Cache capabilities at startup
        self._initialized = False

    def register(self, provider_name: str, adapter_class: Type[BasePaymentAdapter]) -> None:
        """
        Register a payment provider adapter and cache its capabilities

        Args:
            provider_name: Unique provider identifier (e.g., 'fapshi', 'mtn')
            adapter_class: Adapter class (must inherit from BasePaymentAdapter)

        Raises:
            ValueError: If provider already registered or invalid adapter
        """
        if provider_name in self._adapters:
            logger.warning(f"Provider '{provider_name}' is already registered. Overwriting.")

        if not issubclass(adapter_class, BasePaymentAdapter):
            raise ValueError(
                f"Adapter class must inherit from BasePaymentAdapter. "
                f"Got: {adapter_class}"
            )

        self._adapters[provider_name] = adapter_class

        # PERFORMANCE: Cache capabilities at registration time (once) instead of per-request
        # This prevents creating adapter instances on every API call
        try:
            dummy_adapter = adapter_class({})
            self._capabilities_cache[provider_name] = dummy_adapter.get_capabilities()
            logger.info(f"Payment provider registered with cached capabilities: {provider_name} -> {adapter_class.__name__}")
        except Exception as e:
            logger.error(f"Failed to cache capabilities for {provider_name}: {e}")
            # Still register the adapter, but capabilities won't be cached
            logger.info(f"Payment provider registered (no capabilities): {provider_name} -> {adapter_class.__name__}")

    def get_adapter(self, provider_name: str, config: Dict) -> BasePaymentAdapter:
        """
        Get adapter instance for provider

        Args:
            provider_name: Provider identifier
            config: Decrypted provider configuration

        Returns:
            Adapter instance initialized with config

        Raises:
            ValueError: If provider not registered
        """
        if provider_name not in self._adapters:
            raise ValueError(
                f"Payment provider '{provider_name}' is not registered. "
                f"Available providers: {', '.join(self.list_providers())}"
            )

        adapter_class = self._adapters[provider_name]
        return adapter_class(config)

    def is_registered(self, provider_name: str) -> bool:
        """Check if provider is registered"""
        return provider_name in self._adapters

    def list_providers(self) -> List[str]:
        """Get list of all registered provider names"""
        return list(self._adapters.keys())

    def get_cached_capabilities(self, provider_name: str) -> Optional[Dict]:
        """
        Get cached capabilities for a provider (FAST - no adapter instantiation)

        Args:
            provider_name: Provider identifier

        Returns:
            Cached capabilities dict or None if not cached
        """
        return self._capabilities_cache.get(provider_name)

    def get_all_cached_capabilities(self) -> Dict[str, Dict]:
        """
        Get all cached capabilities (FAST - no adapter instantiation)

        Returns:
            Dict mapping provider names to their cached capabilities
        """
        return self._capabilities_cache.copy()

    def get_provider_info(self) -> Dict[str, Dict]:
        """
        Get information about all registered providers (uses cached capabilities)

        Returns:
            Dict mapping provider names to their metadata
        """
        info = {}
        for provider_name, adapter_class in self._adapters.items():
            # Use cached capabilities instead of creating adapter instances
            capabilities = self._capabilities_cache.get(provider_name)
            info[provider_name] = {
                'name': provider_name,
                'class': adapter_class.__name__,
                'capabilities': capabilities
            }

        return info

    def unregister(self, provider_name: str) -> None:
        """
        Unregister a provider (useful for testing)

        Args:
            provider_name: Provider to remove
        """
        if provider_name in self._adapters:
            del self._adapters[provider_name]
            # Also remove from capabilities cache
            self._capabilities_cache.pop(provider_name, None)
            logger.info(f"Payment provider unregistered: {provider_name}")

    def clear(self) -> None:
        """Clear all registered providers (useful for testing)"""
        self._adapters.clear()
        self._capabilities_cache.clear()
        self._initialized = False
        logger.info("Payment provider registry cleared")


# Global registry instance
registry = PaymentProviderRegistry()


def initialize_providers():
    """
    Initialize and register all available payment providers
    Called during Django app startup
    """
    if registry._initialized:
        logger.info("Payment providers already initialized")
        return

    logger.info("Initializing payment providers...")

    # Import and register providers
    # Only import providers that are configured and available

    try:
        from ..providers.fapshi.adapter import FapshiAdapter
        registry.register('fapshi', FapshiAdapter)
    except ImportError as e:
        logger.warning(f"Could not register Fapshi adapter: {e}")

    # Future providers (uncomment when implemented)
    # try:
    #     from ..providers.mtn.adapter import MtnAdapter
    #     registry.register('mtn', MtnAdapter)
    # except ImportError as e:
    #     logger.warning(f"Could not register MTN adapter: {e}")

    # try:
    #     from ..providers.orange.adapter import OrangeAdapter
    #     registry.register('orange', OrangeAdapter)
    # except ImportError as e:
    #     logger.warning(f"Could not register Orange adapter: {e}")

    # try:
    #     from ..providers.flutterwave.adapter import FlutterwaveAdapter
    #     registry.register('flutterwave', FlutterwaveAdapter)
    # except ImportError as e:
    #     logger.warning(f"Could not register Flutterwave adapter: {e}")

    registry._initialized = True
    logger.info(f"Payment providers initialized: {', '.join(registry.list_providers())}")


# Auto-initialize on module import (will be called during Django startup)
# Can be disabled by setting PAYMENTS_AUTO_REGISTER=False in settings
from django.conf import settings
if getattr(settings, 'PAYMENTS_AUTO_REGISTER', True):
    try:
        initialize_providers()
    except Exception as e:
        logger.error(f"Failed to auto-initialize payment providers: {e}")
