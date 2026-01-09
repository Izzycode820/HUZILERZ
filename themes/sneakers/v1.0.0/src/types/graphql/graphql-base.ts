export type Maybe<T> = T | null;
export type InputMaybe<T> = T | null;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export interface Scalars {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  BigInt: { input: unknown; output: unknown; }
  DateTime: { input: string; output: string; }
  Decimal: { input: string; output: string; }
  JSONString: { input: unknown; output: unknown; }
  UUID: { input: string; output: string; }
}

/**
 * Add product to cart with variant support
 *
 * Performance: Uses select_for_update to prevent race conditions
 * Security: Validates stock availability
 */
export interface AddToCart {
  __typename: 'AddToCart';
  cart: Maybe<CartType>;
}

/** Input type for adding items to cart with variant support */
export interface AddToCartInput {
  productId: Scalars['ID']['input'];
  quantity: Scalars['Int']['input'];
  sessionId: Scalars['String']['input'];
  variantId?: InputMaybe<Scalars['ID']['input']>;
}

/** Input for address data */
export interface AddressInput {
  /** City */
  city?: InputMaybe<Scalars['String']['input']>;
  /** Address ID (for update/remove operations) */
  id?: InputMaybe<Scalars['Int']['input']>;
  /** Nearby landmark */
  landmark?: InputMaybe<Scalars['String']['input']>;
  /** Address label (e.g., Home, Work) */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Contact phone for this address */
  phone?: InputMaybe<Scalars['String']['input']>;
  /** Cameroon region */
  region?: InputMaybe<Scalars['String']['input']>;
  /** Street address */
  street?: InputMaybe<Scalars['String']['input']>;
}

/**
 * Input for address operations
 *
 * All fields are optional - provide only the operations you need
 */
export interface AddressOperationsInput {
  /** Add new address(es) */
  add?: InputMaybe<Array<InputMaybe<AddressInput>>>;
  /** Remove address by ID */
  remove?: InputMaybe<Scalars['Int']['input']>;
  /** Set default address by ID */
  setDefault?: InputMaybe<Scalars['Int']['input']>;
  /** Update existing address (requires id) */
  update?: InputMaybe<AddressInput>;
}

/**
 * Applied discount details for cart display
 *
 * Lightweight type showing only customer-facing discount info
 */
export interface AppliedDiscountType {
  __typename: 'AppliedDiscountType';
  code: Scalars['String']['output'];
  discountAmount: Maybe<Scalars['Decimal']['output']>;
  discountType: Scalars['String']['output'];
  itemDiscounts: Maybe<Array<Maybe<ItemDiscountType>>>;
  name: Scalars['String']['output'];
}

/**
 * Apply best automatic discount to cart
 *
 * Performance: Evaluates all automatic discounts and applies best one
 */
