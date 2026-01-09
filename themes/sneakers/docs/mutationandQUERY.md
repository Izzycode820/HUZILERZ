 FOR THE FIRST THEME WE WILL ````
 ● Short answer: Create intentional collections in the admin      
  side that the theme expects.

  Reasoning:
  - Hardcode collection slugs like "featured", "just-added",     
  "sale" in the theme sections
  - When a merchant installs this theme, create those
  collections automatically (or provide setup instructions)      
  - This proves your GraphQL flow works end-to-end with
  predictable data
  - Theme works out-of-the-box with sample products

  Example:
  - Featured section → queries
  GET_PRODUCTS_BY_COLLECTION(slug: "featured", limit: 6)
  - Just Added section → queries
  GET_PRODUCTS_BY_COLLECTION(slug: "just-added", limit: 6)       
  - Categories section → queries GET_ALL_COLLECTIONS() for       
  sidebar

  Later when you add Puck, you make those slugs configurable.    
   But for proving the architecture, hardcoded expected
  collections is cleaner and faster to test.

  This mirrors how Shopify demo themes work - they expect        
  certain collections to exist and populate them during
  setup.

  Should we start converting these sections to use GraphQL       
  hooks?
  ````
 📄 PAGES & OPERATIONS LIST

  1. Home Page (/)

  Sections:
  - Hero Banner - Static (Puck content only)
  - Featured Collection - GET_PRODUCTS_BY_COLLECTION(slug, limit: 6)        
  - Sale Banner - Static (Puck content only)
  - Just Added Collection - GET_PRODUCTS_BY_COLLECTION(slug, limit: 6)      
  - Categories Section - GET_ALL_COLLECTIONS() +
  GET_PRODUCTS_BY_COLLECTION(slug, limit: 20)
  - Our Goals - Static (Puck content only)
  - Values - Static (Puck content only)

  2. Products Page (/products)

  - Filters - GET_COLLECTIONS_FOR_FILTERS()
  - Product Grid - GET_PRODUCTS_PAGINATED(filters, page, limit: 20)

  3. Product Details Page (/products/[id])

  - Product Info - GET_PRODUCT_DETAILS(id)
  - Related Products - GET_RELATED_PRODUCTS(productId, collectionId,        
  limit: 4)

  4. Cart Page (/cart)

  - Cart Items - GET_CART(sessionId)
  - Update Cart - UPDATE_CART_ITEM(sessionId, itemId, quantity)
  - Remove Item - REMOVE_FROM_CART(sessionId, itemId)

  5. Checkout Page (/checkout)

  - Order Summary - GET_CART(sessionId)
  - Create Order - CREATE_WHATSAPP_ORDER(input)

  6. Collection Page (/collections/[slug])

  - Collection Info - GET_COLLECTION_BY_SLUG(slug)
  - Products - GET_PRODUCTS_BY_COLLECTION(slug, page, limit: 20)

  7. Order Tracking Page (/track/[orderId])

  - Order Status - GET_ORDER_STATUS(orderId)

  ---
  🔧 GRAPHQL OPERATIONS SUMMARY

  QUERIES:

  1. GET_ALL_COLLECTIONS() - For sidebar/categories
  2. GET_COLLECTIONS_BY_SLUGS(slugs) - For featured sections
  3. GET_COLLECTIONS_FOR_FILTERS() - For product filters
  4. GET_PRODUCTS_PAGINATED(filters, page, limit) - Main product listing    
  5. GET_PRODUCTS_BY_COLLECTION(slug, page, limit) - Collection products    
  6. GET_PRODUCT_DETAILS(id) - Single product with variants
  7. GET_RELATED_PRODUCTS(productId, collectionId, limit) - Related
  products
  8. GET_CART(sessionId) - Cart with items
  9. GET_ORDER_STATUS(orderId) - Order tracking

  MUTATIONS:

  1. CREATE_CART(storeSlug) - Create new cart session
  2. ADD_TO_CART(input) - Add item to cart (with variants)
  3. UPDATE_CART_ITEM(sessionId, itemId, quantity) - Update quantity        
  4. REMOVE_FROM_CART(sessionId, itemId) - Remove item
  5. CREATE_WHATSAPP_ORDER(input) - Create WhatsApp order

  ---
  📁 REQUIRED PAGES:

  1. / - Home
  2. /products - All products
  3. /products/[id] - Product details
  4. /cart - Shopping cart
  5. /checkout - Checkout
  6. /collections/[slug] - Collection page
  7. /track/[orderId] - Order tracking
  8. /about - Static page (Puck only)