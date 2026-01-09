# Theme Sync System Implementation Guide

## Overview
This document outlines the step-by-step implementation of the theme sync system from development to production scale.

## Phase 1: Local Development (Current)

### Architecture
```
Frontend (Next.js) ←→ Backend (Django) ←→ Database (PostgreSQL)
                          ↑
                    Local File System (Themes)
```

### Implementation Steps

#### 1.1 Local Theme Storage Structure
```
/themes/
├── kendustorenew/
│   ├── v1.0.0/
│   │   ├── build/           # npm run build output
│   │   ├── theme-metadata.json
│   │   └── puck-config.json
│   └── README.md
├── restaurant-classic/
│   └── v1.0.0/
└── sync-manifest.json       # Tracks all themes
```  
 Yes, exactly! Every update = new version folder:

  - Bug fix → v1.0.1/
  - New feature → v1.1.0/
  - Major redesign → v2.0.0/

  Why this works:
  - Users on v1.0.0 keep working
  - New users get v1.1.0 automatically
  - Existing users see "Update available" notification
  - They choose when to update to v1.1.0
  - All versions stay in CDN for rollback

  Git integration: Each version folder matches a Git tag.

#### 1.2 Backend Services to Implement

**1.2.1 Theme Discovery Service**
- Scans `/themes/` directory
- Detects new theme versions
- Validates theme metadata
- Returns available themes

**1.2.2 Template Registry Service**
- Registers themes in database
- Generates UUIDs for themes
- Manages version tracking
- Handles theme updates

**1.2.3 Local CDN Proxy**
- Serves theme files from local file system
- Handles static asset delivery
- Provides development CDN URLs

#### 1.3 Sync Command
```bash
# Manual sync command
python manage.py sync_theme kendustorenew

# Bulk sync all themes
python manage.py sync_all_themes

# Check sync status
python manage.py theme_status
```

#### 1.4 Database Schema
```sql
-- Template master record
Template
- id (UUID, primary key)
- name
- slug
- description
- template_type (ecommerce, restaurant, blog, services)
- price_tier (free, paid, exclusive)
- price_amount
- status (draft, published, archived)
- version
- cdn_paths (JSON)
- puck_config (JSON)
- created_at
- updated_at

-- Template versions
TemplateVersion
- id (UUID)
- template_id (FK)
- version (semantic version)
- cdn_paths (JSON)
- changelog
- created_at

-- User customizations
TemplateCustomization
- id (UUID)
- workspace_id (FK)
- template_id (FK)
- template_version_id (FK)
- puck_config (JSON)
- custom_css
- custom_js
- created_at
- updated_at
```

#### 1.5 API Endpoints

**Theme Discovery**
- `GET /api/themes/` - List all available themes
- `GET /api/themes/search/` - Search themes with filters
- `GET /api/themes/{id}/` - Get theme details

**Theme Sync**
- `POST /api/themes/sync/` - Manual theme sync trigger
- `GET /api/themes/sync/status/` - Get sync status

**Theme Usage**
- `POST /api/themes/{id}/use/` - Apply theme to workspace
- `GET /api/workspaces/{id}/template/` - Get workspace template
- `POST /api/workspaces/{id}/template/update/` - Update customization

## Phase 2: GitHub Integration (Next)

### Architecture
```
GitHub Repository → GitHub Actions → CDN → Database
       ↑
Developer Push
```

### Implementation Steps

#### 2.1 GitHub Repository Structure
```
theme-repository/
├── .github/
│   └── workflows/
│       └── deploy-theme.yml
├── src/                    # Source code
├── build/                  # Built assets
├── theme-metadata.json
├── puck-config.json
└── package.json
```

#### 2.2 GitHub Actions Workflow
```yaml
name: Deploy Theme
on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Build theme
        run: |
          npm install
          npm run build

      - name: Deploy to CDN
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Sync to Database
        run: |
          curl -X POST ${{ secrets.BACKEND_URL }}/api/themes/sync/ \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}"
```

#### 2.3 Webhook Integration
- GitHub webhook triggers backend sync
- Automatic theme registration
- Version management

## Phase 3: Production Scale (Future)

### Architecture
```
Developer CLI → CDN (AWS S3/Cloudflare) → Database
     ↑
Git Integration
```

### Implementation Steps

#### 3.1 CLI Tool Development
```bash
# Install CLI
npm install -g @huzilaz/theme-cli

# Login
huzilaz theme login

# Push theme
huzilaz theme push kendustorenew

# Create new theme
huzilaz theme create my-theme

# List themes
huzilaz theme list
```

#### 3.2 CDN Integration
- AWS S3 for file storage
- Cloudflare for global delivery
- Version-based cache busting
- Asset optimization

#### 3.3 Advanced Features
- Theme marketplace
- User ratings and reviews
- Analytics and usage tracking
- A/B testing for themes
- Template inheritance

## Development Priority Order

### Immediate (Week 1-2)
1. Local theme discovery service
2. Manual sync command
3. Basic theme store frontend
4. Local CDN proxy

### Short Term (Week 3-4)
1. GitHub repository setup
2. GitHub Actions workflow
3. Webhook integration
4. Automated sync

### Medium Term (Month 2)
1. CLI tool development
2. Production CDN setup
3. Advanced theme features
4. User analytics

### Long Term (Month 3+)
1. Theme marketplace
2. Advanced customization
3. Performance optimization
4. Scale infrastructure

## Success Metrics

### Development Phase
- [ ] Themes can be discovered locally
- [ ] Themes can be applied to workspaces
- [ ] Puck customization works
- [ ] Local sync command functional

### Production Phase
- [ ] Automated GitHub deployment
- [ ] CDN serving theme files
- [ ] User theme management
- [ ] Performance benchmarks met

## Risk Mitigation

### Development Risks
- **Local file system limitations**: Use relative paths and environment variables
- **Manual sync process**: Document clear procedures
- **Testing complexity**: Create comprehensive test suite

### Production Risks
- **CDN costs**: Implement caching and optimization
- **Version conflicts**: Use semantic versioning strictly
- **User data loss**: Implement backup and rollback procedures

## Next Steps
1. Implement Phase 1 services
2. Test local theme lifecycle
3. Deploy to staging environment
4. Gather user feedback
5. Iterate based on usage patterns