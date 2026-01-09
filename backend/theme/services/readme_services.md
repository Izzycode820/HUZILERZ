# Theme Services Documentation

This document provides a comprehensive overview of all Django services in the theme module, including their full file locations, purposes, best practices, and design thinking.

## Service Files Location

### Core Theme Management Services

#### 1. Theme Registry Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\theme_registry_service.py`
- **Purpose**: Manages theme registry and database integration for frontend consumption
- **Best Practices**:
  - Uses manifest-based discovery for local filesystem (dev) and CDN index (prod)
  - Provides comprehensive caching with 1-hour timeout
  - Handles UUID generation and version tracking
  - Provides template configuration for Puck editor
  - Includes security measures and input validation
  - Supports tenant-based theme isolation
- **Design Thinking**:
  - Bridges local file system with database storage
  - Environment-aware discovery (development vs production)
  - Supports both manifest-based and database-based themes
  - Provides component registry for theme-specific Puck components
  - Includes cache invalidation for registry updates

#### 2. Theme Loader Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\theme_loader_service.py`
- **Purpose**: Hybrid theme loader combining manifest discovery with database configuration storage
- **Best Practices**:
  - Keeps puck_config and puck_data in database as source of truth
  - Uses manifests for theme discovery and metadata
  - Frontend loads dynamically using manifest references
  - No migration away from database system required
  - Provides fallback mechanisms for missing manifests
- **Design Thinking**:
  - Combines best of both worlds: manifest discovery + database configuration
  - Enables smooth transition from database to CDN-based themes
  - Supports both development and production environments
  - Provides detailed loader statistics and health monitoring

#### 3. Theme Discovery Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\theme_discovery_service.py`
- **Purpose**: Discovers themes via theme-manifest.json files in development and CDN in production
- **Best Practices**:
  - Environment-aware discovery (file scanning in dev, CDN fetch in prod)
  - Comprehensive error handling with retry logic
  - Performance optimization with scan limits and caching
  - Security measures including path validation and input sanitization
  - Auto-detects preview images and validates theme metadata
- **Design Thinking**:
  - Follows production-ready principles with security and performance
  - Supports both local development and production CDN deployment
  - Includes comprehensive validation for theme versions and metadata
  - Provides detailed discovery statistics and health monitoring

### Template Management Services

#### 4. Template Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\template_service.py`
- **Purpose**: Core template business logic with filtering, sorting, and search capabilities
- **Best Practices**:
  - Optimized queries with proper field selection for performance
  - PostgreSQL full-text search integration for advanced search
  - Comprehensive error handling and validation
  - Pagination support with count queries
  - Field optimization to exclude large JSON fields
- **Design Thinking**:
  - Industry-standard filtering and search patterns
  - Performance-first approach with database optimization
  - Supports multiple sorting criteria and relevance ranking
  - Includes template detail retrieval with view count tracking

#### 5. Template Analytics Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\template_analytics_service.py`
- **Purpose**: Analytics, categorization, ratings, and usage metrics for templates
- **Best Practices**:
  - Performance analytics with database aggregation
  - Usage metrics with growth calculations
  - Category performance tracking
  - Template leaderboard with ranking
  - Preview system data preparation
- **Design Thinking**:
  - Comprehensive analytics for template marketplace
  - Supports category-based performance analysis
  - Includes usage growth tracking and trend analysis
  - Provides template leaderboard for marketplace discovery

### Customization Services

#### 6. Template Customization Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\template_customization_service.py`
- **Purpose**: Manages template cloning, customization, and workspace integration
- **Best Practices**:
  - Atomic operations with database transactions
  - Comprehensive validation for workspace-template compatibility
  - Version control for customization changes
  - History tracking with undo functionality
  - Role-based access (preview vs active)
- **Design Thinking**:
  - Enables non-destructive customization through versioning
  - Supports staging/production environments
  - Provides undo/redo capabilities through version history
  - Includes workspace-template compatibility validation

#### 7. Customization Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\customization_service.py`
- **Purpose**: User template customization management, backups, and updates
- **Best Practices**:
  - Customization backup before updates
  - Template updates with customization preservation
  - Restoration capabilities from backups
  - Update notification management
  - No GitHub operations (pure user customization)
- **Design Thinking**:
  - Focuses on user-specific customization management
  - Enables safe updates with backup/restore capabilities
  - Supports customization preservation during template updates
  - Provides comprehensive backup history

### Version and Sync Services

#### 8. Template Version Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\template_version_service.py`
- **Purpose**: Template developer operations with GitHub integration
- **Best Practices**:
  - GitHub-based template version management
  - Template developer rollbacks (GitHub revert commits)
  - Version history and commit tracking
  - Template release management
  - Developer-only operations (not for user rollbacks)
- **Design Thinking**:
  - Separate service for template developer operations
  - GitHub integration for professional version control
  - Supports template developer rollbacks via Git reverts
  - Provides comprehensive version history

#### 9. Sync Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\sync_service.py`
- **Purpose**: Template sync system with Git-to-CDN pipeline and user update management
- **Best Practices**:
  - Git-to-CDN sync operations with progress tracking
  - User update notification system
  - Update type determination (minor, major, breaking)
  - Customization preservation scoring
  - Sync history and rollback capabilities
- **Design Thinking**:
  - Implements Google Play Store-like update notification system
  - Supports progressive rollout patterns
  - Includes breaking change awareness
  - Provides comprehensive sync operation monitoring

#### 10. GitHub Integration Service
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\services\github_integration_service.py`
- **Purpose**: GitHub API integration for template version control
- **Best Practices**:
  - Comprehensive error handling and retry logic
  - Rate limiting and authentication management
  - Revert commit creation for rollbacks
  - Commit history and details retrieval
  - Repository access validation
- **Design Thinking**:
  - Production-ready GitHub API integration
  - Supports professional Git workflows
  - Includes comprehensive error handling
  - Provides repository validation and access control

## Service Relationships

```
ThemeRegistryService ←→ ThemeDiscoveryService
ThemeLoaderService ←→ ThemeDiscoveryService + TemplateService
TemplateService ←→ TemplateAnalyticsService
TemplateCustomizationService ←→ CustomizationService
SyncService ←→ GitHubIntegrationService + TemplateVersionService
TemplateVersionService ←→ GitHubIntegrationService
```

## Key Design Patterns

1. **Hybrid Loading Pattern**: Combines manifest discovery with database configuration storage
2. **Service Layer Pattern**: Business logic separated from models and views
3. **Caching Pattern**: Performance optimization with strategic caching
4. **Error Handling Pattern**: Comprehensive error handling with validation
5. **Transaction Pattern**: Atomic operations with database transactions
6. **Version Control Pattern**: Git integration for professional template management

## Security Considerations

- Input validation and sanitization across all services
- Path traversal prevention in file operations
- GitHub API authentication and rate limiting
- Database transaction safety
- Resource limits and timeouts

## Performance Optimizations

- Strategic caching for registry and discovery operations
- Database query optimization with field selection
- Pagination and count queries for large datasets
- Performance monitoring with statistics
- CDN integration for asset delivery

This documentation provides AI systems with complete context about the theme services, enabling efficient navigation and understanding of the service layer architecture.