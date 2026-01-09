import { NextRequest, NextResponse } from 'next/server';

/*
================================================================================
SUBSCRIPTION SUSPENSION - TWO-LAYER DEFENSE (OPTION B)
================================================================================

LAYER 1: MIDDLEWARE (THIS FILE) - Fast JWT Check
-------------------------------------------------
- Checks JWT subscription.status (stateless, no DB hit)
- Redirects 'suspended' users to /workspace/reactivate
- Does NOT redirect 'cancelled' users (they keep access until expires_at)
- Acceptable delay: 0-15 minutes (JWT refresh interval)
- Use case: Block page access (reads)

Status Semantics:
- 'suspended' = Non-payment, grace period expired (immediate block)
- 'cancelled' = User cancelled but paid period still valid (keep access)

LAYER 2: API LAYER - DB Verification (To Implement)
----------------------------------------------------
Add DB check before critical mutations (writes/payments):

Example in GraphQL resolvers:
```python
# In subscription mutations (createSubscription, renewSubscription, etc.)
@login_required
def resolve_renew_subscription(self, info, input):
    user = info.context.user

    # CRITICAL: Verify current status from DB (not JWT)
    subscription = user.subscription
    if subscription.status == 'suspended':
        raise GraphQLError(
            "Your subscription is suspended. Please reactivate your plan.",
            extensions={'code': 'SUBSCRIPTION_SUSPENDED'}
        )

    # Proceed with renewal...
```

Apply to these endpoints:
- renewSubscription (payment)
- createSubscription (payment)
- upgradeSubscription (payment)
- Any product/theme creation endpoints
- Any store settings mutations

Why two layers?
- Middleware: Fast (no DB), catches 99% of cases
- API: Authoritative (DB source of truth), prevents race conditions
- Combined: Fast UX + bulletproof security

Delay Scenario:
- 10:00 AM - Grace period ends → DB: status='suspended'
- 10:01 AM - User still has JWT with status='active' (15 min TTL)
- 10:01-10:16 AM - Can browse workspace (middleware allows)
- 10:01 AM - Tries to create product → API blocks (DB check)
- 10:16 AM - JWT refreshes → Middleware redirects

Acceptable tradeoff: User can browse for <15 mins, but blocked from actions.

 Examples:
  # Product mutations
  resolve_create_product → Check suspended
  resolve_update_product → Check suspended
  resolve_delete_product → Check suspended

  # Theme mutations  
  resolve_install_theme → Check suspended
  resolve_customize_theme → Check suspended

  # Store settings
  resolve_update_store_settings → Check suspended

  # Subscription mutations
  resolve_renew_subscription → Check suspended
  resolve_upgrade_subscription → Check suspended

  ---
  BUT - Middleware Already Handles Most Cases!

  Since middleware redirects /workspace → /workspace/reactivate, suspended users can't even access pages that make these API calls.

  API checks are just a safety net for the JWT delay edge case:
  - User has stale JWT (status='active' but DB is 'suspended')
  - Middleware lets them browse for <15 mins
  - They try to mutate data via API call
  - API blocks them (DB check)

  ---
  Simpler Approach (Recommended for early stage):

  Create a reusable decorator/guard:

  def require_active_subscription(resolver):
      def wrapper(self, info, *args, **kwargs):
          user = info.context.user
          if user.subscription.status == 'suspended':
              raise GraphQLError(
                  "Subscription suspended. Reactivate to continue.",
                  extensions={'code': 'SUBSCRIPTION_SUSPENDED'}
              )
          return resolver(self, info, *args, **kwargs)
      return wrapper

  # Apply to ALL workspace mutations
  @require_active_subscription
  def resolve_create_product(self, info, input):
  
================================================================================
*/

// Configuration for the middleware
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.).*)',
  ],
};

// Known system domains (add your production domain here)
const SYSTEM_DOMAINS = ['localhost', 'localhost:3000', 'huzilerz.com', 'www.huzilerz.com', 'api.huzilerz.com'];
const SUBDOMAIN_SUFFIX = '.huzilerz.com';

// Protected routes that require authentication
const PROTECTED_ROUTES = ['/workspace', '/settings'];

// Auth routes (public - no auth required)
const AUTH_ROUTES = ['/auth/login', '/auth/signup', '/auth/register'];

// Public routes (accessible without auth)
const PUBLIC_ROUTES = ['/', '/pricing', '/features', '/about', '/contact', '/camp', '/showcase', '/blog', '/resources', '/billing'];

/**
 * Check if hostname is a custom domain (not system domain)
 */
function isCustomDomain(hostname: string): boolean {
  return !SYSTEM_DOMAINS.includes(hostname) && !hostname.endsWith(SUBDOMAIN_SUFFIX);
}

/**
 * Check if hostname is a subdomain
 */
function isSubdomain(hostname: string): boolean {
  return hostname.endsWith(SUBDOMAIN_SUFFIX) && hostname !== 'huzilerz.com';
}

/**
 * Extract subdomain from hostname
 */
function extractSubdomain(hostname: string): string {
  return hostname.replace(SUBDOMAIN_SUFFIX, '');
}

/**
 * Handle custom domain routing
 */
function handleCustomDomain(request: NextRequest, hostname: string): NextResponse {
  const url = request.nextUrl.clone();

  // Rewrite to store page with custom domain flag
  url.pathname = `/store/custom-domain`;
  url.searchParams.set('domain', hostname);
  url.searchParams.set('path', request.nextUrl.pathname);

  return NextResponse.rewrite(url);
}

