"""
Simple Runner for Order Queries with Manual Token
Just set your token and run all query tests
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from test_auth import auth_helper


def run_order_queries_with_token(token):
    """Run all order query tests with provided token"""

    # Set the token
    auth_helper.set_token(token)

    test_runner = get_runner(settings)
    runner = test_runner(verbosity=2, interactive=True)

    # Run only query tests
    test_suite = runner.build_suite([
        'workspace.store.tests.orders.test_order_queries'
    ])

    print("🚀 Running Order Query Tests...")
    print("=" * 50)
    print(f" Using token: {token[:20]}...")

    result = runner.run_suite(test_suite)

    print("=" * 50)
    if result.wasSuccessful():
        print(" All order query tests passed!")
    else:
        print(" Some order query tests failed!")

    return result.wasSuccessful()


if __name__ == '__main__':
    # Replace with your actual JWT token
    YOUR_TOKEN = "your_jwt_token_here"

    if YOUR_TOKEN == "your_jwt_token_here":
        print(" Please replace 'your_jwt_token_here' with your actual JWT token")
        sys.exit(1)

    success = run_order_queries_with_token(YOUR_TOKEN)
    sys.exit(0 if success else 1)