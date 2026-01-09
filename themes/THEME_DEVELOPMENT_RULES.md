# Theme Development Rules

## Core Principles

1. **GraphQL-Only:** All data fetching via GraphQL (NO REST for storefront data)
2. **Theme-Specific Queries:** Each theme queries ONLY fields it displays
3. **Puck-Customizable:** Content editable via Puck (NOT code/CSS)
4. **Cameroon-First:** WhatsApp checkout + Mobile Money payments
5. **Multi-Tenant:** X-Store-Hostname header identifies workspace

## Architecture

**Master Theme Pattern:**
- One theme build hosted on CDN
- Runtime data fetching via GraphQL
- Apollo Client with X-Store-Hostname middleware
- Backend resolves workspace from hostname
- Workspace isolation at database level

**Preview vs Production:**
- Preview: Demo workspace with seeded mock data
- Production: User workspace with real products
- Same theme code, different data source

## Required Folder Structure

```
theme-name/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/
│   │   ├── ui/          # Reusable components
│   │   ├── puck/        # Puck-editable sections
│   │   └── ecommerce/   # Product, Cart, Checkout
│   ├── lib/
│   │   ├── apollo-client.ts    # GraphQL client with X-Store-Hostname
│   │   └── apollo-provider.tsx # Provider wrapper
│   ├── graphql/
│   │   ├── queries.ts   # Product, Cart queries
│   │   └── mutations.ts # Cart, Checkout mutations
│   └── config/
│       └── theme-config.ts     # Theme capabilities
├── puck.config.tsx      # Puck component definitions
├── puck.config.json     # Generated config (for backend)
└── puck.data.json       # Default layout
```

## Tech Stack Requirements

**Required:**
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Apollo Client (with X-Store-Hostname middleware)
- Puck (@measured/puck)

**Prohibited:**
- Any Plasmic packages
- Redux/Zustand (use Context API)
- styled-components (use Tailwind)
- REST APIs for data fetching

## Apollo Client Setup

**Location:** `src/lib/apollo-client.ts`

**Requirements:**
1. Use `HttpLink` (NOT UploadHttpLink)
2. Send `X-Store-Hostname` header via `setContext` middleware
3. Extract hostname from `window.location.hostname`
4. Endpoint: `http://localhost:8000/api/workspaces/storefront/graphql/` (dev)
5. Set `credentials: 'include'`

**Provider:** Wrap app in `layout.tsx` with ApolloProvider

## Theme Tiers & Features

### Free Tier (10k FCFA/month)
- Product browsing
- Session-based cart
- WhatsApp checkout ONLY
- Order tracking
- No payment integration
- No variants
- No regional inventory

### Paid Tier (15k-20k FCFA/month)
- All Free features
- Mobile Money payments
- Product variants (optional)
- Dual checkout (WhatsApp + Payment)
- Discount banners

### Exclusive Tier (50k-200k FCFA/month)
- All Paid features
- Regional inventory display
- Advanced filtering
- Analytics integration
- Customer accounts (future)

## Theme Configuration

**File:** `src/config/theme-config.ts`

**Required Fields:**
- `name` - Theme display name
- `tier` - 'free' | 'paid' | 'exclusive'
- `version` - Semantic version
- `compatibleWorkspaceTypes` - ['store'] (required)
- `capabilities` - Feature flags object

**Capability Flags:**
- `hasPaymentCheckout` - Free: false, Paid/Exclusive: true
- `hasWhatsAppCheckout` - All: true
- `supportsVariants` - Theme-specific
- `showsRegionalInventory` - Exclusive: true, others: false
- `hasDiscountBanners` - Paid/Exclusive: true
- `hasAdvancedFilters` - Exclusive: true

## GraphQL Integration

### Query Rules
1. Fetch ONLY fields your theme displays
2. Use pagination (max 50 items per page)
3. Include `storeSlug` or workspace identifier in variables
4. Cache results via Apollo
5. Handle loading and error states

### Required Queries
- `GET_PRODUCTS` - Product listing
- `GET_PRODUCT_DETAIL` - Single product
- `GET_CART` - Shopping cart

### Required Mutations
- `CREATE_CART` - Initialize session
- `ADD_TO_CART` - Add item
- `UPDATE_CART_ITEM` - Update quantity
- `REMOVE_FROM_CART` - Remove item
- `CREATE_WHATSAPP_ORDER` - WhatsApp checkout (ALL themes)
- `CHECKOUT_WITH_PAYMENT` - Payment checkout (Paid/Exclusive only)

### Field Selection by Tier
**Free:** id, name, price, images, inStock
**Paid:** + variants (size, color, sku)
**Exclusive:** + inventoryByRegion (region, quantity, available)

## Puck Integration

