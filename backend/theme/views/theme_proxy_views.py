"""
Theme File Proxy Views - Development Support
Serves local theme files over HTTP in development (production uses CDN)

Industry Standard Pattern:
- Shopify: Serves theme assets via Rails in dev, Shopify CDN in prod
- Webflow: Local proxy in dev, Fastly CDN in prod
- WordPress: PHP serves themes in dev, CDN in prod
"""
import logging
import mimetypes
from pathlib import Path
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.conf import settings

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def theme_file_proxy_view(request, file_path: str):
    """
    Proxy local theme files in development

    Security:
    - Only serves files from /themes/ directory
    - Path traversal protection
    - CORS headers for module loading
    - Content-Type validation

    Performance:
    - Direct file serving (no processing)
    - Browser caching via Cache-Control
    - Gzip handled by nginx/middleware in prod

    Args:
        file_path: Relative path from themes/ root (e.g., "sneakers/v1.0.0/entry.mjs")

    Returns:
        HttpResponse with file contents and correct MIME type

    Example:
        GET /api/themes/local-proxy/sneakers/v1.0.0/entry.mjs
        -> Serves /themes/sneakers/v1.0.0/entry.mjs
    """
    try:
        # Get themes root directory
        # Assumes themes/ is at project root level
        project_root = Path(settings.BASE_DIR).parent
        themes_root = project_root / 'themes'

        # Resolve full file path
        requested_file = (themes_root / file_path).resolve()

        # Security: Prevent path traversal attacks
        # Ensure resolved path is within themes directory
        if not str(requested_file).startswith(str(themes_root.resolve())):
            logger.warning(f"Path traversal attempt blocked: {file_path}")
            return HttpResponse('Forbidden: Path traversal detected', status=403)

        # Check file exists
        if not requested_file.exists():
            logger.info(f"Theme file not found: {file_path}")
            raise Http404(f"Theme file not found: {file_path}")

        # Security: Only serve specific file types
        allowed_extensions = {'.mjs', '.js', '.json', '.css', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.map'}
        if requested_file.suffix.lower() not in allowed_extensions:
            logger.warning(f"Blocked disallowed file type: {requested_file.suffix}")
            return HttpResponse('Forbidden: File type not allowed', status=403)

        # Determine MIME type
        content_type = get_content_type(requested_file)

        # Read and serve file
        with open(requested_file, 'rb') as f:
            content = f.read()

        # Create response with appropriate headers
        response = HttpResponse(content, content_type=content_type)

        # CORS headers for module loading (required for ES modules)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        # Caching for development (short cache to allow quick updates)
        # In production, CDN handles caching
        response['Cache-Control'] = 'public, max-age=60'  # 1 minute cache

        # Module preload hint for better performance
        if requested_file.suffix in ['.mjs', '.js']:
            response['X-Content-Type-Options'] = 'nosniff'

        logger.debug(f"Served theme file: {file_path} ({content_type})")
        return response

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving theme file {file_path}: {str(e)}")
        return HttpResponse(f'Internal Server Error: {str(e)}', status=500)


def get_content_type(file_path: Path) -> str:
    """
    Determine correct MIME type for theme files

    Critical: .mjs and .js must be 'application/javascript' for ES modules
    """
    extension = file_path.suffix.lower()

    # Override mimetypes for ES modules (critical for browser import)
    mime_overrides = {
        '.mjs': 'application/javascript',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.css': 'text/css',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.map': 'application/json',
    }

    if extension in mime_overrides:
        return mime_overrides[extension]

    # Fallback to Python's mimetypes
    guessed_type, _ = mimetypes.guess_type(str(file_path))
    return guessed_type or 'application/octet-stream'


@require_http_methods(["OPTIONS"])
def theme_file_proxy_options(request, file_path: str):
    """
    Handle CORS preflight requests for theme files
    Required for ES module imports from different origin
    """
    response = HttpResponse()
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Access-Control-Max-Age'] = '86400'  # 24 hours
    return response
