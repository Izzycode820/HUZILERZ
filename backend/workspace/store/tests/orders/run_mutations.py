"""
Simple Runner for Order Mutations with Manual Token
Just set your token and run all mutation tests
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


def run_order_mutations_with_token(token):
    """Run all order mutation tests with provided token"""

    # Set the token as environment variable
    os.environ['JWT_TOKEN'] = token

    test_runner = get_runner(settings)
    runner = test_runner(verbosity=2, interactive=True)

    # Run only mutation tests
    test_suite = runner.build_suite([
        'workspace.store.tests.orders.test_order_mutations'
    ])

    print("Running Order Mutation Tests...")
    print("=" * 50)
    print(f"Using token: {token[:20]}...")

    result = runner.run_suite(test_suite)

    print("=" * 50)
    if result.wasSuccessful():
        print(" All order mutation tests passed!")
    else:
        print(" Some order mutation tests failed!")

    return result.wasSuccessful()


if __name__ == '__main__':
    # Replace with your actual JWT token
    YOUR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozNiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcm5hbWUiOiJiYWJheWFnYSIsImV4cCI6MTc2MTE1MDM0MiwiaWF0IjoxNzYxMTQ5NDQyLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiVWFDSF9nSTNBWHI3dG9XWG5KUGVHQSIsImlzcyI6Imh1c3RsZXJ6LmNhbXAiLCJhdWQiOiJodXN0bGVyei5jYW1wIiwid29ya3NwYWNlX2lkIjoiMzI0N2U1N2UtMWM0OC00OWU5LWFmNzktOWViYzlmZWMxNjc3Iiwid29ya3NwYWNlX3R5cGUiOiJzdG9yZSIsIndvcmtzcGFjZV9wZXJtaXNzaW9ucyI6WyJhZG1pbiJdLCJ3b3Jrc3BhY2Vfcm9sZSI6Im93bmVyIiwic3Vic2NyaXB0aW9uIjp7InRpZXIiOiJmcmVlIiwic3RhdHVzIjoiYWN0aXZlIiwicGxhbl9pZCI6bnVsbCwiZmVhdHVyZXNfYml0bWFwIjowLCJleHBpcmVzX2F0IjpudWxsLCJ1c2FnZV9oYXNoIjoiZnJlZV91c2VyIiwibGltaXRzIjp7Im1heF93b3Jrc3BhY2VzIjoxLCJkZXBsb3ltZW50X2FsbG93ZWQiOmZhbHNlLCJzdG9yYWdlX2diIjowLjUsImJhbmR3aWR0aF9nYiI6MCwic2l0ZXNfbGltaXQiOjB9LCJ0cmlhbCI6eyJlbGlnaWJsZSI6dHJ1ZSwidXNlZF90cmlhbCI6ZmFsc2UsImN1cnJlbnRfdGllciI6bnVsbCwiZXhwaXJlc19hdCI6bnVsbCwiY2FuX3VwZ3JhZGUiOmZhbHNlLCJkYXlzX3JlbWFpbmluZyI6MCwidXNlZF9hdCI6bnVsbH0sInRlbXBsYXRlcyI6eyJvd25lZF9jb3VudCI6MCwib3duZWRfdGVtcGxhdGVzIjpbXSwiYm9udXNfZWxpZ2libGUiOnRydWUsImxhc3RfYm9udXNfdXNlZCI6bnVsbH0sIndvcmtzcGFjZV9pZCI6IjMyNDdlNTdlLTFjNDgtNDllOS1hZjc5LTllYmM5ZmVjMTY3NyJ9LCJmZWF0dXJlX2FjY2VzcyI6eyJiaXRtYXAiOjAsInRpZXIiOiJmcmVlIiwiZXhwaXJlcyI6bnVsbH19.g7te27QBdEPvQ6vPwVOChr64Bjf_7wXo-6QhvTyRvPk"

    if YOUR_TOKEN == "your_jwt_token_here":
        print(" Please replace 'your_jwt_token_here' with your actual JWT token")
        sys.exit(1)

    success = run_order_mutations_with_token(YOUR_TOKEN)
    sys.exit(0 if success else 1)