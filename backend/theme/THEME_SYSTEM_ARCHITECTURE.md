# Theme System Architecture & Implementation Plan

**Last Updated:** 2025-11-23
**Status:** Planning → Implementation
**Migration:** REST → GraphQL

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Data Flow](#data-flow)
4. [GraphQL Schema](#graphql-schema)
5. [Database Schema](#database-schema)
6. [User Flows](#user-flows)
7. [Implementation Checklist](#implementation-checklist)
8. [Migration Notes](#migration-notes)

---

## System Overview

Shopify-like theme system for Cameroon e-commerce SaaS using:
- **Puck** as the visual editor (not Plasmic)
- **GraphQL** for all API communication (no REST)
- **Theme Registry** for dynamic component loading
- **Manifest-based** theme discovery (deprecated entry files)
- **Multi-tenancy** with workspace isolation

### Key Concepts

**Master Theme:**
- Lives in monorepo: `themes/sneakers/v1.0.0/`
- Contains: manifest.json, puck.config.json, puck.data.json
- One build hosted on CDN
- All users share the same theme UI code

**Theme Customization:**
- User's personalized version
- Contains: cloned puck.config + puck.data
- Linked to workspace (user's store)
- Multiple customizations per workspace (library model)
- Only ONE active (published) at a time

**Theme Discovery:**
- `python manage.py sync_themes` scans filesystem
- Extracts manifest, puck config, puck data
- Registers in database
- No CDN pipeline yet (future: GitHub Actions)

---

## Architecture Decisions

### 1. Authentication Strategy

| Endpoint | Access Level | Reason |
|----------|--------------|--------|
| `themes` query | **PUBLIC** | Browse theme store without account |
| `themeDetails` query | **PUBLIC** | View details + demo before signup |
| `themeCustomization` query | **AUTHENTICATED + WORKSPACE-SCOPED** | User must own workspace |
| All mutations | **AUTHENTICATED + WORKSPACE-SCOPED** | Prevent unauthorized modifications |

**Workspace Scoping Rule:**
If mutation/query has `workspaceId`, verify user owns that workspace.

### 2. GraphQL vs REST

**Decision: Full GraphQL**

✅ **Reasons:**
- Storefront already uses GraphQL (consistency)
- Flexible queries (list vs detail vs customization)
- Single endpoint (`/api/workspaces/graphql/`)
- Type safety with auto-generated types
- Easier evolution (add fields without breaking clients)
- Batching (load theme + customization + workspace in one query)

❌ **REST Downsides:**
- 6 separate endpoints to maintain
- Over-fetching in listing endpoints
- Multiple round trips
- Version management complexity

### 3. Theme Library Model (Shopify Pattern)

**Multiple themes per workspace:**
- User can add multiple themes to their library
- Only ONE published at a time (`isActive: true`)
- Can customize any theme (published or draft)
- Switching = publish different one (auto-unpublishes current)
- "Add Theme" ≠ replace (adds to library)

**Better UX:**
- Experiment without losing current setup
- A/B test different themes
- Seasonal theme switching
- Fallback to previous theme easily

### 4. Data Visibility in Editor

**Shopify Model (We Follow):**
- Editor loads with user's LIVE data
- No placeholders or mock data
- GraphQL queries fetch real products/collections
- Components show actual images, prices, names
- Empty states handled gracefully

**How:**
- Customization links to `workspaceId`
- Apollo Client sends `X-Store-Hostname` header
- Backend resolves workspace → scopes queries
- Puck components query user's real data
- Field pickers (collections, products) populated dynamically

### 5. Slug vs ID Usage

**Both used strategically:**
- `customizationId` (UUID) → Load editor, save progress
- `workspaceId` (UUID) → Scope data queries
- `themeSlug` (string) → Load UI components from registry

**Flow:**
```
themeCustomization(id: uuid) → { workspaceId, themeSlug, puckData }
↓
workspaceId → X-Store-Hostname → GraphQL queries for user data
themeSlug → THEME_REGISTRY[slug] → Load React components
```

### 6. Domain Strategy

**One domain per workspace, not per theme**
- Workspace: `johns-shop.huzilerz.com`
- Active theme renders on that domain
- Switching themes = same domain, different UI
- Draft themes: No domain, only editor preview

**User can:**
- Rename customization ("Summer Sale Theme")
- But domain stays the same
- Theme name is just a label

---

## Data Flow

### Theme Discovery (Dev → Database)

```
1. Developer creates theme in /themes/sneakers/v1.0.0/
   ├── theme-manifest.json
   ├── puck.config.json
   ├── puck.data.json
   └── src/ (components)

2. Run: python manage.py sync_themes
   ↓
   Scans filesystem for manifest files
   ↓
   Extracts: manifest, puck.config, puck.data
   ↓
   Saves to Theme table:
   - slug: "ecommerce-sneakers"
   - manifest_data (JSONB)
   - master_puck_config (JSONB)
   - master_puck_data (JSONB)
   - features, tier, version, etc.

3. Theme appears in store listing
```

### Theme Selection (User Journey)

```
1. USER BROWSES STORE
   Query: themes(tier: FREE)
   Returns: [{ slug, name, previewImage, tier }]

2. USER VIEWS DETAILS
   Query: themeDetails(slug: "ecommerce-sneakers")
   Returns: { description, features, demoUrl, screenshots }
   User clicks demoUrl → sees live preview on demo workspace

3. USER ADDS THEME
   Mutation: addTheme(workspaceId, "ecommerce-sneakers")
   Backend:
   - Clone master_puck_config → customized_puck_config
   - Clone master_puck_data → customized_puck_data
   - Create ThemeCustomization record
   - Link to workspaceId
   - Set isActive: false (draft)
   Returns: { id: uuid, workspaceId, themeSlug }

4. REDIRECT TO EDITOR
   Frontend: /editor?customizationId=uuid-123

5. EDITOR LOADS
   Query: themeCustomization(id: uuid-123)
   Returns: { workspaceId, themeSlug, puckData, puckConfig }

   Frontend:
   - THEME_REGISTRY[themeSlug] → import('@themes/sneakers')
   - Apollo Client configured with workspace hostname
   - Puck initializes with user's puckData + puckConfig

6. LIVE DATA IN EDITOR
   Puck components query GraphQL:
   - GET_COLLECTIONS → User's collections
   - GET_PRODUCTS → User's products
   - Empty states if no data

   User edits:
   - Select collection from dropdown (real data)
   - Pick products for featured section
   - Configure hero image, text, colors
   - Preview shows real products

7. SAVE PROGRESS
   Mutation: updateThemeCustomization(id, puckData, puckConfig)
   - Saves both data and config
   - Keeps isActive: false (still draft)

8. PUBLISH THEME
   Mutation: publishTheme(id: uuid-123)
   Backend transaction:
   - Set all workspace themes to isActive: false
   - Set this theme to isActive: true
   - Update publishedAt timestamp

   Theme now live at: johns-shop.huzilerz.com

9. MANAGE LIBRARY
   Query: myThemes(workspaceId)
   Returns: All user's themes (active + drafts)

   Can:
   - Switch active theme (publish different one)
   - Duplicate theme (experiment with variations)
   - Delete drafts (can't delete active)
   - Rename themes
```

### Runtime Data Flow (Storefront)

```
Customer visits: johns-shop.huzilerz.com
↓
Frontend sends: X-Store-Hostname: johns-shop.huzilerz.com
↓
Backend middleware resolves workspace
↓
Fetch active theme customization (isActive: true)
↓
Returns: { themeSlug, puckData, puckConfig }
↓
Frontend: THEME_REGISTRY[themeSlug] → Load components
↓
Render theme with user's puck customization + workspace data
```

---

## GraphQL Schema

### Queries

```graphql
type Query {
  """
  PUBLIC - Browse theme store
  Returns light data for listing view
  """
  themes(
    tier: ThemeTier
  ): [ThemeStoreListing!]!

  """
  PUBLIC - View theme details
  Returns rich data for decision-making (NO puck files)
  """
  themeDetails(slug: String!): ThemeDetails!

  """
  AUTHENTICATED + WORKSPACE-SCOPED
  Get all themes in user's library
  """
  myThemes(workspaceId: ID!): [ThemeCustomization!]!

  """
  AUTHENTICATED + WORKSPACE-SCOPED
  Get specific customization for editor
  """
  themeCustomization(id: ID!): ThemeCustomization!
}
```

### Mutations

```graphql
type Mutation {
  """
  Add theme to user's library (clone from master)
  Creates draft customization linked to workspace
  """
  addTheme(
    workspaceId: ID!
    themeSlug: String!
  ): ThemeCustomization!

  """
  Save customization progress
  Updates both puck data and config
  """
  updateThemeCustomization(
    id: ID!
    puckData: JSON!
    puckConfig: JSON!
  ): ThemeCustomization!

  """
  Publish theme (make it live)
  Auto-unpublishes any other active theme
  """
  publishTheme(id: ID!): ThemeCustomization!

  """
  Remove theme from library
  Cannot delete active theme
  """
  deleteTheme(id: ID!): Boolean!

  """
  Duplicate customization
  For experimenting with variations
  """
  duplicateTheme(id: ID!): ThemeCustomization!

  """
  Rename customization
  User-friendly label
  """
  renameTheme(id: ID!, name: String!): ThemeCustomization!
}
```

### Types

```graphql
"""
Light data for theme store browsing
"""
type ThemeStoreListing {
  slug: String!
  name: String!
  previewImage: String!
  tier: ThemeTier!
  version: String!
  description: String
}

"""
Rich data for decision-making
NO puck files (users don't need to see engineering details)
"""
type ThemeDetails {
  slug: String!
  name: String!
  description: String!
  version: String!
  tier: ThemeTier!

  # Visual assets
  previewImage: String!
  demoUrl: String!

  # Features & capabilities
  features: [String!]!
  capabilities: JSON!

  # Technical info
  compatibility: JSON!
  tags: [String!]

  # Metadata
  author: String
  lastUpdated: DateTime!
}

"""
User's customization in their library
"""
type ThemeCustomization {
  id: ID!
  workspace: Workspace!
  themeSlug: String!
  themeName: String!  # User can rename

  # User's custom data (BOTH modifiable)
  customizedPuckData: JSON!
  customizedPuckConfig: JSON!

  # State
  isActive: Boolean!

  # Metadata
  createdAt: DateTime!
  lastEditedAt: DateTime!
  publishedAt: DateTime
}

enum ThemeTier {
  FREE
  PAID
  EXCLUSIVE
}
```

---



---

## User Flows

### Flow 1: Browse & Add Theme

```
User Action: Visit theme store
↓
Query: themes()
Display: Grid of themes with preview images
↓
User Action: Click theme card
↓
Query: themeDetails(slug)
Display: Full details, features, demo link
↓
User Action: Click "Try Demo"
Opens: demo_url in new tab (demo workspace)
↓
User Action: Click "Add to My Store"
↓
Mutation: addTheme(workspaceId, themeSlug)
Backend: Clone master puck files, create customization
↓
Redirect: /editor?customizationId=uuid
```

### Flow 2: Customize Theme

```
User arrives at: /editor?customizationId=uuid
↓
Query: themeCustomization(id)
Returns: { workspaceId, themeSlug, puckData, puckConfig }
↓
Frontend loads:
- THEME_REGISTRY[themeSlug] (components)
- Apollo configured with workspace
- Puck initialized with user's data
↓
Puck components query:
- GET_COLLECTIONS (for collection picker)
- GET_PRODUCTS (for product selector)
- Show user's real data
↓
User edits:
- Select collection: "Summer Shoes"
- Configure hero text, image
- Adjust product grid settings
- Preview shows real products
↓
Auto-save every 30s OR manual save:
Mutation: updateThemeCustomization(id, puckData, puckConfig)
↓
User clicks "Publish":
Mutation: publishTheme(id)
Backend: Unpublish old theme, publish this one
↓
Success: "Theme published to johns-shop.huzilerz.com"
```

### Flow 3: Manage Theme Library

```
User: Navigate to Themes page
↓
Query: myThemes(workspaceId)
Returns: [
  { id: 1, themeName: "Sneakers", isActive: true },
  { id: 2, themeName: "Summer Sale", isActive: false },
  { id: 3, themeName: "Minimalist", isActive: false }
]
↓
Display: List with actions
- Active theme: "Customize" button
- Drafts: "Edit", "Publish", "Delete" buttons
↓
User Action: Click "Publish" on draft
↓
Mutation: publishTheme(id: 2)
Backend:
- Theme 1 isActive → false
- Theme 2 isActive → true
↓
Success: "Summer Sale theme is now live"
↓
User Action: Click "Duplicate" on active theme
↓
Mutation: duplicateTheme(id: 1)
Creates: "Sneakers Copy" (draft)
↓
User can experiment without affecting live theme
```

### Flow 4: Switch Themes

```
User has:
- Theme A (active, customized)
- Theme B (draft, customized)
↓
User Action: Publish Theme B
↓
Mutation: publishTheme(id: themeB.id)
↓
Backend transaction:
1. UPDATE theme_customizations
   SET is_active = false
   WHERE workspace_id = X AND is_active = true
2. UPDATE theme_customizations
   SET is_active = true, published_at = NOW()
   WHERE id = themeB.id
↓
Result:
- Theme A: still in library, now draft
- Theme B: now active on johns-shop.huzilerz.com
↓
User can switch back anytime (Theme A is preserved)
```

---

## Implementation Checklist = done ✅

### Phase 1: Backend Cleanup (Current)

- [ ] Remove entry file logic from manifest scanning
- [ ] Update manifest.json schema (remove `entry` field)
- [ ] Clean up service layer (remove entry-related code)
- [ ] Document existing workspace scoping patterns
- [ ] List current REST endpoints (for migration reference)

### Phase 2: Database Migration = done ✅

- [ ] Add `screenshots` field to themes table (JSONB array)
- [ ] Add `theme_name` field to customizations table
- [ ] Add unique constraint for one active theme per workspace
- [ ] Migrate existing data (if any)
- [ ] Test constraint enforcement

### Phase 3: GraphQL Schema = patialy, we still need to register the one url for themes, delete the views and the serializer file

- [ ] Define types (Theme, ThemeCustomization, etc.)
- [ ] Implement queries (themes, themeDetails, myThemes, themeCustomization)
- [ ] Implement mutations (addTheme, updateThemeCustomization, publishTheme, etc.)
- [ ] Add workspace scoping middleware to resolvers
- [ ] Add authentication checks
- [ ] Write unit tests for resolvers

### Phase 4: Service Layer = done ✅

- [ ] ThemeService.list_themes(tier=None)
- [ ] ThemeService.get_theme_details(slug)
- [ ] ThemeService.clone_theme(workspace_id, theme_slug)
- [ ] ThemeService.update_customization(id, puck_data, puck_config)
- [ ] ThemeService.publish_theme(id) (with transaction)
- [ ] ThemeService.delete_theme(id) (with validation)
- [ ] ThemeService.duplicate_theme(id)
- [ ] ThemeService.get_user_themes(workspace_id)

### Phase 5: Frontend Integration

- [ ] Update Apollo queries to use new GraphQL schema
- [ ] Update theme store listing page
- [ ] Update theme details page
- [ ] Update Puck editor initialization
- [ ] Implement theme library management UI
- [ ] Add publish/unpublish flows
- [ ] Add theme switching UI
- [ ] Handle empty states in Puck components

### Phase 6: Testing

- [ ] Test public queries (unauthenticated access)
- [ ] Test workspace scoping (user can only see their themes)
- [ ] Test one-active-theme constraint
- [ ] Test publish transaction (old theme unpublished)
- [ ] Test live data in Puck editor
- [ ] Test theme switching preserves customizations
- [ ] Test delete validation (can't delete active)
- [ ] Load testing (multiple users, large puck data)

### Phase 7: Deprecation

- [ ] Mark old REST endpoints as deprecated
- [ ] Add deprecation warnings
- [ ] Monitor usage (ensure no clients using old endpoints)
- [ ] Remove REST endpoints after grace period
- [ ] Update documentation

---

## Migration Notes

### REST to GraphQL Migration

**Old Endpoints (To Remove):**
1. `GET /themes/` - List themes
2. `GET /themes/:slug/` - Theme details
3. `POST /themes/clone/` - Clone theme
4. `GET /themes/customizations/:id/` - Get customization
5. `PATCH /themes/customizations/:id/` - Update customization
6. `POST /themes/customizations/:id/publish/` - Publish theme

**New GraphQL (Replacement):**
1. `Query: themes`
2. `Query: themeDetails`
3. `Mutation: addTheme`
4. `Query: themeCustomization`
5. `Mutation: updateThemeCustomization`
6. `Mutation: publishTheme`

**Migration Strategy:**
1. Implement GraphQL schema alongside REST
2. Update frontend to use GraphQL
3. remove rest

### Entry File Deprecation

**Old Method:** = removed ✅
- Manifest contained `entry.dev` and `entry.prod` paths
- Backend looked for entry files to load themes
- Complex path resolution logic

**New Method:** = done ✅
- Manifest only contains `puck_config` and `puck_data` paths
- Frontend uses THEME_REGISTRY for component loading
- Backend only stores puck files in DB

**Files to Clean:** = done ✅
- `theme-manifest.json` - Remove `entry` field
- Service layer - Remove entry file resolution
- Discovery command - Skip entry file scanning


TODO in the feature when the core is working...
## Edge Cases & Considerations

### 1. Theme Versioning
**Scenario:** Theme v1.0.0 updated to v2.0.0
**Decision:** User keeps v1.0.0 (backward compatibility)
**Future:** Add "Update theme" feature (migrate puck data)

### 2. Deleted Themes
**Scenario:** Theme removed from store, user has customization
**Decision:** Keep customization working (soft delete theme)
**Implementation:** Theme.status = "deprecated" (don't delete row)

### 3. Empty States in Editor
**Scenario:** User has no products/collections
**Handling:**
- Collection picker shows "Create your first collection"
- Product grid shows placeholder with CTA
- Theme still functional, just empty

### 4. Concurrent Editing
**Scenario:** User opens editor in two tabs
**Handling:**
- Optimistic updates with conflict resolution
- Last write wins
- Consider websocket sync (future)

### 5. Large Puck Data
**Scenario:** User adds 100+ sections, JSONB becomes huge
**Handling:**
- Set reasonable limits (max 50 sections)
- Paginate section editor
- Warn user about performance

### 6. Theme Tier Upgrades
**Scenario:** Free theme user upgrades to paid tier
**Handling:**
- Unlock new features in puck config
- Preserve existing customizations
- Show upgrade prompt for locked features

### 7. Workspace Deletion
**Scenario:** User deletes workspace
**Handling:**
- CASCADE delete theme_customizations
- Master themes unaffected
- Consider soft delete with grace period

---

## Future Enhancements

### Near-term
- [ ] Theme preview without adding to library
- [ ] Theme ratings & reviews
- [ ] Featured themes section
- [ ] Theme search & filtering
- [ ] Customization history (undo/redo)
- [ ] Theme export/import (backup)

### Long-term
- [ ] GitHub Actions for CDN deployment
- [ ] Theme marketplace (3rd party developers)
- [ ] A/B testing (run two themes, split traffic)
- [ ] Scheduled theme publishing
- [ ] Theme analytics (which sections used most)
- [ ] AI-powered theme suggestions

---

## References

### Documentation
- Puck Editor: https://puck.app/docs
- Shopify Themes: https://shopify.dev/docs/themes
- GraphQL Best Practices: https://graphql.org/learn/best-practices/

### Internal Docs
- [Theme Development Rules](../themes/THEME_DEVELOPMENT_RULES.md)
- [Legacy README](../themes/README%20legacy.md)
- Theme Registry: `frontend/src/registry/theme-registry.ts`
- Manifest Example: `themes/sneakers/v1.0.0/theme-manifest.json`

### Related Systems
- Workspace scoping: Service layer patterns (to review)
- Apollo Client: X-Store-Hostname middleware
- Multi-tenancy: Workspace resolution middleware

---

**Next Steps:**
1. Review backend service layer structure
2. Identify files to clean (entry logic)
3. Design GraphQL resolvers with workspace scoping
4. Begin implementation

---

*This document is a living spec. Update as implementation progresses.*
