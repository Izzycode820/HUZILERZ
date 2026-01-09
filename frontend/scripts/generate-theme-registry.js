#!/usr/bin/env node
/**
 * Theme Registry Auto-Generator
 *
 * Scans the themes directory and automatically generates the theme registry file.
 * Run this script whenever you add, remove, or update themes.
 *
 * Usage:
 *   node scripts/generate-theme-registry.js
 *   npm run generate-registry
 *
 * Features:
 * - Auto-discovers themes in /themes directory
 * - Handles multiple versions per theme
 * - Generates TypeScript-safe registry
 * - Validates theme structure
 */

const fs = require('fs');
const path = require('path');

// Configuration
const THEMES_DIR = path.join(__dirname, '../../themes');
const REGISTRY_OUTPUT = path.join(__dirname, '../src/registry/theme-registry.ts');

/**
 * Scan themes directory and build registry data
 */
function scanThemes() {
  console.log('🔍 Scanning themes directory:', THEMES_DIR);

  if (!fs.existsSync(THEMES_DIR)) {
    console.error('❌ Themes directory not found:', THEMES_DIR);
    process.exit(1);
  }

  const themes = [];
  const themeNames = fs.readdirSync(THEMES_DIR);

  for (const themeName of themeNames) {
    const themePath = path.join(THEMES_DIR, themeName);

    // Skip if not a directory
    if (!fs.statSync(themePath).isDirectory()) {
      continue;
    }

    // Find versions
    const versions = fs.readdirSync(themePath).filter((item) => {
      const versionPath = path.join(themePath, item);
      return fs.statSync(versionPath).isDirectory();
    });

    if (versions.length === 0) {
      console.warn(`⚠️  No versions found for theme: ${themeName}`);
      continue;
    }

    // Use latest version (or implement version sorting)
    const latestVersion = versions.sort().reverse()[0];
    const puckConfigPath = path.join(themePath, latestVersion, 'puck.config.tsx');

    // Validate puck.config.tsx exists
    if (!fs.existsSync(puckConfigPath)) {
      console.warn(`⚠️  No puck.config.tsx found for: ${themeName}/${latestVersion}`);
      continue;
    }

    // Try to load manifest for metadata
    const manifestPath = path.join(themePath, latestVersion, 'theme-manifest.json');
    let metadata = null;

    if (fs.existsSync(manifestPath)) {
      try {
        metadata = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
      } catch (error) {
        console.warn(`⚠️  Failed to parse manifest for ${themeName}:`, error.message);
      }
    }

    themes.push({
      name: themeName,
      slug: metadata?.slug || themeName,
      version: latestVersion,
      path: `@themes/${themeName}`,
      description: metadata?.description || '',
    });

    console.log(`✅ Found theme: ${themeName} (${latestVersion})`);
  }

  console.log(`\n📦 Total themes discovered: ${themes.length}`);
  return themes;
}

/**
 * Generate TypeScript registry file content
 */
function generateRegistryContent(themes) {
  const registryEntries = themes
    .map((theme) => {
      const comment = theme.description
        ? `  // ${theme.description}`
        : `  // ${theme.name} v${theme.version}`;

      return `${comment}\n  '${theme.slug}': () => import('${theme.path}'),`;
    })
    .join('\n');

  return `/**
 * Theme Registry - Production Multi-Tenant Architecture
 *
 * Loads master Puck configs (with render functions) from theme source.
 * User customizations (puck.data) are stored in database per workspace.
 *
 * Architecture:
 * - Master Config: Shared puck.config.tsx (this registry) - Read Only
 * - User Data: Per-workspace puck_data JSON (from DB) - Customizable
 *
 * ⚠️  AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
 * Generated on: ${new Date().toISOString()}
 * Total themes: ${themes.length}
 *
 * To update this file, run:
 *   npm run generate-registry
 */

import type { Config } from '@measured/puck';

type ThemeConfigLoader = () => Promise<{
  config?: Config;
  default?: Config;
}>;

/**
 * Theme Registry
 *
 * Maps theme slugs to puck.config.tsx modules.
 * Each config contains render functions (cannot be serialized to DB).
 */
export const THEME_REGISTRY: Record<string, ThemeConfigLoader> = {
${registryEntries}
};

/**
 * Load master theme Puck config (shared by all users)
 *
 * @param themeSlug - Theme identifier (e.g., 'ecommerce-sneakers')
 * @returns Full Puck Config with render functions
 * @throws Error if theme not found in registry
 */
export async function loadThemeConfig(themeSlug: string): Promise<Config> {
  console.log('🔵 [ThemeRegistry] Loading master config for:', themeSlug);

  const loader = THEME_REGISTRY[themeSlug];

  if (!loader) {
    const availableThemes = Object.keys(THEME_REGISTRY);
    console.error('❌ [ThemeRegistry] Theme not found:', themeSlug);
    console.error('📋 [ThemeRegistry] Available:', availableThemes);
    throw new Error(
      \`Theme "\${themeSlug}" not found. Available: \${availableThemes.join(', ')}\`
    );
  }

  try {
    const startTime = performance.now();
    const themeModule = await loader();

    const config = themeModule.config || themeModule.default;

    if (!config) {
      throw new Error(\`Theme "\${themeSlug}" missing puck.config export\`);
    }

    const loadTime = performance.now() - startTime;
    console.log(\`✅ [ThemeRegistry] Config loaded in \${loadTime.toFixed(2)}ms\`);
    console.log('📦 [ThemeRegistry] Components:', Object.keys(config.components || {}));

    return config;
  } catch (error) {
    console.error('❌ [ThemeRegistry] Failed to load:', error);
    throw error;
  }
}

/**
 * Get list of available theme slugs
 */
export function getAvailableThemes(): string[] {
  return Object.keys(THEME_REGISTRY);
}

/**
 * Check if a theme exists in the registry
 */
export function isThemeAvailable(themeSlug: string): boolean {
  return themeSlug in THEME_REGISTRY;
}

/**
 * Preload theme components (optional optimization)
 */
export function preloadTheme(themeSlug: string): void {
  const loader = THEME_REGISTRY[themeSlug];
  if (loader) {
    loader().catch((error) => {
      console.warn(\`Failed to preload theme "\${themeSlug}":\`, error);
    });
  }
}

export const REGISTRY_SIZE = ${themes.length};
export const REGISTRY_THEMES = [${themes.map((t) => `'${t.slug}'`).join(', ')}];

console.log(\`📦 [ThemeRegistry] Initialized with \${REGISTRY_SIZE} theme(s)\`);
`;
}

/**
 * Main execution
 */
function main() {
  console.log('🚀 Theme Registry Generator\n');

  // Scan themes
  const themes = scanThemes();

  if (themes.length === 0) {
    console.error('\n❌ No themes found. Please add themes to:', THEMES_DIR);
    process.exit(1);
  }

  // Generate registry content
  const registryContent = generateRegistryContent(themes);

  // Ensure output directory exists
  const outputDir = path.dirname(REGISTRY_OUTPUT);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
    console.log('✅ Created registry directory:', outputDir);
  }

  // Write registry file
  fs.writeFileSync(REGISTRY_OUTPUT, registryContent, 'utf-8');

  console.log('\n✅ Registry generated successfully!');
  console.log('📄 Output:', REGISTRY_OUTPUT);
  console.log('📦 Themes registered:', themes.length);
  console.log('\n🎯 Next steps:');
  console.log('   1. Restart your dev server to apply changes');
  console.log('   2. Import from: import { loadThemeConfig } from "@/registry/theme-registry"');
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { scanThemes, generateRegistryContent };
