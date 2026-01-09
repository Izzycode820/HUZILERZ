"""
Simple Authentication Helper for Manual Token Testing
Just expects a JWT token with workspace claims - no user/workspace creation
"""


class ManualAuthHelper:
    """
    Helper class for manual JWT token testing
    Just expects a token with workspace claims - no setup required
    """

    def __init__(self):
        self.token = None

    def set_token(self, token):
        """Set the JWT token manually"""
        self.token = token
        print(f"Token set: {token[:20]}...")

    def get_graphql_context(self):
        """Get GraphQL context with manual token"""
        if not self.token:
            raise ValueError("No token set. Please call set_token() first with your JWT token.")

        # Create a mock request with the token - just like the GUI
        class MockRequest:
            def __init__(self, token):
                self.headers = {'Authorization': f'Bearer {token}'}

        # Get workspace from token claims
        import jwt
        try:
            decoded = jwt.decode(self.token, options={"verify_signature": False})
            workspace_id = decoded.get('workspace_id')

            # Import workspace model
            from workspace.core.models import Workspace
            workspace = Workspace.objects.get(id=workspace_id)

        except Exception as e:
            raise ValueError(f"Failed to get workspace from token: {e}")

        return {
            'request': MockRequest(self.token),
            'workspace': workspace
        }


# Global instance for easy access
auth_helper = ManualAuthHelper()