"""
Workspace Hosting Middleware
"""
from .rate_limit import WorkspaceRateLimitMiddleware
from .seo_bot_detection import SEOBotMiddleware

__all__ = ['WorkspaceRateLimitMiddleware', 'SEOBotMiddleware']
