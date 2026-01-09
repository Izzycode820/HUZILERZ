"""
Comprehensive Order Query Tests
Tests all order queries with manual token insertion
"""

from django.test import TestCase
from graphene.test import Client
from workspace.store.graphql.schema import schema
from .test_auth import auth_helper
from .test_data import create_test_products, create_test_orders


class OrderQueryTestCase(TestCase):
    """
    Order query tests with manual token insertion
    Just expects a JWT token with workspace claims
    """

    def setUp(self):
        """Set up test data and authentication"""
        # IMPORTANT: You need to manually set your JWT token before running tests
        # Call: auth_helper.set_token("your_jwt_token_here") before running tests

        # Get authenticated context with manual token
        self.context = auth_helper.get_graphql_context()

        # Create test workspace and data
        from workspace.core.models import Workspace

        self.workspace = Workspace.objects.create(
            name='Test Store',
            slug='test-store',
            type='store',
            status='active'
        )

        # Create test products
        self.products = create_test_products(self.workspace)

        # Create test orders
        self.orders = create_test_orders(self.workspace, self.products)

        # GraphQL client
        self.client = Client(schema)

    def test_get_all_orders_query(self):
        """Test getting all orders with pagination"""
        query = '''
            query {
                orders(first: 10) {
                    edges {
                        node {
                            id
                            orderNumber
                            status
                            orderSource
                            customerEmail
                            customerName
                            totalAmount
                            currency
                            createdAt
                        }
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        '''

        # Execute with authentication context
        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        # Assertions
        self.assertIsNone(result.get('errors'))
        self.assertIn('orders', result['data'])
        self.assertEqual(len(result['data']['orders']['edges']), 3)

        # Verify order data
        orders_data = result['data']['orders']['edges']
        order_numbers = [edge['node']['orderNumber'] for edge in orders_data]
        self.assertIn('ORD-001', order_numbers)
        self.assertIn('ORD-002', order_numbers)
        self.assertIn('ORD-003', order_numbers)

    def test_get_order_by_id_query(self):
        """Test getting single order by ID"""
        order = self.orders['pending_order']

        query = f'''
            query {{
                order(id: "{order.id}") {{
                    id
                    orderNumber
                    status
                    orderSource
                    customerEmail
                    customerName
                    customerPhone
                    shippingRegion
                    totalAmount
                    currency
                    items {{
                        id
                        productName
                        productSku
                        quantity
                        unitPrice
                        totalPrice
                    }}
                }}
            }}
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get('errors'))
        self.assertEqual(result['data']['order']['orderNumber'], 'ORD-001')
        self.assertEqual(result['data']['order']['status'], 'PENDING')
        self.assertEqual(result['data']['order']['orderSource'], 'WHATSAPP')
        self.assertEqual(len(result['data']['order']['items']), 1)

    def test_get_orders_by_status_query(self):
        """Test getting orders by status"""
        query = '''
            query {
                ordersByStatus(status: "PENDING") {
                    id
                    orderNumber
                    status
                    customerEmail
                    totalAmount
                }
            }
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['ordersByStatus']), 1)
        self.assertEqual(result['data']['ordersByStatus'][0]['status'], 'PENDING')
        self.assertEqual(result['data']['ordersByStatus'][0]['orderNumber'], 'ORD-001')

    def test_get_orders_by_region_query(self):
        """Test getting orders by shipping region"""
        query = '''
            query {
                ordersByRegion(region: "littoral") {
                    id
                    orderNumber
                    shippingRegion
                    customerEmail
                    totalAmount
                }
            }
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['ordersByRegion']), 1)
        self.assertEqual(result['data']['ordersByRegion'][0]['shippingRegion'], 'LITTORAL')

    def test_get_orders_by_source_query(self):
        """Test getting orders by source"""
        query = '''
            query {
                ordersBySource(source: "manual") {
                    id
                    orderNumber
                    orderSource
                    customerEmail
                    totalAmount
                }
            }
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['ordersBySource']), 1)
        self.assertEqual(result['data']['ordersBySource'][0]['orderSource'], 'MANUAL')

    def test_get_recent_orders_query(self):
        """Test getting recent orders"""
        query = '''
            query {
                recentOrders(limit: 2) {
                    id
                    orderNumber
                    status
                    customerEmail
                    totalAmount
                    createdAt
                }
            }
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['recentOrders']), 2)

        # Should return most recent orders first
        order_numbers = [order['orderNumber'] for order in result['data']['recentOrders']]
        self.assertIn('ORD-003', order_numbers)
        self.assertIn('ORD-002', order_numbers)

    def test_orders_query_with_filters(self):
        """Test orders query with multiple filters"""
        query = '''
            query {
                orders(
                    first: 10
                    status: "PENDING"
                    orderSource: "WHATSAPP"
                    shippingRegion: "LITTORAL"
                ) {
                    edges {
                        node {
                            id
                            orderNumber
                            status
                            orderSource
                            shippingRegion
                            customerEmail
                        }
                    }
                }
            }
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get('errors'))
        self.assertEqual(len(result['data']['orders']['edges']), 1)

        order = result['data']['orders']['edges'][0]['node']
        self.assertEqual(order['status'], 'PENDING')
        self.assertEqual(order['orderSource'], 'WHATSAPP')
        self.assertEqual(order['shippingRegion'], 'LITTORAL')

    def test_order_query_performance(self):
        """Test order query performance"""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        query = '''
            query {
                orders(first: 10) {
                    edges {
                        node {
                            id
                            orderNumber
                            status
                            customerEmail
                            totalAmount
                        }
                    }
                }
            }
        '''

        context = auth_helper.get_graphql_context()

        with CaptureQueriesContext(connection) as context_queries:
            result = self.client.execute(query, context_value=context)

        # Should execute with reasonable number of queries (< 5)
        self.assertLess(len(context_queries.captured_queries), 5)
        self.assertIsNone(result.get('errors'))

    def test_order_not_found(self):
        """Test query for non-existent order"""
        query = '''
            query {
                order(id: "non-existent-id") {
                    id
                    orderNumber
                }
            }
        '''

        context = auth_helper.get_graphql_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNotNone(result.get('errors'))
        self.assertIn("Order not found", str(result['errors']))