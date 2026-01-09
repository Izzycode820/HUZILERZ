# Theme Models Documentation

This document provides a comprehensive overview of all Django models in the theme module, including their full file locations, purposes, best practices, and design thinking.

## Model Files Location

### Primary Models

#### 1. Template Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\template.py`
- **Purpose**: Master template model representing themes/templates in the system
- **Best Practices**:
  - Uses UUID as primary key for distributed systems compatibility
  - Implements semantic versioning for template versions
  - Supports multiple template types (e-commerce, services, blog, restaurant)
  - Includes comprehensive pricing tiers (free, paid, exclusive)
  - Tracks usage metrics (views, downloads, active usage)
  - Integrates with GitHub for version control
  - Supports dynamic theme loading via CDN
- **Design Thinking**:
  - Follows e-commerce marketplace patterns with pricing tiers
  - Implements Google Play Store-like update notification system
  - Supports both development (localhost) and production (CDN) environments
  - Includes comprehensive validation for workspace compatibility
  - Uses JSON fields for flexible configuration storage

#### 2. TemplateVersion Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\template_version.py`
- **Purpose**: Tracks different versions of templates with semantic versioning
- **Best Practices**:
  - Enforces semantic versioning format (X.Y.Z)
  - Validates CDN path formats for both development and production
  - Tracks Git integration (commit hashes, tags)
  - Manages compatibility requirements (min workspace version, dependencies)
  - Includes performance metrics (file size, load time)
- **Design Thinking**:
  - Supports smooth updates with breaking change detection
  - Enables rollback capabilities through version history
  - Provides CDN integration for asset delivery
  - Includes changelog tracking for user transparency

#### 3. TemplateAsset Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\template_asset.py`
- **Purpose**: Manages files and resources associated with templates
- **Best Practices**:
  - Supports multiple asset types (images, stylesheets, scripts, configs, fonts)
  - Validates file extensions based on asset type
  - Enforces file size limits (50MB max)
  - Generates checksums for file integrity
  - Automatically generates CDN URLs and paths
- **Design Thinking**:
  - Prevents path traversal attacks through validation
  - Ensures asset type consistency with file extensions
  - Provides comprehensive file metadata tracking
  - Supports both public and private asset access

#### 4. TemplateCategory Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\template_category.py`
- **Purpose**: Organizes templates in the theme store by type and price tier
- **Best Practices**:
  - Supports categorization by template type and price tier
  - Includes visual elements (icons, background colors)
  - Provides sorting and featured status management
  - Validates price tier filters and color formats
- **Design Thinking**:
  - Enables flexible storefront organization
  - Supports both automatic and manual categorization
  - Provides visual customization for store presentation
  - Includes template counting and featured template retrieval

### Customization Models

#### 5. TemplateCustomization Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\template_customization.py`
- **Purpose**: Stores user-specific template modifications for workspaces
- **Best Practices**:
  - Implements version control for customization changes
  - Supports both draft and published states
  - Manages active vs preview environments
  - Tracks customization size for performance monitoring
  - Includes CDN cache invalidation support
- **Design Thinking**:
  - Enables non-destructive customization through versioning
  - Supports staging/production environments
  - Provides undo/redo capabilities through version history
  - Includes comprehensive validation for workspace-template compatibility
  - Manages cache keys for efficient CDN updates

#### 6. CustomizationHistory Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\customization_history.py`
- **Purpose**: Provides audit trail and undo functionality for customization changes
- **Best Practices**:
  - Tracks detailed change information (old/new values)
  - Supports multiple action types (create, update, delete, publish, revert)
  - Categorizes changes by type (Puck, CSS, JS, status, role)
  - Includes user context (IP, user agent, session)
  - Provides undo functionality for reversible actions
- **Design Thinking**:
  - Enables comprehensive audit trails for compliance
  - Supports user-friendly undo operations
  - Calculates change summaries automatically
  - Provides detailed change analysis for different data types

### Sync and Notification Models

#### 7. UpdateNotification Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\sync_models.py`
- **Purpose**: Manages user update prompts following Google Play Store model
- **Best Practices**:
  - Supports multiple update types (minor, major, security, breaking)
  - Tracks notification status lifecycle (pending, sent, read, dismissed, accepted)
  - Includes customization preservation scoring
  - Provides estimated update time calculations
- **Design Thinking**:
  - Implements progressive rollout patterns
  - Supports user choice in update adoption
  - Includes breaking change awareness
  - Tracks user interaction with notifications

#### 8. SyncLog Model
- **File Location**: `c:\S.T.E.V.E\V2\HUZILERZ\backend\theme\models\sync_models.py`
- **Purpose**: Tracks Git-to-CDN sync operations for template deployment
- **Best Practices**:
  - Supports multiple sync types (automatic, manual, rollback, emergency)
  - Tracks sync progress with percentage calculations
  - Includes error handling and stack trace storage
  - Provides performance metrics (duration, file counts)
- **Design Thinking**:
  - Enables reliable deployment pipeline monitoring
  - Supports both automated and manual deployment workflows
  - Provides comprehensive error reporting for debugging
  - Includes rollback capabilities for failed deployments

## Model Relationships

```
Template (1) ←→ (N) TemplateVersion
TemplateVersion (1) ←→ (N) TemplateAsset
Template (1) ←→ (N) TemplateCustomization
TemplateCustomization (1) ←→ (N) CustomizationHistory
Template (1) ←→ (N) UpdateNotification
Template (1) ←→ (N) SyncLog
TemplateCategory (N) ←→ (N) Template (via filtering)
```

## Database Tables

- `theme_templates` - Master template storage
- `theme_template_versions` - Template version history
- `theme_template_assets` - Template file assets
- `theme_template_categories` - Template categorization
- `theme_template_customizations` - User customizations
- `theme_customization_history` - Customization audit trail
- `theme_update_notifications` - Update notification tracking
- `theme_sync_logs` - Deployment sync operations

## Key Design Patterns

1. **Version Control Pattern**: All user modifications are versioned and reversible
2. **Marketplace Pattern**: Templates follow e-commerce patterns with pricing and categorization
3. **CDN Integration Pattern**: All assets are delivered via CDN with cache management
4. **Git Integration Pattern**: Version control integration for template source management
5. **Notification Pattern**: Progressive update notifications following app store models
6. **Audit Trail Pattern**: Comprehensive change tracking for compliance and debugging

## Security Considerations

- Path traversal prevention in file paths
- JSON validation for configuration fields
- Size limits for custom CSS/JS to prevent performance issues
- Workspace-template compatibility validation
- User authentication and authorization for customization access

## Performance Optimizations

- Database indexes on frequently queried fields
- Atomic operations for counter increments
- CDN caching with cache key invalidation
- Efficient version comparison algorithms
- Progress tracking for large operations

This documentation provides AI systems with complete context about the theme models, enabling efficient navigation and understanding of the codebase structure.