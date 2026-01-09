"""
Comprehensive Order Mutation Tests
Tests all order mutations with manual token insertion
"""

import os
import json
from django.test import TestCase
from graphene.test import Client
from workspace.store.graphql.schema import schema
from .test_auth import auth_helper
from .test_data import create_test_products, create_test_orders


class OrderMutationTestCase(TestCase):
    """
    Order mutation tests with manual token insertion
    Just expects a JWT token with workspace claims
    """

    def setUp(self):
        """Set up test data and authentication"""
        # Get token from environment variable
        token = os.environ.get('JWT_TOKEN')
        if not token:
            raise ValueError("JWT_TOKEN environment variable not set. Please set it before running tests.")

        # Set token and get context
        auth_helper.set_token(token)
        self.context = auth_helper.get_graphql_context()

        # Get workspace from token claims instead of creating one
        # The workspace should already exist in your system
        from workspace.core.models import Workspace
        workspace_id = "3247e57e-1c48-49e9-af79-9ebc9fec1677"  # From your token

        try:
            self.workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            raise ValueError(f"Workspace {workspace_id} not found. Please ensure the workspace exists.")

        self.products = create_test_products(self.workspace)
        self.orders = create_test_orders(self.workspace, self.products)

        # GraphQL client
        self.client = Client(schema)

    def test_create_order_mutation(self):
        """Test creating a new order"""
        mutation = '''
            mutation CreateOrder($orderData: OrderCreateInput!) {
                createOrder(orderData: $orderData) {
                    success
                    order {
                        id
                        orderNumber
                        status
                        orderSource
                        customerEmail
                        customerName
                        totalAmount
                        currency
                    }
                    message
                    error
                    unavailableItems
                }
            }
        '''

        variables = {
            "orderData": {
                "orderSource": "MANUAL",
                "customerEmail": "newcustomer@example.com",
                "customerName": "New Customer",
                "customerPhone": "+237611223344",
                "shippingRegion": "LITTORAL",
                "shippingAddress": {
                    "street": "321 New Street",
                    "city": "Douala",
                    "region": "LITTORAL",
                    "country": "Cameroon",
                    "postalCode": "00237"
                },
                "billingAddress": {
                    "street": "321 New Street",
                    "city": "Douala",
                    "region": "LITTORAL",
                    "country": "Cameroon",
                    "postalCode": "00237"
                },
                "shippingCost": "5000.00",
                "taxAmount": "0.00",
                "discountAmount": "0.00",
                "paymentMethod": "CASH",
                "currency": "XAF",
                "notes": "Test order creation",
                "items": [
                    {
                        "productId": str(self.products['product1'].id),
                        "variantId": str(self.products['variant1'].id),
                        "quantity": 2,
                        "unitPrice": "15000.00"
                    },
                    {
                        "productId": str(self.products['product2'].id),
                        "variantId": str(self.products['variant2'].id),
                        "quantity": 1,
                        "unitPrice": "25000.00"
                    }
                ]
            }
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['createOrder']['success'])
        self.assertIsNotNone(result['data']['createOrder']['order'])
        self.assertEqual(result['data']['createOrder']['order']['customerEmail'], 'newcustomer@example.com')
        self.assertEqual(result['data']['createOrder']['order']['orderSource'], 'MANUAL')

    def test_update_order_status_mutation(self):
        """Test updating order status"""
        order = self.orders['pending_order']

        mutation = '''
            mutation UpdateOrderStatus($orderId: String!, $newStatus: String!) {
                updateOrderStatus(orderId: $orderId, newStatus: $newStatus) {
                    success
                    order {
                        id
                        orderNumber
                        status
                        updatedAt
                    }
                    message
                    error
                }
            }
        '''

        variables = {
            "orderId": str(order.id),
            "newStatus": "PROCESSING"
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['updateOrderStatus']['success'])
        self.assertEqual(result['data']['updateOrderStatus']['order']['status'], 'PROCESSING')

    def test_cancel_order_mutation(self):
        """Test cancelling an order"""
        order = self.orders['pending_order']

        mutation = '''
            mutation CancelOrder($orderId: String!, $reason: String) {
                cancelOrder(orderId: $orderId, reason: $reason) {
                    success
                    order {
                        id
                        orderNumber
                        status
                    }
                    message
                    error
                }
            }
        '''

        variables = {
            "orderId": str(order.id),
            "reason": "Customer requested cancellation"
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['cancelOrder']['success'])
        self.assertEqual(result['data']['cancelOrder']['order']['status'], 'CANCELLED')

    def test_bulk_update_order_status_mutation(self):
        """Test bulk updating order statuses"""
        order1 = self.orders['pending_order']
        order2 = self.orders['processing_order']

        mutation = '''
            mutation BulkUpdateOrderStatus($bulkData: BulkStatusUpdateInput!) {
                bulkUpdateOrderStatus(bulkData: $bulkData) {
                    success
                    totalUpdates
                    successfulUpdates
                    failedUpdates
                    message
                    error
                }
            }
        '''

        variables = {
            "bulkData": {
                "updates": [
                    {
                        "orderId": str(order1.id),
                        "newStatus": "COMPLETED"
                    },
                    {
                        "orderId": str(order2.id),
                        "newStatus": "SHIPPED"
                    }
                ]
            }
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['bulkUpdateOrderStatus']['success'])
        self.assertEqual(result['data']['bulkUpdateOrderStatus']['totalUpdates'], 2)
        self.assertEqual(result['data']['bulkUpdateOrderStatus']['successfulUpdates'], 2)

    def test_get_order_analytics_mutation(self):
        """Test getting order analytics"""
        mutation = '''
            mutation GetOrderAnalytics($periodDays: Int) {
                getOrderAnalytics(periodDays: $periodDays) {
                    analytics {
                        periodDays
                        totalOrders
                        totalRevenue
                        averageOrderValue
                        pendingOrders
                        completedOrders
                        cancelledOrders
                    }
                    sourceBreakdown {
                        orderSource
                        count
                        revenue
                    }
                    regionalBreakdown {
                        shippingRegion
                        count
                        revenue
                    }
                    success
                    error
                }
            }
        '''

        variables = {
            "periodDays": 30
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['getOrderAnalytics']['success'])

        analytics = result['data']['getOrderAnalytics']['analytics']
        self.assertEqual(analytics['periodDays'], 30)
        self.assertEqual(analytics['totalOrders'], 3)

    def test_create_order_validation_error(self):
        """Test order creation with invalid data"""
        mutation = '''
            mutation CreateOrder($orderData: OrderCreateInput!) {
                createOrder(orderData: $orderData) {
                    success
                    order {
                        id
                    }
                    message
                    error
                }
            }
        '''

        # Invalid data - missing required fields
        variables = {
            "orderData": {
                "orderSource": "MANUAL",
                "customerEmail": "",  # Empty email
                "customerName": "",   # Empty name
                "shippingRegion": "INVALID_REGION",
                "shippingAddress": {
                    "street": "321 New Street",
                    "city": "Douala",
                    "region": "LITTORAL",
                    "country": "Cameroon",
                    "postalCode": "00237"
                },
                "items": []  # Empty items
            }
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        # Should have validation errors
        self.assertIsNotNone(result.get('errors') or result['data']['createOrder']['error'])

    def test_update_nonexistent_order(self):
        """Test updating non-existent order"""
        mutation = '''
            mutation UpdateOrderStatus($orderId: String!, $newStatus: String!) {
                updateOrderStatus(orderId: $orderId, newStatus: $newStatus) {
                    success
                    order {
                        id
                    }
                    message
                    error
                }
            }
        '''

        variables = {
            "orderId": "non-existent-order-id",
            "newStatus": "PROCESSING"
        }

        result = self.client.execute(mutation, variables=variables, context_value=self.context)

        self.assertFalse(result['data']['updateOrderStatus']['success'])
        self.assertIsNotNone(result['data']['updateOrderStatus']['error'])

    def test_order_mutation_performance(self):
        """Test order mutation performance"""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        order = self.orders['pending_order']

        mutation = '''
            mutation UpdateOrderStatus($orderId: String!, $newStatus: String!) {
                updateOrderStatus(orderId: $orderId, newStatus: $newStatus) {
                    success
                    order {
                        id
                        orderNumber
                        status
                    }
                }
            }
        '''

        variables = {
            "orderId": str(order.id),
            "newStatus": "PROCESSING"
        }

        with CaptureQueriesContext(connection) as context_queries:
            result = self.client.execute(mutation, variables=variables, context_value=self.context)

        # Should execute with reasonable number of queries (< 10)
        self.assertLess(len(context_queries.captured_queries), 10)
        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['updateOrderStatus']['success'])