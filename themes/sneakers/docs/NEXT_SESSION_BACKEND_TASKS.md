

### 2. Demo Workspace Creation

**Location:** `backend/workspace/management/commands/create_demo_workspace.py`

**Requirements:**
- Create workspace with slug: `demo-store`
- Set `is_demo = True` flag
- Create DeployedSite: `demo-store.huzilerz.com`
- Link to Sneakers theme
- Admin-managed only (no user ownership)

**Command:**
```bash
python manage.py create_demo_workspace --theme=sneakers
```

**What it should do:**
1. Create Workspace (slug='demo-store', name='Demo Store', is_demo=True)
2. Create DeployedSite (subdomain='demo-store', workspace=demo_workspace)
3. Link theme configuration (theme='sneakers', version='1.0.0')
4. Create default Puck config from theme's puck.data.json
5. Set workspace status to 'active'

---

### 3. Demo Data Seeding - Comprehensive Product & Category Setup

**Location:** `backend/workspace/management/commands/seed_sneakers_demo.py`

**Requirements:**
- Seed 100 products
- Create 7 categories
- Distribute products across categories
- Add realistic product data (names, prices, descriptions, images)
- Support multiple variants per product
- Add sale prices for some products

**Categories to Create:**
1. **Men's Sneakers** (25 products)
2. **Women's Sneakers** (25 products)
3. **Kids' Sneakers** (15 products)
4. **Running Shoes** (15 products)
5. **Basketball Shoes** (10 products)
6. **Casual Sneakers** (10 products)
7. **Featured** (Best sellers - 10 products, can overlap with other categories)

**Command:**
```bash
python manage.py seed_sneakers_demo --products=100 --clear
```

**Flags:**
- `--products=N` - Number of products to create (default: 100)
- `--clear` - Clear existing demo data before seeding
- `--images` - Download/generate placeholder images

**Product Data Requirements:**
- Names: Realistic sneaker names (e.g., "Air Max Pro", "Ultra Boost Runner")
- Prices: Range from 15,000 XAF to 85,000 XAF
- Sale prices: 30% of products should have compareAtPrice (10-25% off)
- Stock: Random stock levels (0-50 units)
- Descriptions: Realistic bullet points (3-5 per product)
- Images: Use placeholder image service or real sneaker images
- Variants: 40% of products should have size/color variants

**Image Strategy:**
- Use `https://picsum.photos/800/800?random={product_id}` for quick placeholders
- OR use real sneaker images from Unsplash API
- Store in MediaUpload model with optimized/thumbnail versions

**Data Distribution:**
```python
CATEGORY_DISTRIBUTION = {
    'mens-sneakers': 25,
    'womens-sneakers': 25,
    'kids-sneakers': 15,
    'running-shoes': 15,
    'basketball-shoes': 10,
    'casual-sneakers': 10,
    'featured': 10,  # Best sellers
}
```

**Product Template Example:**
```python
{
    'name': 'Air Max Pro Running Shoe',
    'slug': 'air-max-pro-running-shoe',
    'description': '''
• Lightweight mesh upper for breathability
• Air cushioning for maximum comfort
• Durable rubber outsole
• Available in multiple colors
• Perfect for running and casual wear
    ''',
    'price': 45000,  # XAF
    'compareAtPrice': 55000,  # 18% off
    'inStock': True,
    'stockQuantity': 35,
    'brand': 'Nike',
    'categories': ['running-shoes', 'mens-sneakers'],
    'variants': [
        {'size': '40', 'color': 'Black', 'sku': 'AMP-BLK-40'},
        {'size': '41', 'color': 'Black', 'sku': 'AMP-BLK-41'},
        {'size': '40', 'color': 'White', 'sku': 'AMP-WHT-40'},
    ]
}
```

---

### 4. Dynamic Collection Selector for Puck

**Location:** `backend/workspace/storefront/graphql/queries/get_collections_for_puck.py`

