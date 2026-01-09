# HUZILERZ Platform Data Flow Architecture

## 📋 **Document Purpose**

This document describes how data flows through the HUZILERZ platform between three distinct systems:
1. **SaaS Backend** (Django API + Database) - Central brain
2. **Admin Dashboard** (React UI) - Store owner interface
3. **Deployed Themes** (React/Next.js) - Customer-facing storefront

---

## 🏗️ **System Architecture Overview**

### **The Three Independent Systems**

```
┌─────────────────────┐
│   ADMIN DASHBOARD   │ ← Store owner manages business
│   (React/Next.js)   │
└──────────┬──────────┘
           │ API Calls
           ↓
┌─────────────────────┐
│    SAAS BACKEND     │ ← Central source of truth
│  (Django + Postgres)│
└──────────┬──────────┘
           │ Webhooks + API
           ↓
┌─────────────────────┐
│  DEPLOYED THEMES    │ ← Customers browse & buy
│   (React/Next.js)   │
└─────────────────────┘
```

### **Key Principle: Backend-Centric Architecture**

**All systems communicate through the backend - NEVER directly with each other**

- Admin Dashboard → Backend → Database
- Deployed Theme → Backend → Database
- Backend → Webhook → Deployed Theme
- Backend → WebSocket/Polling → Admin Dashboard

---

## 🔄 **Data Flow Scenarios**

### **Scenario 1: Store Admin Adds a Product**

**Flow:**
1. Store owner opens Admin Dashboard
2. Navigates to Products page
3. Fills out product form (name, price, description, images)
4. Clicks "Save Product"

**What Happens:**

```
Admin Dashboard
    ↓ User clicks "Save"
    ↓ Frontend sends: POST /api/workspaces/{id}/store/products/
    ↓ {
    ↓   "name": "Blue T-Shirt",
    ↓   "price": 5000,
    ↓   "description": "...",
    ↓   "images": [...]
    ↓ }

SaaS Backend
    ↓ Receives API request
    ↓ Validates data
    ↓ Saves to Products table in database
    ↓ Creates SyncEvent record:
    ↓   - event_type: "product.created"
    ↓   - entity_id: "product-123"
    ↓   - workspace_id: "workspace-456"

Sync System Triggers
    ↓ Finds all deployed sites for workspace-456
    ↓ Creates WebhookDelivery for each site
    ↓ Sends webhook to deployed themes:
    ↓   POST https://user-store.huzilerz.com/api/sync/webhook
    ↓   {
    ↓     "event": "product.created",
    ↓     "product_id": "product-123",
    ↓     "workspace_id": "workspace-456"
    ↓   }

Deployed Theme
    ↓ Receives webhook at /api/sync/webhook endpoint
    ↓ Validates webhook signature
    ↓ Marks product cache as stale
    ↓ On next customer visit:
    ↓   - Fetches: GET /api/workspaces/456/store/products/
    ↓   - Updates display with new product
    ↓   - Customer sees "Blue T-Shirt" in catalog
```

**Backup (if webhook fails):**
- PollingState triggers every 1 minute
- Deployed theme checks for updates
- Fetches new products from API
- Updates display

---

### **Scenario 2: Customer Places an Order**

**Flow:**
1. Customer visits deployed theme storefront
2. Browses products, adds to cart
3. Proceeds to checkout
4. Completes payment

**What Happens:**

