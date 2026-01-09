# Huzilaz Theme Sync System

## Overview
Template sync system manages updates between master themes in Git and production CDN, with Google Play Store-style user update management.

## Sync Triggers

### Automatic Sync
- Git push to main branch triggers build pipeline
- Automated deployment to CDN
- Template metadata updated in database

### Manual Sync
- Developer control for major changes
- Version-specific deployments via Git tags
- Emergency rollback capabilities

## Version Management

### Semantic Versioning
- `v1.0.0`, `v1.1.0`, `v2.0.0` Git tags
- CDN directories: `/themes/boutique/v1.0.0/`
- Database tracks all versions internally

### Theme Store Display
- Only latest approved version shown to users
- Version history maintained for admin
- New users automatically get latest version

## User Update Strategy

### Google Play Store Model
- **New users**: Automatically get latest version
- **Existing users**: Manual opt-in updates only
- Update notifications in Puck editor
- Customizations preserved during updates

### Update Flow
1. Developer releases new template version
2. Theme store updates to show latest version
3. Existing users see "Update available" notification
4. User manually chooses to update
5. System merges new features with existing customizations
6. User deploys updated version

## Infrastructure Integration

### CDN Architecture
- All tiers use same master theme files from CDN
- User customizations stored in database only
- No per-tier theme file duplication

### 3-Tier Hosting (Separate System)
- **POOL**: Shared hosting for Beginning tier
- **BRIDGE**: Dedicated hosting for Pro tier
- **SILO**: Isolated hosting for Enterprise tier
- Theme sync operates independently of hosting tiers

## Technical Implementation

### Sync Pipeline
```
Git Push → Build Process → CDN Deployment → Database Update
```

### Database Models
- TemplateVersion: Tracks Git versions and CDN paths
- UserTemplate: Links users to specific template versions
- UpdateNotification: Manages user update prompts

### API Endpoints
- `POST /api/templates/sync` - Trigger manual sync
- `GET /api/templates/{id}/updates` - Check for updates
- `POST /api/templates/{id}/update` - User update request

## Update Safety

### Customization Preservation
- Puck configurations maintained during updates
- Visual customizations (colors, text) preserved
- Layout changes handled gracefully
- No data loss on update

### Rollback Capability
- Previous versions remain in CDN
- Quick rollback for problematic updates
- User can revert to previous version if needed