**Requirements:**
- New GraphQL query: `collectionsForPuck`
- Returns simple list of collections (id, name, slug)
- Scoped to workspace
- Optimized for Puck editor (lightweight response)

**GraphQL Query:**
```graphql
query CollectionsForPuck($storeSlug: String!) {
  collectionsForPuck(storeSlug: $storeSlug) {
    id
    name
    slug
    productCount
  }
}
```

**Frontend Integration:** (Note for future)
- Create custom Puck field type
- Fetch collections via this query
- Render as dropdown in Puck sidebar
- Save selected slug to Puck config

---

### 5. Update Workspace Model

**Location:** `backend/workspace/models.py`

**Add Fields:**
```python
class Workspace(models.Model):
    # ... existing fields ...
    is_demo = models.BooleanField(default=False, db_index=True)
    demo_theme = models.CharField(max_length=100, blank=True, null=True)
    is_admin_managed = models.BooleanField(default=False)
```

**Purpose:**
- `is_demo`: Flag for demo workspaces
- `demo_theme`: Which theme this workspace demos
- `is_admin_managed`: Prevent user modifications

---



## 📋 Testing Checklist

After implementing backend tasks:

**Session Management:**
- [ ] Create guest session via GraphQL
- [ ] Session persists for 7 days
- [ ] Cart associates with session
- [ ] Expired sessions are cleaned up

**Demo Workspace:**
- [ ] `demo-store` workspace created successfully
- [ ] Accessible at `demo-store.huzilerz.com` (or localhost)
- [ ] Flagged as demo (`is_demo=True`)
- [ ] Admin-managed flag set

**Demo Data:**
- [ ] 100 products created
- [ ] 7 categories created
- [ ] Products distributed correctly
- [ ] Images loaded properly
- [ ] Variants work
- [ ] Sale prices display correctly
- [ ] Products queryable via GraphQL

**Collections for Puck:**
- [ ] Query returns all collections
- [ ] Scoped to correct workspace
- [ ] Lightweight response (no heavy fields)

---

## 🚀 Deployment Sequence

1. Run migrations (add `is_demo`, session model, etc.)
2. Create demo workspace: `python manage.py create_demo_workspace --theme=sneakers`
3. Seed demo data: `python manage.py seed_sneakers_demo --products=100`
4. Verify GraphQL endpoints work
5. Test session creation from frontend
6. Verify Puck config loads correctly

---

## 📝 Frontend Follow-up Tasks (After Backend Complete)

**Session Context Provider:**
```typescript
// src/contexts/SessionContext.tsx
- Auto-create session on mount if missing
- Store sessionId in localStorage
- Provide sessionId to all cart operations
```

**Custom Puck Collection Selector:**
```typescript
// src/lib/puck/fields/CollectionSelector.tsx
- Fetch collections via collectionsForPuck query
- Render dropdown in Puck sidebar
- Handle selection and save to config
```

---

## 🎯 Success Criteria

Backend is ready when:
1. ✅ Guest sessions create automatically
2. ✅ Demo workspace has 100 products across 7 categories
3. ✅ All products have images, variants, realistic data
4. ✅ Collections query works for Puck
5. ✅ Frontend can browse demo store with real data
6. ✅ Cart operations work with sessions
7. ✅ WhatsApp checkout creates real orders

---

## ⚠️ Important Notes

1. **Use XAF currency** - All prices in FCFA (Cameroon francs)
2. **Cameroon context** - Product names/descriptions should feel local
3. **Mobile-first data** - Ensure images are optimized for 3G
4. **Demo is read-only for users** - Only admins can modify demo workspace
5. **Session expiry** - Auto-cleanup cron job recommended

---

## 📌 Priority Order

1. **HIGH**: Session management (blocks cart/checkout)
2. **HIGH**: Demo workspace creation
3. **HIGH**: Demo data seeding (100 products)
4. **MEDIUM**: Collections for Puck query
5. **LOW**: Cleanup commands, optimization

---

**Next Session:** Start with session management, then demo workspace, then seeding script.
