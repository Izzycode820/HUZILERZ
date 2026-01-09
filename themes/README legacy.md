# Theme Development Guide

## Architecture Overview

**One Backend, One Master Theme, Many Workspaces**
- Backend: `api.huzilerz.com` (single GraphQL endpoint)
- Themes: CDN-hosted React apps (one master per theme)
- Workspaces: Database tenants (each user gets their own)

## Data Flow

### Theme → Backend Communication
1. Theme sends `X-Store-Hostname` header with subdomain/domain
2. Backend middleware extracts hostname → looks up workspace
3. GraphQL resolvers auto-scope queries to that workspace
4. Theme receives only that tenant's data

### Preview vs Production
**Preview (Demo Workspace):**
- Theme connects to demo workspace (`sneakers-demo.huzilerz.com`)
- Shows beautiful mock products seeded via management command
- Users see theme in action before purchase

**Production (User Workspace):**
- Theme connects to user's workspace (`user-123-johns-shop.huzilerz.com`)
- Shows user's actual products
- Same theme code, different data source

## Theme Setup

### 1. Apollo Client Configuration
**Location:** `src/lib/apollo-client.ts`

**Required:**
- Send `X-Store-Hostname` header extracted from `window.location.hostname`
- GraphQL endpoint: `http://localhost:8000/api/workspaces/storefront/graphql/` (dev) or `https://api.huzilerz.com/api/workspaces/storefront/graphql/` (prod)
- Use `HttpLink` (NOT upload link for themes)

**Setup:**
- Create Apollo Client with store identification middleware
- Wrap app with ApolloProvider in layout

### 2. Puck Configuration
**Build Config:** Run `npm run build:puck-config` to generate `puck.config.json`
**Master Data:** Create `puck.data.json` with default layout
**Backend Sync:** Run `python manage.py sync_themes` to register theme

### 3. Required Files
- `puck.config.tsx` - Component definitions
- `puck.config.json` - Generated config for backend
- `puck.data.json` - Default page layout
- `theme-config.ts` - Theme capabilities & tier

## Development Workflow

### Local Development
**Backend:** `localhost:8000`
**Theme:** `localhost:3001`
**Flow:** Theme extracts hostname → sends to backend → backend resolves workspace → returns data

#### Hostname Extraction Methods (Dev Environment)

Since localhost doesn't have subdomains, we need special handling in development:

**Method 1: Query Parameter Override (Recommended for Quick Testing)**
```
http://localhost:3001                    → demo-store (default)
http://localhost:3001?store=johns-shop   → johns-shop
http://localhost:3001?store=any-workspace → any-workspace
```

**Implementation:**
- Add query param check in `src/lib/utils/store-identifier.ts`
- Parse `?store=` parameter when hostname is localhost
- Falls back to demo-store if no param provided

**Pros:**
- Easy to switch between stores (just change URL param)
- No system configuration needed
- Can share URLs with ?store= in them

**Cons:**
- URL looks different than production
- Need to remember to add ?store= param

---

**Method 2: /etc/hosts File (Realistic Production Simulation)**
```
http://demo-store.local:3001   → demo-store
http://johns-shop.local:3001   → johns-shop
```

**Setup:**
1. Edit hosts file:
   - Mac/Linux: `/etc/hosts`
   - Windows: `C:\Windows\System32\drivers\etc\hosts`
2. Add entries:
   ```
   127.0.0.1  demo-store.local
   127.0.0.1  johns-shop.local
   127.0.0.1  any-workspace.local
   ```
3. Update `store-identifier.ts` to handle `.local` domains

**Pros:**
- URL structure matches production (subdomain-based)
- More realistic testing environment
- No need to remember query params

**Cons:**
- Requires system file modification
- Need to add entry for each test workspace

---

**Recommended Approach:**
- Start with Method 1 for quick iteration
- Use Method 2 when testing multi-tenant features or final QA

### Demo Data Setup
1. Add `is_demo=True` flag to Workspace model
2. Create management command: `python manage.py seed_theme_demo --theme=sneakers`
3. Seed demo products, collections, images
4. Create DeployedSite linking demo workspace to subdomain

### Publishing Flow
**Not Built Yet (Future):**
1. User customizes Puck data in admin
2. Admin saves to database
3. Subdomain assigned automatically
4. Theme fetches user's Puck data + products
5. Site live instantly (no build needed)

## Deployment

### Theme Deployment (One-Time)
- Build Next.js app
- Upload to CDN
- Register in backend theme registry

### User Site Deployment (Per User)
- Clone master Puck config
- Link to user's workspace
- Assign subdomain
- Theme automatically connects to user's data

## Key Principles

1. **One Master Theme:** Never duplicate theme code per user
2. **Runtime Data Fetching:** Themes fetch data at runtime via GraphQL
3. **Database Multi-Tenancy:** Workspace isolation via middleware
4. **Demo Workspaces:** Preview themes with beautiful mock data
5. **No Static Generation:** Themes are dynamic, not pre-built per user
6. **Header-Based Identification:** X-Store-Hostname tells backend which workspace

## Troubleshooting

**Theme can't fetch data:**
- Check `X-Store-Hostname` header is sent
- Verify workspace exists with matching subdomain
- Check DeployedSite record links workspace to subdomain

**Demo preview empty:**
- Run `python manage.py seed_theme_demo --theme=<name>`
- Verify demo workspace has `is_demo=True`
- Check DeployedSite points to demo workspace

**Puck config not loading:**
- Run `npm run build:puck-config`
- Verify `puck.config.json` exists
- Run `python manage.py sync_themes`
