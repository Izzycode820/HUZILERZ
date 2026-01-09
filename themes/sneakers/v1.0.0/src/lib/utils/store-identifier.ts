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
  const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN || 'huzilerz.com';

  // DEV: localhost → use query param
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const params = new URLSearchParams(window.location.search);
    const storeParam = params.get('store');

    console.log('[StoreIdentifier] DEV mode - Query param:', storeParam || 'demo-store (default)');

    return storeParam || 'demo-store';
  }

  // PRODUCTION: Extract subdomain from hostname
  // e.g. "johns-shop.huzilerz.com" -> "johns-shop"
  // We remove the root domain from the hostname to get the subdomain
  if (hostname.includes(rootDomain)) {
    // case: store.huzilerz.com
    const subdomain = hostname.replace(`.${rootDomain}`, '');
    console.log('[StoreIdentifier] PRODUCTION mode - Subdomain:', subdomain);
    return subdomain;
  }

  // Fallback: If hostname doesn't match root domain (e.g. custom domain), 
  // we might return the whole hostname or handle differently. 
  // For now, assume the subdomain IS the slug if we are not on root domain 
  // (or return fallback if logic strictly requires subdomain)

  // Alternative simple split logic if not using rootDomain matching:
  const parts = hostname.split('.');
  if (parts.length >= 2) {
    // Just take the first part
    return parts[0];
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