```
Deployed Theme (Storefront)
    ↓ Customer clicks "Place Order"
    ↓ Frontend sends: POST /api/workspaces/456/store/orders/
    ↓ {
    ↓   "customer_email": "customer@email.com",
    ↓   "items": [{"product_id": "product-123", "quantity": 2}],
    ↓   "total_amount": 10000
    ↓ }

SaaS Backend
    ↓ Receives order request
    ↓ Validates inventory availability
    ↓ Creates Order record in database
    ↓ Reduces product stock quantity
    ↓ Creates SyncEvent: "order.created"
    ↓ Creates ActivityEvent for analytics

Two Parallel Actions:

Action 1: Update Deployed Theme
    ↓ Sends webhook to theme:
    ↓   POST https://user-store.huzilerz.com/api/sync/webhook
    ↓   {
    ↓     "event": "order.created",
    ↓     "order_id": "order-789"
    ↓   }
    ↓ Theme shows order confirmation to customer

Action 2: Notify Store Admin
    ↓ WebSocket broadcast to Admin Dashboard:
    ↓   {
    ↓     "type": "new_order",
    ↓     "order": {...}
    ↓   }
    ↓ OR Admin Dashboard polls: GET /api/workspaces/456/store/orders/
    ↓ Admin sees "New Order" notification in real-time
```

**Result:**
- Customer sees order confirmation
- Store admin sees new order in dashboard
- Inventory automatically updated
- Analytics recorded

---

### **Scenario 3: Visitor Analytics Tracking**

**Flow:**
1. Customer lands on deployed theme
2. Page loads in browser

**What Happens:**

```
Deployed Theme Loads
    ↓ React theme includes tracking script (built-in)
    ↓ Script executes automatically:
    ↓   <Script src="/analytics/track.js" />
    ↓   <Script>
    ↓     HuzilerzAnalytics.init({
    ↓       workspaceId: process.env.NEXT_PUBLIC_WORKSPACE_ID,
    ↓       siteId: process.env.NEXT_PUBLIC_SITE_ID,
    ↓       endpoint: '/api/analytics/track'
    ↓     });
    ↓   </Script>

Tracking Events Sent
    ↓ Page view: POST /api/analytics/track/
    ↓ {
    ↓   "event": "page_view",
    ↓   "workspace_id": "456",
    ↓   "page": "/products",
    ↓   "timestamp": "2025-10-11T10:30:00Z",
    ↓   "session_id": "session-xyz",
    ↓   "referrer": "google.com"
    ↓ }

SaaS Backend
    ↓ Receives tracking event
    ↓ Saves to VisitorEvent table
    ↓ Aggregates for real-time analytics

Store Admin Dashboard
    ↓ Opens Analytics page
    ↓ Fetches: GET /api/workspaces/456/analytics/dashboard/?days=30
    ↓ Backend aggregates VisitorEvent data:
    ↓   - Total visitors: COUNT(DISTINCT session_id)
    ↓   - Page views: COUNT(*)
    ↓   - Top pages: GROUP BY page
    ↓ Dashboard displays charts and metrics
```

**Continuous Tracking:**
- Button click → `analytics.trackEvent('button_click', {button: 'buy'})`
- Add to cart → `analytics.trackEvent('add_to_cart', {product: '123'})`
- Scroll depth → `analytics.trackEvent('scroll', {depth: 75})`

All events go to backend, admin sees aggregated data in dashboard.

---

### **Scenario 4: Sync System Keeping Data Fresh**

**How Deployed Themes Stay Updated:**

**Method 1: Webhooks (Primary)**

```
Backend Change
    ↓ Any data update (product, price, stock)
    ↓ Creates SyncEvent
    ↓ Triggers WebhookDelivery

WebhookDelivery Process
    ↓ Attempts delivery: POST to deployed theme webhook endpoint
    ↓ Max 8 retries with exponential backoff
    ↓ Retry intervals: 1m, 2m, 4m, 8m, 16m, 32m, 1h, 2h
    ↓ Marks as delivered or failed

Deployed Theme Response
    ↓ Receives webhook
    ↓ Validates HMAC signature
    ↓ Invalidates relevant cache
    ↓ Revalidates data on next request
```

**Method 2: Polling (Backup)**

```
PollingState Scheduler
    ↓ Every 1 minute, checks for changes
    ↓ Queries: Last updated timestamp > last_poll_at
    ↓ If changes detected:
    ↓   - Deployed theme fetches fresh data
    ↓   - Updates cache/state
    ↓   - Marks poll as completed

Ensures:
    ↓ Even if all webhooks fail
    ↓ Maximum 1-minute data delay
    ↓ Deployed themes stay synchronized
```

