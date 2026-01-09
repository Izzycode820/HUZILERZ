"""
Test Data Fixtures for Order Testing
Shopify-style test data for comprehensive order testing
"""

from workspace.core.models import Workspace
from authentication.models.user import User
from workspace.store.models import Order, OrderItem, Product, ProductVariant


def create_test_workspace():
    """Create test workspace"""
    return Workspace.objects.create(
        name='Test Store',
        slug='test-store',
        type='store',
        status='active'
    )


def create_test_user():
    """Create test user"""
    return User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        first_name='Test',
        last_name='Admin'
    )


def create_test_products(workspace):
    """Create test products for order testing"""
    product1 = Product.objects.create(
        workspace=workspace,
        name='Test Product 1',
        sku='TP001',
        price=15000.00,
        status='published',
        is_active=True
    )

    product2 = Product.objects.create(
        workspace=workspace,
        name='Test Product 2',
        sku='TP002',
        price=25000.00,
        status='published',
        is_active=True
    )

    # Create variants
    variant1 = ProductVariant.objects.create(
        product=product1,
        workspace=workspace,
        sku='TP001-M',
        option1='Size M',
        price=15000.00,
        track_inventory=True
    )

    variant2 = ProductVariant.objects.create(
        product=product2,
        workspace=workspace,
        sku='TP002-L',
        option1='Size L',
        price=25000.00,
        track_inventory=True
    )

    return {
        'product1': product1,
        'product2': product2,
        'variant1': variant1,
        'variant2': variant2
    }


def create_test_orders(workspace, products):
    """Create test orders with different statuses and sources"""

    # Pending WhatsApp order
    pending_order = Order.objects.create(
        workspace=workspace,
        order_number='ORD-001',
        order_source='whatsapp',
        customer_email='customer1@example.com',
        customer_name='John Doe',
        customer_phone='+237612345678',
        shipping_region='littoral',
        shipping_address={
            'street': '123 Main Street',
            'city': 'Douala',
            'region': 'littoral',
            'country': 'Cameroon',
            'postal_code': '00237'
        },
        billing_address={
            'street': '123 Main Street',
            'city': 'Douala',
            'region': 'littoral',
            'country': 'Cameroon',
            'postal_code': '00237'
        },
        status='pending',
        payment_status='pending',
        payment_method='cash',
        subtotal=30000.00,
        shipping_cost=5000.00,
        total_amount=35000.00,
        currency='XAF'
    )

    # Processing manual order
    processing_order = Order.objects.create(
        workspace=workspace,
        order_number='ORD-002',
        order_source='manual',
        customer_email='customer2@example.com',
        customer_name='Jane Smith',
        customer_phone='+237698765432',
        shipping_region='centre',
        shipping_address={
            'street': '456 Central Avenue',
            'city': 'Yaounde',
            'region': 'centre',
            'country': 'Cameroon',
            'postal_code': '00237'
        },
        billing_address={
            'street': '456 Central Avenue',
            'city': 'Yaounde',
            'region': 'centre',
            'country': 'Cameroon',
            'postal_code': '00237'
        },
        status='processing',
        payment_status='paid',
        payment_method='mobile_money',
        subtotal=25000.00,
        shipping_cost=3000.00,
        total_amount=28000.00,
        currency='XAF'
    )

    # Completed payment order
    completed_order = Order.objects.create(
        workspace=workspace,
        order_number='ORD-003',
        order_source='payment',
        customer_email='customer3@example.com',
        customer_name='Bob Wilson',
        customer_phone='+237655443322',
        shipping_region='far_north',
        shipping_address={
            'street': '789 North Road',
            'city': 'Garoua',
            'region': 'far_north',
            'country': 'Cameroon',
            'postal_code': '00237'
        },
        billing_address={
            'street': '789 North Road',
            'city': 'Garoua',
            'region': 'far_north',
            'country': 'Cameroon',
            'postal_code': '00237'
        },
        status='delivered',
        payment_status='paid',
        payment_method='card',
        subtotal=40000.00,
        shipping_cost=7000.00,
        total_amount=47000.00,
        currency='XAF'
    )

    # Create order items
    OrderItem.objects.create(
        order=pending_order,
        product=products['product1'],
        variant=products['variant1'],
        product_name='Test Product 1',
        product_sku='TP001-M',
        quantity=2,
        unit_price=15000.00
    )

    OrderItem.objects.create(
        order=processing_order,
        product=products['product2'],
        variant=products['variant2'],
        product_name='Test Product 2',
        product_sku='TP002-L',
        quantity=1,
        unit_price=25000.00
    )

    OrderItem.objects.create(
        order=completed_order,
        product=products['product1'],
        variant=products['variant1'],
        product_name='Test Product 1',
        product_sku='TP001-M',
        quantity=1,
        unit_price=15000.00
    )

    OrderItem.objects.create(
        order=completed_order,
        product=products['product2'],
        variant=products['variant2'],
        product_name='Test Product 2',
        product_sku='TP002-L',
        quantity=1,
        unit_price=25000.00
    )

    return {
        'pending_order': pending_order,
        'processing_order': processing_order,
        'completed_order': completed_order
    }


def get_order_create_input():
    """Get valid order creation input data"""
    return {
        'orderSource': 'manual',
        'customerEmail': 'newcustomer@example.com',
        'customerName': 'New Customer',
        'customerPhone': '+237611223344',
        'shippingRegion': 'littoral',
        'shippingAddress': {
            'street': '321 New Street',
            'city': 'Douala',
            'region': 'littoral',
            'country': 'Cameroon',
            'postalCode': '00237'
        },
        'billingAddress': {
            'street': '321 New Street',
            'city': 'Douala',
            'region': 'littoral',
            'country': 'Cameroon',
            'postalCode': '00237'
        },
        'shippingCost': '5000.00',
        'taxAmount': '0.00',
        'discountAmount': '0.00',
        'paymentMethod': 'cash',
        'currency': 'XAF',
        'notes': 'Test order creation',
        'items': [
            {
                'productId': 'product-uuid-1',
                'variantId': 'variant-uuid-1',
                'quantity': 2,
                'unitPrice': '15000.00'
            },
            {
                'productId': 'product-uuid-2',
                'variantId': 'variant-uuid-2',
                'quantity': 1,
                'unitPrice': '25000.00'
            }
        ]
    }