"""
Subscription Plan Showcase GraphQL Types - PUBLIC ACCESS

Provides types for browsing subscription plans
No authentication required - public plan listing
"""

import graphene
import yaml
from pathlib import Path
from graphene_django import DjangoObjectType
from subscription.models import SubscriptionPlan
from .common_types import BaseConnection

# Showcase configuration path
SHOWCASE_CONFIG_PATH = Path(__file__).parent.parent.parent / "services" / "plans_showcase.yaml"
_showcase_config_cache = None

def get_showcase_config():
    """Load showcase config - cached in production, reloadable in dev"""
    global _showcase_config_cache
    from django.conf import settings
    
    # In dev, always reload; in production, cache once
    if settings.DEBUG or _showcase_config_cache is None:
        with open(SHOWCASE_CONFIG_PATH, 'r') as f:
            _showcase_config_cache = yaml.safe_load(f)
    return _showcase_config_cache


class PlanCapabilitiesType(graphene.ObjectType):
    """
    Plan capabilities/features from YAML
    Matches plans.yaml structure exactly
    """
    # Limits
    product_limit = graphene.Int()
    staff_limit = graphene.Int()
    workspace_limit = graphene.Int()
    theme_library_limit = graphene.Int()

    # Features
    custom_domain = graphene.Boolean()
    payment_processing = graphene.Boolean()
    deployment_allowed = graphene.Boolean()
    dedicated_support = graphene.Boolean()

    # Tiers/levels (string values: none, basic, pro, advanced, read_only, full)
    analytics = graphene.String()
    automation = graphene.String()
    api_access = graphene.String()

    # Storage
    storage_gb = graphene.Float()


class PlanBadgeType(graphene.ObjectType):
    """
    Badge display for plan cards (e.g., "Most popular", "Best value")
    Loaded from plans_showcase.yaml
    """
    text = graphene.String()
    tone = graphene.String()  # neutral | highlight | warning


class PlanPricingDisplayType(graphene.ObjectType):
    """
    Pricing display configuration for plan cards
    Controls how pricing is shown (intro, standard, starting_at, free)
    """
    mode = graphene.String()  # free | intro | standard | starting_at
    intro_label = graphene.String()
    intro_suffix = graphene.String()
    starting_label = graphene.String()
    has_intro_discount = graphene.Boolean()
    supports_yearly_billing = graphene.Boolean()


class PlanCTAType(graphene.ObjectType):
    """
    Call-to-action button text configuration
    Changes based on whether it's the current plan
    """
    default = graphene.String()
    current_plan = graphene.String()


class PlanShowcaseType(graphene.ObjectType):
    """
    Complete showcase/presentation configuration for a plan
    Separates UI concerns from pricing/capability data
    Based on Shopify pricing page pattern
    """
    order = graphene.Int()
    name_override = graphene.String()
    tagline = graphene.String()
    badge = graphene.Field(PlanBadgeType)
    pricing_display = graphene.Field(PlanPricingDisplayType)
    cta = graphene.Field(PlanCTAType)
    highlighted_features = graphene.List(graphene.String)


class PlanType(DjangoObjectType):
    """
    Public plan type for plan listing/browsing

    Contains pricing and basic info
    Features loaded dynamically from YAML
    """

    id = graphene.ID(required=True)

    # Computed fields
    is_free = graphene.Boolean()
    is_paid = graphene.Boolean()
    target_market_description = graphene.String()

    # Pricing fields
    intro_price = graphene.Float()
    intro_duration_days = graphene.Int()
    regular_price_monthly = graphene.Float()
    regular_price_yearly = graphene.Float()

    # Dynamic capabilities from YAML
    capabilities = graphene.Field(PlanCapabilitiesType)

    # Showcase/presentation config from plans_showcase.yaml
    showcase = graphene.Field(PlanShowcaseType)

    class Meta:
        model = SubscriptionPlan
        fields = (
            'id', 'name', 'tier', 'description',
            'intro_price', 'intro_duration_days',
            'regular_price_monthly', 'regular_price_yearly',
            'is_active',
            'created_at', 'updated_at'
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        """Return plain UUID instead of encoded ID"""
        return str(self.id)

    def resolve_is_free(self, info):
        """Check if plan is free tier"""
        return self.tier == 'free'

    def resolve_is_paid(self, info):
        """Check if plan is paid tier"""
        return self.tier != 'free'

    def resolve_target_market_description(self, info):
        """Return target market description"""
        return self.target_market

    def resolve_intro_price(self, info):
        return float(self.intro_price) if self.intro_price else 0.0

    def resolve_intro_duration_days(self, info):
        return self.intro_duration_days

    def resolve_regular_price_monthly(self, info):
        return float(self.regular_price_monthly) if self.regular_price_monthly else 0.0

    def resolve_regular_price_yearly(self, info):
        return float(self.regular_price_yearly) if self.regular_price_yearly else 0.0

    def resolve_capabilities(self, info):
        """
        Load capabilities from YAML via CapabilityEngine
        Returns flat dict matching YAML structure
        """
        capabilities_dict = self.get_capabilities()

        # CapabilityEngine returns normalized dict with 'unlimited' → 0
        # Return as PlanCapabilitiesType (GraphQL will map dict keys to type fields)
        return PlanCapabilitiesType(
            product_limit=capabilities_dict.get('product_limit'),
            staff_limit=capabilities_dict.get('staff_limit'),
            workspace_limit=capabilities_dict.get('workspace_limit'),
            theme_library_limit=capabilities_dict.get('theme_library_limit'),
            custom_domain=capabilities_dict.get('custom_domain'),
            payment_processing=capabilities_dict.get('payment_processing'),
            deployment_allowed=capabilities_dict.get('deployment_allowed'),
            dedicated_support=capabilities_dict.get('dedicated_support'),
            analytics=capabilities_dict.get('analytics'),
            automation=capabilities_dict.get('automation'),
            api_access=capabilities_dict.get('api_access'),
            storage_gb=capabilities_dict.get('storage_gb')
        )

    def resolve_showcase(self, info):
        """
        Load showcase/presentation config from plans_showcase.yaml
        Returns display configuration for Shopify-style pricing cards
        Uses dynamic loader for dev hot-reload
        """
        data = get_showcase_config().get(self.tier)
        if not data:
            return None

        return PlanShowcaseType(
            order=data.get("order"),
            name_override=data.get("name_override"),
            tagline=data.get("tagline"),
            badge=PlanBadgeType(**data.get("badge", {})) if data.get("badge") else None,
            pricing_display=PlanPricingDisplayType(**data.get("pricing_display", {})) if data.get("pricing_display") else None,
            cta=PlanCTAType(**data.get("cta", {})) if data.get("cta") else None,
            highlighted_features=data.get("highlighted_features", []),
        )
