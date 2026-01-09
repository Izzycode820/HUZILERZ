"""
Store Analytics GraphQL Types

Type definitions for analytics dashboard and metrics.
Tier-gated types for BASIC, PRO, and ADVANCED features.

Follows workspace auto-scoping pattern from store module.
"""

import graphene
from graphene import ObjectType, String, Int, Float, List, Field
from graphene_django import DjangoObjectType



class PaymentBreakdown(ObjectType):
    """Payment method distribution - BASIC tier"""
    mobile_money = Int(description="Orders paid via Mobile Money")
    cash_on_delivery = Int(description="Orders paid via Cash on Delivery")
    card = Int(description="Orders paid via Card")
    whatsapp = Int(description="Orders via WhatsApp")
    bank_transfer = Int(description="Orders paid via Bank Transfer")


class DashboardCard(ObjectType):
    """
    Metric card for dashboard display - BASIC tier
    Represents a single KPI with trend information
    """
    title = String(required=True, description="Card title (e.g., 'Total Revenue')")
    value = String(required=True, description="Formatted display value")
    trend = String(required=True, description="Trend percentage (e.g., '+12.5%')")
    trend_direction = String(required=True, description="'up' or 'down'")


class ChartDataPoint(ObjectType):
    """Single data point in time-series chart - BASIC tier"""
    date = String(required=True, description="ISO date (YYYY-MM-DD)")
    orders = Int(required=True, description="Order count for the day")
    revenue = Float(required=True, description="Revenue for the day")


class ChartConfig(ObjectType):
    """Chart series configuration"""
    label = String(required=True, description="Display label")
    color = String(required=True, description="CSS color value")


class ChartSeriesConfig(ObjectType):
    """Chart series configurations for orders and revenue"""
    orders = Field(ChartConfig, description="Orders series config")
    revenue = Field(ChartConfig, description="Revenue series config")


class ChartData(ObjectType):
    """Time-series chart data with configuration - BASIC tier"""
    data = List(ChartDataPoint, required=True, description="Chart data points")
    config = Field(ChartSeriesConfig, description="Series configurations")


class FunnelStage(ObjectType):
    """Single stage in conversion funnel - PRO tier"""
    name = String(required=True, description="Stage name")
    count = Int(required=True, description="Count at this stage")
    rate = Float(required=True, description="Percentage of previous stage")


class FunnelMetrics(ObjectType):
    """Funnel summary metrics - PRO tier"""
    conversion_rate = Float(description="Overall conversion rate")
    abandonment_rate = Float(description="Cart abandonment rate")
    cart_abandoned = Int(description="Number of abandoned carts")


class ConversionFunnel(ObjectType):
    """
    Conversion funnel data - PRO tier
    Shows customer journey: Page View -> Cart -> Checkout -> Order
    """
    stages = List(FunnelStage, required=True, description="Funnel stages")
    metrics = Field(FunnelMetrics, description="Summary metrics")


class CustomerMetrics(ObjectType):
    """Customer analytics - PRO tier"""
    new_customers = Int(description="New customers in period")
    returning_customers = Int(description="Returning customers in period")
    total = Int(description="Total unique customers")
    new_rate = Float(description="Percentage of new customers")


class StoreAnalytics(ObjectType):
    """
    Complete store analytics dashboard - tier-gated
    
    BASIC: cards, chart, payment_breakdown
    PRO: + funnel, customers
    ADVANCED: + (future features)
    
    Workspace is auto-scoped via GraphQL context (no workspace field needed).
    """
    # Metadata
    analytics_level = String(required=True, description="Analytics capability level")
    generated_at = String(required=True, description="Generation timestamp")
    has_access = graphene.Boolean(required=True, description="Whether workspace has analytics access")
    
    # BASIC tier
    cards = List(DashboardCard, description="4 metric cards")
    chart = Field(ChartData, description="Orders/Revenue chart")
    payment_breakdown = Field(PaymentBreakdown, description="Payment method split")
    
    # PRO tier (nullable - None if tier not met)
    funnel = Field(ConversionFunnel, description="Conversion funnel (PRO+)")
    customers = Field(CustomerMetrics, description="Customer metrics (PRO+)")
    
    # Error handling
    error = String(description="Error message if access denied")
    required_plan = String(description="Required plan for access")

