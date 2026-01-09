"""
Capability Engine - Converts plan definitions into runtime capability maps
Single source of truth for feature enforcement across the platform
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

PLANS_YAML_PATH = Path(__file__).parent / 'plans.yaml'
CACHE_KEY_PREFIX = 'plan_capabilities'
CACHE_TIMEOUT = 60 * 60  # 1 hour


class CapabilityEngine:
    """
    Capability Engine - Loads plan definitions and generates capability maps

    Flow:
        YAML file → CapabilityEngine → workspace.capabilities → Runtime gating
    """

    @classmethod
    def load_plans_yaml(cls) -> Dict[str, Any]:
        """
        Load and parse plans.yaml
        Cached for performance
        """
        cache_key = f"{CACHE_KEY_PREFIX}_yaml"
        cached_plans = cache.get(cache_key)

        if cached_plans:
            return cached_plans

        try:
            with open(PLANS_YAML_PATH, 'r') as f:
                plans_data = yaml.safe_load(f)

            cache.set(cache_key, plans_data, CACHE_TIMEOUT)
            return plans_data

        except FileNotFoundError:
            logger.error(f"plans.yaml not found at {PLANS_YAML_PATH}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing plans.yaml: {e}")
            raise

    @classmethod
    def get_plan_capabilities(cls, tier: str) -> Dict[str, Any]:
        """
        Get capability map for a specific tier

        IMPORTANT: Returns ONLY capabilities section (not pricing)
        Pricing is handled separately by SubscriptionPlan model

        Args:
            tier: Tier slug (free, beginner, pro, enterprise)

        Returns:
            Dict of capabilities for the tier (features only, no pricing)
        """
        cache_key = f"{CACHE_KEY_PREFIX}_{tier}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        plans = cls.load_plans_yaml()

        if 'tiers' not in plans:
            raise ValueError("Invalid plans.yaml structure - missing 'tiers' key")

        if tier not in plans['tiers']:
            logger.error(f"Tier '{tier}' not found in plans.yaml")
            # Fallback to free tier
            tier = 'free'

        tier_data = plans['tiers'][tier]

        # Extract ONLY the capabilities section (not pricing)
        capabilities = tier_data.get('capabilities', {})

        if not capabilities:
            logger.warning(f"No capabilities section found for tier '{tier}'")
            return {}

        # Normalize 'unlimited' to 0 for consistency
        capabilities = cls._normalize_capabilities(capabilities)

        cache.set(cache_key, capabilities, CACHE_TIMEOUT)
        return capabilities

    @classmethod
    def _normalize_capabilities(cls, capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize capability values
        - 'unlimited' → 0
        - 'none' → None or False depending on context
        """
        normalized = {}

        for key, value in capabilities.items():
            if value == 'unlimited':
                normalized[key] = 0  # 0 means unlimited in our system
            elif value == 'none':
                # Context-dependent normalization
                if 'limit' in key or key in ['payment_methods', 'analytics', 'automation', 'api_access']:
                    normalized[key] = None
                else:
                    normalized[key] = False
            else:
                normalized[key] = value

        return normalized

    @classmethod
    def generate_workspace_capabilities(cls, user, trial_override=None) -> Dict[str, Any]:
        """
        Generate merged capability map for a workspace

        Merge priority:
            1. Plan capabilities (base)
            2. Trial overrides (if trial active)
            3. Admin overrides (future feature)

        Args:
            user: User instance
            trial_override: Optional trial tier override

        Returns:
            Merged capability dict
        """
        # Get base plan capabilities
        try:
            subscription = user.subscription
            tier = subscription.plan.tier
        except:
            # No subscription = free tier
            tier = 'free'

        # Start with plan capabilities
        capabilities = cls.get_plan_capabilities(tier)

        # Apply trial override if active
        if trial_override:
            trial_capabilities = cls.get_plan_capabilities(trial_override)
            capabilities.update(trial_capabilities)

        # Future: Apply admin overrides here

        return capabilities

    @classmethod
    def clear_cache(cls):
        """Clear all capability caches (use after plans.yaml changes)"""
        cache_keys = [
            f"{CACHE_KEY_PREFIX}_yaml",
            f"{CACHE_KEY_PREFIX}_free",
            f"{CACHE_KEY_PREFIX}_beginning",
            f"{CACHE_KEY_PREFIX}_pro",
            f"{CACHE_KEY_PREFIX}_enterprise",
        ]
        for key in cache_keys:
            cache.delete(key)

        logger.info("Capability cache cleared")

    @classmethod
    def validate_plans_yaml(cls) -> bool:
        """
        Validate plans.yaml structure (nested pricing + capabilities)
        Returns True if valid, raises ValueError if invalid
        """
        plans = cls.load_plans_yaml()

        required_tiers = ['free', 'beginning', 'pro', 'enterprise']

        # Required pricing fields
        required_pricing_fields = ['intro', 'regular']
        required_intro_fields = ['price', 'duration_days', 'eligible_once']
        required_regular_fields = ['monthly', 'yearly']

        # Required capability fields
        required_capability_fields = [
            'product_limit', 'staff_limit', 'workspace_limit',
            'custom_domain', 'analytics', 'storage_gb', 'automation',
            'theme_library_limit', 'deployment_allowed', 'dedicated_support',
            'api_access'
        ]

        if 'tiers' not in plans:
            raise ValueError("Missing 'tiers' key in plans.yaml")

        for tier in required_tiers:
            if tier not in plans['tiers']:
                raise ValueError(f"Missing required tier: {tier}")

            tier_data = plans['tiers'][tier]

            # Validate pricing section exists
            if 'pricing' not in tier_data:
                raise ValueError(f"Missing 'pricing' section in tier '{tier}'")

            pricing = tier_data['pricing']

            # Validate intro and regular sections
            for section in required_pricing_fields:
                if section not in pricing:
                    raise ValueError(f"Missing 'pricing.{section}' section in tier '{tier}'")

            # Validate intro fields
            intro = pricing['intro']
            for field in required_intro_fields:
                if field not in intro:
                    raise ValueError(f"Missing 'pricing.intro.{field}' in tier '{tier}'")

            # Validate regular fields
            regular = pricing['regular']
            for field in required_regular_fields:
                if field not in regular:
                    raise ValueError(f"Missing 'pricing.regular.{field}' in tier '{tier}'")

            # Validate capabilities section exists
            if 'capabilities' not in tier_data:
                raise ValueError(f"Missing 'capabilities' section in tier '{tier}'")

            capabilities = tier_data['capabilities']

            # Validate capability fields
            for field in required_capability_fields:
                if field not in capabilities:
                    raise ValueError(f"Missing 'capabilities.{field}' in tier '{tier}'")

        logger.info("plans.yaml validation passed (nested structure)")
        return True