export interface ApplyAutomaticDiscounts {
  __typename: 'ApplyAutomaticDiscounts';
  cart: Maybe<CartType>;
  discountApplied: Maybe<Scalars['Boolean']['output']>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for applying automatic discounts */
export interface ApplyAutomaticDiscountsInput {
  sessionId: Scalars['String']['input'];
}

/**
 * Apply discount code to cart
 *
 * Performance: Atomic transaction with proper locking
 * Security: Validates discount before application
 */
export interface ApplyDiscountToCart {
  __typename: 'ApplyDiscountToCart';
  cart: Maybe<CartType>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for applying discount code to cart */
export interface ApplyDiscountToCartInput {
  discountCode: Scalars['String']['input'];
  sessionId: Scalars['String']['input'];
}

/**
 * Public payment method info for storefront checkout
 *
 * Security: Only exposes public info (no credentials)
 * Usage: Payment method selector in checkout
 */
export interface AvailablePaymentMethodType {
  __typename: 'AvailablePaymentMethodType';
  /** Merchant's checkout URL for redirect (Fapshi) */
  checkoutUrl: Maybe<Scalars['String']['output']>;
  /** Brief description of payment method */
  description: Maybe<Scalars['String']['output']>;
  /** Human-readable name (e.g., 'Mobile Money (MTN/Orange)') */
  displayName: Scalars['String']['output'];
  /** Provider identifier (e.g., 'fapshi') */
  provider: Scalars['String']['output'];
}

/**
 * Available shipping regions query result
 *
 * Returns list of regions with calculated shipping costs
 * for current cart products
 */
export interface AvailableShippingRegions {
  __typename: 'AvailableShippingRegions';
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  regions: Maybe<Array<Maybe<ShippingRegionType>>>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/**
 * GraphQL type for CartItem model
 *
 * Performance: Uses select_related for product optimization
 */
export interface CartItemType extends Node {
  __typename: 'CartItemType';
  addedAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Price at time of adding to cart */
  priceSnapshot: Scalars['Decimal']['output'];
  product: Maybe<ProductType>;
  /** Quantity of product in cart */
  quantity: Scalars['Int']['output'];
  totalPrice: Maybe<Scalars['Decimal']['output']>;
  updatedAt: Scalars['DateTime']['output'];
  variant: Maybe<ProductVariantType>;
}

/**
 * GraphQL type for Cart model
 *
 * Performance: Uses prefetch_related for items optimization
 */
export interface CartType extends Node {
  __typename: 'CartType';
  /** When cart was abandoned */
  abandonedAt: Maybe<Scalars['DateTime']['output']>;
  appliedDiscount: Maybe<AppliedDiscountType>;
  /** Cart currency */
  currency: Scalars['String']['output'];
  discountAmount: Maybe<Scalars['Decimal']['output']>;
  discountCode: Maybe<Scalars['String']['output']>;
  hasDiscount: Maybe<Scalars['Boolean']['output']>;
  id: Scalars['ID']['output'];
  /** Whether cart is active */
  isActive: Scalars['Boolean']['output'];
  isEmpty: Maybe<Scalars['Boolean']['output']>;
  isGuestCart: Maybe<Scalars['Boolean']['output']>;
  itemCount: Maybe<Scalars['Int']['output']>;
  items: Maybe<Array<Maybe<CartItemType>>>;
  /** Unique session identifier for guest carts */
  sessionId: Scalars['String']['output'];
  /** Cart subtotal (sum of item totals) */
  subtotal: Scalars['Decimal']['output'];
  total: Maybe<Scalars['Decimal']['output']>;
}

/**
 * GraphQL type for Category model - Collections in storefront
 *
 * Matches admin model structure exactly
 * Themes can query only the fields they need
 */
export interface CategoryType extends Node {
  __typename: 'CategoryType';
  /** Category banner image */
  categoryImage: Maybe<MediaUploadType>;
  createdAt: Scalars['DateTime']['output'];
  /** Collection description */
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** Whether collection is featured on homepage */
  isFeatured: Scalars['Boolean']['output'];
  /** Whether collection is visible to customers */
  isVisible: Scalars['Boolean']['output'];
  /** SEO meta description */
  metaDescription: Scalars['String']['output'];
  /** SEO meta title */
  metaTitle: Scalars['String']['output'];
  /** Collection name */
  name: Scalars['String']['output'];
  productCount: Maybe<Scalars['Int']['output']>;
  /** URL-friendly identifier */
  slug: Scalars['String']['output'];
  /** Manual sort order for admin drag-drop */
  sortOrder: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface CategoryTypeConnection {
  __typename: 'CategoryTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<CategoryTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `CategoryType` and its cursor. */
export interface CategoryTypeEdge {
  __typename: 'CategoryTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node: Maybe<CategoryType>;
}

/** Clear all items from cart */
export interface ClearCart {
  __typename: 'ClearCart';
  cart: Maybe<CartType>;
}

/** Input type for clearing cart */
export interface ClearCartInput {
  sessionId: Scalars['String']['input'];
}

/**
 * Create cash on delivery order mutation
 *
 * Performance: < 200ms with proper locking
 * Security: Comprehensive input validation
 * Reliability: Atomic transaction, no race conditions
 */
export interface CreateCodOrder {
  __typename: 'CreateCODOrder';
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  orderId: Maybe<Scalars['ID']['output']>;
  orderNumber: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for cash on delivery order */
export interface CreateCodOrderInput {
  customerInfo: CustomerInfoInput;
  sessionId: Scalars['String']['input'];
  shippingRegion: Scalars['String']['input'];
}

/**
 * Create new guest cart and session
 *
 * Security: Rate limited to prevent abuse
 * Performance: Atomic transaction
 */
export interface CreateCart {
  __typename: 'CreateCart';
  cart: Maybe<CartType>;
  expiresAt: Maybe<Scalars['DateTime']['output']>;
  sessionId: Maybe<Scalars['String']['output']>;
}

/**
 * Create payment order mutation (Fapshi, mobile money, etc)
 *
 * Performance: < 200ms with proper locking
 * Security: Comprehensive input validation
 * Reliability: Atomic transaction, no race conditions
 */
export interface CreatePaymentOrder {
  __typename: 'CreatePaymentOrder';
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  orderId: Maybe<Scalars['ID']['output']>;
  orderNumber: Maybe<Scalars['String']['output']>;
  paymentUrl: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for payment order (Fapshi, etc) */
export interface CreatePaymentOrderInput {
  customerInfo: CustomerInfoInput;
  paymentMethod: Scalars['String']['input'];
  sessionId: Scalars['String']['input'];
  shippingRegion: Scalars['String']['input'];
}

/**
 * Create WhatsApp order mutation
 *
 * Performance: < 200ms with proper locking
 * Security: Comprehensive input validation
 * Reliability: Atomic transaction, no race conditions
 */
export interface CreateWhatsAppOrder {
  __typename: 'CreateWhatsAppOrder';
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  orderId: Maybe<Scalars['ID']['output']>;
  orderNumber: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
  whatsappLink: Maybe<Scalars['String']['output']>;
}

/** Input type for WhatsApp order creation */
export interface CreateWhatsAppOrderInput {
  customerInfo: CustomerInfoInput;
  sessionId: Scalars['String']['input'];
  shippingRegion: Scalars['String']['input'];
  whatsappNumber: Scalars['String']['input'];
}

/**
 * Input type for customer information
 * Simplified for Cameroon context
 */
export interface CustomerInfoInput {
  address?: InputMaybe<Scalars['String']['input']>;
  city?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  phone?: InputMaybe<Scalars['String']['input']>;
  region?: InputMaybe<Scalars['String']['input']>;
}

/**
 * Customer login with password - Phone-first authentication
 *
 * Security: Password verification with check_password
 * Validates customer credentials and returns session token
 */
export interface CustomerLogin {
  __typename: 'CustomerLogin';
  customer: Maybe<Scalars['JSONString']['output']>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  sessionToken: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Customer logout - Invalidate session */
export interface CustomerLogout {
  __typename: 'CustomerLogout';
  message: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Customer signup with password - Phone-first approach
 *
 * Security: Password is hashed using Django's make_password
 * Creates customer account and returns session token
 */
export interface CustomerSignup {
  __typename: 'CustomerSignup';
  customer: Maybe<Scalars['JSONString']['output']>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  sessionToken: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Result type for discount code validation */
export interface DiscountValidationType {
  __typename: 'DiscountValidationType';
  discountCode: Maybe<Scalars['String']['output']>;
  discountName: Maybe<Scalars['String']['output']>;
  discountType: Maybe<Scalars['String']['output']>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  valid: Scalars['Boolean']['output'];
}

/**
 * Get customer order summary
 *
 * Returns order statistics (total orders, total spent, etc.)
 */
export interface GetCustomerOrders {
  __typename: 'GetCustomerOrders';
  error: Maybe<Scalars['String']['output']>;
  orderSummary: Maybe<Scalars['JSONString']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Get customer profile data
 *
 * Returns complete profile with addresses, preferences, and order stats
 */
export interface GetCustomerProfile {
  __typename: 'GetCustomerProfile';
  error: Maybe<Scalars['String']['output']>;
  profile: Maybe<Scalars['JSONString']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Image type with WebP support and multiple variations
 *
 * Provides optimized images for different use cases:
 * - url: Original uploaded image
 * - optimized/optimized_webp: 1200px for product pages
 * - thumbnail/thumbnail_webp: 300px for product cards
 * - tiny/tiny_webp: 150px for list views
 *
 * Frontend usage:
 * - Storefront: Use optimized_webp (best performance)
 * - Product cards: Use thumbnail_webp
 * - List views: Use tiny_webp
 */
export interface ImageType {
  __typename: 'ImageType';
  /** Original image height in pixels */
  height: Maybe<Scalars['Int']['output']>;
  /** Upload ID */
  id: Maybe<Scalars['ID']['output']>;
  /** Optimized JPEG (1200px, fallback) */
  optimized: Maybe<Scalars['String']['output']>;
  /** Optimized WebP (1200px, 25-34% smaller) */
  optimizedWebp: Maybe<Scalars['String']['output']>;
  /** Thumbnail JPEG (300px, fallback) */
  thumbnail: Maybe<Scalars['String']['output']>;
  /** Thumbnail WebP (300px, 25-34% smaller) */
  thumbnailWebp: Maybe<Scalars['String']['output']>;
  /** Tiny JPEG (150px, fallback) */
  tiny: Maybe<Scalars['String']['output']>;
  /** Tiny WebP (150px, 25-34% smaller) */
  tinyWebp: Maybe<Scalars['String']['output']>;
  /** Original image URL */
  url: Maybe<Scalars['String']['output']>;
  /** Original image width in pixels */
  width: Maybe<Scalars['Int']['output']>;
}

/** Individual item discount breakdown for buy_x_get_y and amount_off_product */
export interface ItemDiscountType {
  __typename: 'ItemDiscountType';
  discountAmount: Scalars['Decimal']['output'];
  originalPrice: Scalars['Decimal']['output'];
  productId: Scalars['ID']['output'];
  productName: Scalars['String']['output'];
  quantity: Maybe<Scalars['Int']['output']>;
  quantityDiscounted: Maybe<Scalars['Int']['output']>;
}

/**
 * Media Upload GraphQL Type - URL-focused design
 *
 * Returns:
 * - Direct URLs (not nested objects)
 * - Minimal metadata
 * - Optimized for frontend consumption
 */
export interface MediaUploadType {
  __typename: 'MediaUploadType';
  /** File size in bytes */
  fileSize: Scalars['BigInt']['output'];
  /** Image/video height in pixels */
  height: Maybe<Scalars['Int']['output']>;
  id: Scalars['UUID']['output'];
  /** Type of media (image, video, 3D model) */
  mediaType: MedialibMediaUploadMediaTypeChoices;
  /** Additional metadata (format, duration for videos, etc.) */
  metadata: Scalars['JSONString']['output'];
  /** MIME type (e.g., image/jpeg, video/mp4) */
  mimeType: Scalars['String']['output'];
  /** Optimized version URL (for images) */
  optimizedUrl: Maybe<Scalars['String']['output']>;
  /** Original filename from upload */
  originalFilename: Scalars['String']['output'];
  /** Processing status */
  status: MedialibMediaUploadStatusChoices;
  /** Thumbnail URL (for images/videos) */
  thumbnailUrl: Maybe<Scalars['String']['output']>;
  uploadedAt: Scalars['DateTime']['output'];
  /** Primary media URL (CDN) */
  url: Maybe<Scalars['String']['output']>;
  /** Image/video width in pixels */
  width: Maybe<Scalars['Int']['output']>;
}

/** An enumeration. */
export enum MedialibMediaUploadMediaTypeChoices {
  /** 3D Model */
  A_3DModel = 'A_3D_MODEL',
  /** Document */
  Document = 'DOCUMENT',
  /** Image */
  Image = 'IMAGE',
  /** Video */
  Video = 'VIDEO'
}

/** An enumeration. */
export enum MedialibMediaUploadStatusChoices {
  /** Completed */
  Completed = 'COMPLETED',
  /** Failed */
  Failed = 'FAILED',
  /** Orphaned */
  Orphaned = 'ORPHANED',
  /** Pending */
  Pending = 'PENDING',
  /** Processing */
  Processing = 'PROCESSING'
}

/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface Mutation {
  __typename: 'Mutation';
  /**
   * Add product to cart with variant support
   *
   * Performance: Uses select_for_update to prevent race conditions
   * Security: Validates stock availability
   */
  addToCart: Maybe<AddToCart>;
  /**
   * Apply best automatic discount to cart
   *
   * Performance: Evaluates all automatic discounts and applies best one
   */
  applyAutomaticDiscounts: Maybe<ApplyAutomaticDiscounts>;
  /**
   * Apply discount code to cart
   *
   * Performance: Atomic transaction with proper locking
   * Security: Validates discount before application
   */
  applyDiscountToCart: Maybe<ApplyDiscountToCart>;
  /** Clear all items from cart */
  clearCart: Maybe<ClearCart>;
  /**
   * Create new guest cart and session
   *
   * Security: Rate limited to prevent abuse
   * Performance: Atomic transaction
   */
  createCart: Maybe<CreateCart>;
  /**
   * Create cash on delivery order mutation
   *
   * Performance: < 200ms with proper locking
   * Security: Comprehensive input validation
   * Reliability: Atomic transaction, no race conditions
   */
  createCodOrder: Maybe<CreateCodOrder>;
  /**
   * Create payment order mutation (Fapshi, mobile money, etc)
   *
   * Performance: < 200ms with proper locking
   * Security: Comprehensive input validation
   * Reliability: Atomic transaction, no race conditions
   */
  createPaymentOrder: Maybe<CreatePaymentOrder>;
  /**
   * Create WhatsApp order mutation
   *
   * Performance: < 200ms with proper locking
   * Security: Comprehensive input validation
   * Reliability: Atomic transaction, no race conditions
   */
  createWhatsappOrder: Maybe<CreateWhatsAppOrder>;
  /**
   * Customer login with password - Phone-first authentication
   *
   * Security: Password verification with check_password
   * Validates customer credentials and returns session token
   */
  customerLogin: Maybe<CustomerLogin>;
  /** Customer logout - Invalidate session */
  customerLogout: Maybe<CustomerLogout>;
  /**
   * Customer signup with password - Phone-first approach
   *
   * Security: Password is hashed using Django's make_password
   * Creates customer account and returns session token
   */
  customerSignup: Maybe<CustomerSignup>;
  /**
   * Get customer order summary
   *
   * Returns order statistics (total orders, total spent, etc.)
   */
  getCustomerOrders: Maybe<GetCustomerOrders>;
  /**
   * Get customer profile data
   *
   * Returns complete profile with addresses, preferences, and order stats
   */
  getCustomerProfile: Maybe<GetCustomerProfile>;
  /**
   * Remove discount from cart
   *
   * Performance: Atomic transaction
   */
  removeDiscountFromCart: Maybe<RemoveDiscountFromCart>;
  /** Remove item from cart with variant support */
  removeFromCart: Maybe<RemoveFromCart>;
  /** Update cart item quantity with variant support */
  updateCartItem: Maybe<UpdateCartItem>;
  /**
   * Consolidated profile update mutation
   *
   * Updates profile, addresses, and preferences in ONE operation
   * All parameters are optional - update only what you need
   *
   * Cameroon Market: Phone-first, mobile-optimized, single atomic operation
   */
  updateCustomerProfile: Maybe<UpdateCustomerProfile>;
  /**
   * Validate customer session token
   *
   * Used to check if session is still valid and get customer data
   */
  validateCustomerSession: Maybe<ValidateCustomerSession>;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationAddToCartArgs {
  input: AddToCartInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationApplyAutomaticDiscountsArgs {
  input: ApplyAutomaticDiscountsInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationApplyDiscountToCartArgs {
  input: ApplyDiscountToCartInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationClearCartArgs {
  input: ClearCartInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationCreateCodOrderArgs {
  input: CreateCodOrderInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationCreatePaymentOrderArgs {
  input: CreatePaymentOrderInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationCreateWhatsappOrderArgs {
  input: CreateWhatsAppOrderInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationCustomerLoginArgs {
  password: Scalars['String']['input'];
  phone: Scalars['String']['input'];
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationCustomerLogoutArgs {
  sessionToken: Scalars['String']['input'];
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationCustomerSignupArgs {
  city?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  password: Scalars['String']['input'];
  phone: Scalars['String']['input'];
  region?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationGetCustomerOrdersArgs {
  customerId: Scalars['String']['input'];
  sessionToken: Scalars['String']['input'];
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationGetCustomerProfileArgs {
  customerId: Scalars['String']['input'];
  sessionToken: Scalars['String']['input'];
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationRemoveDiscountFromCartArgs {
  input: RemoveDiscountFromCartInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationRemoveFromCartArgs {
  input: RemoveFromCartInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationUpdateCartItemArgs {
  input: UpdateCartItemInput;
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationUpdateCustomerProfileArgs {
  addressesData?: InputMaybe<AddressOperationsInput>;
  customerId: Scalars['String']['input'];
  preferencesData?: InputMaybe<PreferencesInput>;
  profileData?: InputMaybe<ProfileDataInput>;
  sessionToken: Scalars['String']['input'];
}


/**
 * Root Mutation type
 *
 * Combines all mutation fields from different modules:
 * - CartMutations: Shopping cart operations
 * - CheckoutMutations: Checkout and order creation
 * - CustomerAuthMutations: Customer signup/login/logout
 * - CustomerProfileMutations: Customer profile management
 * - DiscountMutations: Discount application and removal
 */
export interface MutationValidateCustomerSessionArgs {
  sessionToken: Scalars['String']['input'];
}

/** An object with an ID */
export interface Node {
  /** The ID of the object */
  id: Scalars['ID']['output'];
}

/**
 * Limited order info for public tracking
 * Used for order tracking without authentication
 */
export interface OrderTrackingType {
  __typename: 'OrderTrackingType';
  createdAt: Maybe<Scalars['DateTime']['output']>;
  estimatedDelivery: Maybe<Scalars['DateTime']['output']>;
  orderNumber: Maybe<Scalars['String']['output']>;
  status: Maybe<Scalars['String']['output']>;
  totalAmount: Maybe<Scalars['Decimal']['output']>;
  trackingNumber: Maybe<Scalars['String']['output']>;
}

/**
 * GraphQL type for Package model
 *
 * Features:
 * - Simple shipping package configuration
 * - Region-based fees stored in JSON (multiple regions per package)
 * - Cameroon-specific flexibility
 */
export interface PackageType extends Node {
  __typename: 'PackageType';
  createdAt: Scalars['DateTime']['output'];
  /** Estimated delivery time (e.g., '1-2', '3-5 days') */
  estimatedDays: Scalars['String']['output'];
  fullDescription: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Whether this package is active */
  isActive: Scalars['Boolean']['output'];
  /** Shipping method (e.g., 'Car', 'Bike', 'Moto-taxi') */
  method: Scalars['String']['output'];
  /** Package name (e.g., 'Buea Car Shipping') */
  name: Scalars['String']['output'];
  /** Type of package */
  packageType: WorkspaceStorePackagePackageTypeChoices;
  productCount: Maybe<Scalars['Int']['output']>;
  /** Shipping fees by region in XAF format: {'yaounde': 1500, 'douala': 1200, 'buea': 1000} */
  regionFees: Scalars['JSONString']['output'];
  /** Package size */
  size: WorkspaceStorePackageSizeChoices;
  updatedAt: Scalars['DateTime']['output'];
  /** Use this package as default fallback for products without shipping */
  useAsDefault: Scalars['Boolean']['output'];
  /** Weight capacity in kg */
  weight: Maybe<Scalars['Decimal']['output']>;
}

/** The Relay compliant `PageInfo` type, containing data necessary to paginate this connection. */
export interface PageInfo {
  __typename: 'PageInfo';
  /** When paginating forwards, the cursor to continue. */
  endCursor: Maybe<Scalars['String']['output']>;
  /** When paginating forwards, are there more items? */
  hasNextPage: Scalars['Boolean']['output'];
  /** When paginating backwards, are there more items? */
  hasPreviousPage: Scalars['Boolean']['output'];
  /** When paginating backwards, the cursor to continue. */
  startCursor: Maybe<Scalars['String']['output']>;
}

/** Input for communication preferences */
export interface PreferencesInput {
  /** Receive email notifications */
  emailNotifications?: InputMaybe<Scalars['Boolean']['input']>;
  /** Receive SMS notifications */
  smsNotifications?: InputMaybe<Scalars['Boolean']['input']>;
  /** Receive WhatsApp notifications */
  whatsappNotifications?: InputMaybe<Scalars['Boolean']['input']>;
}

/**
 * Comprehensive Product type matching admin model structure
 *
 * Themes can query only the fields they need
 * All fields match admin model exactly
 */
export interface ProductType extends Node {
  __typename: 'ProductType';
  /** Allow orders when out of stock */
  allowBackorders: Scalars['Boolean']['output'];
  /** Product barcode */
  barcode: Scalars['String']['output'];
  /** Product brand */
  brand: Scalars['String']['output'];
  /** Primary product category */
  category: Maybe<CategoryType>;
  /** Original price for discounts */
  compareAtPrice: Maybe<Scalars['Decimal']['output']>;
  /** Cost/wholesale price */
  costPrice: Maybe<Scalars['Decimal']['output']>;
  createdAt: Scalars['DateTime']['output'];
  /** Product description */
  description: Scalars['String']['output'];
  /** Whether product has variants */
  hasVariants: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  inStock: Maybe<Scalars['Boolean']['output']>;
  /** Inventory health status */
  inventoryHealth: WorkspaceStoreProductInventoryHealthChoices;
  /** Available stock quantity */
  inventoryQuantity: Scalars['Int']['output'];
  isOnSale: Maybe<Scalars['Boolean']['output']>;
  /** Uploaded images for this product in upload order */
  mediaUploads: Maybe<Array<Maybe<ImageType>>>;
  /** SEO meta description */
  metaDescription: Scalars['String']['output'];
  /** SEO meta title */
  metaTitle: Scalars['String']['output'];
  /** Product name */
  name: Scalars['String']['output'];
  /** Product options for variants (e.g., [{'name': 'Size', 'values': ['S', 'M', 'L']}]) */
  options: Scalars['JSONString']['output'];
  /** Shipping package for this product (optional - falls back to default if not set) */
  package: Maybe<PackageType>;
  /** Selling price (required) */
  price: Scalars['Decimal']['output'];
  /** Type of product */
  productType: WorkspaceStoreProductProductTypeChoices;
  /** When product was published */
  publishedAt: Maybe<Scalars['DateTime']['output']>;
  /** Needs shipping */
  requiresShipping: Scalars['Boolean']['output'];
  salePercentage: Maybe<Scalars['Float']['output']>;
  /** Stock Keeping Unit */
  sku: Scalars['String']['output'];
  /** URL-friendly identifier */
  slug: Scalars['String']['output'];
  /** Product status */
  status: WorkspaceStoreProductStatusChoices;
  stockStatus: Maybe<Scalars['String']['output']>;
  /** Product tags for search */
  tags: Scalars['JSONString']['output'];
  /** Whether to track inventory */
  trackInventory: Scalars['Boolean']['output'];
  updatedAt: Scalars['DateTime']['output'];
  variantOptions: Maybe<Scalars['JSONString']['output']>;
  variants: Maybe<Array<Maybe<ProductVariantType>>>;
  /** Product vendor */
  vendor: Scalars['String']['output'];
  /** Product weight (kg) */
  weight: Maybe<Scalars['Decimal']['output']>;
}

export interface ProductTypeConnection {
  __typename: 'ProductTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<ProductTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `ProductType` and its cursor. */
export interface ProductTypeEdge {
  __typename: 'ProductTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node: Maybe<ProductType>;
}

/**
 * Comprehensive ProductVariant type matching admin model structure
 *
 * Used when theme supports variant selection
 * All fields match admin model exactly
 */
export interface ProductVariantType extends Node {
  __typename: 'ProductVariantType';
  /** Barcode (ISBN, UPC, GTIN, etc.) */
  barcode: Maybe<Scalars['String']['output']>;
  /** Compare at price (overrides product compare_at_price) */
  compareAtPrice: Maybe<Scalars['Decimal']['output']>;
  /** Cost per item (overrides product cost_price) */
  costPrice: Maybe<Scalars['Decimal']['output']>;
  createdAt: Scalars['DateTime']['output'];
  displayPrice: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  inStock: Maybe<Scalars['Boolean']['output']>;
  /** Available for purchase */
  isActive: Scalars['Boolean']['output'];
  /** Option (e.g., Size, Color) */
  option1: Maybe<Scalars['String']['output']>;
  /** Additional option */
  option2: Maybe<Scalars['String']['output']>;
  /** Third option (if needed) */
  option3: Maybe<Scalars['String']['output']>;
  /** Display position */
  position: Scalars['Int']['output'];
  /** Price (overrides product price) */
  price: Maybe<Scalars['Decimal']['output']>;
  /** Stock Keeping Unit */
  sku: Scalars['String']['output'];
  totalStock: Maybe<Scalars['Int']['output']>;
  /** Track inventory for this variant */
  trackInventory: Scalars['Boolean']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

/** Input for basic profile data */
export interface ProfileDataInput {
  /** Customer city */
  city?: InputMaybe<Scalars['String']['input']>;
  /** Customer type (individual, business, etc.) */
  customerType?: InputMaybe<Scalars['String']['input']>;
  /** Customer email (optional) */
  email?: InputMaybe<Scalars['String']['input']>;
  /** Customer name */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Cameroon region */
  region?: InputMaybe<Scalars['String']['input']>;
}

/** Response type for resolved puck data query */
export interface PuckDataResolvedResponse {
  __typename: 'PuckDataResolvedResponse';
  data: Maybe<Scalars['JSONString']['output']>;
  message: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface Query {
  __typename: 'Query';
  /** Get available payment methods for checkout */
  availablePaymentMethods: Maybe<Array<Maybe<AvailablePaymentMethodType>>>;
  /** Get available shipping regions with prices for current cart */
  availableShippingRegions: Maybe<AvailableShippingRegions>;
  /** Get cart by session ID */
  cart: Maybe<CartType>;
  /** Browse categories with filtering and pagination */
  categories: Maybe<CategoryTypeConnection>;
  /** Get specific categories by their slugs */
  categoriesBySlugs: Maybe<Array<Maybe<CategoryType>>>;
  /** Get single category details by slug */
  category: Maybe<CategoryType>;
  /** Get single category details by ID */
  categoryById: Maybe<CategoryType>;
  /** Get count of categories matching criteria */
  categoryCount: Maybe<Scalars['Int']['output']>;
  /** Get products from a specific category with filtering */
  categoryProducts: Maybe<Array<Maybe<ProductType>>>;
  /** Get featured categories for homepage */
  featuredCategories: Maybe<Array<Maybe<CategoryType>>>;
  /** Get newest products */
  newProducts: Maybe<Array<Maybe<ProductType>>>;
  /** Get single product details by slug with variants */
  product: Maybe<ProductType>;
  /** Get single product details by ID */
  productById: Maybe<ProductType>;
  /** Get count of products matching criteria */
  productCount: Maybe<Scalars['Int']['output']>;
  /** Browse published products with filtering and pagination */
  products: Maybe<ProductTypeConnection>;
  /** Get products currently on sale */
  productsOnSale: Maybe<Array<Maybe<ProductType>>>;
  /** Fetch active theme's puck data with resolved section data for storefront (uses X-Store-Hostname header for workspace identification) */
  publicPuckDataResolved: Maybe<PuckDataResolvedResponse>;
  /** Get products related to a specific product */
  relatedProducts: Maybe<Array<Maybe<ProductType>>>;
  /** Search products by query string */
  searchProducts: Maybe<Array<Maybe<ProductType>>>;
  /** Get public store settings (name, WhatsApp, currency, etc.) */
  storeSettings: Maybe<StoreSettingsType>;
  /** Track order by order number + phone (secure, no authentication required) */
  trackOrder: Maybe<OrderTrackingType>;
  /** Validate discount code before applying to cart */
  validateDiscountCode: Maybe<DiscountValidationType>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryAvailableShippingRegionsArgs {
  sessionId: Scalars['String']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCartArgs {
  sessionId: Scalars['String']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCategoriesArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isFeatured?: InputMaybe<Scalars['Boolean']['input']>;
  isVisible?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCategoriesBySlugsArgs {
  slugs: Array<InputMaybe<Scalars['String']['input']>>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCategoryArgs {
  categorySlug: Scalars['String']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCategoryByIdArgs {
  categoryId: Scalars['ID']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCategoryCountArgs {
  isVisible?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryCategoryProductsArgs {
  categorySlug: Scalars['String']['input'];
  inStock?: InputMaybe<Scalars['Boolean']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  maxPrice?: InputMaybe<Scalars['Float']['input']>;
  minPrice?: InputMaybe<Scalars['Float']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryFeaturedCategoriesArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryNewProductsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryProductArgs {
  productSlug: Scalars['String']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryProductByIdArgs {
  productId: Scalars['ID']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryProductCountArgs {
  categorySlug?: InputMaybe<Scalars['String']['input']>;
  inStock?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryProductsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  brand?: InputMaybe<Scalars['String']['input']>;
  brand_Icontains?: InputMaybe<Scalars['String']['input']>;
  category?: InputMaybe<Scalars['ID']['input']>;
  categorySlug?: InputMaybe<Scalars['String']['input']>;
  createdAt?: InputMaybe<Scalars['DateTime']['input']>;
  createdAt_Gte?: InputMaybe<Scalars['DateTime']['input']>;
  createdAt_Lte?: InputMaybe<Scalars['DateTime']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  inStock?: InputMaybe<Scalars['Boolean']['input']>;
  inventoryHealth?: InputMaybe<WorkspaceStoreProductInventoryHealthChoices>;
  inventoryQuantity?: InputMaybe<Scalars['Int']['input']>;
  inventoryQuantity_Gte?: InputMaybe<Scalars['Int']['input']>;
  inventoryQuantity_Lte?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  maxPrice?: InputMaybe<Scalars['Float']['input']>;
  minPrice?: InputMaybe<Scalars['Float']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  price?: InputMaybe<Scalars['Decimal']['input']>;
  price_Gte?: InputMaybe<Scalars['Decimal']['input']>;
  price_Lte?: InputMaybe<Scalars['Decimal']['input']>;
  productType?: InputMaybe<WorkspaceStoreProductProductTypeChoices>;
  requiresShipping?: InputMaybe<Scalars['Boolean']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
  sku_Icontains?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<WorkspaceStoreProductStatusChoices>;
  vendor_Icontains?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryProductsOnSaleArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryRelatedProductsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
  productId: Scalars['ID']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QuerySearchProductsArgs {
  categorySlug?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  query: Scalars['String']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryTrackOrderArgs {
  orderNumber: Scalars['String']['input'];
  phone: Scalars['String']['input'];
}


/**
 * Root Query type
 *
 * Combines all query fields from different modules:
 * - ProductQueries: Comprehensive product operations
 * - CategoryQueries: Category operations
 * - CartQueries: Shopping cart operations
 * - OrderQueries: Order management operations
 * - PuckDataResolvedQuery: Theme puck data with resolved section data
 * - DiscountQueries: Discount validation and info
 * - CheckoutQueries: Checkout operations (shipping, tracking)
 * - StoreSettingsQueries: Public store settings (WhatsApp, etc.)
 * - PaymentQueries: Available payment methods
 */
export interface QueryValidateDiscountCodeArgs {
  discountCode: Scalars['String']['input'];
  sessionId: Scalars['String']['input'];
}

/**
 * Remove discount from cart
 *
 * Performance: Atomic transaction
 */
export interface RemoveDiscountFromCart {
  __typename: 'RemoveDiscountFromCart';
  cart: Maybe<CartType>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for removing discount from cart */
export interface RemoveDiscountFromCartInput {
  sessionId: Scalars['String']['input'];
}

/** Remove item from cart with variant support */
export interface RemoveFromCart {
  __typename: 'RemoveFromCart';
  cart: Maybe<CartType>;
}

/** Input type for removing items from cart with variant support */
export interface RemoveFromCartInput {
  productId: Scalars['ID']['input'];
  sessionId: Scalars['String']['input'];
  variantId?: InputMaybe<Scalars['ID']['input']>;
}

/**
 * Shipping region with pricing information
 *
 * Used by frontend to display shipping options dropdown
 * Each region shows total shipping cost and estimated delivery
 */
export interface ShippingRegionType {
  __typename: 'ShippingRegionType';
  /** Estimated delivery time (e.g., '2-3', '3-5 days') */
  estimatedDays: Maybe<Scalars['String']['output']>;
  /** Region name (e.g., 'buea', 'yaounde') */
  name: Maybe<Scalars['String']['output']>;
  /** Total shipping cost for this region in XAF */
  price: Maybe<Scalars['Decimal']['output']>;
}

/**
 * Public store settings for storefront display
 *
 * Security: Only exposes customer-facing settings
 * Usage: Header, footer, checkout, contact pages
 */
export interface StoreSettingsType {
  __typename: 'StoreSettingsType';
  /** Store currency code (e.g., XAF) */
  currency: Maybe<Scalars['String']['output']>;
  /** Store phone number */
  phoneNumber: Maybe<Scalars['String']['output']>;
  /** Store tagline or description */
  storeDescription: Maybe<Scalars['String']['output']>;
  /** Display name of the store */
  storeName: Maybe<Scalars['String']['output']>;
  /** Customer support email */
  supportEmail: Maybe<Scalars['String']['output']>;
  /** WhatsApp number for orders (e.g., 237699999999) */
  whatsappNumber: Maybe<Scalars['String']['output']>;
}

/** Update cart item quantity with variant support */
export interface UpdateCartItem {
  __typename: 'UpdateCartItem';
  cart: Maybe<CartType>;
}

/** Input type for updating cart item quantities with variant support */
export interface UpdateCartItemInput {
  productId: Scalars['ID']['input'];
  quantity: Scalars['Int']['input'];
  sessionId: Scalars['String']['input'];
  variantId?: InputMaybe<Scalars['ID']['input']>;
}

/**
 * Consolidated profile update mutation
 *
 * Updates profile, addresses, and preferences in ONE operation
 * All parameters are optional - update only what you need
 *
 * Cameroon Market: Phone-first, mobile-optimized, single atomic operation
 */
export interface UpdateCustomerProfile {
  __typename: 'UpdateCustomerProfile';
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  profile: Maybe<Scalars['JSONString']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Validate customer session token
 *
 * Used to check if session is still valid and get customer data
 */
export interface ValidateCustomerSession {
  __typename: 'ValidateCustomerSession';
  customer: Maybe<Scalars['JSONString']['output']>;
  error: Maybe<Scalars['String']['output']>;
  message: Maybe<Scalars['String']['output']>;
  success: Maybe<Scalars['Boolean']['output']>;
}

/** An enumeration. */
export enum WorkspaceStorePackagePackageTypeChoices {
  /** Box */
  Box = 'BOX',
  /** Envelope */
  Envelope = 'ENVELOPE',
  /** Soft Package */
  SoftPackage = 'SOFT_PACKAGE'
}

/** An enumeration. */
export enum WorkspaceStorePackageSizeChoices {
  /** Large */
  Large = 'LARGE',
  /** Medium */
  Medium = 'MEDIUM',
  /** Small */
  Small = 'SMALL'
}

/** An enumeration. */
export enum WorkspaceStoreProductInventoryHealthChoices {
  /** Critical */
  Critical = 'CRITICAL',
  /** Healthy */
  Healthy = 'HEALTHY',
  /** Low Stock */
  Low = 'LOW',
  /** Out of Stock */
  OutOfStock = 'OUT_OF_STOCK'
}

/** An enumeration. */
export enum WorkspaceStoreProductProductTypeChoices {
  /** Digital Product */
  Digital = 'DIGITAL',
  /** Physical Product */
  Physical = 'PHYSICAL',
  /** Service */
  Service = 'SERVICE'
}

/** An enumeration. */
export enum WorkspaceStoreProductStatusChoices {
  /** Draft */
  Draft = 'DRAFT',
  /** Published */
  Published = 'PUBLISHED'
}
