# Kiks Shoe Theme - GraphQL Operations & Data Flow

## 🎯 Theme Overview
**Kiks** - Simple, effective shoe storefront with WhatsApp-only checkout

## 📁 Page Structure & Sections

### 1. Home Page (`/`)

#### Sections:
- **Hero Banner** (Puck-editable)
  - Image, headline, CTA text
  - Links to target collection
  - *Operation*: Static content (Puck config)

- **Featured Collections** (User-selected)
  - User chooses 2-3 collections to feature
  - Grid layout with collection image, name, product count
  - *Operation*: `GET_COLLECTIONS_BY_SLUGS(slugs: [String!]!)`

- **Promo Banner** (Puck-editable)
  - Sale/deal messaging (e.g., "3 for X")
  - Links to "Sale" collection
  - *Operation*: Static content (Puck config)

- **Category Sidebar + Products**
  - Left: All collections as clickable categories
  - Right: Products from selected category
  - *Operations*:
    - `GET_ALL_COLLECTIONS` (for sidebar)
    - `GET_PRODUCTS_BY_COLLECTION(slug: String!, page: Int)` (for grid)

### 2. Products Page (`/products`)

#### Layout:
- **Filters Sidebar**
  - Collections filter (multi-select)
  - Price range
  - Size/color filters (if variants exist)
- **Product Grid**
  - Product cards with: image, name, price, compare_at_price, variant chips
  - Pagination (20 products per page)

#### Operations:
- `GET_PRODUCTS_PAGINATED(filters: ProductFilters!, page: Int!, limit: Int!)`
- `GET_COLLECTIONS_FOR_FILTERS` (for filter sidebar)

### 3. Product Details Page (`/products/[id]`)

#### Sections:
- **Product Gallery** (multiple images)
- **Product Info** (name, price, compare_at_price, description)
- **Variant Selector** (size, color chips)
- **Add to Cart** button
- **Related Products** (from same collection)

#### Operations:
- `GET_PRODUCT_DETAILS(id: ID!)` (with variants, images)
- `GET_RELATED_PRODUCTS(productId: ID!, collectionId: ID!)`

### 4. Cart Page (`/cart`)

#### Layout:
- **Cart Items List**
  - Product image, name, variant, quantity, price
  - Quantity adjuster, remove button
- **Cart Summary**
  - Subtotal, item count
  - Checkout CTA

#### Operations:
- `GET_CART(sessionId: String!)`
- `UPDATE_CART_ITEM(sessionId: String!, itemId: ID!, quantity: Int!)`
- `REMOVE_FROM_CART(sessionId: String!, itemId: ID!)`

### 5. Checkout Page (`/checkout`)

#### Layout:
- **Order Summary** (cart items review)
- **Customer Info Form**
  - Name, phone, address, notes
- **WhatsApp Order Button**

#### Operations:
- `CREATE_WHATSAPP_ORDER(input: WhatsAppOrderInput!)`

### 6. About Page (`/about`)
- Static content (Puck-editable)
- No GraphQL operations needed

## 🔧 GraphQL Operations Specification

### Queries

#### 1. Collection Operations
```graphql
# Get specific collections by slugs (for featured sections)
query GET_COLLECTIONS_BY_SLUGS($slugs: [String!]!) {
  collections(slugs: $slugs) {
    id
    name
    slug
    image
    productCount
  }
}

# Get all collections (for category sidebar)
query GET_ALL_COLLECTIONS {
  collections {
    id
    name
    slug
    productCount
  }
}
```

