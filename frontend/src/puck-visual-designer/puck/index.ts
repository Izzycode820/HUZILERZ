/**
 * Puck Visual Designer - Production Multi-Tenant System
 *
 * Architecture:
 * - Master Config: Shared puck.config.tsx (from registry)
 * - User Data: Per-workspace puck_data JSON (from DB)
 */

// Core components
export { default as Editor } from './core/UniversalEditor';
export { default as Preview } from './core/UniversalPreview';

// Type definitions
export type {
  Config,
  Data,
  ThemeMetadata
} from './core/types';

// Theme registry (for loading master configs)
export { loadThemeConfig } from '@/registry/theme-registry';
