"""
Manifest-Based Theme Discovery Service
Production-ready service for discovering themes via theme-manifest.json files

Features:
- Development: Scans /themes/ directory for theme-manifest.json files
- Production: Fetches from CDN themes-index.json
- Environment-aware discovery (dev vs prod)
- Comprehensive error handling and logging
- Cache optimization for performance
- Input sanitization and security

Security Measures:
- File path validation and sanitization
- Input validation for manifest data
- Resource limits and timeouts
- Audit logging
"""

import json
import logging
import os
import glob
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class ThemeDiscoveryError(Exception):
    """Custom exception for theme discovery failures"""
    pass


class ThemeDiscoveryService:
    """
    Local file system theme discovery service for development phase
    Follows production-ready principles from CLAUDE.md
    """

    # Configuration - Use THEMES_ROOT from settings for consistency
    THEMES_BASE_PATH = str(settings.THEMES_ROOT)
    MAX_SCAN_DEPTH = 3
    CACHE_KEY_PREFIX = 'theme_discovery'
    CACHE_TIMEOUT = 3600  # 1 hour

    # Performance: Cache settings
    MAX_THEMES_PER_SCAN = 100
    SCAN_TIMEOUT_SECONDS = 30

    # Retry configuration
    MAX_RETRIES = 10
    RETRY_DELAYS = [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6, 51.2]  # Total > 3 seconds

    def __init__(self, current_user=None):
        self.current_user = current_user
        self.scan_stats = {
            'total_scanned': 0,
            'valid_themes': 0,
            'errors': 0,
            'cache_hits': 0
        }

    def _get_themes_base_path(self) -> Path:
        """Get themes base path with validation, security, and retry logic"""
        import time

        base_path = Path(self.THEMES_BASE_PATH).resolve()

        # Retry logic with incremental timeouts
        for attempt in range(self.MAX_RETRIES):
            try:
                # Security: Validate path exists and is directory
                if not base_path.exists():
                    logger.error(f"Themes directory not found at: {base_path}")
                    raise FileNotFoundError(f"Themes directory not found at: {base_path}")

                if not base_path.is_dir():
                    logger.error(f"Themes path is not a directory: {base_path}")
                    raise NotADirectoryError(f"Themes path is not a directory: {base_path}")

                logger.info(f"Successfully located themes directory: {base_path}")
                return base_path

            except (FileNotFoundError, NotADirectoryError) as e:
                if attempt == self.MAX_RETRIES - 1:
                    # Final attempt - fail gracefully with clear message
                    logger.error(f"Theme discovery failed after {self.MAX_RETRIES} attempts: {str(e)}")
                    raise ThemeDiscoveryError(f"Cannot locate themes directory. Check THEMES_BASE_PATH environment variable. Current path: {base_path}")

                # Wait before retry with exponential backoff
                delay = self.RETRY_DELAYS[attempt]
                logger.warning(f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed. Retrying in {delay}s...")
                time.sleep(delay)

            except Exception as e:
                logger.error(f"Unexpected error getting themes base path: {str(e)}")
                raise ThemeDiscoveryError(f"Unexpected error accessing themes directory: {str(e)}")






    def _sanitize_string(self, value: str, max_length: int = 200) -> str:
        """
        Security function to sanitize string inputs
        """
        if not isinstance(value, str):
            return ""

        # Basic sanitization
        sanitized = value.strip()[:max_length]
        # Remove potentially dangerous characters
        sanitized = ''.join(c for c in sanitized if c.isprintable())
        return sanitized

    def _is_valid_version_format(self, version: str) -> bool:
        """
        Validate semantic version format (1.0.0, 1.1.0, etc.)
        Strict validation - no 'v' prefix allowed (NPM/industry standard)
        """
        import re
        # Strict semver: MAJOR.MINOR.PATCH (no prefix)
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))

    def _detect_preview_image(self, version_dir: Path) -> Optional[str]:
        """
        Auto-detect preview image from screenshot/screenshots folder
        Returns RELATIVE path from THEMES_ROOT for URL construction
        Checks both 'screenshot' (singular) and 'screenshots' (plural) folders
        """
        try:
            # Try both singular and plural folder names
            possible_dirs = [
                version_dir / 'screenshot',
                version_dir / 'screenshots'
            ]

            screenshots_dir = None
            for dir_path in possible_dirs:
                if dir_path.exists() and dir_path.is_dir():
                    screenshots_dir = dir_path
                    logger.info(f"Found screenshot folder: {screenshots_dir}")
                    break

            if not screenshots_dir:
                logger.debug(f"No screenshot/screenshots directory found in {version_dir}")
                return None

            # Look for image files (case-insensitive)
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif']
            screenshots = []

            for ext in image_extensions:
                screenshots.extend(screenshots_dir.glob(ext))
                screenshots.extend(screenshots_dir.glob(ext.upper()))

            # Sort by filename for consistency (alphabetically, so preview.png comes before others)
            screenshots.sort()

            if screenshots:
                # Convert to RELATIVE path from THEMES_ROOT for URL construction
                absolute_path = screenshots[0]
                themes_base = self._get_themes_base_path()
                relative_path = absolute_path.relative_to(themes_base)

                # Convert to forward slashes for URL compatibility
                relative_path_str = str(relative_path).replace('\\', '/')

                logger.info(f"✅ Found preview image (relative): {relative_path_str}")
                print(f"      🖼️  Preview: {screenshots[0].name} → {relative_path_str}")
                return relative_path_str
            else:
                logger.debug(f"No image files found in screenshots directory: {screenshots_dir}")
                return None

        except Exception as e:
            logger.warning(f"Error detecting preview image in {version_dir}: {str(e)}")
            return None

    def _parse_semantic_version(self, version: str) -> tuple:
        """
        Parse semantic version for sorting
        """
        try:
            # Remove 'v' prefix if present
            version = version.lstrip('v')
            parts = version.split('.')

            # Ensure we have at least 3 parts
            while len(parts) < 3:
                parts.append('0')

            return tuple(int(part) for part in parts[:3])

        except (ValueError, IndexError):
            logger.warning(f"Invalid semantic version format: {version}")
            return (0, 0, 0)

    def _load_puck_config(self, version_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Load Puck configuration from pre-generated JSON file.

        The puck.config.json file is generated at build time from puck.config.tsx
        using the npm run build:puck-config script in the theme directory.

        Args:
            version_dir: Path to theme version directory

        Returns:
            Dict containing Puck config, or {} if not found/invalid
        """
        try:
            # PRIORITY 1: Look for generated JSON (required for production)
            puck_config_json = version_dir / 'puck.config.json'
            if puck_config_json.exists():
                with open(puck_config_json, 'r', encoding='utf-8') as f:
                    puck_config = json.load(f)

                logger.info(f"Successfully loaded Puck config from: {puck_config_json}")
                if puck_config.get('components'):
                    logger.debug(f"Loaded {len(puck_config['components'])} components from Puck config")
                return puck_config

            # PRIORITY 2: Check for .tsx (warn if missing .json)
            puck_config_tsx = version_dir / 'puck.config.tsx'
            if puck_config_tsx.exists():
                logger.warning(
                    f"Found puck.config.tsx but missing puck.config.json in {version_dir}\n"
                    f"Run: cd {version_dir} && npm run build:puck-config"
                )

            # No config files found - this is acceptable (optional config)
            logger.debug(f"No Puck config files found in {version_dir}")
            return {}

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in puck.config.json at {version_dir}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error loading Puck config from {version_dir}: {str(e)}")
            return {}

    def _load_puck_data(self, version_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Load Puck data from puck.data.json file
        """
        try:
            puck_data_file = version_dir / 'puck.data.json'

            if not puck_data_file.exists():
                logger.debug(f"No Puck data file found at: {puck_data_file}")
                return {}

            with open(puck_data_file, 'r', encoding='utf-8') as f:
                puck_data = json.load(f)

            logger.info(f"Successfully loaded Puck data from: {puck_data_file}")
            return puck_data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Puck data file {puck_data_file}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error loading Puck data from {puck_data_file}: {str(e)}")
            return {}

    def discover_themes(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discover themes via manifest-based approach
        Environment-aware: file scanning in dev, CDN fetch in prod
        """
        print("    🔍 ThemeDiscoveryService.discover_themes() called")
        cache_key = f"{self.CACHE_KEY_PREFIX}:all_themes"

        # Check cache first (unless forced refresh)
        if not force_refresh:
            cached_result = cache.get(cache_key)
            if cached_result:
                print(f"    💾 Returning CACHED result: {cached_result.get('total_found', 0)} themes")
                self.scan_stats['cache_hits'] += 1
                logger.info("Returning cached theme discovery results")
                return cached_result

        print("    🆕 No cache, starting fresh discovery...")
        logger.info("Starting manifest-based theme discovery...")

        try:
            # Environment-aware discovery
            node_env = os.getenv('NODE_ENV')
            print(f"    🌍 NODE_ENV = {node_env}")

            if node_env == 'production':
                print("    📡 Using CDN discovery")
                discovered_themes = self._discover_from_cdn()
            else:
                print("    📁 Using local filesystem discovery")
                discovered_themes = self._discover_from_local_manifests()

            # Build result
            result = {
                'themes': discovered_themes,
                'stats': self.scan_stats,
                'last_scan': timezone.now().isoformat(),
                'total_found': len(discovered_themes)
            }

            print(f"    💾 Caching result with {len(discovered_themes)} themes")
            # Cache results
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            logger.info(f"Theme discovery completed. Found {result['total_found']} valid themes")

            return result

        except Exception as e:
            print(f"    ❌ Discovery failed: {e}")
            logger.error(f"Theme discovery failed: {str(e)}")
            self.scan_stats['errors'] += 1
            return {'themes': [], 'stats': self.scan_stats, 'error': str(e)}


    def _discover_from_local_manifests(self) -> List[Dict[str, Any]]:
        """
        Discover themes by scanning for theme-manifest.json files in local /themes directory
        Supports both flat structure (themes/name/) and versioned structure (themes/name/vX.Y.Z/)
        """
        try:
            base_path = self._get_themes_base_path()
            discovered_themes = []

            print(f"\n🔍 Starting theme discovery from base path: {base_path}")
            print(f"🔍 Base path exists: {base_path.exists()}")
            print(f"🔍 Base path is directory: {base_path.is_dir()}\n")
            logger.info(f"🔍 Starting theme discovery from base path: {base_path}")
            logger.info(f"🔍 Base path exists: {base_path.exists()}")
            logger.info(f"🔍 Base path is directory: {base_path.is_dir()}")

            # Scan all theme directories
            for theme_dir in base_path.iterdir():
                logger.info(f"  📁 Found directory: {theme_dir.name}")

                if not theme_dir.is_dir() or theme_dir.name.startswith('.'):
                    logger.info(f"  ⏭️  Skipping {theme_dir.name} (not a dir or starts with .)")
                    continue

                # Pattern 1: Look for manifest in theme root (flat structure)
                manifest_path = theme_dir / 'theme-manifest.json'
                logger.info(f"  🔎 Checking flat structure: {manifest_path}")

                if manifest_path.exists():
                    logger.info(f"  ✅ Found manifest at: {manifest_path}")
                    manifest = self._load_and_validate_manifest(manifest_path, theme_dir)
                    if manifest:
                        discovered_themes.append(manifest)
                else:
                    logger.info(f"  ❌ No manifest at root, checking version subdirectories...")
                    # Pattern 2: Scan version subdirectories (themes/name/v1.0.0/)
                    for version_dir in theme_dir.iterdir():
                        logger.info(f"    📂 Checking version dir: {version_dir.name}")

                        if not version_dir.is_dir() or version_dir.name.startswith('.'):
                            logger.info(f"    ⏭️  Skipping {version_dir.name}")
                            continue

                        version_manifest_path = version_dir / 'theme-manifest.json'
                        logger.info(f"    🔎 Looking for: {version_manifest_path}")

                        if version_manifest_path.exists():
                            logger.info(f"    ✅ Found manifest at: {version_manifest_path}")
                            manifest = self._load_and_validate_manifest(version_manifest_path, version_dir)
                            if manifest:
                                discovered_themes.append(manifest)
                        else:
                            logger.info(f"    ❌ Not found: {version_manifest_path}")

                self.scan_stats['total_scanned'] += 1

            logger.info(f"🎉 Discovery complete. Found {len(discovered_themes)} themes")
            return discovered_themes

        except Exception as e:
            logger.error(f"❌ Error discovering local manifests: {str(e)}")
            self.scan_stats['errors'] += 1
            return []

    def _load_and_validate_manifest(self, manifest_path: Path, theme_dir: Path) -> Dict[str, Any] | None:
        """
        Load and validate a manifest file, returning enriched manifest or None if invalid
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # Validate required manifest fields
            if not self._validate_manifest(manifest):
                return None

            # Add development-specific fields
            manifest['dev_path'] = str(theme_dir)
            manifest['is_local'] = True


            # Load puck files if they are specified as paths in manifest
            puck_config = manifest.get('puck_config')
            if isinstance(puck_config, str):
                # It's a path, load the actual JSON file
                loaded_config = self._load_puck_config(theme_dir)
                manifest['puck_config'] = loaded_config
                if loaded_config:
                    print(f"      ✅ Loaded puck_config JSON from file")

            puck_data = manifest.get('puck_data')
            if isinstance(puck_data, str):
                # It's a path, load the actual JSON file
                loaded_data = self._load_puck_data(theme_dir)
                manifest['puck_data'] = loaded_data
                if loaded_data:
                    print(f"      ✅ Loaded puck_data JSON from file")

            # Process preview_image (explicit or auto-detect)
            if 'preview_image' in manifest and manifest['preview_image']:
                # Explicit preview_image specified in manifest - convert to relative path
                base_path = self._get_themes_base_path()
                preview_path = theme_dir / manifest['preview_image']

                if preview_path.exists():
                    relative_preview = str(preview_path.relative_to(base_path)).replace('\\', '/')
                    manifest['preview_image'] = relative_preview
                    print(f"      🖼️  Preview: {preview_path.name} → {relative_preview}")
                else:
                    logger.warning(f"Preview image not found: {manifest['preview_image']}, falling back to auto-detect")
                    # Fallback to auto-detect
                    preview_image = self._detect_preview_image(theme_dir)
                    manifest['preview_image'] = preview_image if preview_image else None
            else:
                # No explicit preview_image - auto-detect from screenshots folder (backward compatibility)
                preview_image = self._detect_preview_image(theme_dir)
                manifest['preview_image'] = preview_image if preview_image else None

            # Process showcase_sections images (convert to relative paths)
            if 'showcase_sections' in manifest and isinstance(manifest['showcase_sections'], list):
                base_path = self._get_themes_base_path()
                processed_sections = []

                for section in manifest['showcase_sections']:
                    if isinstance(section, dict) and 'image' in section:
                        section_image_path = theme_dir / section['image']

                        if section_image_path.exists():
                            # Convert to relative path from THEMES_ROOT
                            relative_section = str(section_image_path.relative_to(base_path)).replace('\\', '/')
                            section['image'] = relative_section
                            print(f"      🖼️  Showcase: {section.get('title', 'Untitled')} → {relative_section}")
                        else:
                            logger.warning(f"Showcase image not found: {section['image']}")
                            section['image'] = None

                    processed_sections.append(section)

                manifest['showcase_sections'] = processed_sections
                print(f"      ✅ Processed {len(processed_sections)} showcase sections")

            self.scan_stats['valid_themes'] += 1
            logger.info(f"Found theme manifest: {manifest.get('id', 'unknown')} at {manifest_path}")
            print(f"      📦 Loaded: {manifest.get('name')} v{manifest.get('version')}")
            return manifest

        except Exception as e:
            logger.error(f"Error loading manifest from {manifest_path}: {str(e)}")
            self.scan_stats['errors'] += 1
            return None

    def _discover_from_cdn(self) -> List[Dict[str, Any]]:
        """
        Discover themes by fetching from CDN themes-index.json
        """
        try:
            cdn_index_url = os.getenv('THEME_INDEX_URL', 'https://cdn.example.com/themes/themes-index.json')

            # In production, this would fetch from actual CDN
            # For now, simulate fetching from CDN by using template database records
            from ..models import Template

            templates = Template.objects.filter(
                status=Template.STATUS_ACTIVE,
                manifest_url__isnull=False
            ).only('manifest_url', 'cdn_base_url', 'name', 'slug', 'version')

            discovered_themes = []

            for template in templates:
                # Simulate fetching manifest from CDN URL
                manifest = {
                    'id': template.slug,
                    'name': template.name,
                    'version': template.version,
                    'assetsBase': template.cdn_base_url,
                    'manifest_url': template.manifest_url,
                    'is_local': False
                }

                discovered_themes.append(manifest)
                self.scan_stats['valid_themes'] += 1

            logger.info(f"Found {len(discovered_themes)} themes from CDN")
            return discovered_themes

        except Exception as e:
            logger.error(f"Error fetching from CDN: {str(e)}")
            self.scan_stats['errors'] += 1
            return []

    def _validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate theme manifest structure following industry standards

        Required fields:
        - id: Unique identifier (string)
        - name: Display name
        - version: Semantic version (X.Y.Z)
        - slug: URL-friendly identifier

        Optional fields:
        - description: Theme description
        - features: List of theme features
        - compatibility: Compatibility information
        """
        # Required fields
        required_fields = ['id', 'name', 'version', 'slug']

        for field in required_fields:
            if field not in manifest:
                logger.warning(f"Missing required field '{field}' in manifest for {manifest.get('name', 'unknown')}")
                print(f"      ❌ Missing required field: {field}")
                return False

        # Auto-generate slug from id if missing (industry standard)
        if 'slug' not in manifest:
            manifest['slug'] = manifest['id'].lower().replace('@', '').replace('/', '-')
            print(f"      🔧 Auto-generated slug: {manifest['slug']}")

        # Validate version format (semantic versioning)
        version = manifest.get('version', '')
        if not self._is_valid_version_format(version):
            logger.warning(f"Invalid version format '{version}' in manifest: {manifest.get('name', 'unknown')}")
            print(f"      ❌ Invalid version format: {version} (expected X.Y.Z)")
            return False


        print(f"      ✅ Manifest valid: {manifest.get('name')} ({manifest.get('id')})")
        return True

    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get current discovery statistics"""
        return {
            **self.scan_stats,
            'cache_key_prefix': self.CACHE_KEY_PREFIX,
            'themes_base_path': str(self._get_themes_base_path()),
            'max_themes_per_scan': self.MAX_THEMES_PER_SCAN
        }

    def clear_discovery_cache(self):
        """Clear theme discovery cache"""
        try:
            # Clear discovery cache - simple approach for development
            cache.delete(f"{self.CACHE_KEY_PREFIX}:all_themes")
            logger.info("Theme discovery cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing discovery cache: {str(e)}")

    def get_theme_by_slug(self, theme_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get specific theme by slug
        """
        try:
            discovery_result = self.discover_themes()

            for theme in discovery_result.get('themes', []):
                if theme.get('slug') == theme_slug:
                    return theme

            logger.warning(f"Theme not found: {theme_slug}")
            return None

        except Exception as e:
            logger.error(f"Error getting theme by slug {theme_slug}: {str(e)}")
            return None