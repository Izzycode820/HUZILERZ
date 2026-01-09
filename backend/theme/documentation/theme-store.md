# Huzilaz Theme Store & Discovery System

## Core Features

### 1. Template Catalog
- Browse all available templates
- Filter by: Template type (ecommerce/services/blog/restaurant), Price tier (free/paid/exclusive), Workspace compatibility
- Sort by: Popularity, Rating, Newest, Price
- Search by: Template name, description, features

### 2. Template Preview System
- Live Puck preview with actual template functionality
- Feature highlights and specifications including workspace compatibility

### 3. User Experience
- "Try before you buy" demo mode
- Template ratings system
- Template usage metrics (views, downloads, active usage)

## API Endpoints

### Template Discovery:
```
GET /api/templates - List all templates with filters
GET /api/templates/search - Search templates
GET /api/templates/{id} - Get template details
```

### User Actions:
```
POST /api/templates/{id}/use - Clone template to workspace
POST /api/templates/{id}/rate - Add rating (1-5 stars)
GET /api/templates/{id}/ratings - Get template ratings
```

## Database Models

### Template Model:
```python
class Template:
    id, name, description, slug
    template_type (ecommerce/services/blog/restaurant)
    price_tier (free/paid/exclusive)
    price_amount (for paid/exclusive)
    workspace_types (list of compatible workspaces)
    version, status (draft/active/deprecated)
    demo_url
    rating, rating_count, download_count, view_count
    created_at, updated_at
```

### TemplateCategory:
```python
class TemplateCategory:
    id, name, slug, description
    template_type, price_tier_filters
    sort_order, is_featured
```

### TemplateRating:
```python
class TemplateRating:
    id, template, user, rating (1-5)
    created_at
```

## Merchant Experience Flow

### User Journey:
1. Browse Theme Store → Find template
2. Click "Use Theme" → System creates template clone
3. Puck Editor Loads → User edits template with workspace data
4. Status Management:
   - User saves → Status: "saved" → Template deployable
   - User abandons → Status: "draft" → Template not deployable
5. Deployment → Only "saved" templates can be deployed

### Status States:
- draft: Editing abandoned, not deployable
- saved: Editing completed, ready for deployment
- deployed: Template live on storefront





### 2. Template Validation
- Automatic compatibility checking



## Performance

### Caching Strategy:
- Template listings cached with filters
- Popular templates in memory cache
- CDN for template assets
- Database query optimization for search

### Search Optimization:
- Full-text search on template metadata
- Filter indexes for common queries
- Search result caching
- Autocomplete suggestions