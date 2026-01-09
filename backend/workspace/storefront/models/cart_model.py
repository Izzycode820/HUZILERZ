# Cart Model - Shopping cart management for storefront (customer-facing)
# Clean implementation following Shopify patterns with atomic operations

from django.db import models
from django.db import transaction
from decimal import Decimal
import uuid
from workspace.core.models.base_models import TenantScopedModel


class Cart(TenantScopedModel):
    """
    Shopping cart model following Shopify patterns
    Supports guest carts via session_id

    Engineering Principles Applied:
    - Performance: Session-based carts for quick responses
    - Scalability: Concurrent safe operations with atomic transactions
    - Maintainability: Clear cart/checkout separation
    - Security: Atomic stock management
    - Simplicity: Standard checkout flow states
    - Production-Ready: Race condition prevention
    """

    # Session-based cart for guest users
    session_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique session identifier for guest carts"
    )

    # User association for authenticated users (FUTURE ENHANCEMENT)
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts',
        help_text="Authenticated user (optional - for future customer accounts)"
    )

    # Cart metadata
    currency = models.CharField(max_length=3, default='XAF', help_text="Cart currency")

    # Cart state
    is_active = models.BooleanField(default=True, help_text="Whether cart is active")
    abandoned_at = models.DateTimeField(null=True, blank=True, help_text="When cart was abandoned")

    # Cart totals (cached for performance)
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Cart subtotal (sum of item totals)"
    )

    # Discount tracking
    discount_code = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Applied discount code"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Discount amount applied to cart"
    )
    applied_discount = models.ForeignKey(
        'workspace_store.Discount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
        help_text="Reference to applied discount"
    )

    class Meta:
        app_label = 'workspace_storefront'
        db_table = 'storefront_carts'
        indexes = [
            models.Index(fields=['workspace', 'session_id']),
            models.Index(fields=['workspace', 'user', 'is_active']),
            models.Index(fields=['abandoned_at']),
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email} - {self.workspace.name}"
        return f"Guest Cart {self.session_id[:8]}... - {self.workspace.name}"

    def save(self, *args, **kwargs):
        # Generate session ID if not provided for guest carts
        if not self.session_id and not self.user:
            self.session_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

    # BUSINESS LOGIC PROPERTIES
    @property
    def item_count(self):
        """Get number of distinct items in cart (not total quantity)"""
        return self.items.count()  # Count distinct products, not sum of quantities

    @property
    def is_guest_cart(self):
        """Check if this is a guest cart"""
        return self.user is None

    @property
    def is_empty(self):
        """Check if cart is empty"""
        return self.items.count() == 0

    # BUSINESS METHODS
    def calculate_totals(self):
        """Recalculate cart totals from items"""
        self.subtotal = sum(
            item.total_price for item in self.items.all()
        )
        self.save(update_fields=['subtotal'])

    @transaction.atomic
    def add_item(self, product, quantity=1):
        """Add item to cart with atomic operations"""
        from workspace.store.models import Product

        # Lock product for stock check
        product = Product.objects.select_for_update().get(id=product.id)

        # Check stock availability
        if product.track_inventory and product.stock_quantity < quantity:
            if not product.allow_backorders:
                raise ValueError(f"Insufficient stock for {product.name}")

        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={
                'quantity': quantity,
                'price_snapshot': product.price
            }
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Recalculate totals
        self.calculate_totals()

        return cart_item

    @transaction.atomic
    def update_item_quantity(self, product_id, quantity):
        """Update item quantity with atomic operations"""
        from workspace.store.models import Product

        if quantity <= 0:
            return self.remove_item(product_id)

        # Lock product for stock check
        product = Product.objects.select_for_update().get(id=product_id)

        # Check stock availability
        if product.track_inventory and product.stock_quantity < quantity:
            if not product.allow_backorders:
                raise ValueError(f"Insufficient stock for {product.name}")

        cart_item = self.items.get(product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()

        # Recalculate totals
        self.calculate_totals()

        return cart_item

    def remove_item(self, product_id):
        """Remove item from cart"""
        try:
            cart_item = self.items.get(product_id=product_id)
            cart_item.delete()
            self.calculate_totals()
            return True
        except CartItem.DoesNotExist:
            return False

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
        self.subtotal = 0
        self.save(update_fields=['subtotal'])

    def mark_abandoned(self):
        """Mark cart as abandoned"""
        from django.utils import timezone

        self.is_active = False
        self.abandoned_at = timezone.now()
        self.save(update_fields=['is_active', 'abandoned_at'])

    # TODO: FUTURE - Implement when customer accounts are added
    def merge_with_user_cart(self, user):
        """Merge guest cart with user cart (FUTURE ENHANCEMENT)"""
        if self.user:
            raise ValueError("Cart already belongs to a user")

        # Get or create user cart
        user_cart, created = Cart.objects.get_or_create(
            workspace=self.workspace,
            user=user,
            is_active=True,
            defaults={'currency': self.currency}
        )

        # Merge items
        for item in self.items.all():
            try:
                user_cart.add_item(item.product, item.quantity)
            except ValueError:
                # Skip items with insufficient stock
                continue

        # Mark guest cart as inactive
        self.mark_abandoned()

        return user_cart


class CartItem(models.Model):
    """
    Individual items within a shopping cart
    Captures price snapshot for price consistency
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        'workspace_store.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )

    # Variant support for products with options (size, color, etc.)
    variant = models.ForeignKey(
        'workspace_store.ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items',
        help_text="Selected product variant (optional)"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Quantity of product in cart"
    )

    # Price snapshot for consistency
    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price at time of adding to cart"
    )

    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'workspace_storefront'
        db_table = 'storefront_cart_items'
        unique_together = ['cart', 'product', 'variant']  # Include variant to match get_or_create logic
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def total_price(self):
        """Calculate total price for this item"""
        return self.quantity * self.price_snapshot

    def save(self, *args, **kwargs):
        # Ensure price snapshot is set
        if not self.price_snapshot and self.product:
            self.price_snapshot = self.product.price
        super().save(*args, **kwargs)

        # Update cart totals
        if self.cart:
            self.cart.calculate_totals()