### What is Puck?
Content editor for admins to customize text, images, section visibility WITHOUT touching code.

### Editable Elements
- Hero text & images
- Section titles
- Promo banners
- Product grid limits
- Footer content
- Color selections (from preset options)

### NOT Editable
- CSS styles
- JavaScript logic
- Component structure
- Layout

### Required Files
- `puck.config.tsx` - Component field definitions
- `puck.config.json` - Generated config (run `npm run build:puck-config`)
- `puck.data.json` - Default content

### Component Pattern
- Define `fields` object with editable properties
- Define `defaultProps` with sensible defaults
- Implement `render` function with hardcoded layout
- Store components in `components/puck/`

## State Management

**Use React Context + useReducer ONLY**

**Required Contexts:**
1. **SessionContext** - Guest session ID management
2. **CartContext** - Shopping cart state (synced with GraphQL)
3. **StoreContext** - Store settings & capabilities

**Session Creation:**
- Auto-create on first cart interaction
- 7-day expiry
- Store in localStorage + backend

## Data Fetching Pattern

**Flow:**
1. Theme extracts hostname from `window.location.hostname`
2. Apollo Client sends `X-Store-Hostname` header
3. Backend middleware resolves workspace
4. GraphQL queries auto-scoped to workspace
5. Theme receives only that workspace's data

**Never:**
- Don't send workspace ID in query variables (handled by middleware)
- Don't use REST for product/cart data
- Don't hardcode workspace identifiers

## Checkout Flows

### WhatsApp Checkout (ALL Themes)
1. Validate cart items
2. Collect customer info (name, phone, address)
3. Create order via `CREATE_WHATSAPP_ORDER` mutation
4. Generate WhatsApp link with pre-filled message
5. Redirect to WhatsApp

### Payment Checkout (Paid/Exclusive)
1. Validate cart items
2. Collect customer info + payment method
3. Create order via `CHECKOUT_WITH_PAYMENT` mutation
4. Redirect to Fapshi payment gateway
5. Handle webhook response

## Cameroon-Specific Requirements

- Phone format: +237 XXX XXX XXX
- Currency: XAF only (no USD/EUR)
- Regional names: Douala, Yaoundé, Buea, Bafoussam, etc.
- Mobile Money: MTN MoMo, Orange Money
- WhatsApp: Primary communication channel
- Mobile-first design (80% users on mobile)

## Pre-Deployment Checklist

- [ ] Apollo Client sends `X-Store-Hostname` header
- [ ] `theme-config.ts` configured correctly
- [ ] `puck.config.json` generated
- [ ] GraphQL queries fetch tier-appropriate fields
- [ ] WhatsApp checkout implemented
- [ ] Payment checkout (if Paid/Exclusive)
- [ ] Session management working
- [ ] Mobile responsive (375px min width)
- [ ] Images optimized (WebP, lazy-loaded)
- [ ] TypeScript strict mode passes
- [ ] No REST calls for storefront data
- [ ] Currency displays in XAF
- [ ] Regional data accurate

## Testing Requirements

**Free Themes:**
- Product browsing works
- Cart creates session automatically
- WhatsApp order generates correct message
- Order created in DB with `source: 'whatsapp'`

**Paid Themes:**
- All Free tests +
- Variant selector works (if applicable)
- Dual checkout displays correctly
- Payment redirect works
- Both order types create DB records

**Exclusive Themes:**
- All Paid tests +
- Regional inventory displays
- Advanced filters work
- Shipping calculation accurate

## Performance Targets

- Page load: < 3s on 3G (Africa-critical)
- GraphQL queries: < 500ms response
- Cart operations: < 200ms
- Initial JS bundle: < 200KB

## Common Mistakes to Avoid

1. Using REST for product/cart data
2. Not sending X-Store-Hostname header
3. Over-fetching GraphQL fields
4. Hardcoding workspace identifiers
5. Making CSS/layout Puck-editable
6. Not handling session expiry
7. Forgetting mobile-first design
8. Using non-XAF currency

## Demo Data Setup

**Create Demo Workspace:**
1. Add `is_demo=True` field to Workspace model
2. Create management command: `seed_theme_demo`
3. Seed beautiful products, collections, images
4. Create DeployedSite with demo subdomain
5. Theme preview connects to demo workspace

**Purpose:**
- Show theme with real-looking data
- Users see theme capabilities before purchase
- No empty/broken previews

## Documentation Requirements

**Each theme must include:**
1. README.md - Setup instructions, features, env variables
2. THEME_CAPABILITIES.md - GraphQL queries used, Puck sections, checkout flows
3. Changelog for version updates

---

**These rules ensure consistency, quality, and Cameroon market fit across all Huzilerz themes.**
