export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
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
  BigInt: { input: any; output: any; }
  DateTime: { input: string; output: string; }
  Decimal: { input: any; output: any; }
  JSONString: { input: any; output: any; }
  UUID: { input: string; output: string; }
  Upload: { input: any; output: any; }
}

/**
 * Accept workspace invitation
 * Creates membership when user accepts invite via email link
 *
 * Public mutation: No permission required (uses invite token)
 * Security: Token-based validation, single-use
 */
export interface AcceptInvite {
  __typename?: 'AcceptInvite';
  error?: Maybe<Scalars['String']['output']>;
  member?: Maybe<WorkspaceMemberType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Add comment to order timeline */
export interface AddOrderComment {
  __typename?: 'AddOrderComment';
  comment?: Maybe<OrderCommentType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Add a payment method to workspace.
 *
 * For Fapshi: Requires checkout_url from merchant's Fapshi dashboard.
 * Uses atomic transaction to ensure data integrity.
 */
export interface AddPaymentMethod {
  __typename?: 'AddPaymentMethod';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  paymentMethod?: Maybe<MerchantPaymentMethodType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for adding a payment method to workspace. */
export interface AddPaymentMethodInput {
  /** Fapshi checkout URL from merchant's Fapshi dashboard */
  checkoutUrl?: InputMaybe<Scalars['String']['input']>;
  /** Payment provider identifier (e.g., 'fapshi') */
  providerName: Scalars['String']['input'];
}

/**
 * Add products to category with atomic transaction
 *
 * Security: Validates workspace ownership for both category and products
 * Integrity: Uses @transaction.atomic for rollback
 * Performance: Bulk operation for multiple products
 */
export interface AddProductsToCategory {
  __typename?: 'AddProductsToCategory';
  addedCount?: Maybe<Scalars['Int']['output']>;
  category?: Maybe<CategoryType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Simple address input for Cameroon context
 * Used for shipping and billing addresses in orders
 */
export interface AddressInput {
  /** Street/physical address */
  address?: InputMaybe<Scalars['String']['input']>;
  /** City */
  city?: InputMaybe<Scalars['String']['input']>;
  /** Cameroon region */
  region?: InputMaybe<Scalars['String']['input']>;
}

/**
 * Archive an order to remove it from active view
 *
 * Performance: Atomic update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Validates order can be archived before update
 */
export interface ArchiveOrder {
  __typename?: 'ArchiveOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * GraphQL type for available payment providers.
 * Used when adding new payment methods.
 */
export interface AvailableProviderType {
  __typename?: 'AvailableProviderType';
  /** Whether already configured for workspace */
  alreadyAdded?: Maybe<Scalars['Boolean']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  displayName: Scalars['String']['output'];
  provider: Scalars['String']['output'];
  /** Whether checkout URL is required */
  requiresUrl?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Process multiple CSV files in bulk with background jobs
 *
 * Performance: Async processing with progress tracking
 * Scalability: Background job processing for large batches
 * Reliability: Job queuing with retry mechanisms
 */
export interface BulkCsvProcessing {
  __typename?: 'BulkCSVProcessing';
  jobIds?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
  totalFiles?: Maybe<Scalars['Int']['output']>;
}

/** Response type for bulk delete operations */
export interface BulkDeleteResponse {
  __typename?: 'BulkDeleteResponse';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  operationId?: Maybe<Scalars['String']['output']>;
  processedCount?: Maybe<Scalars['Int']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Process multiple documents in bulk with background jobs
 *
 * Performance: Async processing with progress tracking
 * Scalability: Handles large batches with background workers
 * Reliability: Job queuing with retry mechanisms
 */
export interface BulkDocumentProcessing {
  __typename?: 'BulkDocumentProcessing';
  job?: Maybe<DocumentProcessingJob>;
  success?: Maybe<Scalars['Boolean']['output']>;
  totalDocuments?: Maybe<Scalars['Int']['output']>;
}

/**
 * Unified mutation for bulk product imports from ANY file type
 *
 * CONSOLIDATES: CSV uploads, document uploads, image uploads
 * USES: ProductImportService for ALL business logic
 * PARSERS: Only extract data, no validation/creation
 *
 * Flow:
 * 1. Detect file type (CSV vs Document)
 * 2. Route to appropriate parser for extraction
 * 3. ProductImportService validates & imports
 * 4. Return job_id for progress tracking
 *
 * Performance: Async processing, returns immediately with job_id
 * Scalability: Handles 10,000+ products via chunked processing
 * Reliability: Atomic transactions, continues on errors
 * Security: File size limits, workspace scoping, input validation
 */
export interface BulkImportProducts {
  __typename?: 'BulkImportProducts';
  errors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  progress?: Maybe<ImportProgressType>;
  result?: Maybe<ImportResultType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * GraphQL type for BulkOperation model
 *
 * Features:
 * - All bulk operation fields with proper typing
 * - Shopify-style operation types
 * - Progress tracking and analytics
 * - Custom computed fields
 */
export interface BulkOperationType extends Node {
  __typename?: 'BulkOperationType';
  createdAt: Scalars['DateTime']['output'];
  errorMessage: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  isCompleted?: Maybe<Scalars['Boolean']['output']>;
  isFailed?: Maybe<Scalars['Boolean']['output']>;
  isProcessing?: Maybe<Scalars['Boolean']['output']>;
  operationType: WorkspaceStoreBulkOperationOperationTypeChoices;
  operationTypeDisplay?: Maybe<Scalars['String']['output']>;
  processedItems: Scalars['Int']['output'];
  status: WorkspaceStoreBulkOperationStatusChoices;
  successRate?: Maybe<Scalars['Float']['output']>;
  totalItems: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
  workspace: WorkspaceType;
}

export interface BulkOperationTypeConnection {
  __typename?: 'BulkOperationTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<BulkOperationTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `BulkOperationType` and its cursor. */
export interface BulkOperationTypeEdge {
  __typename?: 'BulkOperationTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<BulkOperationType>;
}

/**
 * Unified input for bulk product imports (CSV, PDF, Images, Excel)
 *
 * Validation: File type, size limits (50MB), format validation
 * Security: File upload restrictions and workspace scoping
 */
export interface BulkProductImportInput {
  /** Auto-create categories if not found in workspace */
  createMissingCategories?: InputMaybe<Scalars['Boolean']['input']>;
  /** Base64 encoded file content */
  file: Scalars['String']['input'];
  /** Original filename with extension */
  filename: Scalars['String']['input'];
}

/** Response type for bulk publish operations */
export interface BulkPublishResponse {
  __typename?: 'BulkPublishResponse';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  operationId?: Maybe<Scalars['String']['output']>;
  processedCount?: Maybe<Scalars['Int']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for bulk status updates
 *
 * Validation: Batch size limits and status validation
 * Security: Workspace scoping for all updates
 */
export interface BulkStatusUpdateInput {
  updates: Array<InputMaybe<StatusUpdateInput>>;
}

/**
 * Input for bulk inventory updates
 *
 * Validation: Batch size limits and quantity validation
 * Security: Workspace scoping for all updates
 */
export interface BulkStockUpdateInput {
  updates: Array<InputMaybe<UpdateInventoryInput>>;
}

/**
 * Process bulk order status updates
 *
 * Performance: Optimized bulk operations with transaction
 * Scalability: Handles up to 500 updates per batch
 * Reliability: Atomic transaction with rollback on failure
 */
export interface BulkUpdateOrderStatus {
  __typename?: 'BulkUpdateOrderStatus';
  error?: Maybe<Scalars['String']['output']>;
  failedUpdates?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  successfulUpdates?: Maybe<Scalars['Int']['output']>;
  totalUpdates?: Maybe<Scalars['Int']['output']>;
}

/** Response type for bulk update operations */
export interface BulkUpdateResponse {
  __typename?: 'BulkUpdateResponse';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  operationId?: Maybe<Scalars['String']['output']>;
  processedCount?: Maybe<Scalars['Int']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Bulk update stock quantities for multiple inventory items
 *
 * Performance: Optimized bulk operations with transaction
 * Scalability: Handles up to 1000 updates per batch
 * Reliability: Atomic transaction with rollback on failure
 */
export interface BulkUpdateStock {
  __typename?: 'BulkUpdateStock';
  error?: Maybe<Scalars['String']['output']>;
  failedUpdates?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  successfulUpdates?: Maybe<Scalars['Int']['output']>;
  totalUpdates?: Maybe<Scalars['Int']['output']>;
}

/** GraphQL type for CSV parsing progress */
export interface CsvParseProgressType {
  __typename?: 'CSVParseProgressType';
  currentRow?: Maybe<Scalars['Int']['output']>;
  errorsCount?: Maybe<Scalars['Int']['output']>;
  jobId?: Maybe<Scalars['String']['output']>;
  percentComplete?: Maybe<Scalars['Int']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  totalRows?: Maybe<Scalars['Int']['output']>;
  validProductsCount?: Maybe<Scalars['Int']['output']>;
}

/** GraphQL type for CSV parsing result */
export interface CsvParseResultType {
  __typename?: 'CSVParseResultType';
  errors?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  jobId?: Maybe<Scalars['String']['output']>;
  processingTime?: Maybe<Scalars['Float']['output']>;
  products?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
  totalRows?: Maybe<Scalars['Int']['output']>;
  validProducts?: Maybe<Scalars['Int']['output']>;
  warnings?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
}

/**
 * Input for CSV upload operation
 *
 * Validation: File type, size limits, and format validation
 * Security: File upload restrictions and workspace scoping
 */
export interface CsvUploadInput {
  file: Scalars['String']['input'];
  filename: Scalars['String']['input'];
}

/**
 * Cancel pending workspace invitation
 *
 * Requires: 'staff:invite' permission
 */
export interface CancelInvite {
  __typename?: 'CancelInvite';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Cancel an order with validation and inventory restoration
 *
 * Performance: Atomic cancellation with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive validation and rollback
 */
export interface CancelOrder {
  __typename?: 'CancelOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

export interface CategoryReorderInput {
  id: Scalars['ID']['input'];
  sortOrder: Scalars['Int']['input'];
}

/**
 * GraphQL type for Category model
 *
 * Features:
 * - All category fields with proper typing
 * - Hierarchical parent/child relationships
 * - Breadcrumb navigation
 * - Category analytics properties
 * - SEO optimization fields
 */
export interface CategoryType extends Node {
  __typename?: 'CategoryType';
  createdAt: Scalars['DateTime']['output'];
  /** Collection description */
  description: Scalars['String']['output'];
  /** Featured image URL from featured_media FK */
  featuredImageUrl?: Maybe<Scalars['String']['output']>;
  /** Featured image for this category/collection */
  featuredMedia?: Maybe<MediaUploadType>;
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
  /** Count of products in this collection */
  productCount?: Maybe<Scalars['Int']['output']>;
  /** URL-friendly identifier */
  slug: Scalars['String']['output'];
  /** Manual sort order for admin drag-drop */
  sortOrder: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface CategoryTypeConnection {
  __typename?: 'CategoryTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<CategoryTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `CategoryType` and its cursor. */
export interface CategoryTypeEdge {
  __typename?: 'CategoryTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<CategoryType>;
}

/**
 * Change workspace member's role
 * Used in member details page and users list
 *
 * Requires: 'staff:role_change' permission
 * Security: Prevents self-privilege escalation, owner role changes
 */
export interface ChangeStaffRole {
  __typename?: 'ChangeStaffRole';
  error?: Maybe<Scalars['String']['output']>;
  member?: Maybe<WorkspaceMemberType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for changing staff member's role
 * Used in member details page role assignment
 *
 * Fields:
 * - member_id: Membership ID to update (required)
 * - new_role_id: New role to assign (required)
 */
export interface ChangeStaffRoleInput {
  memberId: Scalars['ID']['input'];
  newRoleId: Scalars['ID']['input'];
}

/**
 * GraphQL type for ChannelOrder model
 *
 * Features:
 * - Cross-platform order tracking
 * - Sync status monitoring
 */
export interface ChannelOrderType extends Node {
  __typename?: 'ChannelOrderType';
  /** Order ID in the sales channel */
  channelOrderId: Scalars['String']['output'];
  /** Order status in the sales channel */
  channelStatus: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Order currency */
  currency: Scalars['String']['output'];
  /** Customer email from sales channel */
  customerEmail?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Whether order is synchronized with local system */
  isSynced: Scalars['Boolean']['output'];
  /** Last synchronization attempt timestamp */
  lastSyncAttempt?: Maybe<Scalars['DateTime']['output']>;
  /** Local order ID (if synchronized) */
  localOrderId?: Maybe<Scalars['String']['output']>;
  /** Order status in local system */
  localStatus?: Maybe<Scalars['String']['output']>;
  /** Order amount in the sales channel */
  orderAmount: Scalars['Decimal']['output'];
  salesChannel?: Maybe<SalesChannelType>;
  /** Number of synchronization attempts */
  syncAttempts: Scalars['Int']['output'];
  /** Last synchronization error message */
  syncError?: Maybe<Scalars['String']['output']>;
  updatedAt: Scalars['DateTime']['output'];
}

export interface ChannelOrderTypeConnection {
  __typename?: 'ChannelOrderTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<ChannelOrderTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `ChannelOrderType` and its cursor. */
export interface ChannelOrderTypeEdge {
  __typename?: 'ChannelOrderTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<ChannelOrderType>;
}

/**
 * GraphQL type for ChannelProduct model
 *
 * Features:
 * - Product visibility per channel
 * - Channel-specific pricing
 * - Sync tracking
 */
export interface ChannelProductType extends Node {
  __typename?: 'ChannelProductType';
  /** Channel-specific inventory quantity */
  channelInventory: Scalars['Int']['output'];
  /** Channel-specific price (overrides base price) */
  channelPrice?: Maybe<Scalars['Decimal']['output']>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Whether product is visible on this channel */
  isVisible: Scalars['Boolean']['output'];
  /** Last synchronization timestamp */
  lastSyncedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Product ID in the sales channel */
  productId: Scalars['String']['output'];
  salesChannel?: Maybe<SalesChannelType>;
  /** Whether to sync inventory with this channel */
  syncInventory: Scalars['Boolean']['output'];
  /** Whether to sync pricing with this channel */
  syncPricing: Scalars['Boolean']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface ChannelProductTypeConnection {
  __typename?: 'ChannelProductTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<ChannelProductTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `ChannelProductType` and its cursor. */
export interface ChannelProductTypeEdge {
  __typename?: 'ChannelProductTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<ChannelProductType>;
}

/** Chart series configuration */
export interface ChartConfig {
  __typename?: 'ChartConfig';
  /** CSS color value */
  color: Scalars['String']['output'];
  /** Display label */
  label: Scalars['String']['output'];
}

/** Time-series chart data with configuration - BASIC tier */
export interface ChartData {
  __typename?: 'ChartData';
  /** Series configurations */
  config?: Maybe<ChartSeriesConfig>;
  /** Chart data points */
  data: Array<Maybe<ChartDataPoint>>;
}

/** Single data point in time-series chart - BASIC tier */
export interface ChartDataPoint {
  __typename?: 'ChartDataPoint';
  /** ISO date (YYYY-MM-DD) */
  date: Scalars['String']['output'];
  /** Order count for the day */
  orders: Scalars['Int']['output'];
  /** Revenue for the day */
  revenue: Scalars['Float']['output'];
}

/** Chart series configurations for orders and revenue */
export interface ChartSeriesConfig {
  __typename?: 'ChartSeriesConfig';
  /** Orders series config */
  orders?: Maybe<ChartConfig>;
  /** Revenue series config */
  revenue?: Maybe<ChartConfig>;
}

/**
 * Clear import progress from cache (cleanup)
 *
 * Use after: Import completed and user acknowledged results
 */
export interface ClearImportProgress {
  __typename?: 'ClearImportProgress';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Conversion funnel data - PRO tier
 * Shows customer journey: Page View -> Cart -> Checkout -> Order
 */
export interface ConversionFunnel {
  __typename?: 'ConversionFunnel';
  /** Summary metrics */
  metrics?: Maybe<FunnelMetrics>;
  /** Funnel stages */
  stages: Array<Maybe<FunnelStage>>;
}

/**
 * Create a cash on delivery order
 *
 * Payment status remains 'pending' until marked as paid on delivery
 */
export interface CreateCashOnDeliveryOrder {
  __typename?: 'CreateCashOnDeliveryOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
  unavailableItems?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
}

/**
 * Create new category with atomic transaction (Shopify-style)
 *
 * Security: Validates workspace ownership
 * Integrity: Uses @transaction.atomic for rollback
 * Hierarchical: Validates parent relationships
 * Images: Accepts single image file upload
 */
export interface CreateCategory {
  __typename?: 'CreateCategory';
  category?: Maybe<CategoryType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Create customer with atomic transaction using CustomerMutationService
 *
 * Performance: Atomic creation with validation
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive validation and rollback
 */
export interface CreateCustomer {
  __typename?: 'CreateCustomer';
  customer?: Maybe<CustomerType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Create discount with service layer orchestration */
export interface CreateDiscount {
  __typename?: 'CreateDiscount';
  discount?: Maybe<DiscountType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Create inventory entries for a new variant across multiple locations
 *
 * Performance: Bulk creation with transaction
 * Scalability: Handles multiple location assignments
 * Reliability: Atomic operation with rollback
 */
export interface CreateInventoryForVariant {
  __typename?: 'CreateInventoryForVariant';
  createdCount?: Maybe<Scalars['Int']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  inventoryItems?: Maybe<Array<Maybe<InventoryItemType>>>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Create location (warehouse/store) */
export interface CreateLocation {
  __typename?: 'CreateLocation';
  error?: Maybe<Scalars['String']['output']>;
  location?: Maybe<LocationType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Create a new order with validation and inventory checks
 *
 * Performance: Atomic creation with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive error handling with rollback
 */
export interface CreateOrder {
  __typename?: 'CreateOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
  unavailableItems?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
}

/** Create shipping package */
export interface CreatePackage {
  __typename?: 'CreatePackage';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  package?: Maybe<PackageType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Create product using ProductService
 *
 * Core required: name, price
 * Optional: All other fields including variants, shipping, SEO
 * Performance: Atomic creation with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive validation and rollback
 */
export interface CreateProduct {
  __typename?: 'CreateProduct';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  product?: Maybe<ProductType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Create sales channel with atomic transaction */
export interface CreateSalesChannel {
  __typename?: 'CreateSalesChannel';
  message?: Maybe<Scalars['String']['output']>;
  salesChannel?: Maybe<SalesChannelType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Create a WhatsApp order
 *
 * Creates order and sends WhatsApp DM to admin
 */
export interface CreateWhatsAppOrder {
  __typename?: 'CreateWhatsAppOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
  unavailableItems?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
}

/**
 * Input for customer creation
 *
 * Validation: Required fields and data structure
 * Security: Workspace scoping via JWT middleware
 */
export interface CustomerCreateInput {
  address?: InputMaybe<Scalars['String']['input']>;
  city?: InputMaybe<Scalars['String']['input']>;
  customerType?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  phone: Scalars['String']['input'];
  region?: InputMaybe<Scalars['String']['input']>;
  smsNotifications?: InputMaybe<Scalars['Boolean']['input']>;
  tags?: InputMaybe<Scalars['JSONString']['input']>;
  whatsappNotifications?: InputMaybe<Scalars['Boolean']['input']>;
}

/** GraphQL type for Customer History */
export interface CustomerHistoryType extends Node {
  __typename?: 'CustomerHistoryType';
  /** Type of action (e.g., 'order_placed', 'note_added') */
  action: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  details?: Maybe<Scalars['JSONString']['output']>;
  displayMessage?: Maybe<Scalars['String']['output']>;
  /** The ID of the object */
  id: Scalars['ID']['output'];
  /** User who performed the action (if applicable) */
  performedBy?: Maybe<UserType>;
}

/** Customer analytics - PRO tier */
export interface CustomerMetrics {
  __typename?: 'CustomerMetrics';
  /** New customers in period */
  newCustomers?: Maybe<Scalars['Int']['output']>;
  /** Percentage of new customers */
  newRate?: Maybe<Scalars['Float']['output']>;
  /** Returning customers in period */
  returningCustomers?: Maybe<Scalars['Int']['output']>;
  /** Total unique customers */
  total?: Maybe<Scalars['Int']['output']>;
}

/** Input for customer tag operations */
export interface CustomerTagUpdateInput {
  addTags?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  removeTags?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
}

/**
 * GraphQL type for Customer model
 *
 * Features:
 * - All customer fields with proper typing
 * - Cameroon region support
 * - Order tracking
 * - Address management for order creation
 */
export interface CustomerType extends Node {
  __typename?: 'CustomerType';
  /** Customer street/physical address */
  address: Scalars['String']['output'];
  averageOrderValue?: Maybe<Scalars['Decimal']['output']>;
  /** Customer city */
  city: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Customer type for segmentation */
  customerType: WorkspaceCoreCustomerCustomerTypeChoices;
  /** Customer email (optional) */
  email: Scalars['String']['output'];
  /** First order date */
  firstOrderAt?: Maybe<Scalars['DateTime']['output']>;
  hasEmail?: Maybe<Scalars['Boolean']['output']>;
  history?: Maybe<Array<Maybe<CustomerHistoryType>>>;
  id: Scalars['ID']['output'];
  /** Whether customer is active */
  isActive: Scalars['Boolean']['output'];
  isFrequentBuyer?: Maybe<Scalars['Boolean']['output']>;
  isHighValue?: Maybe<Scalars['Boolean']['output']>;
  isVerified?: Maybe<Scalars['Boolean']['output']>;
  /** Last order date */
  lastOrderAt?: Maybe<Scalars['DateTime']['output']>;
  lifetimeValue?: Maybe<Scalars['Decimal']['output']>;
  /** Customer full name */
  name: Scalars['String']['output'];
  /** Primary customer identifier (MTN/Orange Mobile Money) */
  phone: Scalars['String']['output'];
  /** Cameroon region */
  region?: Maybe<WorkspaceCoreCustomerRegionChoices>;
  /** Opt-in for SMS notifications */
  smsNotifications: Scalars['Boolean']['output'];
  /** Customer tags for segmentation ['vip', 'wholesale', 'frequent', 'student'] */
  tags: Scalars['JSONString']['output'];
  /** Total orders across all workspaces */
  totalOrders: Scalars['Int']['output'];
  /** Total amount spent across all workspaces */
  totalSpent: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
  /** When customer was verified */
  verifiedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Opt-in for WhatsApp notifications */
  whatsappNotifications: Scalars['Boolean']['output'];
}

export interface CustomerTypeConnection {
  __typename?: 'CustomerTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<CustomerTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `CustomerType` and its cursor. */
export interface CustomerTypeEdge {
  __typename?: 'CustomerTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<CustomerType>;
}

/**
 * Input for customer updates
 *
 * Validation: Field validation and data integrity
 * Security: Workspace scoping via JWT middleware
 */
export interface CustomerUpdateInput {
  address?: InputMaybe<Scalars['String']['input']>;
  city?: InputMaybe<Scalars['String']['input']>;
  customerType?: InputMaybe<Scalars['String']['input']>;
  email?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  region?: InputMaybe<Scalars['String']['input']>;
  smsNotifications?: InputMaybe<Scalars['Boolean']['input']>;
  tags?: InputMaybe<Scalars['JSONString']['input']>;
  whatsappNotifications?: InputMaybe<Scalars['Boolean']['input']>;
}

/**
 * Metric card for dashboard display - BASIC tier
 * Represents a single KPI with trend information
 */
export interface DashboardCard {
  __typename?: 'DashboardCard';
  /** Card title (e.g., 'Total Revenue') */
  title: Scalars['String']['output'];
  /** Trend percentage (e.g., '+12.5%') */
  trend: Scalars['String']['output'];
  /** 'up' or 'down' */
  trendDirection: Scalars['String']['output'];
  /** Formatted display value */
  value: Scalars['String']['output'];
}

/**
 * Delete category with atomic transaction
 *
 * Security: Validates workspace ownership
 * Integrity: Uses @transaction.atomic for rollback
 * Safety: Prevents deletion of categories with products
 * Hierarchical: Handles orphaned children
 */
export interface DeleteCategory {
  __typename?: 'DeleteCategory';
  deletedId?: Maybe<Scalars['ID']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Delete customer with validation and atomic transaction using CustomerMutationService
 *
 * Performance: Atomic deletion with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive validation and rollback
 */
export interface DeleteCustomer {
  __typename?: 'DeleteCustomer';
  deletedId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Delete discount with service layer orchestration */
export interface DeleteDiscount {
  __typename?: 'DeleteDiscount';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Delete location */
export interface DeleteLocation {
  __typename?: 'DeleteLocation';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Delete media upload (soft delete)
 *
 * User can manually manage their storage
 */
export interface DeleteMedia {
  __typename?: 'DeleteMedia';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Delete shipping package */
export interface DeletePackage {
  __typename?: 'DeletePackage';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Delete product with validation and atomic transaction using ProductService
 *
 * Performance: Atomic deletion with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive validation and rollback
 */
export interface DeleteProduct {
  __typename?: 'DeleteProduct';
  deletedId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Delete sales channel with atomic transaction */
export interface DeleteSalesChannel {
  __typename?: 'DeleteSalesChannel';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Input for creating/updating discounts */
export interface DiscountInput {
  appliesToAllCustomers?: InputMaybe<Scalars['Boolean']['input']>;
  appliesToAllProducts?: InputMaybe<Scalars['Boolean']['input']>;
  appliesToCustomerTypes?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  appliesToRegions?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  bxgyDiscountType?: InputMaybe<Scalars['String']['input']>;
  bxgyValue?: InputMaybe<Scalars['Decimal']['input']>;
  canCombineWithOrderDiscounts?: InputMaybe<Scalars['Boolean']['input']>;
  canCombineWithProductDiscounts?: InputMaybe<Scalars['Boolean']['input']>;
  categoryIds?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  code: Scalars['String']['input'];
  customerBuysProductIds?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  customerBuysQuantity?: InputMaybe<Scalars['Int']['input']>;
  customerBuysType?: InputMaybe<Scalars['String']['input']>;
  customerBuysValue?: InputMaybe<Scalars['Decimal']['input']>;
  customerGetsProductIds?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  customerGetsQuantity?: InputMaybe<Scalars['Int']['input']>;
  customerSegmentation?: InputMaybe<Scalars['JSONString']['input']>;
  discountType: Scalars['String']['input'];
  discountValueType?: InputMaybe<Scalars['String']['input']>;
  endsAt?: InputMaybe<Scalars['DateTime']['input']>;
  limitOnePerCustomer?: InputMaybe<Scalars['Boolean']['input']>;
  limitTotalUses?: InputMaybe<Scalars['Boolean']['input']>;
  maxUsesPerOrder?: InputMaybe<Scalars['Int']['input']>;
  method?: InputMaybe<Scalars['String']['input']>;
  minimumPurchaseAmount?: InputMaybe<Scalars['Decimal']['input']>;
  minimumQuantityItems?: InputMaybe<Scalars['Int']['input']>;
  minimumRequirementType?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  productIds?: InputMaybe<Array<InputMaybe<Scalars['ID']['input']>>>;
  startsAt?: InputMaybe<Scalars['DateTime']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
  usageLimit?: InputMaybe<Scalars['Int']['input']>;
  usageLimitPerCustomer?: InputMaybe<Scalars['Int']['input']>;
  value?: InputMaybe<Scalars['Decimal']['input']>;
}

/**
 * GraphQL type for Discount model
 *
 * Features:
 * - All discount fields with proper typing
 * - Computed status properties
 * - Usage tracking
 * - Support for amount_off_product and buy_x_get_y discount types
 */
export interface DiscountType extends Node {
  __typename?: 'DiscountType';
  /** Whether discount applies to all customers */
  appliesToAllCustomers: Scalars['Boolean']['output'];
  /** Whether discount applies to all products */
  appliesToAllProducts: Scalars['Boolean']['output'];
  /** Customer types this discount applies to */
  appliesToCustomerTypes: Scalars['JSONString']['output'];
  /** Cameroon regions this discount applies to */
  appliesToRegions: Scalars['JSONString']['output'];
  /** Discount type for buy_x_get_y (percentage, amount_off_each, free) */
  bxgyDiscountType?: Maybe<WorkspaceStoreDiscountBxgyDiscountTypeChoices>;
  /** Discount value for buy_x_get_y */
  bxgyValue?: Maybe<Scalars['Decimal']['output']>;
  /** Can combine with order discounts */
  canCombineWithOrderDiscounts: Scalars['Boolean']['output'];
  /** Can combine with product discounts */
  canCombineWithProductDiscounts: Scalars['Boolean']['output'];
  /** Specific category IDs this discount applies to */
  categoryIds: Scalars['JSONString']['output'];
  /** Discount code (e.g., SUMMER20, WELCOME10) */
  code: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Specific product IDs for customer buys - for buy_x_get_y */
  customerBuysProductIds: Scalars['JSONString']['output'];
  /** Customer buys quantity - for buy_x_get_y */
  customerBuysQuantity?: Maybe<Scalars['Int']['output']>;
  /** Customer buys type - for buy_x_get_y */
  customerBuysType?: Maybe<WorkspaceStoreDiscountCustomerBuysTypeChoices>;
  /** Customer buys minimum purchase amount - for buy_x_get_y */
  customerBuysValue?: Maybe<Scalars['Decimal']['output']>;
  /** Specific product IDs for customer gets - for buy_x_get_y */
  customerGetsProductIds: Scalars['JSONString']['output'];
  /** Customer gets quantity - for buy_x_get_y */
  customerGetsQuantity?: Maybe<Scalars['Int']['output']>;
  /** Customer targeting rules (regions, types, tags) */
  customerSegmentation: Scalars['JSONString']['output'];
  /** Type of discount */
  discountType: WorkspaceStoreDiscountDiscountTypeChoices;
  /** Discount value type (percentage or fixed_amount) - for amount_off_product */
  discountValueType?: Maybe<WorkspaceStoreDiscountDiscountValueTypeChoices>;
  /** When the discount expires */
  endsAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  isActive?: Maybe<Scalars['Boolean']['output']>;
  isExpired?: Maybe<Scalars['Boolean']['output']>;
  /** Whether to limit to one use per customer */
  limitOnePerCustomer: Scalars['Boolean']['output'];
  /** Whether to limit total number of uses */
  limitTotalUses: Scalars['Boolean']['output'];
  /** Maximum number of times discount can be used per order - for buy_x_get_y */
  maxUsesPerOrder?: Maybe<Scalars['Int']['output']>;
  /** Discount method (discount_code or automatic) */
  method: WorkspaceStoreDiscountMethodChoices;
  /** Minimum purchase amount (FCFA) */
  minimumPurchaseAmount?: Maybe<Scalars['Decimal']['output']>;
  /** Minimum quantity of items */
  minimumQuantityItems?: Maybe<Scalars['Int']['output']>;
  /** Type of minimum purchase requirement */
  minimumRequirementType: WorkspaceStoreDiscountMinimumRequirementTypeChoices;
  /** Discount name for admin reference */
  name: Scalars['String']['output'];
  /** Specific product IDs this discount applies to */
  productIds: Scalars['JSONString']['output'];
  remainingUsage?: Maybe<Scalars['Int']['output']>;
  /** When the discount becomes active */
  startsAt: Scalars['DateTime']['output'];
  status: WorkspaceStoreDiscountStatusChoices;
  /** Total amount discounted across all orders */
  totalDiscountAmount: Scalars['Decimal']['output'];
  /** Total orders that used this discount */
  totalOrders: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
  /** Number of times this discount has been used */
  usageCount: Scalars['Int']['output'];
  /** Maximum number of times this discount can be used */
  usageLimit?: Maybe<Scalars['Int']['output']>;
  /** Maximum usage per customer */
  usageLimitPerCustomer?: Maybe<Scalars['Int']['output']>;
  /** Discount value - for amount_off_product */
  value?: Maybe<Scalars['Decimal']['output']>;
}

export interface DiscountTypeConnection {
  __typename?: 'DiscountTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<DiscountTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `DiscountType` and its cursor. */
export interface DiscountTypeEdge {
  __typename?: 'DiscountTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<DiscountType>;
}

/** Document analysis result with extracted products */
export interface DocumentAnalysisResult {
  __typename?: 'DocumentAnalysisResult';
  confidenceScore?: Maybe<Scalars['Float']['output']>;
  documentType?: Maybe<Scalars['String']['output']>;
  errors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  metadata?: Maybe<Scalars['JSONString']['output']>;
  processingTime?: Maybe<Scalars['Float']['output']>;
  products?: Maybe<Array<Maybe<ExtractedProductType>>>;
  totalPages?: Maybe<Scalars['Int']['output']>;
}

/** Background job for document processing */
export interface DocumentProcessingJob {
  __typename?: 'DocumentProcessingJob';
  estimatedCompletion?: Maybe<Scalars['String']['output']>;
  jobId?: Maybe<Scalars['String']['output']>;
  progress?: Maybe<Scalars['Int']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  totalSteps?: Maybe<Scalars['Int']['output']>;
}

/**
 * Input for document upload operation
 *
 * Validation: File type, size limits, and format validation
 * Security: File upload restrictions and workspace scoping
 */
export interface DocumentUploadInput {
  extractProducts?: InputMaybe<Scalars['Boolean']['input']>;
  file: Scalars['String']['input'];
  filename: Scalars['String']['input'];
  processImages?: InputMaybe<Scalars['Boolean']['input']>;
}

/**
 * Duplicate existing product with variants and inventory using ProductService
 *
 * Performance: Bulk operations with transaction
 * Scalability: Handles complex product structures
 * Reliability: Atomic operation with rollback
 *
 * Smart Naming (if new_name not provided):
 * - Auto-generates: "Product (Copy 1)", "Product (Copy 2)", etc.
 * - Strips existing (Copy N) patterns to avoid nesting
 * - Slug pattern: "product-copy-1", "product-copy-2", etc.
 */
export interface DuplicateProduct {
  __typename?: 'DuplicateProduct';
  error?: Maybe<Scalars['String']['output']>;
  inventoryRecordsCreated?: Maybe<Scalars['Int']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  product?: Maybe<ProductType>;
  success?: Maybe<Scalars['Boolean']['output']>;
  variantsCreated?: Maybe<Scalars['Int']['output']>;
}

/**
 * Extract products from previously uploaded document
 *
 * Performance: Optimized for re-processing existing documents
 * Scalability: Handles multiple document formats and sizes
 * Reliability: Comprehensive error handling and validation
 */
export interface ExtractProductsFromDocument {
  __typename?: 'ExtractProductsFromDocument';
  confidenceScore?: Maybe<Scalars['Float']['output']>;
  errors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  extractedProducts?: Maybe<Array<Maybe<ExtractedProductType>>>;
  processingTime?: Maybe<Scalars['Float']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** GraphQL type for extracted products from documents */
export interface ExtractedProductType {
  __typename?: 'ExtractedProductType';
  brand?: Maybe<Scalars['String']['output']>;
  category?: Maybe<Scalars['String']['output']>;
  compareAtPrice?: Maybe<Scalars['String']['output']>;
  condition?: Maybe<Scalars['String']['output']>;
  confidence?: Maybe<Scalars['Float']['output']>;
  costPrice?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  images?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  name?: Maybe<Scalars['String']['output']>;
  price?: Maybe<Scalars['String']['output']>;
  sellingType?: Maybe<Scalars['String']['output']>;
  sku?: Maybe<Scalars['String']['output']>;
  sourceLocation?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  stockQuantity?: Maybe<Scalars['Int']['output']>;
  subCategory?: Maybe<Scalars['String']['output']>;
}

/** Funnel summary metrics - PRO tier */
export interface FunnelMetrics {
  __typename?: 'FunnelMetrics';
  /** Cart abandonment rate */
  abandonmentRate?: Maybe<Scalars['Float']['output']>;
  /** Number of abandoned carts */
  cartAbandoned?: Maybe<Scalars['Int']['output']>;
  /** Overall conversion rate */
  conversionRate?: Maybe<Scalars['Float']['output']>;
}

/** Single stage in conversion funnel - PRO tier */
export interface FunnelStage {
  __typename?: 'FunnelStage';
  /** Count at this stage */
  count: Scalars['Int']['output'];
  /** Stage name */
  name: Scalars['String']['output'];
  /** Percentage of previous stage */
  rate: Scalars['Float']['output'];
}

/**
 * Get progress of CSV upload and parsing job
 *
 * Performance: Fast cache lookup for progress information
 * Scalability: Handles multiple concurrent progress queries
 * Reliability: Graceful handling of missing job IDs
 */
export interface GetCsvUploadProgress {
  __typename?: 'GetCSVUploadProgress';
  progress?: Maybe<CsvParseProgressType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Get real-time progress of import operation
 *
 * Performance: Fast cache lookup (< 5ms)
 * Scalability: Handles concurrent progress queries
 * Reliability: Graceful handling of expired/missing jobs
 */
export interface GetImportProgress {
  __typename?: 'GetImportProgress';
  message?: Maybe<Scalars['String']['output']>;
  progress?: Maybe<ImportProgressType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Get comprehensive inventory summary for workspace
 *
 * Performance: Optimized aggregations with proper indexing
 * Scalability: Efficient queries for large datasets
 * Security: Workspace scoping and permission validation
 */
export interface GetInventorySummary {
  __typename?: 'GetInventorySummary';
  error?: Maybe<Scalars['String']['output']>;
  recentActivity?: Maybe<RecentActivityType>;
  success?: Maybe<Scalars['Boolean']['output']>;
  summary?: Maybe<InventorySummaryType>;
}

/**
 * Get low stock alerts for workspace
 *
 * Performance: Optimized queries for alert detection
 * Scalability: Handles large inventory catalogs
 * Reliability: Comprehensive error handling
 */
export interface GetLowStockAlerts {
  __typename?: 'GetLowStockAlerts';
  alerts?: Maybe<Array<Maybe<LowStockAlertType>>>;
  error?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  totalAlerts?: Maybe<Scalars['Int']['output']>;
}

/** Real-time import progress tracking */
export interface ImportProgressType {
  __typename?: 'ImportProgressType';
  currentItem?: Maybe<Scalars['Int']['output']>;
  errors?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  failedImports?: Maybe<Scalars['Int']['output']>;
  jobId?: Maybe<Scalars['String']['output']>;
  percentComplete?: Maybe<Scalars['Int']['output']>;
  stage?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  successfulImports?: Maybe<Scalars['Int']['output']>;
  totalItems?: Maybe<Scalars['Int']['output']>;
  warnings?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
}

/** Final result of bulk import operation */
export interface ImportResultType {
  __typename?: 'ImportResultType';
  bulkOperationId?: Maybe<Scalars['String']['output']>;
  createdProductIds?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  errors?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  failedImports?: Maybe<Scalars['Int']['output']>;
  jobId?: Maybe<Scalars['String']['output']>;
  processingTime?: Maybe<Scalars['Float']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  successfulImports?: Maybe<Scalars['Int']['output']>;
  totalItems?: Maybe<Scalars['Int']['output']>;
  warnings?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
}

/** Input for inventory-related fields (Shopify-style) */
export interface InventoryInput {
  allowBackorders?: InputMaybe<Scalars['Boolean']['input']>;
  /** Stock available for sale */
  available?: InputMaybe<Scalars['Int']['input']>;
  barcode?: InputMaybe<Scalars['String']['input']>;
  /** Condition: new, refurbished, second_hand, etc. */
  condition?: InputMaybe<Scalars['String']['input']>;
  inventoryQuantity?: InputMaybe<Scalars['Int']['input']>;
  /** Location ID for inventory */
  locationId?: InputMaybe<Scalars['ID']['input']>;
  /** Total stock on hand */
  onhand?: InputMaybe<Scalars['Int']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
}

/**
 * GraphQL type for inventory item in mutation responses
 *
 * Used instead of JSONString for proper type safety
 */
export interface InventoryItemType {
  __typename?: 'InventoryItemType';
  id?: Maybe<Scalars['String']['output']>;
  locationId?: Maybe<Scalars['String']['output']>;
  locationName?: Maybe<Scalars['String']['output']>;
  quantity?: Maybe<Scalars['Int']['output']>;
}

/** GraphQL type for inventory summary */
export interface InventorySummaryType {
  __typename?: 'InventorySummaryType';
  averageStock?: Maybe<Scalars['Float']['output']>;
  lowStockItems?: Maybe<Scalars['Int']['output']>;
  outOfStockItems?: Maybe<Scalars['Int']['output']>;
  totalItems?: Maybe<Scalars['Int']['output']>;
  totalStock?: Maybe<Scalars['Int']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
}

/**
 * GraphQL type for Inventory model
 *
 * Features:
 * - All inventory fields with proper typing
 * - Variant and location relationships
 * - Stock status properties
 * - Atomic operations support
 * - Shopify-style inventory tracking
 */
export interface InventoryType extends Node {
  __typename?: 'InventoryType';
  /** Stock available for sale */
  available?: Maybe<Scalars['Int']['output']>;
  /** Condition of inventory items */
  condition?: Maybe<WorkspaceStoreInventoryConditionChoices>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Whether inventory is available for sale */
  isAvailable: Scalars['Boolean']['output'];
  /** Whether inventory is below location's low stock threshold */
  isLowStock?: Maybe<Scalars['Boolean']['output']>;
  /** Location where inventory is stored */
  location?: Maybe<LocationType>;
  /** Total stock on hand (committed inventory) */
  onhand?: Maybe<Scalars['Int']['output']>;
  /** Product primary image with all variations (thumbnail, WebP, etc.) */
  productImage?: Maybe<MediaUploadType>;
  /** Product name derived from variant */
  productName?: Maybe<Scalars['String']['output']>;
  /** Available stock quantity at this location (deprecated, use onhand/available) */
  quantity: Scalars['Int']['output'];
  /** SKU (Stock Keeping Unit) from variant */
  sku?: Maybe<Scalars['String']['output']>;
  /** Human-readable stock status: 'in_stock', 'low_stock', or 'out_of_stock' */
  stockStatus?: Maybe<Scalars['String']['output']>;
  updatedAt: Scalars['DateTime']['output'];
  /** Product variant for this inventory entry */
  variant?: Maybe<ProductVariantType>;
}

export interface InventoryTypeConnection {
  __typename?: 'InventoryTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<InventoryTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `InventoryType` and its cursor. */
export interface InventoryTypeEdge {
  __typename?: 'InventoryTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<InventoryType>;
}

export interface InventoryUpdateInput {
  locationId: Scalars['ID']['input'];
  quantity: Scalars['Int']['input'];
  variantId: Scalars['ID']['input'];
}

/**
 * Invite staff to workspace with email and role
 * Following Shopify "Add users" pattern
 *
 * Requires: 'staff:invite' permission
 * Flow: Creates invite -> Sends email (async) -> User accepts -> Membership created
 */
export interface InviteStaff {
  __typename?: 'InviteStaff';
  error?: Maybe<Scalars['String']['output']>;
  invite?: Maybe<WorkspaceInviteType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for inviting staff to workspace
 * Following Shopify "Add users" modal pattern (supports multiple roles)
 *
 * Fields:
 * - email: Email of user to invite (required)
 * - role_ids: List of role IDs to assign (required, supports multiple)
 */
export interface InviteStaffInput {
  email: Scalars['String']['input'];
  roleIds: Array<Scalars['ID']['input']>;
}

/** Input for creating/updating locations */
export interface LocationInput {
  addressLine1: Scalars['String']['input'];
  addressLine2?: InputMaybe<Scalars['String']['input']>;
  city: Scalars['String']['input'];
  email?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  isPrimary?: InputMaybe<Scalars['Boolean']['input']>;
  lowStockThreshold?: InputMaybe<Scalars['Int']['input']>;
  managerName?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  phone?: InputMaybe<Scalars['String']['input']>;
  region: Scalars['String']['input'];
}

/**
 * GraphQL type for Location model
 *
 * Features:
 * - All location fields with proper typing
 * - Inventory relationship with DataLoader
 * - Regional analytics properties
 * - Cameroon region-specific data
 */
export interface LocationType extends Node {
  __typename?: 'LocationType';
  /** Street address */
  addressLine1: Scalars['String']['output'];
  /** Additional address info */
  addressLine2: Scalars['String']['output'];
  /** Whether this location can be deactivated (no inventory) */
  canDeactivate?: Maybe<Scalars['Boolean']['output']>;
  /** City name */
  city: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Contact email */
  email: Scalars['String']['output'];
  /** Formatted full address including city and region */
  fullAddress?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Active and operational */
  isActive: Scalars['Boolean']['output'];
  /** Primary/default location */
  isPrimary: Scalars['Boolean']['output'];
  /** Number of low stock alerts */
  lowStockAlerts: Scalars['Int']['output'];
  /** Number of low stock items at this location */
  lowStockItems?: Maybe<Scalars['Int']['output']>;
  /** Low stock alert threshold */
  lowStockThreshold: Scalars['Int']['output'];
  /** Location manager */
  managerName: Scalars['String']['output'];
  /** Location name (e.g., Douala Main Store) */
  name: Scalars['String']['output'];
  /** Number of out-of-stock items at this location */
  outOfStockItems?: Maybe<Scalars['Int']['output']>;
  /** Contact phone */
  phone: Scalars['String']['output'];
  /** Cameroon region */
  region: WorkspaceStoreLocationRegionChoices;
  /** Total products at location */
  totalProducts: Scalars['Int']['output'];
  /** Total stock quantity at this location */
  totalStock?: Maybe<Scalars['Int']['output']>;
  /** Total inventory value */
  totalStockValue: Scalars['Decimal']['output'];
  /** Total inventory value at this location */
  totalValue?: Maybe<Scalars['Float']['output']>;
  updatedAt: Scalars['DateTime']['output'];
}

/** GraphQL type for low stock alerts */
export interface LowStockAlertType {
  __typename?: 'LowStockAlertType';
  currentQuantity?: Maybe<Scalars['Int']['output']>;
  locationId?: Maybe<Scalars['String']['output']>;
  locationName?: Maybe<Scalars['String']['output']>;
  lowStockThreshold?: Maybe<Scalars['Int']['output']>;
  needsReorder?: Maybe<Scalars['Boolean']['output']>;
  stockStatus?: Maybe<Scalars['String']['output']>;
  variantId?: Maybe<Scalars['String']['output']>;
  variantName?: Maybe<Scalars['String']['output']>;
}

/**
 * Mark order as paid (for COD and WhatsApp orders)
 *
 * Performance: Atomic update with proper validation
 * Security: Workspace scoping and permission validation
 * Use Case: Admin marks COD/WhatsApp orders as paid upon delivery/confirmation
 */
export interface MarkOrderAsPaid {
  __typename?: 'MarkOrderAsPaid';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
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
  __typename?: 'MediaUploadType';
  /** File size in bytes */
  fileSize: Scalars['BigInt']['output'];
  /** Image/video height in pixels */
  height?: Maybe<Scalars['Int']['output']>;
  id: Scalars['UUID']['output'];
  /** Type of media (image, video, 3D model) */
  mediaType: MedialibMediaUploadMediaTypeChoices;
  /** Additional metadata (format, duration for videos, etc.) */
  metadata: Scalars['JSONString']['output'];
  /** MIME type (e.g., image/jpeg, video/mp4) */
  mimeType: Scalars['String']['output'];
  /** Optimized version URL (for images) */
  optimizedUrl?: Maybe<Scalars['String']['output']>;
  /** Original filename from upload */
  originalFilename: Scalars['String']['output'];
  /** Processing status */
  status: MedialibMediaUploadStatusChoices;
  /** Thumbnail URL (for images/videos) */
  thumbnailUrl?: Maybe<Scalars['String']['output']>;
  uploadedAt: Scalars['DateTime']['output'];
  /** Primary media URL (CDN) */
  url?: Maybe<Scalars['String']['output']>;
  /** Image/video width in pixels */
  width?: Maybe<Scalars['Int']['output']>;
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
 * GraphQL type for MerchantPaymentMethod model.
 *
 * Exposes payment method configuration for workspace settings.
 */
export interface MerchantPaymentMethodType extends Node {
  __typename?: 'MerchantPaymentMethodType';
  capabilities?: Maybe<ProviderCapabilitiesType>;
  /** Merchant's payment checkout URL (for external redirect providers) */
  checkoutUrl?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  /** Human-readable provider name */
  displayName?: Maybe<Scalars['String']['output']>;
  /** Merchant has enabled this payment method */
  enabled: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  lastUsedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Payment provider (fapshi, mtn, orange, flutterwave) */
  providerName: Scalars['String']['output'];
  /** Success rate percentage */
  successRate?: Maybe<Scalars['Float']['output']>;
  successfulTransactions: Scalars['Int']['output'];
  totalTransactions: Scalars['Int']['output'];
  updatedAt: Scalars['DateTime']['output'];
  /** URL validated or credentials verified */
  verified: Scalars['Boolean']['output'];
}

/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface Mutation {
  __typename?: 'Mutation';
  /**
   * Accept workspace invitation
   * Creates membership when user accepts invite via email link
   *
   * Public mutation: No permission required (uses invite token)
   * Security: Token-based validation, single-use
   */
  acceptInvite?: Maybe<AcceptInvite>;
  /** Add comment to order timeline */
  addOrderComment?: Maybe<AddOrderComment>;
  /**
   * Add a payment method to workspace.
   *
   * For Fapshi: Requires checkout_url from merchant's Fapshi dashboard.
   * Uses atomic transaction to ensure data integrity.
   */
  addPaymentMethod?: Maybe<AddPaymentMethod>;
  /**
   * Add products to category with atomic transaction
   *
   * Security: Validates workspace ownership for both category and products
   * Integrity: Uses @transaction.atomic for rollback
   * Performance: Bulk operation for multiple products
   */
  addProductsToCategory?: Maybe<AddProductsToCategory>;
  /**
   * Archive an order to remove it from active view
   *
   * Performance: Atomic update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Validates order can be archived before update
   */
  archiveOrder?: Maybe<ArchiveOrder>;
  /**
   * Process multiple CSV files in bulk with background jobs
   *
   * Performance: Async processing with progress tracking
   * Scalability: Background job processing for large batches
   * Reliability: Job queuing with retry mechanisms
   */
  bulkCsvProcessing?: Maybe<BulkCsvProcessing>;
  /**
   * Delete multiple products in background
   *
   * Follows GraphQL architecture standards:
   * - Service layer integration
   * - Proper typed response
   * - Input validation
   * - Workspace scoping
   */
  bulkDeleteProducts?: Maybe<BulkDeleteResponse>;
  /**
   * Process multiple documents in bulk with background jobs
   *
   * Performance: Async processing with progress tracking
   * Scalability: Handles large batches with background workers
   * Reliability: Job queuing with retry mechanisms
   */
  bulkDocumentProcessing?: Maybe<BulkDocumentProcessing>;
  /**
   * Unified mutation for bulk product imports from ANY file type
   *
   * CONSOLIDATES: CSV uploads, document uploads, image uploads
   * USES: ProductImportService for ALL business logic
   * PARSERS: Only extract data, no validation/creation
   *
   * Flow:
   * 1. Detect file type (CSV vs Document)
   * 2. Route to appropriate parser for extraction
   * 3. ProductImportService validates & imports
   * 4. Return job_id for progress tracking
   *
   * Performance: Async processing, returns immediately with job_id
   * Scalability: Handles 10,000+ products via chunked processing
   * Reliability: Atomic transactions, continues on errors
   * Security: File size limits, workspace scoping, input validation
   */
  bulkImportProducts?: Maybe<BulkImportProducts>;
  /**
   * Publish multiple products in background
   *
   * Follows GraphQL architecture standards:
   * - Service layer integration
   * - Proper typed response
   * - Input validation
   * - Workspace scoping
   */
  bulkPublishProducts?: Maybe<BulkPublishResponse>;
  /**
   * Unpublish multiple products in background
   *
   * Follows GraphQL architecture standards:
   * - Service layer integration
   * - Proper typed response
   * - Input validation
   * - Workspace scoping
   */
  bulkUnpublishProducts?: Maybe<BulkPublishResponse>;
  /**
   * Update inventory for multiple variants across regions
   *
   * Follows GraphQL architecture standards:
   * - Service layer integration
   * - Proper typed response
   * - Input validation
   * - Workspace scoping
   */
  bulkUpdateInventory?: Maybe<BulkUpdateResponse>;
  /**
   * Process bulk order status updates
   *
   * Performance: Optimized bulk operations with transaction
   * Scalability: Handles up to 500 updates per batch
   * Reliability: Atomic transaction with rollback on failure
   */
  bulkUpdateOrderStatus?: Maybe<BulkUpdateOrderStatus>;
  /**
   * Update prices for multiple products in background
   *
   * Follows GraphQL architecture standards:
   * - Service layer integration
   * - Proper typed response
   * - Input validation
   * - Workspace scoping
   */
  bulkUpdatePrices?: Maybe<BulkUpdateResponse>;
  /**
   * Bulk update stock quantities for multiple inventory items
   *
   * Performance: Optimized bulk operations with transaction
   * Scalability: Handles up to 1000 updates per batch
   * Reliability: Atomic transaction with rollback on failure
   */
  bulkUpdateStock?: Maybe<BulkUpdateStock>;
  /**
   * Cancel pending workspace invitation
   *
   * Requires: 'staff:invite' permission
   */
  cancelInvite?: Maybe<CancelInvite>;
  /**
   * Cancel an order with validation and inventory restoration
   *
   * Performance: Atomic cancellation with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive validation and rollback
   */
  cancelOrder?: Maybe<CancelOrder>;
  /**
   * Change workspace member's role
   * Used in member details page and users list
   *
   * Requires: 'staff:role_change' permission
   * Security: Prevents self-privilege escalation, owner role changes
   */
  changeStaffRole?: Maybe<ChangeStaffRole>;
  /**
   * Clear import progress from cache (cleanup)
   *
   * Use after: Import completed and user acknowledged results
   */
  clearImportProgress?: Maybe<ClearImportProgress>;
  /**
   * Create a cash on delivery order
   *
   * Payment status remains 'pending' until marked as paid on delivery
   */
  createCashOnDeliveryOrder?: Maybe<CreateCashOnDeliveryOrder>;
  /**
   * Create new category with atomic transaction (Shopify-style)
   *
   * Security: Validates workspace ownership
   * Integrity: Uses @transaction.atomic for rollback
   * Hierarchical: Validates parent relationships
   * Images: Accepts single image file upload
   */
  createCategory?: Maybe<CreateCategory>;
  /**
   * Create customer with atomic transaction using CustomerMutationService
   *
   * Performance: Atomic creation with validation
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive validation and rollback
   */
  createCustomer?: Maybe<CreateCustomer>;
  /** Create discount with service layer orchestration */
  createDiscount?: Maybe<CreateDiscount>;
  /**
   * Create inventory entries for a new variant across multiple locations
   *
   * Performance: Bulk creation with transaction
   * Scalability: Handles multiple location assignments
   * Reliability: Atomic operation with rollback
   */
  createInventoryForVariant?: Maybe<CreateInventoryForVariant>;
  /** Create location (warehouse/store) */
  createLocation?: Maybe<CreateLocation>;
  /**
   * Create a new order with validation and inventory checks
   *
   * Performance: Atomic creation with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive error handling with rollback
   */
  createOrder?: Maybe<CreateOrder>;
  /** Create shipping package */
  createPackage?: Maybe<CreatePackage>;
  /**
   * Create product using ProductService
   *
   * Core required: name, price
   * Optional: All other fields including variants, shipping, SEO
   * Performance: Atomic creation with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive validation and rollback
   */
  createProduct?: Maybe<CreateProduct>;
  /** Create sales channel with atomic transaction */
  createSalesChannel?: Maybe<CreateSalesChannel>;
  /**
   * Create a WhatsApp order
   *
   * Creates order and sends WhatsApp DM to admin
   */
  createWhatsappOrder?: Maybe<CreateWhatsAppOrder>;
  /**
   * Delete category with atomic transaction
   *
   * Security: Validates workspace ownership
   * Integrity: Uses @transaction.atomic for rollback
   * Safety: Prevents deletion of categories with products
   * Hierarchical: Handles orphaned children
   */
  deleteCategory?: Maybe<DeleteCategory>;
  /**
   * Delete customer with validation and atomic transaction using CustomerMutationService
   *
   * Performance: Atomic deletion with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive validation and rollback
   */
  deleteCustomer?: Maybe<DeleteCustomer>;
  /** Delete discount with service layer orchestration */
  deleteDiscount?: Maybe<DeleteDiscount>;
  /** Delete location */
  deleteLocation?: Maybe<DeleteLocation>;
  /**
   * Delete media upload (soft delete)
   *
   * User can manually manage their storage
   */
  deleteMedia?: Maybe<DeleteMedia>;
  /** Delete shipping package */
  deletePackage?: Maybe<DeletePackage>;
  /**
   * Delete product with validation and atomic transaction using ProductService
   *
   * Performance: Atomic deletion with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive validation and rollback
   */
  deleteProduct?: Maybe<DeleteProduct>;
  /** Delete sales channel with atomic transaction */
  deleteSalesChannel?: Maybe<DeleteSalesChannel>;
  /**
   * Duplicate existing product with variants and inventory using ProductService
   *
   * Performance: Bulk operations with transaction
   * Scalability: Handles complex product structures
   * Reliability: Atomic operation with rollback
   *
   * Smart Naming (if new_name not provided):
   * - Auto-generates: "Product (Copy 1)", "Product (Copy 2)", etc.
   * - Strips existing (Copy N) patterns to avoid nesting
   * - Slug pattern: "product-copy-1", "product-copy-2", etc.
   */
  duplicateProduct?: Maybe<DuplicateProduct>;
  /**
   * Extract products from previously uploaded document
   *
   * Performance: Optimized for re-processing existing documents
   * Scalability: Handles multiple document formats and sizes
   * Reliability: Comprehensive error handling and validation
   */
  extractProductsFromDocument?: Maybe<ExtractProductsFromDocument>;
  /**
   * Get progress of CSV upload and parsing job
   *
   * Performance: Fast cache lookup for progress information
   * Scalability: Handles multiple concurrent progress queries
   * Reliability: Graceful handling of missing job IDs
   */
  getCsvUploadProgress?: Maybe<GetCsvUploadProgress>;
  /**
   * Get real-time progress of import operation
   *
   * Performance: Fast cache lookup (< 5ms)
   * Scalability: Handles concurrent progress queries
   * Reliability: Graceful handling of expired/missing jobs
   */
  getImportProgress?: Maybe<GetImportProgress>;
  /**
   * Get comprehensive inventory summary for workspace
   *
   * Performance: Optimized aggregations with proper indexing
   * Scalability: Efficient queries for large datasets
   * Security: Workspace scoping and permission validation
   */
  getInventorySummary?: Maybe<GetInventorySummary>;
  /**
   * Get low stock alerts for workspace
   *
   * Performance: Optimized queries for alert detection
   * Scalability: Handles large inventory catalogs
   * Reliability: Comprehensive error handling
   */
  getLowStockAlerts?: Maybe<GetLowStockAlerts>;
  /**
   * Invite staff to workspace with email and role
   * Following Shopify "Add users" pattern
   *
   * Requires: 'staff:invite' permission
   * Flow: Creates invite -> Sends email (async) -> User accepts -> Membership created
   */
  inviteStaff?: Maybe<InviteStaff>;
  /**
   * Mark order as paid (for COD and WhatsApp orders)
   *
   * Performance: Atomic update with proper validation
   * Security: Workspace scoping and permission validation
   * Use Case: Admin marks COD/WhatsApp orders as paid upon delivery/confirmation
   */
  markOrderAsPaid?: Maybe<MarkOrderAsPaid>;
  /**
   * Reactivate suspended staff member
   *
   * Requires: 'staff:reactivate' permission
   * Security: Can only reactivate SUSPENDED members
   */
  reactivateStaff?: Maybe<ReactivateStaff>;
  /**
   * Remove a payment method from workspace.
   *
   * Uses atomic transaction with row-level locking.
   */
  removePaymentMethod?: Maybe<RemovePaymentMethod>;
  /**
   * Remove products from category with atomic transaction
   *
   * Security: Validates workspace ownership for both category and products
   * Integrity: Uses @transaction.atomic for rollback
   * Performance: Bulk operation for multiple products
   */
  removeProductsFromCategory?: Maybe<RemoveProductsFromCategory>;
  /**
   * Permanently remove staff member from workspace (cannot be reactivated)
   *
   * CRITICAL: This is permanent removal. For temporary suspension, use SuspendStaff.
   *
   * Requires: 'staff:remove' permission
   * Security: Cannot remove self or workspace owner
   */
  removeStaff?: Maybe<RemoveStaff>;
  /**
   * Reorder categories with atomic transaction
   *
   * Security: Validates workspace ownership
   * Integrity: Uses @transaction.atomic for rollback
   * Performance: Bulk update for efficiency
   */
  reorderCategories?: Maybe<ReorderCategories>;
  /**
   * Resend workspace invitation email
   * Extends expiration date and resends email
   *
   * Requires: 'staff:invite' permission
   */
  resendInvite?: Maybe<ResendInvite>;
  /**
   * Suspend staff member from workspace (temporary, can be reactivated)
   *
   * Requires: 'staff:suspend' permission
   * Security: Cannot suspend self or workspace owner
   */
  suspendStaff?: Maybe<SuspendStaff>;
  /** Sync inventory using SalesChannelService */
  syncInventory?: Maybe<SyncInventory>;
  /**
   * Toggle category visibility with atomic transaction
   *
   * Security: Validates workspace ownership
   * Integrity: Uses @transaction.atomic for rollback
   */
  toggleCategoryVisibility?: Maybe<ToggleCategoryVisibility>;
  /**
   * Toggle customer active status with validation using CustomerMutationService
   *
   * Performance: Atomic status update
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive status validation
   */
  toggleCustomerStatus?: Maybe<ToggleCustomerStatus>;
  /**
   * Enable or disable a payment method.
   *
   * Uses atomic transaction with row-level locking.
   */
  togglePaymentMethod?: Maybe<TogglePaymentMethod>;
  /**
   * Toggle product status with validation using ProductService
   *
   * Performance: Atomic status update
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive status validation
   */
  toggleProductStatus?: Maybe<ToggleProductStatus>;
  /**
   * Transfer inventory between locations
   *
   * Performance: Atomic transaction with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Rollback on failure
   */
  transferInventory?: Maybe<TransferInventory>;
  /**
   * Unarchive an order to restore it to active view
   *
   * Performance: Atomic update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Validates order can be unarchived before update
   */
  unarchiveOrder?: Maybe<UnarchiveOrder>;
  /**
   * Update category with atomic transaction (Shopify-style)
   *
   * Security: Validates workspace ownership
   * Integrity: Uses @transaction.atomic for rollback
   * Hierarchical: Validates parent relationships
   * Images: Replace category banner image
   */
  updateCategory?: Maybe<UpdateCategory>;
  /**
   * Update customer with atomic transaction using CustomerMutationService
   *
   * Performance: Atomic update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive error handling with rollback
   */
  updateCustomer?: Maybe<UpdateCustomer>;
  /**
   * Update customer tags with atomic transaction using CustomerMutationService
   *
   * Performance: Atomic tag operations
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive tag validation
   */
  updateCustomerTags?: Maybe<UpdateCustomerTags>;
  /** Update discount with service layer orchestration */
  updateDiscount?: Maybe<UpdateDiscount>;
  /**
   * Update inventory for a variant at a specific location
   *
   * Performance: Atomic update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive error handling with rollback
   */
  updateInventory?: Maybe<UpdateInventory>;
  /** Update location */
  updateLocation?: Maybe<UpdateLocation>;
  /** Update order notes */
  updateOrderNotes?: Maybe<UpdateOrderNotes>;
  /**
   * Update order status with validation and side effects
   *
   * Performance: Atomic update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive status transition validation
   */
  updateOrderStatus?: Maybe<UpdateOrderStatus>;
  /** Update shipping package */
  updatePackage?: Maybe<UpdatePackage>;
  /**
   * Update payment method configuration (e.g., checkout URL).
   *
   * Uses atomic transaction with row-level locking.
   */
  updatePaymentMethod?: Maybe<UpdatePaymentMethod>;
  /**
   * Update product with atomic transaction using ProductService
   *
   * Performance: Atomic update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive error handling with rollback
   */
  updateProduct?: Maybe<UpdateProduct>;
  /**
   * Update product stock quantity with atomic transaction using ProductService
   *
   * Performance: Atomic stock update with proper locking
   * Security: Workspace scoping and permission validation
   * Reliability: Comprehensive validation and rollback
   */
  updateProductStock?: Maybe<UpdateProductStock>;
  /** Update sales channel with atomic transaction */
  updateSalesChannel?: Maybe<UpdateSalesChannel>;
  /**
   * Update store profile settings.
   *
   * Validates Cameroon phone numbers and returns proper error messages.
   * Uses atomic transaction for data integrity.
   */
  updateStoreProfile?: Maybe<UpdateStoreProfile>;
  /** Update variant with atomic transaction */
  updateVariant?: Maybe<UpdateVariant>;
  /**
   * Upload and parse CSV file for bulk product creation
   *
   * Performance: Async processing with progress tracking
   * Scalability: Background job processing for large files
   * Reliability: Comprehensive error handling with retry mechanisms
   * Security: File validation and workspace scoping
   */
  uploadAndParseCsv?: Maybe<UploadAndParseCsv>;
  /**
   * Upload and process document for product extraction
   *
   * Performance: Async processing for large documents
   * Scalability: Background job processing with progress tracking
   * Reliability: Retry mechanisms and comprehensive error handling
   * Security: File validation and workspace scoping
   */
  uploadAndProcessDocument?: Maybe<UploadAndProcessDocument>;
  /**
   * Upload media file with automatic processing (NEW FK-based system)
   *
   * Flow:
   * 1. Upload media → Get upload_id
   * 2. Attach to entity → entity.featured_media_id = upload_id
   *
   * Process:
   * 1. User selects file in UI
   * 2. Immediately upload to backend (entity-agnostic)
   * 3. Return upload_id and preview URL
   * 4. User can attach to product/category later via FK
   *
   * Benefits:
   * - Images persist even if user cancels entity creation
   * - Immediately available in "Recent uploads"
   * - Real upload progress feedback
   * - Can reuse across multiple entities (just set FK)
   */
  uploadMedia?: Maybe<UploadMedia>;
  /**
   * Upload media from URL (download and store)
   *
   * Process:
   * 1. Download file from URL
   * 2. Validate and process
   * 3. Store in MediaUpload table
   */
  uploadMediaFromUrl?: Maybe<UploadMediaFromUrl>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationAcceptInviteArgs {
  token: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationAddOrderCommentArgs {
  isInternal?: InputMaybe<Scalars['Boolean']['input']>;
  message: Scalars['String']['input'];
  orderId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationAddPaymentMethodArgs {
  input: AddPaymentMethodInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationAddProductsToCategoryArgs {
  categoryId: Scalars['ID']['input'];
  productIds: Array<Scalars['ID']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationArchiveOrderArgs {
  orderId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkCsvProcessingArgs {
  csvFiles: Array<InputMaybe<CsvUploadInput>>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkDeleteProductsArgs {
  productIds: Array<InputMaybe<Scalars['ID']['input']>>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkDocumentProcessingArgs {
  documents: Array<InputMaybe<DocumentUploadInput>>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkImportProductsArgs {
  importData: BulkProductImportInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkPublishProductsArgs {
  productIds: Array<InputMaybe<Scalars['ID']['input']>>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkUnpublishProductsArgs {
  productIds: Array<InputMaybe<Scalars['ID']['input']>>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkUpdateInventoryArgs {
  inventoryUpdates: Array<InventoryUpdateInput>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkUpdateOrderStatusArgs {
  bulkData: BulkStatusUpdateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkUpdatePricesArgs {
  priceUpdates: Array<PriceUpdateInput>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationBulkUpdateStockArgs {
  bulkData: BulkStockUpdateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCancelInviteArgs {
  inviteId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCancelOrderArgs {
  orderId: Scalars['String']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationChangeStaffRoleArgs {
  input: ChangeStaffRoleInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationClearImportProgressArgs {
  jobId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateCashOnDeliveryOrderArgs {
  orderData: OrderCreateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateCategoryArgs {
  description?: InputMaybe<Scalars['String']['input']>;
  featuredMediaId?: InputMaybe<Scalars['String']['input']>;
  isFeatured?: InputMaybe<Scalars['Boolean']['input']>;
  isVisible?: InputMaybe<Scalars['Boolean']['input']>;
  metaDescription?: InputMaybe<Scalars['String']['input']>;
  metaTitle?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  slug?: InputMaybe<Scalars['String']['input']>;
  sortOrder?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateCustomerArgs {
  customerData: CustomerCreateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateDiscountArgs {
  input: DiscountInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateInventoryForVariantArgs {
  locationsData: Array<InputMaybe<Scalars['JSONString']['input']>>;
  variantId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateLocationArgs {
  input: LocationInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateOrderArgs {
  orderData: OrderCreateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreatePackageArgs {
  input: PackageInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateProductArgs {
  productData: ProductCreateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateSalesChannelArgs {
  input: SalesChannelInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationCreateWhatsappOrderArgs {
  orderData: OrderCreateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteCategoryArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteCustomerArgs {
  customerId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteDiscountArgs {
  discountId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteLocationArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteMediaArgs {
  uploadId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeletePackageArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteProductArgs {
  productId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDeleteSalesChannelArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationDuplicateProductArgs {
  copyInventory?: InputMaybe<Scalars['Boolean']['input']>;
  copyVariants?: InputMaybe<Scalars['Boolean']['input']>;
  newName?: InputMaybe<Scalars['String']['input']>;
  productId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationExtractProductsFromDocumentArgs {
  documentId: Scalars['ID']['input'];
  extractionOptions?: InputMaybe<Scalars['JSONString']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationGetCsvUploadProgressArgs {
  jobId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationGetImportProgressArgs {
  jobId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationInviteStaffArgs {
  input: InviteStaffInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationMarkOrderAsPaidArgs {
  orderId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationReactivateStaffArgs {
  memberId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationRemovePaymentMethodArgs {
  methodId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationRemoveProductsFromCategoryArgs {
  categoryId: Scalars['ID']['input'];
  productIds: Array<Scalars['ID']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationRemoveStaffArgs {
  memberId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationReorderCategoriesArgs {
  reorderData: Array<CategoryReorderInput>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationResendInviteArgs {
  inviteId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationSuspendStaffArgs {
  input: SuspendStaffInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationSyncInventoryArgs {
  channelId: Scalars['ID']['input'];
  productId: Scalars['String']['input'];
  quantity: Scalars['Int']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationToggleCategoryVisibilityArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationToggleCustomerStatusArgs {
  customerId: Scalars['String']['input'];
  newStatus: Scalars['Boolean']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationTogglePaymentMethodArgs {
  enabled: Scalars['Boolean']['input'];
  methodId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationToggleProductStatusArgs {
  newStatus: Scalars['String']['input'];
  productId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationTransferInventoryArgs {
  transferData: TransferInventoryInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUnarchiveOrderArgs {
  orderId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateCategoryArgs {
  description?: InputMaybe<Scalars['String']['input']>;
  featuredMediaId?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
  isFeatured?: InputMaybe<Scalars['Boolean']['input']>;
  isVisible?: InputMaybe<Scalars['Boolean']['input']>;
  metaDescription?: InputMaybe<Scalars['String']['input']>;
  metaTitle?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  parentId?: InputMaybe<Scalars['ID']['input']>;
  removeFeaturedMedia?: InputMaybe<Scalars['Boolean']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
  sortOrder?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateCustomerArgs {
  customerId: Scalars['String']['input'];
  updateData: CustomerUpdateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateCustomerTagsArgs {
  customerId: Scalars['String']['input'];
  tagOperations: CustomerTagUpdateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateDiscountArgs {
  discountId: Scalars['String']['input'];
  updateData: DiscountInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateInventoryArgs {
  updateData: UpdateInventoryInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateLocationArgs {
  id: Scalars['ID']['input'];
  input: LocationInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateOrderNotesArgs {
  notes: Scalars['String']['input'];
  orderId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateOrderStatusArgs {
  newStatus: Scalars['String']['input'];
  orderId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdatePackageArgs {
  id: Scalars['ID']['input'];
  input: PackageInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdatePaymentMethodArgs {
  input: UpdatePaymentMethodInput;
  methodId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateProductArgs {
  productId: Scalars['String']['input'];
  updateData: ProductUpdateInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateProductStockArgs {
  productId: Scalars['String']['input'];
  stockQuantity: Scalars['Int']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateSalesChannelArgs {
  id: Scalars['ID']['input'];
  input: SalesChannelInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateStoreProfileArgs {
  input: StoreProfileInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUpdateVariantArgs {
  updateData: VariantUpdateInput;
  variantId: Scalars['String']['input'];
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUploadAndParseCsvArgs {
  uploadData: CsvUploadInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUploadAndProcessDocumentArgs {
  uploadData: DocumentUploadInput;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUploadMediaArgs {
  file: Scalars['Upload']['input'];
  processVariations?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Root GraphQL Mutation
 *
 * Combines all mutation types for the admin store API
 * All mutations use @transaction.atomic for data integrity
 */
export interface MutationUploadMediaFromUrlArgs {
  filename?: InputMaybe<Scalars['String']['input']>;
  url: Scalars['String']['input'];
}

/**
 * Type for current user's permissions in workspace
 * Used for frontend UI state management
 */
export interface MyPermissionsType {
  __typename?: 'MyPermissionsType';
  canInviteStaff?: Maybe<Scalars['Boolean']['output']>;
  canManageRoles?: Maybe<Scalars['Boolean']['output']>;
  canRemoveStaff?: Maybe<Scalars['Boolean']['output']>;
  permissions?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  roleName?: Maybe<Scalars['String']['output']>;
}

/** An object with an ID */
export interface Node {
  /** The ID of the object */
  id: Scalars['ID']['output'];
}

/** GraphQL type for OrderComment model */
export interface OrderCommentType extends Node {
  __typename?: 'OrderCommentType';
  author?: Maybe<UserType>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** If true, visible only to staff */
  isInternal: Scalars['Boolean']['output'];
  /** Comment content */
  message: Scalars['String']['output'];
}

/**
 * Input for order creation
 *
 * Validation: Required fields and data structure
 * Security: Workspace scoping via JWT middleware
 * Regional: Cameroon-specific validation for phone and regions
 * Phone-first: customer_id required, customer data fetched from Customer table
 */
export interface OrderCreateInput {
  /** Billing address details */
  billingAddress?: InputMaybe<AddressInput>;
  /** Currency: XAF (default) */
  currency?: InputMaybe<Scalars['String']['input']>;
  /** Customer ID (fetches customer data automatically) */
  customerId: Scalars['String']['input'];
  /** Discount amount in XAF */
  discountAmount?: InputMaybe<Scalars['Decimal']['input']>;
  /** Order items */
  items: Array<InputMaybe<OrderItemInput>>;
  /** Order notes */
  notes?: InputMaybe<Scalars['String']['input']>;
  /** Order source: whatsapp, payment, manual */
  orderSource?: InputMaybe<Scalars['String']['input']>;
  /** Payment method: cash_on_delivery, whatsapp, mobile_money, card, bank_transfer */
  paymentMethod?: InputMaybe<Scalars['String']['input']>;
  /** Shipping address details */
  shippingAddress: AddressInput;
  /** Shipping cost in XAF */
  shippingCost?: InputMaybe<Scalars['Decimal']['input']>;
  /** Cameroon region: centre, littoral, west, northwest, southwest, adamawa, east, far_north, north, south */
  shippingRegion?: InputMaybe<Scalars['String']['input']>;
  /** Tax amount in XAF */
  taxAmount?: InputMaybe<Scalars['Decimal']['input']>;
}

/**
 * GraphQL type for OrderHistory model
 * System-generated timeline events
 */
export interface OrderHistoryType extends Node {
  __typename?: 'OrderHistoryType';
  /** Type of action performed */
  action: WorkspaceStoreOrderHistoryActionChoices;
  createdAt: Scalars['DateTime']['output'];
  /** Additional context about the action (old_status, new_status, etc.) */
  details: Scalars['JSONString']['output'];
  displayMessage?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  performedBy?: Maybe<UserType>;
}

/**
 * Input for order item
 *
 * Validation: Quantity must be positive, unit_price must be valid
 * Security: Product ID validation and workspace scoping
 */
export interface OrderItemInput {
  /** Product ID */
  productId: Scalars['String']['input'];
  /** Quantity (must be positive) */
  quantity: Scalars['Int']['input'];
  /** Unit price in XAF */
  unitPrice: Scalars['Decimal']['input'];
  /** Variant ID (if applicable) */
  variantId?: InputMaybe<Scalars['String']['input']>;
}

/**
 * GraphQL type for OrderItem model
 *
 * Features:
 * - All order item fields with proper typing
 * - Product and variant relationships
 * - Price calculations
 */
export interface OrderItemType extends Node {
  __typename?: 'OrderItemType';
  id: Scalars['ID']['output'];
  product?: Maybe<ProductType>;
  /** Product details at time of order */
  productData: Scalars['JSONString']['output'];
  /** Product name at time of order */
  productName: Scalars['String']['output'];
  /** Product SKU at time of order */
  productSku: Scalars['String']['output'];
  /** Quantity ordered */
  quantity: Scalars['Int']['output'];
  totalPrice?: Maybe<Scalars['Float']['output']>;
  /** Price per unit at time of order */
  unitPrice: Scalars['Decimal']['output'];
  variant?: Maybe<ProductVariantType>;
}

/**
 * GraphQL type for Order model
 *
 * Features:
 * - All order fields with proper typing
 * - Order items relationship with DataLoader
 * - Status tracking and analytics
 * - Cameroon-specific fields (order_source, shipping_region)
 */
export interface OrderType extends Node {
  __typename?: 'OrderType';
  /** When order was archived */
  archivedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Billing address if different from shipping (optional for MoMo/COD) */
  billingAddress?: Maybe<Scalars['JSONString']['output']>;
  canBeArchived?: Maybe<Scalars['Boolean']['output']>;
  canBeCancelled?: Maybe<Scalars['Boolean']['output']>;
  canBeRefunded?: Maybe<Scalars['Boolean']['output']>;
  canBeUnarchived?: Maybe<Scalars['Boolean']['output']>;
  canMarkAsPaid?: Maybe<Scalars['Boolean']['output']>;
  comments?: Maybe<Array<Maybe<OrderCommentType>>>;
  /** When order was confirmed */
  confirmedAt?: Maybe<Scalars['DateTime']['output']>;
  createdAt: Scalars['DateTime']['output'];
  /** Order currency */
  currency: Scalars['String']['output'];
  /** Reference to customer (for relationships and queries) */
  customer?: Maybe<CustomerType>;
  /** Customer email at time of order */
  customerEmail: Scalars['String']['output'];
  /** Customer full name at time of order */
  customerName: Scalars['String']['output'];
  /** Customer phone number at time of order */
  customerPhone: Scalars['String']['output'];
  /** When order was delivered */
  deliveredAt?: Maybe<Scalars['DateTime']['output']>;
  /** Discount applied */
  discountAmount: Scalars['Decimal']['output'];
  history?: Maybe<Array<Maybe<OrderHistoryType>>>;
  id: Scalars['ID']['output'];
  /** Whether order is archived */
  isArchived: Scalars['Boolean']['output'];
  isCashOnDelivery?: Maybe<Scalars['Boolean']['output']>;
  isPaid?: Maybe<Scalars['Boolean']['output']>;
  isWhatsappOrder?: Maybe<Scalars['Boolean']['output']>;
  itemCount?: Maybe<Scalars['Int']['output']>;
  items?: Maybe<Array<Maybe<OrderItemType>>>;
  /** Order notes */
  notes: Scalars['String']['output'];
  /** Unique order identifier */
  orderNumber: Scalars['String']['output'];
  /** Source of the order */
  orderSource: WorkspaceStoreOrderOrderSourceChoices;
  /** Payment method used */
  paymentMethod: WorkspaceStoreOrderPaymentMethodChoices;
  paymentStatus: WorkspaceStoreOrderPaymentStatusChoices;
  requiresPaymentProcessing?: Maybe<Scalars['Boolean']['output']>;
  /** When order was shipped */
  shippedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Complete shipping address */
  shippingAddress: Scalars['JSONString']['output'];
  /** Shipping cost */
  shippingCost: Scalars['Decimal']['output'];
  /** Shipping destination region */
  shippingRegion: WorkspaceStoreOrderShippingRegionChoices;
  status: WorkspaceStoreOrderStatusChoices;
  /** Order subtotal */
  subtotal: Scalars['Decimal']['output'];
  /** Tax amount */
  taxAmount: Scalars['Decimal']['output'];
  timeline?: Maybe<Array<Maybe<TimelineEventType>>>;
  /** Final order total */
  totalAmount: Scalars['Decimal']['output'];
  /** Shipping tracking number */
  trackingNumber: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface OrderTypeConnection {
  __typename?: 'OrderTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<OrderTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `OrderType` and its cursor. */
export interface OrderTypeEdge {
  __typename?: 'OrderTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<OrderType>;
}

/** Input for organization-related fields */
export interface OrganizationInput {
  brand?: InputMaybe<Scalars['String']['input']>;
  categoryId?: InputMaybe<Scalars['String']['input']>;
  productType?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Scalars['JSONString']['input']>;
  vendor?: InputMaybe<Scalars['String']['input']>;
}

/** Input for creating/updating shipping packages */
export interface PackageInput {
  estimatedDays?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  method: Scalars['String']['input'];
  name: Scalars['String']['input'];
  packageType?: InputMaybe<Scalars['String']['input']>;
  regionFees: Scalars['JSONString']['input'];
  size?: InputMaybe<Scalars['String']['input']>;
  useAsDefault?: InputMaybe<Scalars['Boolean']['input']>;
  weight?: InputMaybe<Scalars['Decimal']['input']>;
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
  __typename?: 'PackageType';
  createdAt: Scalars['DateTime']['output'];
  /** Estimated delivery time (e.g., '1-2', '3-5 days') */
  estimatedDays: Scalars['String']['output'];
  fullDescription?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Whether this package is active */
  isActive: Scalars['Boolean']['output'];
  /** Shipping method (e.g., 'Car', 'Bike', 'Moto-taxi') */
  method: Scalars['String']['output'];
  /** Package name (e.g., 'Buea Car Shipping') */
  name: Scalars['String']['output'];
  /** Type of package */
  packageType: WorkspaceStorePackagePackageTypeChoices;
  productCount?: Maybe<Scalars['Int']['output']>;
  /** Shipping fees by region in XAF format: {'yaounde': 1500, 'douala': 1200, 'buea': 1000} */
  regionFees: Scalars['JSONString']['output'];
  /** Package size */
  size: WorkspaceStorePackageSizeChoices;
  updatedAt: Scalars['DateTime']['output'];
  /** Use this package as default fallback for products without shipping */
  useAsDefault: Scalars['Boolean']['output'];
  /** Weight capacity in kg */
  weight?: Maybe<Scalars['Decimal']['output']>;
}

export interface PackageTypeConnection {
  __typename?: 'PackageTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<PackageTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `PackageType` and its cursor. */
export interface PackageTypeEdge {
  __typename?: 'PackageTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<PackageType>;
}

/** The Relay compliant `PageInfo` type, containing data necessary to paginate this connection. */
export interface PageInfo {
  __typename?: 'PageInfo';
  /** When paginating forwards, the cursor to continue. */
  endCursor?: Maybe<Scalars['String']['output']>;
  /** When paginating forwards, are there more items? */
  hasNextPage: Scalars['Boolean']['output'];
  /** When paginating backwards, are there more items? */
  hasPreviousPage: Scalars['Boolean']['output'];
  /** When paginating backwards, the cursor to continue. */
  startCursor?: Maybe<Scalars['String']['output']>;
}

/** Payment method distribution - BASIC tier */
export interface PaymentBreakdown {
  __typename?: 'PaymentBreakdown';
  /** Orders paid via Bank Transfer */
  bankTransfer?: Maybe<Scalars['Int']['output']>;
  /** Orders paid via Card */
  card?: Maybe<Scalars['Int']['output']>;
  /** Orders paid via Cash on Delivery */
  cashOnDelivery?: Maybe<Scalars['Int']['output']>;
  /** Orders paid via Mobile Money */
  mobileMoney?: Maybe<Scalars['Int']['output']>;
  /** Orders via WhatsApp */
  whatsapp?: Maybe<Scalars['Int']['output']>;
}

/**
 * Type for permission summary (used in member details page)
 * Groups permissions by resource for display
 */
export interface PermissionSummaryType {
  __typename?: 'PermissionSummaryType';
  grantedPermissions?: Maybe<Scalars['Int']['output']>;
  permissions?: Maybe<Array<Maybe<PermissionType>>>;
  resource?: Maybe<Scalars['String']['output']>;
  totalPermissions?: Maybe<Scalars['Int']['output']>;
}

/**
 * GraphQL type for Permission model
 * Represents individual permissions like 'product:create', 'order:refund'
 */
export interface PermissionType {
  __typename?: 'PermissionType';
  createdAt: Scalars['DateTime']['output'];
  /** Human-readable description of what this permission allows */
  description: Scalars['String']['output'];
  displayName?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Permission key in format 'resource:action' (e.g., 'product:create') */
  key: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface PriceUpdateInput {
  newPrice: Scalars['Float']['input'];
  productId: Scalars['ID']['input'];
}

/**
 * Input for product creation (Shopify-style)
 *
 * Core required: name, price
 * Optional: All other fields including variants, shipping, SEO, images
 * Security: Workspace scoping via JWT middleware
 *
 * Images: Accepts array of Upload scalars for direct file uploads
 */
export interface ProductCreateInput {
  chargeTax?: InputMaybe<Scalars['Boolean']['input']>;
  chargesAmount?: InputMaybe<Scalars['Decimal']['input']>;
  compareAtPrice?: InputMaybe<Scalars['Decimal']['input']>;
  costPrice?: InputMaybe<Scalars['Decimal']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  /** Featured image ID (product thumbnail) */
  featuredMediaId?: InputMaybe<Scalars['String']['input']>;
  hasVariants?: InputMaybe<Scalars['Boolean']['input']>;
  /** Inventory-related fields */
  inventory?: InputMaybe<InventoryInput>;
  /** Array of media IDs for gallery (images/videos/3D models) */
  mediaIds?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  name: Scalars['String']['input'];
  /** Option definitions (e.g., [{'option_name':'Color', 'option_values': ['Blue', 'Black']}]) */
  options?: InputMaybe<Array<InputMaybe<ProductVariantOptionInput>>>;
  /** Organization-related fields */
  organization?: InputMaybe<OrganizationInput>;
  paymentCharges?: InputMaybe<Scalars['Boolean']['input']>;
  price: Scalars['Decimal']['input'];
  /** SEO-related fields */
  seo?: InputMaybe<SeoInput>;
  /** Shipping-related fields */
  shipping?: InputMaybe<ShippingInput>;
  status?: InputMaybe<Scalars['String']['input']>;
  /** Explicit variants with featured images and inventory */
  variants?: InputMaybe<Array<InputMaybe<VariantInput>>>;
}

/**
 * GraphQL type for Product model
 *
 * Features:
 * - All product fields with proper typing
 * - Variants relationship with DataLoader
 * - Category relationships
 * - Stock and analytics properties
 */
export interface ProductType extends Node {
  __typename?: 'ProductType';
  /** Allow orders when out of stock */
  allowBackorders: Scalars['Boolean']['output'];
  /** Product barcode */
  barcode: Scalars['String']['output'];
  /** Product brand */
  brand: Scalars['String']['output'];
  /** Primary product category */
  category?: Maybe<CategoryType>;
  categoryName?: Maybe<Scalars['String']['output']>;
  /** Whether to charge tax on this product */
  chargeTax: Scalars['Boolean']['output'];
  /** Fixed payment charges amount (if applicable) */
  chargesAmount?: Maybe<Scalars['Decimal']['output']>;
  /** Original price for discounts */
  compareAtPrice?: Maybe<Scalars['Decimal']['output']>;
  conversionRate?: Maybe<Scalars['Float']['output']>;
  /** Cost/wholesale price */
  costPrice?: Maybe<Scalars['Decimal']['output']>;
  createdAt: Scalars['DateTime']['output'];
  /** Product description */
  description: Scalars['String']['output'];
  /** Featured image URL from featured_media FK */
  featuredImageUrl?: Maybe<Scalars['String']['output']>;
  /** Primary product image (thumbnail/featured) */
  featuredMedia?: Maybe<MediaUploadType>;
  hasDimensions?: Maybe<Scalars['Boolean']['output']>;
  /** Whether product has variants */
  hasVariants: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  /** Inventory health status */
  inventoryHealth: WorkspaceStoreProductInventoryHealthChoices;
  /** Available stock quantity */
  inventoryQuantity: Scalars['Int']['output'];
  isInStock?: Maybe<Scalars['Boolean']['output']>;
  isLowStock?: Maybe<Scalars['Boolean']['output']>;
  isOnSale?: Maybe<Scalars['Boolean']['output']>;
  /** Product media gallery (images, videos, 3D models) */
  mediaGallery?: Maybe<Array<Maybe<MediaUploadType>>>;
  /** SEO meta description */
  metaDescription: Scalars['String']['output'];
  /** SEO meta title */
  metaTitle: Scalars['String']['output'];
  /** Product name */
  name: Scalars['String']['output'];
  /** Product options for variants (e.g., [{'name': 'Size', 'values': ['S', 'M', 'L']}]) */
  options: Scalars['JSONString']['output'];
  /** Shipping package for this product (optional - falls back to default if not set) */
  package?: Maybe<PackageType>;
  /** Whether to apply Cameroon mobile money/payment method charges */
  paymentCharges: Scalars['Boolean']['output'];
  /** Selling price (required) */
  price: Scalars['Decimal']['output'];
  /** Type of product */
  productType: WorkspaceStoreProductProductTypeChoices;
  profitAmount?: Maybe<Scalars['Decimal']['output']>;
  profitMargin?: Maybe<Scalars['Float']['output']>;
  /** When product was published */
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Needs shipping */
  requiresShipping: Scalars['Boolean']['output'];
  salePercentage?: Maybe<Scalars['Int']['output']>;
  /** Stock Keeping Unit */
  sku: Scalars['String']['output'];
  /** URL-friendly identifier */
  slug: Scalars['String']['output'];
  /** Product status */
  status: WorkspaceStoreProductStatusChoices;
  stockStatus?: Maybe<Scalars['String']['output']>;
  /** Product tags for search */
  tags: Scalars['JSONString']['output'];
  totalStock?: Maybe<Scalars['Int']['output']>;
  /** Whether to track inventory */
  trackInventory: Scalars['Boolean']['output'];
  updatedAt: Scalars['DateTime']['output'];
  variants?: Maybe<Array<Maybe<ProductVariantType>>>;
  /** Product vendor */
  vendor: Scalars['String']['output'];
  /** Product weight (kg) */
  weight?: Maybe<Scalars['Decimal']['output']>;
}

export interface ProductTypeConnection {
  __typename?: 'ProductTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<ProductTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `ProductType` and its cursor. */
export interface ProductTypeEdge {
  __typename?: 'ProductTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<ProductType>;
}

/**
 * Input for product updates (Shopify-style)
 *
 * Validation: Field validation and data integrity
 * Security: Workspace scoping via JWT middleware
 * Images: Accepts array of Upload scalars for adding new images
 */
export interface ProductUpdateInput {
  chargeTax?: InputMaybe<Scalars['Boolean']['input']>;
  chargesAmount?: InputMaybe<Scalars['Decimal']['input']>;
  compareAtPrice?: InputMaybe<Scalars['Decimal']['input']>;
  costPrice?: InputMaybe<Scalars['Decimal']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  /** Featured image ID (product thumbnail) */
  featuredMediaId?: InputMaybe<Scalars['String']['input']>;
  /** Whether product has variants */
  hasVariants?: InputMaybe<Scalars['Boolean']['input']>;
  /** Inventory-related fields */
  inventory?: InputMaybe<InventoryInput>;
  /** Array of media IDs for gallery (images/videos/3D models) */
  mediaIds?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  name?: InputMaybe<Scalars['String']['input']>;
  /** Option definitions (e.g., [{'option_name':'Color', 'option_values': ['Blue', 'Black']}]) */
  options?: InputMaybe<Array<InputMaybe<ProductVariantOptionInput>>>;
  /** Organization-related fields */
  organization?: InputMaybe<OrganizationInput>;
  paymentCharges?: InputMaybe<Scalars['Boolean']['input']>;
  price?: InputMaybe<Scalars['Decimal']['input']>;
  /** SEO-related fields */
  seo?: InputMaybe<SeoInput>;
  /** Shipping-related fields */
  shipping?: InputMaybe<ShippingInput>;
  status?: InputMaybe<Scalars['String']['input']>;
  /** Update or add variants with featured images */
  variants?: InputMaybe<Array<InputMaybe<VariantInput>>>;
}

/** Input for variant options */
export interface ProductVariantOptionInput {
  optionName: Scalars['String']['input'];
  optionValues: Array<InputMaybe<Scalars['String']['input']>>;
}

/** GraphQL type for ProductVariant model */
export interface ProductVariantType extends Node {
  __typename?: 'ProductVariantType';
  /** Barcode (ISBN, UPC, GTIN, etc.) */
  barcode?: Maybe<Scalars['String']['output']>;
  /** Compare at price (overrides product compare_at_price) */
  compareAtPrice?: Maybe<Scalars['Decimal']['output']>;
  /** Cost per item (overrides product cost_price) */
  costPrice?: Maybe<Scalars['Decimal']['output']>;
  createdAt: Scalars['DateTime']['output'];
  displayName?: Maybe<Scalars['String']['output']>;
  effectivePrice?: Maybe<Scalars['Float']['output']>;
  /** Featured image URL from featured_media FK */
  featuredImageUrl?: Maybe<Scalars['String']['output']>;
  /** Featured image for this variant */
  featuredMedia?: Maybe<MediaUploadType>;
  id: Scalars['ID']['output'];
  inventory?: Maybe<Array<Maybe<InventoryType>>>;
  /** Available for purchase */
  isActive: Scalars['Boolean']['output'];
  isAvailable?: Maybe<Scalars['Boolean']['output']>;
  /** Option (e.g., Size, Color) */
  option1?: Maybe<Scalars['String']['output']>;
  /** Additional option */
  option2?: Maybe<Scalars['String']['output']>;
  /** Third option (if needed) */
  option3?: Maybe<Scalars['String']['output']>;
  /** Display position */
  position: Scalars['Int']['output'];
  /** Price (overrides product price) */
  price?: Maybe<Scalars['Decimal']['output']>;
  /** Parent product */
  product: ProductType;
  /** Stock Keeping Unit */
  sku: Scalars['String']['output'];
  totalStock?: Maybe<Scalars['Int']['output']>;
  /** Track inventory for this variant */
  trackInventory: Scalars['Boolean']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface ProductVariantTypeConnection {
  __typename?: 'ProductVariantTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<ProductVariantTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `ProductVariantType` and its cursor. */
export interface ProductVariantTypeEdge {
  __typename?: 'ProductVariantTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<ProductVariantType>;
}

/**
 * GraphQL type for payment provider capabilities.
 * Nested object within MerchantPaymentMethodType.
 */
export interface ProviderCapabilitiesType {
  __typename?: 'ProviderCapabilitiesType';
  displayName?: Maybe<Scalars['String']['output']>;
  paymentModes?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  supportedCurrencies?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  supportsRefunds?: Maybe<Scalars['Boolean']['output']>;
  supportsWebhooks?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface Query {
  __typename?: 'Query';
  /** Get active sales channels */
  activeChannels?: Maybe<Array<Maybe<SalesChannelType>>>;
  /** Get active discounts */
  activeDiscounts?: Maybe<Array<Maybe<DiscountType>>>;
  /** Get active packages (for product dropdown) */
  activePackages?: Maybe<Array<Maybe<PackageType>>>;
  /** List all available permissions in the system */
  availablePermissions?: Maybe<Array<Maybe<PermissionType>>>;
  /** List payment providers available to add */
  availableProviders?: Maybe<Array<Maybe<AvailableProviderType>>>;
  /** Get bulk operation by ID */
  bulkOperation?: Maybe<BulkOperationType>;
  /** Get paginated list of bulk operations */
  bulkOperations?: Maybe<BulkOperationTypeConnection>;
  /** List all categories with pagination and filtering */
  categories?: Maybe<CategoryTypeConnection>;
  /** Get single category by ID */
  category?: Maybe<CategoryType>;
  /** Get category by slug */
  categoryBySlug?: Maybe<CategoryType>;
  /** Get products in a specific category */
  categoryProducts?: Maybe<Array<Maybe<ProductType>>>;
  /** Get single channel order by ID */
  channelOrder?: Maybe<ChannelOrderType>;
  /** List channel orders with pagination and filtering */
  channelOrders?: Maybe<ChannelOrderTypeConnection>;
  /** Get single channel product by ID */
  channelProduct?: Maybe<ChannelProductType>;
  /** List channel products with pagination and filtering */
  channelProducts?: Maybe<ChannelProductTypeConnection>;
  /** Get single customer by ID */
  customer?: Maybe<CustomerType>;
  /** Get customer by phone number */
  customerByPhone?: Maybe<CustomerType>;
  /** List all customers with pagination and filtering */
  customers?: Maybe<CustomerTypeConnection>;
  /** Get default fallback package */
  defaultPackage?: Maybe<PackageType>;
  /** Get single discount by ID */
  discount?: Maybe<DiscountType>;
  /** Get discount by code */
  discountByCode?: Maybe<DiscountType>;
  /** List all discounts with pagination and filtering */
  discounts?: Maybe<DiscountTypeConnection>;
  /** Get featured categories for homepage */
  featuredCategories?: Maybe<Array<Maybe<CategoryType>>>;
  /** Get featured products */
  featuredProducts?: Maybe<Array<Maybe<ProductType>>>;
  /** List all inventory with pagination and filtering */
  inventory?: Maybe<InventoryTypeConnection>;
  /** Get inventory for specific location */
  inventoryByLocation?: Maybe<Array<Maybe<InventoryType>>>;
  /** Get inventory for specific variant across all regions */
  inventoryByVariant?: Maybe<Array<Maybe<InventoryType>>>;
  /** Get all locations for authenticated workspace */
  locations?: Maybe<Array<Maybe<LocationType>>>;
  /** Get low stock items across all regions */
  lowStockItems?: Maybe<Array<Maybe<InventoryType>>>;
  /** Get permission summary grouped by resource */
  memberPermissionSummary?: Maybe<Array<Maybe<PermissionSummaryType>>>;
  /** Get current user's permissions in workspace */
  myPermissions?: Maybe<MyPermissionsType>;
  /** Get single order by ID */
  order?: Maybe<OrderType>;
  /** List all orders with pagination and filtering */
  orders?: Maybe<OrderTypeConnection>;
  /** Get orders by shipping region */
  ordersByRegion?: Maybe<Array<Maybe<OrderType>>>;
  /** Get orders by source (whatsapp, payment, manual) */
  ordersBySource?: Maybe<Array<Maybe<OrderType>>>;
  /** Get orders by status */
  ordersByStatus?: Maybe<Array<Maybe<OrderType>>>;
  /** Get single package by ID */
  package?: Maybe<PackageType>;
  /** List all packages with pagination and filtering (for dropdown and settings) */
  packages?: Maybe<PackageTypeConnection>;
  /** List configured payment methods for current workspace */
  paymentMethods?: Maybe<Array<Maybe<MerchantPaymentMethodType>>>;
  /** List pending workspace invitations (requires staff:view permission) */
  pendingInvites?: Maybe<Array<Maybe<WorkspaceInviteType>>>;
  /** Get single product by ID */
  product?: Maybe<ProductType>;
  /** List all products with pagination and filtering */
  products?: Maybe<ProductTypeConnection>;
  /** Get products by category */
  productsByCategory?: Maybe<Array<Maybe<ProductType>>>;
  /** Get recent bulk operations */
  recentBulkOperations?: Maybe<Array<Maybe<BulkOperationType>>>;
  /** Get recent customers */
  recentCustomers?: Maybe<Array<Maybe<CustomerType>>>;
  /** Get recent media uploads for current workspace (for media picker) */
  recentMedia?: Maybe<Array<Maybe<MediaUploadType>>>;
  /** Get recent orders */
  recentOrders?: Maybe<Array<Maybe<OrderType>>>;
  /** Get single sales channel by ID */
  salesChannel?: Maybe<SalesChannelType>;
  /** List all sales channels with pagination and filtering */
  salesChannels?: Maybe<SalesChannelTypeConnection>;
  /** Get store analytics dashboard data (tier-gated) */
  storeAnalytics?: Maybe<StoreAnalytics>;
  /** Get store profile settings for current workspace */
  storeProfile?: Maybe<StoreProfileType>;
  /** Get variant by ID */
  variant?: Maybe<ProductVariantType>;
  /** Get paginated list of variants */
  variants?: Maybe<ProductVariantTypeConnection>;
  /** Get variants by product ID */
  variantsByProduct?: Maybe<Array<Maybe<ProductVariantType>>>;
  /** Get single workspace member details (requires staff:view permission) */
  workspaceMember?: Maybe<WorkspaceMemberType>;
  /** List all workspace members with status and roles (requires staff:view permission) */
  workspaceMembers?: Maybe<WorkspaceMemberTypeConnection>;
  /** Get single role with permissions */
  workspaceRole?: Maybe<RoleType>;
  /** List all workspace roles for assignment (requires staff:view permission) */
  workspaceRoles?: Maybe<RoleTypeConnection>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryActiveDiscountsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryBulkOperationArgs {
  id: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryBulkOperationsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  operationType?: InputMaybe<WorkspaceStoreBulkOperationOperationTypeChoices>;
  status?: InputMaybe<WorkspaceStoreBulkOperationStatusChoices>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
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
  search?: InputMaybe<Scalars['String']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryCategoryArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryCategoryBySlugArgs {
  slug: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryCategoryProductsArgs {
  categoryId: Scalars['ID']['input'];
  first?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryChannelOrderArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryChannelOrdersArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channelOrderId?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isSynced?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryChannelProductArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryChannelProductsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isVisible?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  productId?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryCustomerArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryCustomerByPhoneArgs {
  phone: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryCustomersArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  customerType?: InputMaybe<WorkspaceCoreCustomerCustomerTypeChoices>;
  email?: InputMaybe<Scalars['String']['input']>;
  email_Icontains?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  phone?: InputMaybe<Scalars['String']['input']>;
  phone_Icontains?: InputMaybe<Scalars['String']['input']>;
  region?: InputMaybe<WorkspaceCoreCustomerRegionChoices>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryDiscountArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryDiscountByCodeArgs {
  code: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryDiscountsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  code?: InputMaybe<Scalars['String']['input']>;
  code_Icontains?: InputMaybe<Scalars['String']['input']>;
  discountType?: InputMaybe<WorkspaceStoreDiscountDiscountTypeChoices>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  method?: InputMaybe<WorkspaceStoreDiscountMethodChoices>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<WorkspaceStoreDiscountStatusChoices>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryFeaturedCategoriesArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryFeaturedProductsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryInventoryArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isAvailable?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  location?: InputMaybe<Scalars['ID']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  quantity?: InputMaybe<Scalars['Int']['input']>;
  quantity_Gte?: InputMaybe<Scalars['Int']['input']>;
  quantity_Lte?: InputMaybe<Scalars['Int']['input']>;
  variant?: InputMaybe<Scalars['ID']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryInventoryByLocationArgs {
  locationId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryInventoryByVariantArgs {
  variantId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryLowStockItemsArgs {
  threshold?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryMemberPermissionSummaryArgs {
  memberId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryOrderArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryOrdersArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  createdAt?: InputMaybe<Scalars['DateTime']['input']>;
  createdAt_Gte?: InputMaybe<Scalars['DateTime']['input']>;
  createdAt_Lte?: InputMaybe<Scalars['DateTime']['input']>;
  customerEmail?: InputMaybe<Scalars['String']['input']>;
  customerEmail_Icontains?: InputMaybe<Scalars['String']['input']>;
  customerName_Icontains?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isArchived?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  orderNumber?: InputMaybe<Scalars['String']['input']>;
  orderNumber_Icontains?: InputMaybe<Scalars['String']['input']>;
  orderSource?: InputMaybe<WorkspaceStoreOrderOrderSourceChoices>;
  paymentMethod?: InputMaybe<WorkspaceStoreOrderPaymentMethodChoices>;
  paymentStatus?: InputMaybe<WorkspaceStoreOrderPaymentStatusChoices>;
  shippingRegion?: InputMaybe<WorkspaceStoreOrderShippingRegionChoices>;
  status?: InputMaybe<WorkspaceStoreOrderStatusChoices>;
  totalAmount?: InputMaybe<Scalars['Decimal']['input']>;
  totalAmount_Gte?: InputMaybe<Scalars['Decimal']['input']>;
  totalAmount_Lte?: InputMaybe<Scalars['Decimal']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryOrdersByRegionArgs {
  region: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryOrdersBySourceArgs {
  source: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryOrdersByStatusArgs {
  status: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryPackageArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryPackagesArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  method?: InputMaybe<Scalars['String']['input']>;
  method_Icontains?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  packageType?: InputMaybe<WorkspaceStorePackagePackageTypeChoices>;
  size?: InputMaybe<WorkspaceStorePackageSizeChoices>;
  useAsDefault?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryProductArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryProductsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  brand_Icontains?: InputMaybe<Scalars['String']['input']>;
  category?: InputMaybe<Scalars['ID']['input']>;
  createdAt?: InputMaybe<Scalars['DateTime']['input']>;
  createdAt_Gte?: InputMaybe<Scalars['DateTime']['input']>;
  createdAt_Lte?: InputMaybe<Scalars['DateTime']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  hasVariants?: InputMaybe<Scalars['Boolean']['input']>;
  inventoryHealth?: InputMaybe<WorkspaceStoreProductInventoryHealthChoices>;
  inventoryQuantity?: InputMaybe<Scalars['Int']['input']>;
  inventoryQuantity_Gte?: InputMaybe<Scalars['Int']['input']>;
  inventoryQuantity_Lte?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  price?: InputMaybe<Scalars['Decimal']['input']>;
  price_Gte?: InputMaybe<Scalars['Decimal']['input']>;
  price_Lte?: InputMaybe<Scalars['Decimal']['input']>;
  productType?: InputMaybe<WorkspaceStoreProductProductTypeChoices>;
  requiresShipping?: InputMaybe<Scalars['Boolean']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
  sku_Icontains?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<WorkspaceStoreProductStatusChoices>;
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
  vendor_Icontains?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryProductsByCategoryArgs {
  categoryId: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryRecentBulkOperationsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryRecentCustomersArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryRecentMediaArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
  mediaType?: InputMaybe<Scalars['String']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<Scalars['String']['input']>;
  sortOrder?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryRecentOrdersArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QuerySalesChannelArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QuerySalesChannelsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channelType?: InputMaybe<WorkspaceStoreSalesChannelChannelTypeChoices>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryStoreAnalyticsArgs {
  days?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryVariantArgs {
  id: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryVariantsArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
  sku_Icontains?: InputMaybe<Scalars['String']['input']>;
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryVariantsByProductArgs {
  onlyActive?: InputMaybe<Scalars['Boolean']['input']>;
  productId: Scalars['String']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryWorkspaceMemberArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryWorkspaceMembersArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  roleName?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<WorkspaceCoreMembershipStatusChoices>;
  user_Email_Icontains?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryWorkspaceRoleArgs {
  id: Scalars['ID']['input'];
}


/**
 * Root GraphQL Query
 *
 * Combines all query types for the admin store API
 * All queries are automatically workspace-scoped via JWT middleware
 */
export interface QueryWorkspaceRolesArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  isSystem?: InputMaybe<Scalars['Boolean']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}

/**
 * Reactivate suspended staff member
 *
 * Requires: 'staff:reactivate' permission
 * Security: Can only reactivate SUSPENDED members
 */
export interface ReactivateStaff {
  __typename?: 'ReactivateStaff';
  error?: Maybe<Scalars['String']['output']>;
  member?: Maybe<WorkspaceMemberType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** GraphQL type for recent inventory activity */
export interface RecentActivityType {
  __typename?: 'RecentActivityType';
  periodDays?: Maybe<Scalars['Int']['output']>;
  recentRestocks?: Maybe<Scalars['Int']['output']>;
  recentSales?: Maybe<Scalars['Int']['output']>;
}

/**
 * Remove a payment method from workspace.
 *
 * Uses atomic transaction with row-level locking.
 */
export interface RemovePaymentMethod {
  __typename?: 'RemovePaymentMethod';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Remove products from category with atomic transaction
 *
 * Security: Validates workspace ownership for both category and products
 * Integrity: Uses @transaction.atomic for rollback
 * Performance: Bulk operation for multiple products
 */
export interface RemoveProductsFromCategory {
  __typename?: 'RemoveProductsFromCategory';
  category?: Maybe<CategoryType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  removedCount?: Maybe<Scalars['Int']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Permanently remove staff member from workspace (cannot be reactivated)
 *
 * CRITICAL: This is permanent removal. For temporary suspension, use SuspendStaff.
 *
 * Requires: 'staff:remove' permission
 * Security: Cannot remove self or workspace owner
 */
export interface RemoveStaff {
  __typename?: 'RemoveStaff';
  deletedId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Reorder categories with atomic transaction
 *
 * Security: Validates workspace ownership
 * Integrity: Uses @transaction.atomic for rollback
 * Performance: Bulk update for efficiency
 */
export interface ReorderCategories {
  __typename?: 'ReorderCategories';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  updatedCount?: Maybe<Scalars['Int']['output']>;
}

/**
 * Resend workspace invitation email
 * Extends expiration date and resends email
 *
 * Requires: 'staff:invite' permission
 */
export interface ResendInvite {
  __typename?: 'ResendInvite';
  error?: Maybe<Scalars['String']['output']>;
  invite?: Maybe<WorkspaceInviteType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * GraphQL type for Role model
 * Represents workspace roles (Owner, Admin, Staff, ReadOnly)
 */
export interface RoleType extends Node {
  __typename?: 'RoleType';
  createdAt: Scalars['DateTime']['output'];
  /** Description of role responsibilities and permissions */
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** System roles are auto-provisioned and cannot be deleted */
  isSystem: Scalars['Boolean']['output'];
  memberCount?: Maybe<Scalars['Int']['output']>;
  /** Role name (e.g., 'Owner', 'Admin', 'Staff', 'ReadOnly') */
  name: Scalars['String']['output'];
  permissionCount?: Maybe<Scalars['Int']['output']>;
  permissions?: Maybe<Array<Maybe<PermissionType>>>;
  updatedAt: Scalars['DateTime']['output'];
}

export interface RoleTypeConnection {
  __typename?: 'RoleTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<RoleTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
}

/** A Relay edge containing a `RoleType` and its cursor. */
export interface RoleTypeEdge {
  __typename?: 'RoleTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<RoleType>;
}

/** Input for SEO-related fields (Shopify-style) */
export interface SeoInput {
  /** SEO meta description (max 160 chars, defaults to description if empty) */
  metaDescription?: InputMaybe<Scalars['String']['input']>;
  /** SEO meta title (max 60 chars, defaults to name if empty) */
  metaTitle?: InputMaybe<Scalars['String']['input']>;
  /** URL-friendly slug (auto-generated from name if not provided) */
  slug?: InputMaybe<Scalars['String']['input']>;
}

/** Input for creating/updating sales channels */
export interface SalesChannelInput {
  baseUrl?: InputMaybe<Scalars['String']['input']>;
  channelType: Scalars['String']['input'];
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  name: Scalars['String']['input'];
  supportsCustomerSync?: InputMaybe<Scalars['Boolean']['input']>;
  supportsInventorySync?: InputMaybe<Scalars['Boolean']['input']>;
  supportsOrderSync?: InputMaybe<Scalars['Boolean']['input']>;
}

/**
 * GraphQL type for SalesChannel model
 *
 * Features:
 * - All sales channel fields with proper typing
 * - Multi-platform support
 * - Sync status tracking
 */
export interface SalesChannelType extends Node {
  __typename?: 'SalesChannelType';
  activeProducts?: Maybe<Scalars['Int']['output']>;
  /** Base URL for this channel (for web/mobile) */
  baseUrl?: Maybe<Scalars['String']['output']>;
  channelType: WorkspaceStoreSalesChannelChannelTypeChoices;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Whether this sales channel is active */
  isActive: Scalars['Boolean']['output'];
  /** Last synchronization timestamp */
  lastSyncAt?: Maybe<Scalars['DateTime']['output']>;
  /** Sales channel name (e.g., 'Main Website', 'Mobile App', 'Store POS') */
  name: Scalars['String']['output'];
  pendingOrders?: Maybe<Scalars['Int']['output']>;
  /** Whether this channel supports customer synchronization */
  supportsCustomerSync: Scalars['Boolean']['output'];
  /** Whether this channel supports inventory synchronization */
  supportsInventorySync: Scalars['Boolean']['output'];
  /** Whether this channel supports order synchronization */
  supportsOrderSync: Scalars['Boolean']['output'];
  /** Total orders from this channel */
  totalOrders: Scalars['Int']['output'];
  /** Total revenue from this channel */
  totalRevenue: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
}

export interface SalesChannelTypeConnection {
  __typename?: 'SalesChannelTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<SalesChannelTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `SalesChannelType` and its cursor. */
export interface SalesChannelTypeEdge {
  __typename?: 'SalesChannelTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<SalesChannelType>;
}

/** Input for shipping-related fields */
export interface ShippingInput {
  /** Shipping package ID (optional - falls back to default) */
  packageId?: InputMaybe<Scalars['ID']['input']>;
  requiresShipping?: InputMaybe<Scalars['Boolean']['input']>;
  shippingConfig?: InputMaybe<Scalars['JSONString']['input']>;
  weight?: InputMaybe<Scalars['Decimal']['input']>;
}

/**
 * Input for order status update
 *
 * Validation: Valid status transitions
 * Security: Workspace scoping and permission validation
 */
export interface StatusUpdateInput {
  newStatus: Scalars['String']['input'];
  orderId: Scalars['String']['input'];
}

/**
 * Complete store analytics dashboard - tier-gated
 *
 * BASIC: cards, chart, payment_breakdown
 * PRO: + funnel, customers
 * ADVANCED: + (future features)
 *
 * Workspace is auto-scoped via GraphQL context (no workspace field needed).
 */
export interface StoreAnalytics {
  __typename?: 'StoreAnalytics';
  /** Analytics capability level */
  analyticsLevel: Scalars['String']['output'];
  /** 4 metric cards */
  cards?: Maybe<Array<Maybe<DashboardCard>>>;
  /** Orders/Revenue chart */
  chart?: Maybe<ChartData>;
  /** Customer metrics (PRO+) */
  customers?: Maybe<CustomerMetrics>;
  /** Error message if access denied */
  error?: Maybe<Scalars['String']['output']>;
  /** Conversion funnel (PRO+) */
  funnel?: Maybe<ConversionFunnel>;
  /** Generation timestamp */
  generatedAt: Scalars['String']['output'];
  /** Whether workspace has analytics access */
  hasAccess: Scalars['Boolean']['output'];
  /** Payment method split */
  paymentBreakdown?: Maybe<PaymentBreakdown>;
  /** Required plan for access */
  requiredPlan?: Maybe<Scalars['String']['output']>;
}

/**
 * Input type for updating store profile settings.
 * All fields optional - only provided fields are updated.
 */
export interface StoreProfileInput {
  /** Store phone (Cameroon format: +237XXXXXXXXX) */
  phoneNumber?: InputMaybe<Scalars['String']['input']>;
  /** Store description or tagline */
  storeDescription?: InputMaybe<Scalars['String']['input']>;
  /** Primary contact email */
  storeEmail?: InputMaybe<Scalars['String']['input']>;
  /** Display name for the store */
  storeName?: InputMaybe<Scalars['String']['input']>;
  /** Customer support email */
  supportEmail?: InputMaybe<Scalars['String']['input']>;
  /** Store timezone */
  timezone?: InputMaybe<Scalars['String']['input']>;
  /** WhatsApp number (Cameroon format: +237XXXXXXXXX) */
  whatsappNumber?: InputMaybe<Scalars['String']['input']>;
}

/**
 * GraphQL type for StoreProfile model
 *
 * Exposes store settings for the General Settings page.
 */
export interface StoreProfileType extends Node {
  __typename?: 'StoreProfileType';
  createdAt: Scalars['DateTime']['output'];
  /** Store currency (locked to XAF for Cameroon) */
  currency: WorkspaceStoreStoreProfileCurrencyChoices;
  id: Scalars['ID']['output'];
  /** Store phone number (Cameroon format: +237XXXXXXXXX) */
  phoneNumber: Scalars['String']['output'];
  /** Store description or tagline */
  storeDescription: Scalars['String']['output'];
  /** Primary contact email for the store */
  storeEmail: Scalars['String']['output'];
  /** Display name for the store */
  storeName: Scalars['String']['output'];
  /** Customer support email (optional) */
  supportEmail: Scalars['String']['output'];
  /** Store timezone for display purposes */
  timezone: WorkspaceStoreStoreProfileTimezoneChoices;
  updatedAt: Scalars['DateTime']['output'];
  /** WhatsApp number for order notifications (Cameroon format: +237XXXXXXXXX) */
  whatsappNumber: Scalars['String']['output'];
}

/**
 * Suspend staff member from workspace (temporary, can be reactivated)
 *
 * Requires: 'staff:suspend' permission
 * Security: Cannot suspend self or workspace owner
 */
export interface SuspendStaff {
  __typename?: 'SuspendStaff';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for suspending staff member
 *
 * Fields:
 * - member_id: Membership ID to suspend (required)
 * - reason: Reason for suspension (optional)
 */
export interface SuspendStaffInput {
  memberId: Scalars['ID']['input'];
  reason?: InputMaybe<Scalars['String']['input']>;
}

/** Sync inventory using SalesChannelService */
export interface SyncInventory {
  __typename?: 'SyncInventory';
  channelProduct?: Maybe<ChannelProductType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Unified timeline event type that combines OrderComment and OrderHistory */
export interface TimelineEventType {
  __typename?: 'TimelineEventType';
  author?: Maybe<UserType>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  isInternal?: Maybe<Scalars['Boolean']['output']>;
  message: Scalars['String']['output'];
  metadata?: Maybe<Scalars['JSONString']['output']>;
  type: Scalars['String']['output'];
}

/**
 * Toggle category visibility with atomic transaction
 *
 * Security: Validates workspace ownership
 * Integrity: Uses @transaction.atomic for rollback
 */
export interface ToggleCategoryVisibility {
  __typename?: 'ToggleCategoryVisibility';
  category?: Maybe<CategoryType>;
  error?: Maybe<Scalars['String']['output']>;
  isVisible?: Maybe<Scalars['Boolean']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Toggle customer active status with validation using CustomerMutationService
 *
 * Performance: Atomic status update
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive status validation
 */
export interface ToggleCustomerStatus {
  __typename?: 'ToggleCustomerStatus';
  customer?: Maybe<CustomerType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Enable or disable a payment method.
 *
 * Uses atomic transaction with row-level locking.
 */
export interface TogglePaymentMethod {
  __typename?: 'TogglePaymentMethod';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  paymentMethod?: Maybe<MerchantPaymentMethodType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Toggle product status with validation using ProductService
 *
 * Performance: Atomic status update
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive status validation
 */
export interface ToggleProductStatus {
  __typename?: 'ToggleProductStatus';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  product?: Maybe<ProductType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Transfer inventory between locations
 *
 * Performance: Atomic transaction with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Rollback on failure
 */
export interface TransferInventory {
  __typename?: 'TransferInventory';
  error?: Maybe<Scalars['String']['output']>;
  fromInventory?: Maybe<InventoryType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  toInventory?: Maybe<InventoryType>;
}

/** Input for transferring inventory between locations */
export interface TransferInventoryInput {
  fromLocationId: Scalars['String']['input'];
  quantity: Scalars['Int']['input'];
  toLocationId: Scalars['String']['input'];
  variantId: Scalars['String']['input'];
}

/**
 * Unarchive an order to restore it to active view
 *
 * Performance: Atomic update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Validates order can be unarchived before update
 */
export interface UnarchiveOrder {
  __typename?: 'UnarchiveOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update category with atomic transaction (Shopify-style)
 *
 * Security: Validates workspace ownership
 * Integrity: Uses @transaction.atomic for rollback
 * Hierarchical: Validates parent relationships
 * Images: Replace category banner image
 */
export interface UpdateCategory {
  __typename?: 'UpdateCategory';
  category?: Maybe<CategoryType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update customer with atomic transaction using CustomerMutationService
 *
 * Performance: Atomic update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive error handling with rollback
 */
export interface UpdateCustomer {
  __typename?: 'UpdateCustomer';
  customer?: Maybe<CustomerType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update customer tags with atomic transaction using CustomerMutationService
 *
 * Performance: Atomic tag operations
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive tag validation
 */
export interface UpdateCustomerTags {
  __typename?: 'UpdateCustomerTags';
  customer?: Maybe<CustomerType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Update discount with service layer orchestration */
export interface UpdateDiscount {
  __typename?: 'UpdateDiscount';
  discount?: Maybe<DiscountType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update inventory for a variant at a specific location
 *
 * Performance: Atomic update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive error handling with rollback
 */
export interface UpdateInventory {
  __typename?: 'UpdateInventory';
  error?: Maybe<Scalars['String']['output']>;
  inventory?: Maybe<InventoryType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for comprehensive inventory update
 *
 * All fields are optional - update only what's provided
 * Security: Workspace scoping via JWT middleware
 */
export interface UpdateInventoryInput {
  available?: InputMaybe<Scalars['Int']['input']>;
  condition?: InputMaybe<Scalars['String']['input']>;
  locationId: Scalars['String']['input'];
  onhand?: InputMaybe<Scalars['Int']['input']>;
  variantId: Scalars['String']['input'];
}

/** Update location */
export interface UpdateLocation {
  __typename?: 'UpdateLocation';
  error?: Maybe<Scalars['String']['output']>;
  location?: Maybe<LocationType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Update order notes */
export interface UpdateOrderNotes {
  __typename?: 'UpdateOrderNotes';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update order status with validation and side effects
 *
 * Performance: Atomic update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive status transition validation
 */
export interface UpdateOrderStatus {
  __typename?: 'UpdateOrderStatus';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<OrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Update shipping package */
export interface UpdatePackage {
  __typename?: 'UpdatePackage';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  package?: Maybe<PackageType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update payment method configuration (e.g., checkout URL).
 *
 * Uses atomic transaction with row-level locking.
 */
export interface UpdatePaymentMethod {
  __typename?: 'UpdatePaymentMethod';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  paymentMethod?: Maybe<MerchantPaymentMethodType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Input type for updating payment method configuration. */
export interface UpdatePaymentMethodInput {
  /** Updated checkout URL */
  checkoutUrl?: InputMaybe<Scalars['String']['input']>;
  /** Enable/disable payment method */
  enabled?: InputMaybe<Scalars['Boolean']['input']>;
}

/**
 * Update product with atomic transaction using ProductService
 *
 * Performance: Atomic update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive error handling with rollback
 */
export interface UpdateProduct {
  __typename?: 'UpdateProduct';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  product?: Maybe<ProductType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update product stock quantity with atomic transaction using ProductService
 *
 * Performance: Atomic stock update with proper locking
 * Security: Workspace scoping and permission validation
 * Reliability: Comprehensive validation and rollback
 */
export interface UpdateProductStock {
  __typename?: 'UpdateProductStock';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  product?: Maybe<ProductType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Update sales channel with atomic transaction */
export interface UpdateSalesChannel {
  __typename?: 'UpdateSalesChannel';
  message?: Maybe<Scalars['String']['output']>;
  salesChannel?: Maybe<SalesChannelType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update store profile settings.
 *
 * Validates Cameroon phone numbers and returns proper error messages.
 * Uses atomic transaction for data integrity.
 */
export interface UpdateStoreProfile {
  __typename?: 'UpdateStoreProfile';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  storeProfile?: Maybe<StoreProfileType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Update variant with atomic transaction */
export interface UpdateVariant {
  __typename?: 'UpdateVariant';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  variant?: Maybe<ProductVariantType>;
}

/**
 * Upload and parse CSV file for bulk product creation
 *
 * Performance: Async processing with progress tracking
 * Scalability: Background job processing for large files
 * Reliability: Comprehensive error handling with retry mechanisms
 * Security: File validation and workspace scoping
 */
export interface UploadAndParseCsv {
  __typename?: 'UploadAndParseCSV';
  errors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  parseResult?: Maybe<CsvParseResultType>;
  progress?: Maybe<CsvParseProgressType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Upload and process document for product extraction
 *
 * Performance: Async processing for large documents
 * Scalability: Background job processing with progress tracking
 * Reliability: Retry mechanisms and comprehensive error handling
 * Security: File validation and workspace scoping
 */
export interface UploadAndProcessDocument {
  __typename?: 'UploadAndProcessDocument';
  analysisResult?: Maybe<DocumentAnalysisResult>;
  errors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  job?: Maybe<DocumentProcessingJob>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Upload media file with automatic processing (NEW FK-based system)
 *
 * Flow:
 * 1. Upload media → Get upload_id
 * 2. Attach to entity → entity.featured_media_id = upload_id
 *
 * Process:
 * 1. User selects file in UI
 * 2. Immediately upload to backend (entity-agnostic)
 * 3. Return upload_id and preview URL
 * 4. User can attach to product/category later via FK
 *
 * Benefits:
 * - Images persist even if user cancels entity creation
 * - Immediately available in "Recent uploads"
 * - Real upload progress feedback
 * - Can reuse across multiple entities (just set FK)
 */
export interface UploadMedia {
  __typename?: 'UploadMedia';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  upload?: Maybe<MediaUploadType>;
}

/**
 * Upload media from URL (download and store)
 *
 * Process:
 * 1. Download file from URL
 * 2. Validate and process
 * 3. Store in MediaUpload table
 */
export interface UploadMediaFromUrl {
  __typename?: 'UploadMediaFromUrl';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  upload?: Maybe<MediaUploadType>;
}

/**
 * GraphQL type for User model
 * Minimal user information for staff management
 */
export interface UserType {
  __typename?: 'UserType';
  email: Scalars['String']['output'];
  firstName: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  lastName: Scalars['String']['output'];
}

/**
 * Input for variant creation/update with featured image
 *
 * Supports inline variant creation with single featured image
 * All fields optional except options (option1/option2)
 */
export interface VariantInput {
  /** Compare at price */
  compareAtPrice?: InputMaybe<Scalars['Decimal']['input']>;
  /** Cost per item */
  costPrice?: InputMaybe<Scalars['Decimal']['input']>;
  /** Featured image ID (single image per variant) */
  featuredMediaId?: InputMaybe<Scalars['String']['input']>;
  /** Variant inventory data */
  inventory?: InputMaybe<InventoryInput>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** First option (e.g., Color: Red) */
  option1?: InputMaybe<Scalars['String']['input']>;
  /** Second option (e.g., Size: Large) */
  option2?: InputMaybe<Scalars['String']['input']>;
  /** Third option (if needed) */
  option3?: InputMaybe<Scalars['String']['input']>;
  /** Display position */
  position?: InputMaybe<Scalars['Int']['input']>;
  /** Variant price */
  price?: InputMaybe<Scalars['Decimal']['input']>;
}

/** Input for variant updates */
export interface VariantUpdateInput {
  barcode?: InputMaybe<Scalars['String']['input']>;
  compareAtPrice?: InputMaybe<Scalars['Float']['input']>;
  costPrice?: InputMaybe<Scalars['Float']['input']>;
  featuredMediaId?: InputMaybe<Scalars['String']['input']>;
  /** Update inventory per location */
  inventoryUpdates?: InputMaybe<Array<InputMaybe<InventoryUpdateInput>>>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  option1?: InputMaybe<Scalars['String']['input']>;
  option2?: InputMaybe<Scalars['String']['input']>;
  option3?: InputMaybe<Scalars['String']['input']>;
  position?: InputMaybe<Scalars['Int']['input']>;
  price?: InputMaybe<Scalars['Float']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
}

/** An enumeration. */
export enum WorkspaceCoreCustomerCustomerTypeChoices {
  /** Small Business */
  Business = 'BUSINESS',
  /** Corporate */
  Corporate = 'CORPORATE',
  /** Individual */
  Individual = 'INDIVIDUAL',
  /** Student */
  Student = 'STUDENT'
}

/** An enumeration. */
export enum WorkspaceCoreCustomerRegionChoices {
  /** Adamawa */
  Adamawa = 'ADAMAWA',
  /** Centre */
  Centre = 'CENTRE',
  /** East */
  Est = 'EST',
  /** Extreme North */
  ExtremeNord = 'EXTREME_NORD',
  /** Littoral */
  Littoral = 'LITTORAL',
  /** North */
  Nord = 'NORD',
  /** North West */
  NordOuest = 'NORD_OUEST',
  /** West */
  Ouest = 'OUEST',
  /** South */
  Sud = 'SUD',
  /** South West */
  SudOuest = 'SUD_OUEST'
}

/** An enumeration. */
export enum WorkspaceCoreMembershipStatusChoices {
  /** Active */
  Active = 'ACTIVE',
  /** Invited */
  Invited = 'INVITED',
  /** Removed */
  Removed = 'REMOVED',
  /** Suspended */
  Suspended = 'SUSPENDED'
}

/** An enumeration. */
export enum WorkspaceCoreWorkspaceInviteStatusChoices {
  /** Accepted */
  Accepted = 'ACCEPTED',
  /** Cancelled */
  Cancelled = 'CANCELLED',
  /** Consumed */
  Consumed = 'CONSUMED',
  /** Created */
  Created = 'CREATED',
  /** Expired */
  Expired = 'EXPIRED',
  /** Sent */
  Sent = 'SENT'
}

/**
 * GraphQL type for WorkspaceInvite model
 * Represents pending invitations (supports multiple roles like Shopify)
 */
export interface WorkspaceInviteType extends Node {
  __typename?: 'WorkspaceInviteType';
  /** When invitation was accepted */
  acceptedAt?: Maybe<Scalars['DateTime']['output']>;
  createdAt: Scalars['DateTime']['output'];
  /** Email address of person being invited */
  email: Scalars['String']['output'];
  /** When this invitation expires */
  expiresAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** User who sent the invitation */
  invitedBy?: Maybe<UserType>;
  invitedByEmail?: Maybe<Scalars['String']['output']>;
  isExpired?: Maybe<Scalars['Boolean']['output']>;
  isValid?: Maybe<Scalars['Boolean']['output']>;
  role?: Maybe<RoleType>;
  roleNames?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  /** Roles to assign when invite is accepted (supports multiple) */
  roles: RoleTypeConnection;
  status: WorkspaceCoreWorkspaceInviteStatusChoices;
}


/**
 * GraphQL type for WorkspaceInvite model
 * Represents pending invitations (supports multiple roles like Shopify)
 */
export interface WorkspaceInviteTypeRolesArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}

/**
 * GraphQL type for Membership model
 * Represents workspace members with their roles and status
 * Following Shopify pattern (supports multiple roles): User | Status | Roles
 */
export interface WorkspaceMemberType extends Node {
  __typename?: 'WorkspaceMemberType';
  allPermissions?: Maybe<Array<Maybe<PermissionType>>>;
  id: Scalars['ID']['output'];
  /** User who invited this member */
  invitedBy?: Maybe<UserType>;
  isActive?: Maybe<Scalars['Boolean']['output']>;
  isPending?: Maybe<Scalars['Boolean']['output']>;
  isRemoved?: Maybe<Scalars['Boolean']['output']>;
  isSuspended?: Maybe<Scalars['Boolean']['output']>;
  joinedAt: Scalars['DateTime']['output'];
  removedAt?: Maybe<Scalars['DateTime']['output']>;
  /** User who removed this membership */
  removedBy?: Maybe<UserType>;
  role?: Maybe<RoleType>;
  roleNames?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  /** Roles assigned to this membership (supports multiple roles per user) */
  roles: RoleTypeConnection;
  /** Membership status in invitation lifecycle */
  status: WorkspaceCoreMembershipStatusChoices;
  suspendedAt?: Maybe<Scalars['DateTime']['output']>;
  /** User who suspended this membership */
  suspendedBy?: Maybe<UserType>;
  suspensionReason: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
  userEmail?: Maybe<Scalars['String']['output']>;
  userName?: Maybe<Scalars['String']['output']>;
  workspace: WorkspaceType;
}


/**
 * GraphQL type for Membership model
 * Represents workspace members with their roles and status
 * Following Shopify pattern (supports multiple roles): User | Status | Roles
 */
export interface WorkspaceMemberTypeRolesArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}

export interface WorkspaceMemberTypeConnection {
  __typename?: 'WorkspaceMemberTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<WorkspaceMemberTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `WorkspaceMemberType` and its cursor. */
export interface WorkspaceMemberTypeEdge {
  __typename?: 'WorkspaceMemberTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<WorkspaceMemberType>;
}

/** An enumeration. */
export enum WorkspaceStoreBulkOperationOperationTypeChoices {
  /** Bulk Delete Products */
  BulkDelete = 'BULK_DELETE',
  /** Bulk Inventory Update */
  BulkInventoryUpdate = 'BULK_INVENTORY_UPDATE',
  /** Bulk Price Update */
  BulkPriceUpdate = 'BULK_PRICE_UPDATE',
  /** Bulk Publish Products */
  BulkPublish = 'BULK_PUBLISH',
  /** Bulk Unpublish Products */
  BulkUnpublish = 'BULK_UNPUBLISH'
}

/** An enumeration. */
export enum WorkspaceStoreBulkOperationStatusChoices {
  /** Failed */
  Failed = 'FAILED',
  /** Processing */
  Processing = 'PROCESSING',
  /** Success */
  Success = 'SUCCESS'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountBxgyDiscountTypeChoices {
  /** Amount off each */
  AmountOffEach = 'AMOUNT_OFF_EACH',
  /** Free */
  Free = 'FREE',
  /** Percentage */
  Percentage = 'PERCENTAGE'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountCustomerBuysTypeChoices {
  /** Minimum purchase amount */
  MinimumPurchaseAmount = 'MINIMUM_PURCHASE_AMOUNT',
  /** Minimum quantity of items */
  MinimumQuantity = 'MINIMUM_QUANTITY'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountDiscountTypeChoices {
  /** Amount off order */
  AmountOffOrder = 'AMOUNT_OFF_ORDER',
  /** Amount off products */
  AmountOffProduct = 'AMOUNT_OFF_PRODUCT',
  /** Buy X Get Y */
  BuyXGetY = 'BUY_X_GET_Y',
  /** Free Shipping */
  FreeShipping = 'FREE_SHIPPING'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountDiscountValueTypeChoices {
  /** Fixed Amount */
  FixedAmount = 'FIXED_AMOUNT',
  /** Percentage */
  Percentage = 'PERCENTAGE'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountMethodChoices {
  /** Automatic Discount */
  Automatic = 'AUTOMATIC',
  /** Discount Code */
  DiscountCode = 'DISCOUNT_CODE'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountMinimumRequirementTypeChoices {
  /** Minimum purchase amount */
  MinimumAmount = 'MINIMUM_AMOUNT',
  /** Minimum quantity of items */
  MinimumQuantity = 'MINIMUM_QUANTITY',
  /** No minimum requirements */
  None = 'NONE'
}

/** An enumeration. */
export enum WorkspaceStoreDiscountStatusChoices {
  /** Active */
  Active = 'ACTIVE',
  /** Expired */
  Expired = 'EXPIRED',
  /** Inactive */
  Inactive = 'INACTIVE',
  /** Scheduled */
  Scheduled = 'SCHEDULED'
}

/** An enumeration. */
export enum WorkspaceStoreInventoryConditionChoices {
  /** New */
  New = 'NEW',
  /** Refurbished */
  Refurbished = 'REFURBISHED',
  /** Second Hand */
  SecondHand = 'SECOND_HAND',
  /** Used - Acceptable */
  UsedAcceptable = 'USED_ACCEPTABLE',
  /** Used - Good */
  UsedGood = 'USED_GOOD',
  /** Used - Like New */
  UsedLikeNew = 'USED_LIKE_NEW'
}

/** An enumeration. */
export enum WorkspaceStoreLocationRegionChoices {
  /** Adamawa */
  Adamawa = 'ADAMAWA',
  /** Centre */
  Centre = 'CENTRE',
  /** East */
  East = 'EAST',
  /** Far North */
  FarNorth = 'FAR_NORTH',
  /** Littoral */
  Littoral = 'LITTORAL',
  /** North */
  North = 'NORTH',
  /** Northwest */
  Northwest = 'NORTHWEST',
  /** South */
  South = 'SOUTH',
  /** Southwest */
  Southwest = 'SOUTHWEST',
  /** West */
  West = 'WEST'
}

/** An enumeration. */
export enum WorkspaceStoreOrderHistoryActionChoices {
  /** Order Archived */
  Archived = 'ARCHIVED',
  /** Order Cancelled */
  Cancelled = 'CANCELLED',
  /** Order Created */
  Created = 'CREATED',
  /** Customer Notified */
  CustomerNotified = 'CUSTOMER_NOTIFIED',
  /** Delivered */
  Delivered = 'DELIVERED',
  /** Delivery Failed */
  DeliveryFailed = 'DELIVERY_FAILED',
  /** Order Fulfilled */
  Fulfilled = 'FULFILLED',
  /** Marked as Paid */
  MarkedAsPaid = 'MARKED_AS_PAID',
  /** Notes Updated */
  NotesUpdated = 'NOTES_UPDATED',
  /** Out for Delivery */
  OutForDelivery = 'OUT_FOR_DELIVERY',
  /** Partially Fulfilled */
  PartiallyFulfilled = 'PARTIALLY_FULFILLED',
  /** Payment Failed */
  PaymentFailed = 'PAYMENT_FAILED',
  /** Refunded */
  Refunded = 'REFUNDED',
  /** Shipped */
  Shipped = 'SHIPPED',
  /** Status Changed */
  StatusChanged = 'STATUS_CHANGED',
  /** Order Unarchived */
  Unarchived = 'UNARCHIVED',
  /** Order Unfulfilled */
  Unfulfilled = 'UNFULFILLED'
}

/** An enumeration. */
export enum WorkspaceStoreOrderOrderSourceChoices {
  /** Manual Entry */
  Manual = 'MANUAL',
  /** Payment Gateway */
  Payment = 'PAYMENT',
  /** WhatsApp Order */
  Whatsapp = 'WHATSAPP'
}

/** An enumeration. */
export enum WorkspaceStoreOrderPaymentMethodChoices {
  /** Bank Transfer */
  BankTransfer = 'BANK_TRANSFER',
  /** Credit/Debit Card */
  Card = 'CARD',
  /** Cash on Delivery */
  CashOnDelivery = 'CASH_ON_DELIVERY',
  /** Mobile Money */
  MobileMoney = 'MOBILE_MONEY',
  /** WhatsApp Order */
  Whatsapp = 'WHATSAPP'
}

/** An enumeration. */
export enum WorkspaceStoreOrderPaymentStatusChoices {
  /** Failed */
  Failed = 'FAILED',
  /** Paid */
  Paid = 'PAID',
  /** Pending */
  Pending = 'PENDING',
  /** Refunded */
  Refunded = 'REFUNDED'
}

/** An enumeration. */
export enum WorkspaceStoreOrderShippingRegionChoices {
  /** Adamawa Region */
  Adamawa = 'ADAMAWA',
  /** Centre Region */
  Centre = 'CENTRE',
  /** East Region */
  East = 'EAST',
  /** Far North Region */
  FarNorth = 'FAR_NORTH',
  /** Littoral Region */
  Littoral = 'LITTORAL',
  /** North Region */
  North = 'NORTH',
  /** Northwest Region */
  Northwest = 'NORTHWEST',
  /** South Region */
  South = 'SOUTH',
  /** Southwest Region */
  Southwest = 'SOUTHWEST',
  /** West Region */
  West = 'WEST'
}

/** An enumeration. */
export enum WorkspaceStoreOrderStatusChoices {
  /** Cancelled */
  Cancelled = 'CANCELLED',
  /** Confirmed */
  Confirmed = 'CONFIRMED',
  /** Delivered */
  Delivered = 'DELIVERED',
  /** On Hold */
  OnHold = 'ON_HOLD',
  /** Pending */
  Pending = 'PENDING',
  /** Processing */
  Processing = 'PROCESSING',
  /** Refunded */
  Refunded = 'REFUNDED',
  /** Returned */
  Returned = 'RETURNED',
  /** Shipped */
  Shipped = 'SHIPPED',
  /** Unfulfilled */
  Unfulfilled = 'UNFULFILLED'
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

/** An enumeration. */
export enum WorkspaceStoreSalesChannelChannelTypeChoices {
  /** Marketplace */
  Marketplace = 'MARKETPLACE',
  /** Mobile App */
  Mobile = 'MOBILE',
  /** On-site POS */
  Onsite = 'ONSITE',
  /** Social Media */
  Social = 'SOCIAL',
  /** Web Store */
  Web = 'WEB'
}

/** An enumeration. */
export enum WorkspaceStoreStoreProfileCurrencyChoices {
  /** Central African CFA franc */
  Xaf = 'XAF'
}

/** An enumeration. */
export enum WorkspaceStoreStoreProfileTimezoneChoices {
  /** Douala (UTC+1) */
  AfricaDouala = 'AFRICA_DOUALA',
  /** Lagos (UTC+1) */
  AfricaLagos = 'AFRICA_LAGOS'
}

/**
 * GraphQL type for Workspace model
 * Minimal workspace information
 */
export interface WorkspaceType {
  __typename?: 'WorkspaceType';
  id: Scalars['ID']['output'];
  /** Workspace display name */
  name: Scalars['String']['output'];
}