/**
 * Handle subdomain routing
 */
function handleSubdomain(request: NextRequest, hostname: string): NextResponse {
  const subdomain = extractSubdomain(hostname);
  const url = request.nextUrl.clone();

  // Skip if accessing system routes
  if (url.pathname.startsWith('/workspace') ||
    url.pathname.startsWith('/auth') ||
    url.pathname.startsWith('/api')) {
    return NextResponse.next();
  }

  // Rewrite to store page with subdomain
  if (url.pathname === '/') {
    url.pathname = `/store/${subdomain}`;
  } else {
    url.pathname = `/store/${subdomain}${url.pathname}`;
  }

  return NextResponse.rewrite(url);
}

/**
 * Check if route requires authentication
 */
function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some(route => pathname.startsWith(route));
}

/**
 * Check if user is authenticated via refresh token
 */
function isAuthenticated(request: NextRequest): boolean {
  return request.cookies.has('refresh_token');
}

/**
 * Decode JWT and extract subscription status
 * Stateless check - no DB hit (fast)
 * Uses same pattern as src/utils/jwt.ts (Edge runtime compatible)
 */
function getSubscriptionStatus(request: NextRequest): { tier: string; status: string } | null {
  const accessToken = request.cookies.get('access_token')?.value;

  if (!accessToken) return null;

  try {
    // Decode JWT payload (same as extractSubscriptionFromJWT utility)
    const payload = JSON.parse(atob(accessToken.split('.')[1]));

    return {
      tier: payload.subscription?.tier || 'free',
      status: payload.subscription?.status || 'unknown'
    };
  } catch (error) {
    // Invalid JWT format - let auth handle it
    return null;
  }
}

/**
 * Handle authentication for protected routes
 * Following guide's pattern: middleware adds ?next param for SSR protection
 */
function handleAuth(request: NextRequest): NextResponse | null {
  const { pathname, search } = request.nextUrl;

  // 1. Protected route check - redirect to login with intent
  if (isProtectedRoute(pathname) && !isAuthenticated(request)) {
    const url = request.nextUrl.clone();

    // Build intended destination (path + query params)
    const intendedDestination = pathname + search;

    // Redirect to login with ?next param (industry standard)
    url.pathname = '/auth/login';
    url.search = `?next=${encodeURIComponent(intendedDestination)}`;

    return NextResponse.redirect(url);
  }

  // 2. Subscription suspension check - redirect to reactivation page
  // Stateless check via JWT (0-15 min delay acceptable)
  // For immediate blocking on writes, see API layer comment below
  //
  // IMPORTANT: Only redirect 'suspended' status (non-payment)
  // 'cancelled' status = user cancelled but keeps access until expires_at (honor paid period)
  if (pathname.startsWith('/workspace') && pathname !== '/workspace/reactivate' && isAuthenticated(request)) {
    const subscription = getSubscriptionStatus(request);

    if (subscription?.status === 'suspended') {
      const url = request.nextUrl.clone();
      url.pathname = '/workspace/reactivate';
      url.search = ''; // Clear any query params

      return NextResponse.redirect(url);
    }
  }

  // 3. Auth route check - if already logged in, redirect to workspace
  // (prevents logged-in users from seeing login/signup pages)
  if (AUTH_ROUTES.includes(pathname) && isAuthenticated(request)) {
    const url = request.nextUrl.clone();

    // Check if there's a ?next param to redirect to instead
    const next = request.nextUrl.searchParams.get('next');

    if (next && isValidRedirectPath(next)) {
      // User came from protected route, send them back
      url.pathname = next.split('?')[0];
      url.search = next.includes('?') ? '?' + next.split('?')[1] : '';
    } else {
      // Default redirect to workspace
      url.pathname = '/workspace';
      url.search = '';
    }

    return NextResponse.redirect(url);
  }

  return null;
}

/**
 * Validate redirect path for middleware (OWASP-compliant)
 * Prevents open redirect vulnerabilities at SSR level
 */
function isValidRedirectPath(path: string): boolean {
  // Must be relative path
  if (!path.startsWith('/')) return false;

  // Prevent protocol-relative URLs
  if (path.startsWith('//')) return false;

  // Prevent path traversal
  if (path.includes('..')) return false;

  // Dynamic workspace routes: /workspace/[workspace_id]/...
  if (path.match(/^\/workspace\/[a-zA-Z0-9_-]+(\/.*)?$/)) {
    return true;
  }

  // Allowlist check (match frontend allowlist)
  const allowedPaths = ['/billing', '/workspace', '/settings', '/dashboard', '/pricing', '/camp', '/showcase', '/blog', '/resources', '/'];
  return allowedPaths.some(allowed => path.startsWith(allowed));
}

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';

  // Handle authentication for system domain
  if (SYSTEM_DOMAINS.includes(hostname)) {
    const authResponse = handleAuth(request);
    if (authResponse) return authResponse;
  }

  // Handle custom domains
  if (isCustomDomain(hostname)) {
    return handleCustomDomain(request, hostname);
  }

  // Handle subdomains
  if (isSubdomain(hostname)) {
    return handleSubdomain(request, hostname);
  }

  // Default behavior for system domain
  return NextResponse.next();
}