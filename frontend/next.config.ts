import type { NextConfig } from "next";
import fs from "fs";
import path from "path";

/**
 * Auto-discover all theme packages for transpilation
 * Scans the themes directory and returns @themes/* package names
 */
function getThemePackages(): string[] {
  const themesDir = path.join(__dirname, '../themes');

  // Return empty array if themes directory doesn't exist yet
  if (!fs.existsSync(themesDir)) {
    console.warn('⚠️  Themes directory not found:', themesDir);
    return [];
  }

  try {
    const themeNames = fs.readdirSync(themesDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    const packages = themeNames.map(theme => `@themes/${theme}`);

    console.log(`📦 [Next.js] Auto-discovered ${packages.length} theme package(s) for transpilation:`, packages);

    return packages;
  } catch (error) {
    console.error('❌ Failed to scan themes directory:', error);
    return [];
  }
}

// @ts-ignore
const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
});

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    unoptimized: true, // Disable image optimization for local files
    domains: ['localhost'],
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Auto-transpile all theme packages from workspace
  transpilePackages: getThemePackages(),
  experimental: {
    // Allow imports from outside the Next.js root directory (workspace themes)
    externalDir: true,
  },
};

export default withPWA(nextConfig);
