/**
 * Authentication Redirect Utilities
 * Following Next.js 14 patterns and 2024 best practices
 * Based on Vercel/Netlify approach for seamless auth flows
 * Enhanced with OWASP security and type-safe context preservation
 */

// ============================================================================
// Redirect Context Types (Discriminated Unions)
// ============================================================================

/**
 * Redirect context with discriminated union for type safety
 * Each intent has specific required/optional fields
 */
export type RedirectContext =
  | { intent: 'simple' } // Just auth, no context
  | { intent: 'subscription'; plan?: string; period?: 'monthly' | 'yearly' }
  | { intent: 'trial'; plan: string; period?: 'monthly' | 'yearly' } // plan required for trial
  | { intent: 'upgrade'; fromPlan: string; toPlan: string };

/**
 * Extracted parameters from URL
 */
export interface ExtractedParams {
  next?: string;
  intent?: RedirectContext['intent'];
  plan?: string;
  type?: 'trial' | 'standard';
  period?: 'monthly' | 'yearly';
  fromPlan?: string;
  toPlan?: string;
}

// ============================================================================
// Validation Types (Discriminated Union)
// ============================================================================

export type ValidationResult =
  | { valid: true; path: string }
  | { valid: false; reason: string };

// ============================================================================
// Security Validation (OWASP 2024 Compliant)
// ============================================================================

/**
 * Validate redirect path against OWASP best practices
 * Prevents open redirect vulnerabilities
 *
 * @see https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
 */
export function validateRedirectPath(path: string | null | undefined): ValidationResult {
  // 1. Null/undefined check
  if (!path) {
    return { valid: false, reason: 'No path provided' };
  }

  // 2. Must start with / (relative path only)
  if (!path.startsWith('/')) {
    return { valid: false, reason: 'Path must be relative (start with /)' };
  }

  // 3. Prevent protocol-relative URLs (//evil.com)
  if (path.startsWith('//')) {
    return { valid: false, reason: 'Protocol-relative URLs not allowed' };
  }

  // 4. Allowlist check (OWASP recommended)
  const allowedPaths = [
    '/billing',
    '/workspace',
    '/settings',
    '/auth',
    '/dashboard',
    '/', // Homepage
  ];

  const isAllowed = allowedPaths.some(allowed => path.startsWith(allowed));

  if (!isAllowed) {
    return { valid: false, reason: `Path not in allowlist. Allowed: ${allowedPaths.join(', ')}` };
  }

  // 5. Path traversal prevention
  if (path.includes('..')) {
    return { valid: false, reason: 'Path traversal detected' };
  }

  return { valid: true, path };
}

// ============================================================================
// URL Building Functions
// ============================================================================

/**
 * Build login redirect URL with return path and context
 * Pattern: /auth/login?next=/billing/plans&intent=trial&plan=beginning
 *
 * @param currentPath - The path to redirect back to after auth
 * @param context - Optional redirect context with discriminated union
 * @returns Safe redirect URL with validated path
 *
 * @example
 * // Simple redirect
 * buildLoginRedirect('/billing')
 * // Returns: /auth/login?next=%2Fbilling
 *
 * @example
 * // Trial context
 * buildLoginRedirect('/billing/plans', { intent: 'trial', plan: 'pro' })
 * // Returns: /auth/login?next=%2Fbilling%2Fplans&intent=trial&plan=pro
 */
export function buildLoginRedirect(
  currentPath: string,
  context?: RedirectContext
): string {
  const url = new URL('/auth/login', window.location.origin);

  // Validate and add return path
  const validation = validateRedirectPath(currentPath);
  if (validation.valid) {
    url.searchParams.set('next', validation.path);
  } else {
    // Fallback to safe default if validation fails
    console.warn(`Invalid redirect path: ${validation.reason}. Using /billing as fallback.`);
    url.searchParams.set('next', '/billing');
  }

  // Add context params based on discriminated union
  if (context) {
    url.searchParams.set('intent', context.intent);

    switch (context.intent) {
      case 'subscription':
        if (context.plan) url.searchParams.set('plan', context.plan);
        if (context.period) url.searchParams.set('period', context.period);
        break;
      case 'trial':
        url.searchParams.set('plan', context.plan); // Required
        if (context.period) url.searchParams.set('period', context.period);
        break;
      case 'upgrade':
        url.searchParams.set('fromPlan', context.fromPlan);
        url.searchParams.set('toPlan', context.toPlan);
        break;
      case 'simple':
        // No additional params
        break;
    }
  }

  return url.pathname + url.search;
}

