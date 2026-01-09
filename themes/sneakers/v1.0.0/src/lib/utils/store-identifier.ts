/**
 * Store Identifier Utility
 * Extracts store slug from hostname for multi-tenant theme architecture
 * Falls back to demo store if no identifier found
 */

/**
 * Extracts store slug from current hostname
 *
 * Auto-switches between dev and production:
 * - DEV (localhost): Uses ?store= query parameter
 * - PRODUCTION: Extracts subdomain from hostname
 *
 * Examples:
 * - localhost:3001?store=johns-shop → "johns-shop"
 * - localhost:3001 → "demo-store" (default)
 * - johns-shop.huzilerz.com → "johns-shop"
 * - sneakers-demo.huzilerz.com → "sneakers-demo"
 *
 * @returns Store slug identifier
 */
export function getStoreSlug(): string {
  if (typeof window === 'undefined') {
    // Server-side: return fallback
    return 'demo-store';
  }

  const hostname = window.location.hostname;

  // DEV: localhost → use query param
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const params = new URLSearchParams(window.location.search);
    const storeParam = params.get('store');

    console.log('[StoreIdentifier] DEV mode - Query param:', storeParam || 'demo-store (default)');

    return storeParam || 'demo-store';
  }

  // PRODUCTION: Extract subdomain from hostname
  // e.g., "johns-shop.huzilerz.com" → "johns-shop"
  const parts = hostname.split('.');

  if (parts.length >= 2) {
    const subdomain = parts[0];
    console.log('[StoreIdentifier] PRODUCTION mode - Subdomain:', subdomain);
    return subdomain;
  }

  // Fallback to demo if unable to extract
  console.warn('[StoreIdentifier] Unable to extract subdomain, using demo-store');
  return 'demo-store';
}

/**
 * Hook to get store slug (client-side only)
 * Ensures consistent slug across component renders
 */
export function useStoreSlug(): string {
  if (typeof window === 'undefined') {
    return 'demo-store';
  }

  return getStoreSlug();
}