---

## 🎨 **Theme Development Guidelines**

### **What YOU (Developer) Build Into React Themes**

When building React/Next.js themes for users to deploy, you must include:

#### **1. Analytics Tracking (Required for All Themes)**

**Location:** `_app.js` or `layout.tsx` (root layout)

**What to Include:**
- Tracking script initialization
- Page view tracking
- Event tracking utilities
- Session management

**Implementation Approach:**
- Include tracking library in theme dependencies
- Initialize with environment variables
- Automatically send page views
- Provide helper functions for custom events

**Environment Variables Expected:**
- `NEXT_PUBLIC_WORKSPACE_ID` - Identifies the workspace
- `NEXT_PUBLIC_SITE_ID` - Identifies the deployed site
- `NEXT_PUBLIC_API_URL` - Backend API endpoint

**What Gets Tracked:**
- Page views (automatic)
- Navigation events (automatic)
- Button clicks (manual via helper)
- Form submissions (manual via helper)
- E-commerce events (manual via helper)

---

#### **2. Sync Webhook Endpoint (Required for All Themes)**

**Location:** `pages/api/sync/webhook.js` or `app/api/sync/webhook/route.ts`

**Purpose:**
Receive real-time updates from backend when data changes

**What It Does:**
- Receives webhook POST requests from backend
- Validates HMAC signature for security
- Invalidates affected data caches
- Triggers revalidation of relevant pages

**Expected Webhook Format:**
```
POST /api/sync/webhook
Headers:
  X-Webhook-Signature: <HMAC signature>
  Content-Type: application/json

Body:
{
  "event_type": "product.created",
  "entity_id": "product-123",
  "workspace_id": "workspace-456",
  "timestamp": "2025-10-11T10:30:00Z"
}
```

**Webhook Events to Handle:**
- `product.created` - New product added
- `product.updated` - Product details changed
- `product.deleted` - Product removed
- `order.created` - New order placed
- `order.updated` - Order status changed
- `workspace.settings_updated` - Settings changed

**Security Requirements:**
- Must validate HMAC signature
- Reject unsigned webhooks
- Log all webhook attempts
- Rate limit webhook endpoint

---

#### **3. API Data Fetching (Required for All Themes)**

**Purpose:**
Fetch fresh data from backend to display to customers

**API Endpoints Themes Will Call:**

```
Products:
  GET /api/workspaces/{id}/store/products/
  GET /api/workspaces/{id}/store/products/{product_id}/

Orders:
  POST /api/workspaces/{id}/store/orders/
  GET /api/workspaces/{id}/store/orders/{order_id}/

Workspace Settings:
  GET /api/workspaces/{id}/settings/

Analytics (Theme sends events):
  POST /api/analytics/track/
```

**Caching Strategy:**
- Use Next.js ISR (Incremental Static Regeneration)
- Revalidate on webhook receipt
- Fallback to polling if webhooks fail
- Cache user session data client-side

---

#### **4. Environment Configuration (Required)**

**How Themes Receive Configuration:**

**At Build Time:**
- Backend creates `.env.production` file
- Includes workspace_id, site_id, API URLs
- Triggers Next.js build with these variables
- Variables baked into build output

**Environment Variables Provided:**
```
NEXT_PUBLIC_WORKSPACE_ID=workspace-456
NEXT_PUBLIC_SITE_ID=site-789
NEXT_PUBLIC_API_URL=https://api.huzilerz.com
WEBHOOK_SECRET=<secret-for-hmac-validation>
```

**How Themes Use Variables:**
- Tracking initialization
- API endpoint construction
- Webhook signature validation
- Feature toggles based on workspace settings

---

## 🔐 **Security & Data Integrity**

### **Webhook Security**

**HMAC Signature Validation:**

Backend Sends:
```
X-Webhook-Signature: sha256=abc123...
```