/**
 * Build register redirect URL with return path and context
 * Pattern: /auth/register?next=/billing/plans&intent=trial&plan=pro
 */
export function buildRegisterRedirect(
  currentPath: string,
  context?: RedirectContext
): string {
  // Reuse login redirect logic (same URL building, different auth path)
  const loginUrl = buildLoginRedirect(currentPath, context);
  return loginUrl.replace('/auth/login', '/auth/register');
}

// ============================================================================
// Parameter Extraction Functions
// ============================================================================

/**
 * Extract redirect params from URL search params
 * Use after successful authentication to restore context
 *
 * @example
 * const params = extractRedirectParams(searchParams);
 * if (params.intent === 'trial' && params.plan) {
 *   router.push(`/billing/plans?tier=${params.plan}&type=trial`);
 * }
 */
export function extractRedirectParams(searchParams: URLSearchParams): ExtractedParams {
  return {
    next: searchParams.get('next') || undefined,
    intent: (searchParams.get('intent') as RedirectContext['intent']) || undefined,
    plan: searchParams.get('plan') || undefined,
    type: (searchParams.get('type') as 'trial' | 'standard') || undefined,
    period: (searchParams.get('period') as 'monthly' | 'yearly') || undefined,
    fromPlan: searchParams.get('fromPlan') || undefined,
    toPlan: searchParams.get('toPlan') || undefined,
  };
}

/**
 * Get the redirect URL after successful authentication
 * OWASP-compliant with validation
 * Defaults to /billing if no 'next' parameter is provided
 *
 * @param searchParams - URL search params containing 'next'
 * @returns Validated safe redirect path
 */
export function getPostAuthRedirect(searchParams: URLSearchParams): string {
  const next = searchParams.get('next');

  // Validate the redirect path
  const validation = validateRedirectPath(next);

  if (validation.valid) {
    return validation.path;
  }

  // Log security issue and use safe default
  console.warn(`Invalid post-auth redirect: ${validation.reason}. Using /billing as fallback.`);
  return '/billing';
}

/**
 * Reconstruct redirect context from extracted params
 * Converts flat URL params back to discriminated union
 *
 * @param params - Extracted URL parameters
 * @returns Typed RedirectContext or undefined
 */
export function reconstructContext(params: ExtractedParams): RedirectContext | undefined {
  if (!params.intent) {
    return undefined;
  }

  // Reconstruct based on intent discriminant
  switch (params.intent) {
    case 'simple':
      return { intent: 'simple' };
    case 'subscription':
      return { intent: 'subscription', plan: params.plan, period: params.period };
    case 'trial':
      if (!params.plan) {
        console.warn('Trial intent requires plan parameter');
        return undefined;
      }
      return { intent: 'trial', plan: params.plan, period: params.period };
    case 'upgrade':
      if (!params.fromPlan || !params.toPlan) {
        console.warn('Upgrade intent requires fromPlan and toPlan parameters');
        return undefined;
      }
      return { intent: 'upgrade', fromPlan: params.fromPlan, toPlan: params.toPlan };
    default:
      return undefined;
  }
}

// ============================================================================
// Validation Functions
// ============================================================================

/**
 * Validate plan tier parameter
 */
export function isValidPlanTier(plan: string | null): plan is 'beginning' | 'pro' | 'enterprise' {
  return plan === 'beginning' || plan === 'pro' || plan === 'enterprise';
}

/**
 * Validate subscription type parameter
 */
export function isValidSubscriptionType(type: string | null): type is 'trial' | 'standard' {
  return type === 'trial' || type === 'standard';
}

/**
 * Validate billing period parameter
 */
export function isValidBillingPeriod(period: string | null): period is 'monthly' | 'yearly' {
  return period === 'monthly' || period === 'yearly';
}
