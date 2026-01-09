import type { Config, Data } from '@measured/puck';

/**
 * Production Multi-Tenant Types
 *
 * Clean, minimal types for the production architecture.
 */

// Re-export Puck types for convenience
export type { Config, Data };

// Theme metadata (optional, from manifest)
export interface ThemeMetadata {
  name: string;
  version: string;
  description?: string;
  slug: string;
  category?: string;
}