Theme Validates:
1. Extract webhook secret from environment
2. Compute HMAC of request body
3. Compare with signature header
4. Reject if mismatch

**Prevents:**
- Unauthorized data manipulation
- Replay attacks
- Man-in-the-middle attacks

---

### **API Authentication**

**For Public Endpoints (Deployed Themes):**
- No authentication required for viewing products
- Rate limiting per IP address
- CORS restrictions to deployed domain

**For Authenticated Actions (Orders):**
- Customer session tokens
- Workspace ID validation
- Order ownership verification

---

## 📊 **Analytics Data Collection**

### **What Gets Tracked**

**Session-Level Data:**
- Session ID (generated client-side)
- First visit timestamp
- Referrer source
- Device type and browser
- Geographic location (from IP)

**Page-Level Data:**
- Page URL
- Page title
- Time on page
- Scroll depth
- Exit page

**Event-Level Data:**
- Event name (button_click, add_to_cart, etc.)
- Event properties (product ID, amount, etc.)
- Event timestamp
- Event sequence in session

**E-commerce Data:**
- Product views
- Add to cart events
- Checkout initiated
- Purchase completed
- Order value and items

### **How Data Flows to Dashboard**

```
Customer Interaction
    ↓ Event triggered in deployed theme
    ↓ tracking.js sends: POST /api/analytics/track/
    ↓ Backend saves to VisitorEvent table

Store Admin Opens Dashboard
    ↓ Dashboard fetches: GET /api/analytics/dashboard/
    ↓ Backend aggregates:
    ↓   - SELECT COUNT(DISTINCT session_id) AS visitors
    ↓   - SELECT COUNT(*) AS page_views
    ↓   - SELECT page, COUNT(*) AS views GROUP BY page
    ↓   - SELECT DATE(created_at), COUNT(*) GROUP BY date
    ↓ Returns aggregated data

Dashboard Displays:
    ↓ Visitor count cards
    ↓ Traffic trends chart
    ↓ Top pages table
    ↓ Traffic sources breakdown
```

---

## 🔄 **Real-Time Updates**

### **How Admin Dashboard Stays Updated**

**Method 1: WebSocket (Preferred)**

```
Admin Dashboard Opens
    ↓ Connects: ws://api.huzilerz.com/ws/workspace/456/activity/
    ↓ Backend sends initial data
    ↓ Connection stays open

New Order Arrives
    ↓ Backend creates Order record
    ↓ WebSocket broadcast to workspace channel:
    ↓   {
    ↓     "type": "new_order",
    ↓     "order": {...}
    ↓   }
    ↓ Dashboard receives message
    ↓ Updates UI instantly
```

**Method 2: Polling (Fallback)**

```
Dashboard Component Mounts
    ↓ Sets interval: every 30 seconds
    ↓ Fetches: GET /api/workspaces/456/store/orders/?since=<last_fetch>
    ↓ If new orders found:
    ↓   - Update UI
    ↓   - Show notification
```

---

## 🎯 **Deployment Process**

### **How Themes Get Built and Deployed**

**Step 1: User Initiates Deployment**

```
Admin Dashboard
    ↓ User selects theme: "Modern E-commerce"
    ↓ User customizes via Puck editor:
    ↓   - Store name: "My Shop"
    ↓   - Brand colors: #FF5733
    ↓   - Logo image: uploaded
    ↓   - Product categories: enabled
    ↓ User clicks "Deploy"
```

**Step 2: Backend Prepares Deployment**

```
Backend Receives Deployment Request
    ↓ Validates subscription allows deployment
    ↓ Checks resource limits (storage, sites count)
    ↓ Creates deployment record
    ↓ Prepares environment variables:
    ↓   - NEXT_PUBLIC_WORKSPACE_ID=workspace-456
    ↓   - NEXT_PUBLIC_SITE_ID=site-new-123
    ↓   - NEXT_PUBLIC_API_URL=https://api.huzilerz.com
    ↓   - PUCK_DATA=<JSON with user customizations>
    ↓   - WEBHOOK_SECRET=<generated secret>
```

