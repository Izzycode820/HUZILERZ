/**
 * Store Identifier Utilities
 * Extracts store slug from domain for GraphQL API calls
 *
 * Shopify Pattern: Themes automatically identify store from domain
 */

/**
 * Extract store slug from current domain
 *
 * Patterns:
 * - Subdomain: user-123-johns-electronics.huzilerz.com → johns-electronics
 * - Custom Domain: mikeshoes.cm → mikeshoes
 *
 * @returns Store slug string
 */
export function getStoreSlugFromHostname(): string {
  if (typeof window === 'undefined') {
    // Server-side rendering - use environment variable or fallback
    return process.env.STORE_SLUG || 'demo-store';
  }

  const hostname = window.location.hostname;

  // Handle our subdomain pattern
  if (hostname.endsWith('.huzilerz.com')) {
    return extractStoreSlugFromSubdomain(hostname);
  }

  // Handle custom domains
  return extractStoreSlugFromCustomDomain(hostname);
}

/**
 * Extract store slug from subdomain pattern
 * Pattern: user-{user_id}-{store_slug}.huzilerz.com
 */
function extractStoreSlugFromSubdomain(hostname: string): string {
  const subdomain = hostname.replace('.huzilerz.com', '');
  const parts = subdomain.split('-');

  // Pattern: user-{user_id}-{store_slug}
  if (parts.length >= 3 && parts[0] === 'user') {
    // Skip "user" and user_id, join remaining parts
    return parts.slice(2).join('-');
  }

  // Fallback: use subdomain as-is
  return subdomain;
}

/**
 * Extract store slug from custom domain
 * Pattern: {store_slug}.cm or {store_slug}.com
 */
function extractStoreSlugFromCustomDomain(hostname: string): string {
  // Remove TLD (top-level domain)
  const domainParts = hostname.split('.');

  // For .cm domains: mikeshoes.cm → mikeshoes
  // For .com domains: mystore.com → mystore
  if (domainParts.length >= 2) {
    return domainParts.slice(0, -1).join('.');
  }

  return hostname;
}

/**
 * Get GraphQL endpoint URL
 * Can be customized for different environments
 */
export function getGraphQLEndpoint(): string {
  if (typeof window === 'undefined') {
    // Server-side - use environment variable
    return process.env.GRAPHQL_ENDPOINT || '/api/storefront/graphql';
  }

  // Client-side - use relative path
  return '/api/storefront/graphql';
}

/**
 * Make GraphQL request with store slug automatically included
 */
export async function storefrontGraphQL<T = any>(
  query: string,
  variables?: Record<string, any>
): Promise<T> {
  const storeSlug = getStoreSlugFromHostname();

  const response = await fetch(getGraphQLEndpoint(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Store-Slug': storeSlug, // Send as header for security
    },
    body: JSON.stringify({
      query,
      variables: {
        store_slug: storeSlug, // Include in variables for existing queries
        ...variables
      }
    })
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed: ${response.statusText}`);
  }

  const result = await response.json();

  if (result.errors) {
    throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`);
  }

  return result.data;
}

/**
 * React hook for store slug
 */
export function useStoreSlug(): string {
  if (typeof window === 'undefined') {
    return process.env.STORE_SLUG || 'demo-store';
  }

  return getStoreSlugFromHostname();
}

/**
 * React hook for storefront GraphQL
 */
export function useStorefrontGraphQL() {
  const storeSlug = useStoreSlug();

  return {
    storeSlug,
    graphqlEndpoint: getGraphQLEndpoint(),
    makeRequest: storefrontGraphQL
  };
}