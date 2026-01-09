# Discount Models - Shopify-style with Cameroon context
# PRODUCTION-READY: Industry standard models

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

from workspace.core.models.base_models import TenantScopedModel


class Discount(TenantScopedModel):
    """
    Shopify-style discount system for e-commerce

    Production Best Practices:
    - Tenant scoping for multi-workspace
    - Comprehensive discount types
    - Usage limits and tracking
    - Cameroon market optimizations
    """

    # Discount Types
    DISCOUNT_TYPE_CHOICES = [
        ('amount_off_product', 'Amount off products'),
        ('buy_x_get_y', 'Buy X Get Y'),
        ('amount_off_order', 'Amount off order'),  # FUTURE IMPLEMENTATION
        ('free_shipping', 'Free Shipping'),  # FUTURE IMPLEMENTATION
    ]

    # Method Types
    METHOD_CHOICES = [
        ('discount_code', 'Discount Code'),
        ('automatic', 'Automatic Discount'),
    ]

    # Discount Value Types (for amount_off_product)
    DISCOUNT_VALUE_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ]

    # Buy X Get Y Discount Types
    BXGY_DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('amount_off_each', 'Amount off each'),
        ('free', 'Free'),
    ]

    # Customer Buys Types (for buy_x_get_y)
    CUSTOMER_BUYS_TYPE_CHOICES = [
        ('minimum_quantity', 'Minimum quantity of items'),
        ('minimum_purchase_amount', 'Minimum purchase amount'),
    ]

    # Minimum Purchase Requirement Types
    MINIMUM_REQUIREMENT_CHOICES = [
        ('none', 'No minimum requirements'),
        ('minimum_amount', 'Minimum purchase amount'),
        ('minimum_quantity', 'Minimum quantity of items'),
    ]

    # Discount Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
        ('scheduled', 'Scheduled'),
    ]

    # Discount Code
    code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Discount code (e.g., SUMMER20, WELCOME10)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Discount name for admin reference"
    )

    # Method
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default='discount_code',
        db_index=True,
        help_text="Discount method (discount_code or automatic)"
    )

    # Discount Configuration
    discount_type = models.CharField(
        max_length=30,
        choices=DISCOUNT_TYPE_CHOICES,
        default='amount_off_product',
        db_index=True,
        help_text="Type of discount"
    )

    # For amount_off_product
    discount_value_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_VALUE_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Discount value type (percentage or fixed_amount) - for amount_off_product"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Discount value - for amount_off_product"
    )

    # For buy_x_get_y - Customer buys
    customer_buys_type = models.CharField(
        max_length=30,
        choices=CUSTOMER_BUYS_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Customer buys type - for buy_x_get_y"
    )
    customer_buys_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Customer buys quantity - for buy_x_get_y"
    )
    customer_buys_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Customer buys minimum purchase amount - for buy_x_get_y"
    )
    customer_buys_product_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific product IDs for customer buys - for buy_x_get_y"
    )

    # For buy_x_get_y - Customer gets
    customer_gets_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Customer gets quantity - for buy_x_get_y"
    )
    customer_gets_product_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific product IDs for customer gets - for buy_x_get_y"
    )
    bxgy_discount_type = models.CharField(
        max_length=20,
        choices=BXGY_DISCOUNT_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Discount type for buy_x_get_y (percentage, amount_off_each, free)"
    )
    bxgy_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Discount value for buy_x_get_y"
    )
    max_uses_per_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times discount can be used per order - for buy_x_get_y"
    )

    # Usage Limits (Shopify-style)
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this discount can be used"
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this discount has been used"
    )
    usage_limit_per_customer = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum usage per customer"
    )

    # Validity Period
    starts_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the discount becomes active"
    )
    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the discount expires"
    )

    # Minimum Purchase Requirements (Page 2 - Shared)
    minimum_requirement_type = models.CharField(
        max_length=20,
        choices=MINIMUM_REQUIREMENT_CHOICES,
        default='none',
        help_text="Type of minimum purchase requirement"
    )
    minimum_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum purchase amount (FCFA)"
    )
    minimum_quantity_items = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum quantity of items"
    )

    # Customer Targeting
    customer_segmentation = models.JSONField(
        default=dict,
        blank=True,
        help_text="Customer targeting rules (regions, types, tags)"
    )
    applies_to_all_customers = models.BooleanField(
        default=True,
        help_text="Whether discount applies to all customers"
    )

    # Product/Category Targeting
    applies_to_all_products = models.BooleanField(
        default=True,
        help_text="Whether discount applies to all products"
    )
    product_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific product IDs this discount applies to"
    )
    category_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific category IDs this discount applies to"
    )

    # Cameroon-specific Settings
    applies_to_regions = models.JSONField(
        default=list,
        blank=True,
        help_text="Cameroon regions this discount applies to"
    )
    applies_to_customer_types = models.JSONField(
        default=list,
        blank=True,
        help_text="Customer types this discount applies to"
    )

    # Maximum Discount Uses (Page 2 - Shared)
    limit_total_uses = models.BooleanField(
        default=False,
        help_text="Whether to limit total number of uses"
    )
    limit_one_per_customer = models.BooleanField(
        default=False,
        help_text="Whether to limit to one use per customer"
    )

    # Combinations (Page 2 - Shared)
    can_combine_with_product_discounts = models.BooleanField(
        default=False,
        help_text="Can combine with product discounts"
    )
    can_combine_with_order_discounts = models.BooleanField(
        default=False,
        help_text="Can combine with order discounts"
    )

    # Status & Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )

    # Analytics
    total_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount discounted across all orders"
    )
    total_orders = models.PositiveIntegerField(
        default=0,
        help_text="Total orders that used this discount"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'workspace_store_discounts'
        indexes = [
            models.Index(fields=['workspace', 'code']),
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'discount_type']),
            models.Index(fields=['workspace', 'method']),
            models.Index(fields=['workspace', 'starts_at', 'ends_at']),
            models.Index(fields=['code']),
            models.Index(fields=['discount_type', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'code'],
                name='unique_discount_code_per_workspace'
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    # BUSINESS LOGIC PROPERTIES

    @property
    def is_active(self):
        """Check if discount is currently active"""
        now = timezone.now()

        if self.status != 'active':
            return False

        if self.starts_at:
            starts_at = self.starts_at
            if timezone.is_naive(starts_at):
                starts_at = timezone.make_aware(starts_at)
            if starts_at > now:
                return False

        if self.ends_at:
            ends_at = self.ends_at
            if timezone.is_naive(ends_at):
                ends_at = timezone.make_aware(ends_at)
            if ends_at < now:
                return False

        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False

        return True

    @property
    def has_usage_limit_reached(self):
        """Check if usage limit has been reached"""
        return self.usage_limit and self.usage_count >= self.usage_limit

    @property
    def is_expired(self):
        """Check if discount has expired"""
        now = timezone.now()
        if not self.ends_at:
            return False
        ends_at = self.ends_at
        if timezone.is_naive(ends_at):
            ends_at = timezone.make_aware(ends_at)
        return ends_at < now

    @property
    def is_scheduled(self):
        """Check if discount is scheduled for future"""
        now = timezone.now()
        if not self.starts_at:
            return False
        starts_at = self.starts_at
        if timezone.is_naive(starts_at):
            starts_at = timezone.make_aware(starts_at)
        return starts_at > now

    @property
    def average_discount_amount(self):
        """Calculate average discount amount per order"""
        if self.total_orders == 0:
            return Decimal('0.00')
        return self.total_discount_amount / self.total_orders

    # BUSINESS METHODS

    def increment_usage(self, discount_amount=Decimal('0.00')):
        """Increment usage count and total discount amount"""
        self.usage_count += 1
        self.total_discount_amount += discount_amount
        self.total_orders += 1
        self.save(update_fields=[
            'usage_count',
            'total_discount_amount',
            'total_orders'
        ])

    def can_apply_to_customer(self, customer):
        """Check if discount can be applied to specific customer"""
        if self.applies_to_all_customers:
            return True

        # Check customer segmentation
        segmentation = self.customer_segmentation

        # Check region
        if segmentation.get('regions') and customer.region not in segmentation['regions']:
            return False

        # Check customer type
        if segmentation.get('customer_types') and customer.customer_type not in segmentation['customer_types']:
            return False

        # Check tags
        if segmentation.get('tags') and not any(tag in customer.tags for tag in segmentation['tags']):
            return False

        return True

    def can_apply_to_product(self, product_id):
        """Check if discount can be applied to specific product"""
        if self.applies_to_all_products:
            return True

        return str(product_id) in [str(pid) for pid in self.product_ids]

    def can_apply_to_order(self, order_amount, customer=None):
        """Check if discount can be applied to order"""
        # Check minimum order amount
        if self.minimum_order_amount and order_amount < self.minimum_order_amount:
            return False

        # Check customer eligibility
        if customer and not self.can_apply_to_customer(customer):
            return False

        return True

    def calculate_discount_amount(self, order_amount, product_id=None):
        """
        Calculate discount amount for given order amount

        Performance: Optimized calculation with decimal precision
        Reliability: Handles all discount types safely
        """
        if self.discount_type == 'amount_off_product':
            if self.discount_value_type == 'percentage':
                if self.value is None:
                    return Decimal('0.00')
                return order_amount * (self.value / Decimal('100.00'))
            elif self.discount_value_type == 'fixed_amount':
                if self.value is None:
                    return Decimal('0.00')
                return min(self.value, order_amount)
        elif self.discount_type == 'buy_x_get_y':
            # Buy X Get Y discount calculation handled separately in order processing
            return Decimal('0.00')
        elif self.discount_type == 'free_shipping':
            # FUTURE IMPLEMENTATION: Free shipping discount
            return Decimal('0.00')
        elif self.discount_type == 'amount_off_order':
            # FUTURE IMPLEMENTATION: Amount off order discount
            return Decimal('0.00')
        else:
            return Decimal('0.00')


class DiscountUsage(TenantScopedModel):
    """
    Track discount usage for analytics and limits

    Production Best Practices:
    - Usage tracking for analytics
    - Customer-level usage limits
    - Order-level discount application
    """

    discount = models.ForeignKey(
        Discount,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    order_id = models.CharField(
        max_length=100,
        help_text="Order ID where discount was applied"
    )
    customer_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Customer ID who used the discount"
    )

    # Discount Application
    order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Order amount before discount"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount discounted"
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Order amount after discount"
    )

    # Context
    applied_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Customer IP address for fraud detection"
    )

    class Meta:
        app_label = 'workspace_store'
        db_table = 'workspace_store_discount_usages'
        indexes = [
            models.Index(fields=['workspace', 'discount']),
            models.Index(fields=['workspace', 'customer_id']),
            models.Index(fields=['workspace', 'applied_at']),
            models.Index(fields=['discount', 'customer_id']),
        ]

    def __str__(self):
        return f"{self.discount.code} - Order {self.order_id}"