**Step 3: Next.js Build Triggered**

```
Build Process
    ↓ Clone React theme repository
    ↓ Install dependencies: npm install
    ↓ Write .env.production with variables
    ↓ Run build: npm run build
    ↓ Next.js processes:
    ↓   - Reads Puck data from env
    ↓   - Applies user customizations
    ↓   - Builds static pages
    ↓   - Optimizes images and assets
    ↓   - Generates .next/static output
```

**Step 4: Deploy to AWS**

```
Deployment Service
    ↓ Extracts .next/static files
    ↓ Uploads to S3 bucket (per subscription tier)
    ↓ Configures CloudFront distribution
    ↓ Sets up SSL certificate
    ↓ Registers webhook URL with backend
    ↓ Returns deployment URL
```

**Step 5: Site Goes Live**

```
Deployment Complete
    ↓ Site URL: https://my-shop.huzilerz.com
    ↓ SSL active
    ↓ Webhooks configured
    ↓ Analytics tracking active
    ↓ Sync system monitoring
    ↓ User notified of successful deployment
```

---

## 🔍 **Monitoring & Health Checks**

### **System Health Indicators**

**Deployed Theme Health:**
- Webhook delivery success rate > 95%
- API response time < 500ms
- Uptime percentage > 99.5%

**Sync System Health:**
- Webhook retry success rate
- Polling backup activation rate
- Maximum data staleness < 2 minutes

**Analytics System Health:**
- Event ingestion rate
- Data aggregation latency
- Dashboard query performance

**Admin Dashboard Health:**
- WebSocket connection stability
- API call success rate
- Real-time update latency

---

## 📝 **Data Consistency Guarantees**

### **What the Architecture Ensures**

**1. Single Source of Truth**
- All data stored in SaaS Backend database
- Admin Dashboard displays data from backend
- Deployed Themes fetch data from backend
- No local data storage conflicts

**2. Eventual Consistency**
- Webhooks provide near-instant updates (< 1 second)
- Polling ensures maximum 1-minute delay
- All clients eventually see same data

**3. Optimistic Updates**
- Admin Dashboard updates UI immediately
- Backend validation happens async
- UI reverts if backend rejects

**4. Conflict Resolution**
- Backend is authoritative
- Last-write-wins for conflicts
- Timestamps used for ordering

---

## ✅ **Summary: The Complete Loop**

```
1. Store Admin adds product in Dashboard
   → Dashboard sends to Backend
   → Backend saves to Database
   → Backend triggers Sync

2. Sync System notifies Deployed Themes
   → Webhook sent to theme
   → Theme invalidates cache
   → Theme ready to show new product

3. Customer visits Deployed Theme
   → Theme fetches products from Backend
   → Customer sees new product
   → Analytics tracks page view

4. Customer places order in Theme
   → Theme sends order to Backend
   → Backend saves order
   → Backend creates activity event

5. Admin Dashboard shows new order
   → WebSocket pushes notification
   → OR Dashboard polls for updates
   → Admin sees order in real-time

6. The loop continues...
```

---

## 🎯 **Key Takeaways**

**For Developers Building Themes:**
- Include tracking script in all themes
- Implement `/api/sync/webhook` endpoint
- Use environment variables for configuration
- Fetch data from backend APIs, never store locally
- Validate webhook signatures for security

**For Backend Development:**
- Backend is the single source of truth
- All data changes trigger sync events
- Provide both webhooks and polling
- Aggregate analytics data efficiently
- Support both WebSocket and polling for dashboard

**For System Architecture:**
- Three independent systems communicate via backend
- Webhooks for push, polling for backup
- Analytics collected at theme level, aggregated at backend
- Admin Dashboard and Deployed Themes are both clients
- Security through HMAC signatures and API authentication

---

*Last Updated: 2025-10-11*
*Maintainer: Platform Architecture Team*