#### 2. Product Operations
```graphql
# Paginated products with filters
query GET_PRODUCTS_PAGINATED($filters: ProductFilters!, $page: Int!, $limit: Int!) {
  products(filters: $filters, page: $page, limit: $limit) {
    items {
      id
      name
      price
      compare_at_price
      images
      inStock
      variants {
        id
        size
        color
        inStock
      }
    }
    totalCount
    hasNextPage
  }
}

# Products by collection
query GET_PRODUCTS_BY_COLLECTION($slug: String!, $page: Int!) {
  collection(slug: $slug) {
    products(page: $page, limit: 20) {
      items {
        id
        name
        price
        compare_at_price
        images
        inStock
        variants {
          id
          size
          color
          inStock
        }
      }
      totalCount
    }
  }
}

# Single product details
query GET_PRODUCT_DETAILS($id: ID!) {
  product(id: $id) {
    id
    name
    description
    price
    compare_at_price
    images
    inStock
    variants {
      id
      size
      color
      sku
      price
      inStock
    }
    collection {
      id
      name
      slug
    }
  }
}

# Related products
query GET_RELATED_PRODUCTS($productId: ID!, $collectionId: ID!) {
  relatedProducts(productId: $productId, collectionId: $collectionId, limit: 4) {
    id
    name
    price
    compare_at_price
    images
  }
}
```

#### 3. Cart Operations
```graphql
# Get cart with items
query GET_CART($sessionId: String!) {
  cart(sessionId: $sessionId) {
    id
    items {
      id
      product {
        id
        name
        price
        images
      }
      variant {
        id
        size
        color
      }
      quantity
      totalPrice
    }
    subtotal
    itemCount
  }
}
```

### Mutations

#### 1. Cart Mutations
```graphql
# Create new cart session
mutation CREATE_CART($storeSlug: String!) {
  createCart(storeSlug: $storeSlug) {
    sessionId
    expiresAt
    cart {
      id
      items { id product { id name price images } quantity totalPrice }
      subtotal
      itemCount
    }
  }
}

# Add item to cart (with variant support)
mutation ADD_TO_CART($input: AddToCartInput!) {
  addToCart(input: $input) {
    cart {
      id
      items {
        id
        product { id name price images }
        variant { id size color }
        quantity
        totalPrice
      }
      subtotal
      itemCount
    }
  }
}

# Update cart item quantity
mutation UPDATE_CART_ITEM($sessionId: String!, $itemId: ID!, $quantity: Int!) {
  updateCartItem(sessionId: $sessionId, itemId: $itemId, quantity: $quantity) {
    cart {
      id
      items { id quantity totalPrice }
      subtotal
      itemCount
    }
  }
}

# Remove item from cart
mutation REMOVE_FROM_CART($sessionId: String!, $itemId: ID!) {
  removeFromCart(sessionId: $sessionId, itemId: $itemId) {
    cart {
      id
      items { id }
      subtotal
      itemCount
    }
  }
}
```

#### 2. Checkout Mutation
```graphql
# Create WhatsApp order
mutation CREATE_WHATSAPP_ORDER($input: WhatsAppOrderInput!) {
  createWhatsAppOrder(input: $input) {
    success
    orderId
    whatsappLink
    message
  }
}
```

## 🎨 UX Patterns & Data Flow

### Session Management
- **Auto-create session** on first page visit
- **7-day expiry** for cart sessions
- **Session ID** stored in localStorage

### Pagination Strategy
- **Homepage**: 20 products per collection section
- **Products page**: 20 products per page with load more/infinite scroll
- **Collections**: All collections loaded for sidebar

### Variant Handling
- **Product Grid**: Show variant chips if available
- **Product Details**: Full variant selector
- **Cart**: Store selected variant with each item

### Error Handling
- **GraphQL errors**: Show user-friendly messages
- **Network errors**: Retry mechanism with exponential backoff
- **Empty states**: "No products found" with filter suggestions

### Performance Optimizations
- **Query batching**: Combine related queries
- **Cache strategy**: Apollo cache with optimistic updates
- **Image optimization**: Next.js Image component with lazy loading

## 🚀 Next Steps
1. Backend team implements these GraphQL operations
2. Frontend team builds components following this spec
3. Puck config created for editable sections
4. Integration testing for all user flows

---
*This document serves as the single source of truth for Kiks theme data requirements.*