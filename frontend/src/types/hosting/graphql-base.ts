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
  Decimal: { input: string; output: string; }
  JSONString: { input: any; output: any; }
}

/** Bandwidth usage details */
export interface BandwidthUsageType {
  __typename?: 'BandwidthUsageType';
  limitGb: Scalars['Float']['output'];
  percentage: Scalars['Float']['output'];
  remainingGb: Scalars['Float']['output'];
  usedGb: Scalars['Float']['output'];
}

/**
 * Change workspace subdomain (e.g., mystore.huzilerz.com)
 *
 * Free for all tiers - uses SubdomainService
 * Atomic update across WorkspaceInfrastructure and DeployedSite
 * Tracks subdomain history and enforces change limits (2 changes max)
 */
export interface ChangeSubdomain {
  __typename?: 'ChangeSubdomain';
  changesRemaining?: Maybe<Scalars['Int']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  liveUrl?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  newSubdomain?: Maybe<Scalars['String']['output']>;
  previewUrl?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for changing workspace subdomain
 *
 * Used by changeSubdomain mutation
 */
export interface ChangeSubdomainInput {
  /** New subdomain (e.g., 'mystore' for mystore.huzilerz.com) */
  subdomain: Scalars['String']['input'];
  /** Workspace to update */
  workspaceId: Scalars['ID']['input'];
}

/**
 * Connect externally-owned custom domain
 *
 * User must configure DNS records externally
 * System verifies DNS and provisions SSL (Shopify 2-step flow)
 */
export interface ConnectCustomDomain {
  __typename?: 'ConnectCustomDomain';
  dnsRecords?: Maybe<Scalars['JSONString']['output']>;
  domain?: Maybe<CustomDomainType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  verificationInstructions?: Maybe<Scalars['JSONString']['output']>;
}

/**
 * Input for connecting an externally-owned custom domain
 *
 * Used by connectCustomDomain mutation
 */
export interface ConnectCustomDomainInput {
  /** Domain to connect (must be owned externally) */
  domain: Scalars['String']['input'];
  /** Workspace to connect domain to */
  workspaceId: Scalars['ID']['input'];
}

/**
 * Custom domain detail view
 * Used for verification polling and DNS configuration display
 */
export interface CustomDomainDetailType extends Node {
  __typename?: 'CustomDomainDetailType';
  createdAt: Scalars['DateTime']['output'];
  dnsRecordsToAdd?: Maybe<Array<Maybe<DnsRecordType>>>;
  dnsRecordsToRemove?: Maybe<Array<Maybe<DnsRecordType>>>;
  dnsRecordsToUpdate?: Maybe<Array<Maybe<DnsRecordType>>>;
  dnsStatus: Scalars['String']['output'];
  /** Custom domain (e.g., shoppings.com or www.shoppings.com) */
  domain: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** Domain registrar if purchased via platform */
  registrarName?: Maybe<WorkspaceHostingCustomDomainRegistrarNameChoices>;
  /** Whether SSL/TLS is enabled for this domain */
  sslEnabled: Scalars['Boolean']['output'];
  /** When SSL certificate was provisioned */
  sslProvisionedAt?: Maybe<Scalars['DateTime']['output']>;
  status: WorkspaceHostingCustomDomainStatusChoices;
  tlsStatus: Scalars['String']['output'];
  /** When domain ownership was verified */
  verifiedAt?: Maybe<Scalars['DateTime']['output']>;
}

/**
 * Base custom domain type
 * Used for mutation returns - simple fields only
 */
export interface CustomDomainType extends Node {
  __typename?: 'CustomDomainType';
  createdAt: Scalars['DateTime']['output'];
  /** Custom domain (e.g., shoppings.com or www.shoppings.com) */
  domain: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** Whether SSL/TLS is enabled for this domain */
  sslEnabled: Scalars['Boolean']['output'];
  /** When SSL certificate was provisioned */
  sslProvisionedAt?: Maybe<Scalars['DateTime']['output']>;
  status: WorkspaceHostingCustomDomainStatusChoices;
  /** When domain ownership was verified */
  verifiedAt?: Maybe<Scalars['DateTime']['output']>;
}

/** Custom domains usage details */
export interface CustomDomainsUsageType {
  __typename?: 'CustomDomainsUsageType';
  count: Scalars['Int']['output'];
  limit: Scalars['Int']['output'];
}

/** DNS record for domain configuration */
export interface DnsRecordType {
  __typename?: 'DNSRecordType';
  action: Scalars['String']['output'];
  currentValue?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  type: Scalars['String']['output'];
  updateTo?: Maybe<Scalars['String']['output']>;
}

/**
 * Domain purchase status type for queries
 * Extended type with all tracking fields
 */
export interface DomainPurchaseStatusType extends Node {
  __typename?: 'DomainPurchaseStatusType';
  createdAt: Scalars['DateTime']['output'];
  /** Domain purchased (e.g., mystore.com) */
  domainName: Scalars['String']['output'];
  /** Error message if purchase failed */
  errorMessage: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  paymentStatus: WorkspaceHostingDomainPurchasePaymentStatusChoices;
  /** Price charged to customer in FCFA */
  priceFcfa: Scalars['Decimal']['output'];
  status: Scalars['String']['output'];
}

/**
 * Domain purchase type for mutations
 * Simple return type with essential fields
 */
export interface DomainPurchaseType extends Node {
  __typename?: 'DomainPurchaseType';
  createdAt: Scalars['DateTime']['output'];
  /** Domain purchased (e.g., mystore.com) */
  domainName: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  paymentStatus: WorkspaceHostingDomainPurchasePaymentStatusChoices;
  /** Price charged to customer in FCFA */
  priceFcfa: Scalars['Decimal']['output'];
}

/**
 * Domain renewal status type for queries
 * Extended type with all tracking fields
 */
export interface DomainRenewalStatusType extends Node {
  __typename?: 'DomainRenewalStatusType';
  createdAt: Scalars['DateTime']['output'];
  domainName: Scalars['String']['output'];
  errorMessage: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** New expiry date after renewal */
  newExpiryDate?: Maybe<Scalars['DateTime']['output']>;
  paymentStatus?: Maybe<Scalars['String']['output']>;
  /** Domain expiry date before renewal */
  previousExpiryDate: Scalars['DateTime']['output'];
  /** Renewal price in FCFA (charged to customer) */
  renewalPriceFcfa: Scalars['Decimal']['output'];
  renewalStatus: WorkspaceHostingDomainRenewalRenewalStatusChoices;
  renewedAt?: Maybe<Scalars['DateTime']['output']>;
  status: Scalars['String']['output'];
}

/**
 * Domain renewal type for mutations
 * Simple return type with essential fields
 */
export interface DomainRenewalType extends Node {
  __typename?: 'DomainRenewalType';
  createdAt: Scalars['DateTime']['output'];
  domainName: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  isCompleted?: Maybe<Scalars['Boolean']['output']>;
  isFailed?: Maybe<Scalars['Boolean']['output']>;
  isPendingPayment?: Maybe<Scalars['Boolean']['output']>;
  /** Renewal price in FCFA (charged to customer) */
  renewalPriceFcfa: Scalars['Decimal']['output'];
  renewalStatus: WorkspaceHostingDomainRenewalRenewalStatusChoices;
}

/** Complete domain search response with pagination */
export interface DomainSearchResponseType {
  __typename?: 'DomainSearchResponseType';
  available: Scalars['Boolean']['output'];
  hasNextPage: Scalars['Boolean']['output'];
  page: Scalars['Int']['output'];
  pageSize: Scalars['Int']['output'];
  query: Scalars['String']['output'];
  suggestions: Array<Maybe<DomainSearchResultType>>;
  total: Scalars['Int']['output'];
}

/** Domain search result item for buy domain flow */
export interface DomainSearchResultType {
  __typename?: 'DomainSearchResultType';
  available: Scalars['Boolean']['output'];
  category: Scalars['String']['output'];
  domain: Scalars['String']['output'];
  pricePerYear: Scalars['String']['output'];
  priceUsd: Scalars['Float']['output'];
}

/**
 * Unified domain type for main domains list
 * Represents both default subdomain and custom domains
 */
export interface DomainType {
  __typename?: 'DomainType';
  addedAt?: Maybe<Scalars['DateTime']['output']>;
  domain: Scalars['String']['output'];
  id?: Maybe<Scalars['ID']['output']>;
  isPrimary: Scalars['Boolean']['output'];
  managedBy?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  subdomainChangesLimit?: Maybe<Scalars['Int']['output']>;
  subdomainChangesRemaining?: Maybe<Scalars['Int']['output']>;
  type: Scalars['String']['output'];
}

/**
 * Hosting environment resource quota tracker
 *
 * Workspace-scoped - only accessible to user who owns the hosting environment
 * Tracks resource limits and current usage per subscription tier
 */
export interface HostingEnvironmentType extends Node {
  __typename?: 'HostingEnvironmentType';
  activeSitesCount: Scalars['Int']['output'];
  bandwidthUsagePercentage?: Maybe<Scalars['Float']['output']>;
  bandwidthUsedGb: Scalars['Decimal']['output'];
  /** Hosting entitlements: storage_gb, custom_domain, deployment_allowed */
  capabilities: Scalars['JSONString']['output'];
  createdAt: Scalars['DateTime']['output'];
  gracePeriodEnd?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  isDeploymentAllowed?: Maybe<Scalars['Boolean']['output']>;
  lastUsageSync?: Maybe<Scalars['DateTime']['output']>;
  overageCost?: Maybe<OverageCostType>;
  status: WorkspaceHostingHostingEnvironmentStatusChoices;
  storageUsagePercentage?: Maybe<Scalars['Float']['output']>;
  storageUsedGb: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
  usageHistory?: Maybe<UsageHistoryType>;
  usageSummary?: Maybe<UsageSummaryType>;
  user: UserType;
}


/**
 * Hosting environment resource quota tracker
 *
 * Workspace-scoped - only accessible to user who owns the hosting environment
 * Tracks resource limits and current usage per subscription tier
 */
export interface HostingEnvironmentTypeUsageHistoryArgs {
  days?: InputMaybe<Scalars['Int']['input']>;
}

/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface Mutation {
  __typename?: 'Mutation';
  /**
   * Change workspace subdomain (e.g., mystore.huzilerz.com)
   *
   * Free for all tiers - uses SubdomainService
   * Atomic update across WorkspaceInfrastructure and DeployedSite
   * Tracks subdomain history and enforces change limits (2 changes max)
   */
  changeSubdomain?: Maybe<ChangeSubdomain>;
  /**
   * Connect externally-owned custom domain
   *
   * User must configure DNS records externally
   * System verifies DNS and provisions SSL (Shopify 2-step flow)
   */
  connectCustomDomain?: Maybe<ConnectCustomDomain>;
  /**
   * Prepare domain purchase checkpoint
   * Returns AUTHORITATIVE pricing from backend (Source of Truth)
   */
  prepareDomainCheckout?: Maybe<PrepareDomainCheckout>;
  /**
   * Initiate domain purchase (Cameroon mobile money flow)
   *
   * Creates DomainPurchase record → User pays via MTN/Orange → Webhook completes purchase
   * Uses DomainPurchaseService.initiate_purchase()
   */
  purchaseDomain?: Maybe<PurchaseDomain>;
  /**
   * Initiate domain renewal (Cameroon mobile money flow)
   *
   * Creates DomainRenewal record → User pays via MTN/Orange → Webhook completes renewal
   * Uses DomainRenewalService.initiate_renewal()
   */
  renewDomain?: Maybe<RenewDomain>;
  /**
   * Set or update storefront password protection
   *
   * Shopify pattern: "Infrastructure live, business not live"
   * Allows merchants to lock their storefront during development.
   *
   * Args:
   *     workspace_id: ID of workspace
   *     password: Plain text password (will be hashed)
   *              Set to None or empty string to disable protection
   *
   * Returns:
   *     success: Boolean
   *     message: Success/error message
   *     password_enabled: Whether password protection is now active
   *
   * Security:
   *     - Password is hashed using Django's PBKDF2 SHA256
   *     - Never stored in plain text
   *     - Requires workspace ownership (validated by middleware)
   *
   * Examples:
   *     # Enable password protection
   *     mutation {
   *       setStorefrontPassword(
   *         workspaceId: "uuid",
   *         password: "my-secret-password"
   *       ) {
   *         success
   *         message
   *         passwordEnabled
   *       }
   *     }
   *
   *     # Disable password protection
   *     mutation {
   *       setStorefrontPassword(
   *         workspaceId: "uuid",
   *         password: ""
   *       ) {
   *         success
   *         message
   *         passwordEnabled
   *       }
   *     }
   */
  setStorefrontPassword?: Maybe<SetStorefrontPassword>;
  /**
   * Update SEO settings for a deployed storefront
   *
   * Allows merchants to optimize their store for search engines and social sharing.
   * Fields are validated against Google's best practices:
   * - Title: Max 60 chars (Google truncates at ~60)
   * - Description: Max 160 chars (Google truncates at ~160)
   * - Keywords: Optional (less important for modern SEO)
   *
   * Args:
   *     workspace_id: ID of workspace
   *     seo_title: Page title for search results (max 60 chars recommended)
   *     seo_description: Meta description for search snippets (max 160 chars recommended)
   *     seo_keywords: Comma-separated keywords (optional)
   *     seo_image_url: Open Graph image URL for social sharing
   *
   * Returns:
   *     success: Boolean
   *     message: Success/error message
   *     warnings: List of SEO warnings (e.g., "title too long")
   *     seo_settings: Updated SEO settings object
   *
   * Examples:
   *     # Update all SEO fields
   *     mutation {
   *       updateStorefrontSEO(
   *         workspaceId: "uuid",
   *         seoTitle: "My Amazing Store - Quality Products",
   *         seoDescription: "Shop our curated collection of quality products at amazing prices. Free shipping on orders over $50.",
   *         seoKeywords: "online store, quality products, free shipping",
   *         seoImageUrl: "https://cdn.huzilerz.com/my-store/og-image.jpg"
   *       ) {
   *         success
   *         message
   *         warnings
   *         seoSettings {
   *           title
   *           description
   *           keywords
   *           imageUrl
   *         }
   *       }
   *     }
   *
   *     # Update only title and description
   *     mutation {
   *       updateStorefrontSEO(
   *         workspaceId: "uuid",
   *         seoTitle: "Best Shoes Online",
   *         seoDescription: "Find your perfect pair from our collection of premium footwear."
   *       ) {
   *         success
   *         message
   *       }
   *     }
   */
  updateStorefrontSeo?: Maybe<UpdateStorefrontSeo>;
  /**
   * Manually trigger domain verification
   *
   * Use case: User configured DNS and wants immediate verification
   * (instead of waiting for 15-min auto-verification Celery task)
   */
  verifyCustomDomain?: Maybe<VerifyCustomDomain>;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationChangeSubdomainArgs {
  input: ChangeSubdomainInput;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationConnectCustomDomainArgs {
  input: ConnectCustomDomainInput;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationPrepareDomainCheckoutArgs {
  domain: Scalars['String']['input'];
  workspaceId: Scalars['ID']['input'];
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationPurchaseDomainArgs {
  input: PurchaseDomainInput;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationRenewDomainArgs {
  input: RenewDomainInput;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationSetStorefrontPasswordArgs {
  input: SetStorefrontPasswordInput;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationUpdateStorefrontSeoArgs {
  input: UpdateStorefrontSeoInput;
}


/**
 * Hosting management mutations (all require authentication + workspace)
 *
 * Domain Management:
 * - changeSubdomain: Change workspace subdomain
 * - connectCustomDomain: Connect externally-owned domain
 * - verifyCustomDomain: Manually trigger domain verification
 * - purchaseDomain: Initiate domain purchase (mobile money flow)
 * - renewDomain: Initiate domain renewal (mobile money flow)
 *
 * Storefront Management (Concern #2):
 * - setStorefrontPassword: Enable/disable/change storefront password protection
 *
 * SEO Management (Phase 4):
 * - updateStorefrontSEO: Update SEO meta tags (title, description, keywords, image)
 */
export interface MutationVerifyCustomDomainArgs {
  domainId: Scalars['ID']['input'];
}

/** An object with an ID */
export interface Node {
  /** The ID of the object */
  id: Scalars['ID']['output'];
}

/** Overage cost calculation for billing */
export interface OverageCostType {
  __typename?: 'OverageCostType';
  bandwidthOverageGb: Scalars['Float']['output'];
  storageOverageGb: Scalars['Float']['output'];
  totalOverageUsd: Scalars['Float']['output'];
}

/**
 * Prepare domain purchase checkpoint
 * Returns AUTHORITATIVE pricing from backend (Source of Truth)
 */
export interface PrepareDomainCheckout {
  __typename?: 'PrepareDomainCheckout';
  available?: Maybe<Scalars['Boolean']['output']>;
  currency?: Maybe<Scalars['String']['output']>;
  domainName?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  exchangeRate?: Maybe<Scalars['Float']['output']>;
  priceFcfa?: Maybe<Scalars['Float']['output']>;
  priceUsd?: Maybe<Scalars['Float']['output']>;
  registrationPeriodYears?: Maybe<Scalars['Int']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Initiate domain purchase (Cameroon mobile money flow)
 *
 * Creates DomainPurchase record → User pays via MTN/Orange → Webhook completes purchase
 * Uses DomainPurchaseService.initiate_purchase()
 */
export interface PurchaseDomain {
  __typename?: 'PurchaseDomain';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  paymentInstructions?: Maybe<Scalars['String']['output']>;
  purchase?: Maybe<DomainPurchaseType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for purchasing a domain
 *
 * Used by purchaseDomain mutation
 * Requires contact info for WHOIS registration (ICANN requirement)
 */
export interface PurchaseDomainInput {
  /** Street address */
  address: Scalars['String']['input'];
  /** City */
  city: Scalars['String']['input'];
  /** Country code (ISO 2-letter, default: CM for Cameroon) */
  country?: InputMaybe<Scalars['String']['input']>;
  /** Domain to purchase */
  domain: Scalars['String']['input'];
  /** Phone number (e.g., '+237670000000') */
  phone: Scalars['String']['input'];
  /** Postal/ZIP code */
  postalCode: Scalars['String']['input'];
  /** Registration period (1-10 years) */
  registrationPeriodYears?: InputMaybe<Scalars['Int']['input']>;
  /** State/Region */
  state: Scalars['String']['input'];
  /** Workspace to associate domain with */
  workspaceId: Scalars['ID']['input'];
}

/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface Query {
  __typename?: 'Query';
  /** Check if user can deploy new site based on limits */
  checkDeploymentEligibility?: Maybe<Scalars['JSONString']['output']>;
  /** Check if user can upload file based on storage limits */
  checkUploadEligibility?: Maybe<Scalars['JSONString']['output']>;
  /** Get custom domain with DNS/TLS status (for polling) */
  customDomain?: Maybe<CustomDomainDetailType>;
  /** Get all domains (default subdomain + custom domains) */
  domains?: Maybe<Array<Maybe<DomainType>>>;
  /** Get current user's hosting environment and resource quotas */
  myHostingEnvironment?: Maybe<HostingEnvironmentType>;
  /** Calculate current overage costs for billing */
  myOverageCost?: Maybe<OverageCostType>;
  /** Get usage history for analytics charts (default 30 days) */
  myUsageHistory?: Maybe<UsageHistoryType>;
  /** Get detailed usage logs (for debugging/support) */
  myUsageLogs?: Maybe<Array<Maybe<ResourceUsageLogType>>>;
  /** Get current usage summary with percentages (for dashboard) */
  myUsageSummary?: Maybe<UsageSummaryType>;
  /** Track domain purchase progress */
  purchaseStatus?: Maybe<DomainPurchaseStatusType>;
  /** Track domain renewal progress */
  renewalStatus?: Maybe<DomainRenewalStatusType>;
  /** Search domains with pagination */
  searchDomains?: Maybe<DomainSearchResponseType>;
  /** Get storefront settings (password, SEO, domain info) */
  storefrontSettings?: Maybe<StorefrontSettingsType>;
  /** Check if subdomain is available */
  validateSubdomain?: Maybe<SubdomainValidationType>;
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryCheckUploadEligibilityArgs {
  fileSizeBytes: Scalars['Int']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryCustomDomainArgs {
  domainId: Scalars['ID']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryDomainsArgs {
  workspaceId: Scalars['ID']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryMyUsageHistoryArgs {
  days?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryMyUsageLogsArgs {
  days?: InputMaybe<Scalars['Int']['input']>;
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryPurchaseStatusArgs {
  purchaseId: Scalars['ID']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryRenewalStatusArgs {
  renewalId: Scalars['ID']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QuerySearchDomainsArgs {
  page?: InputMaybe<Scalars['Int']['input']>;
  pageSize?: InputMaybe<Scalars['Int']['input']>;
  query: Scalars['String']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryStorefrontSettingsArgs {
  workspaceId: Scalars['ID']['input'];
}


/**
 * Hosting management queries (all require authentication)
 *
 * Domain Management (Clean - matches UI flows):
 * - domains: Get all domains for workspace (default + custom)
 * - validateSubdomain: Check subdomain availability (for change modal)
 * - customDomain: Get domain detail with DNS/TLS status (for polling)
 * - searchDomains: Search domains with pagination (for buy flow)
 * - purchaseStatus: Track purchase progress
 * - renewalStatus: Track renewal progress
 *
 * Storefront Settings:
 * - storefrontSettings: Get preview data (password, title, domain) for UI forms
 *
 * Resource Usage:
 * - myHostingEnvironment: Get resource quotas and limits
 * - myUsageSummary: Get current usage with percentages
 * - myUsageHistory: Get usage history for charts (30 days)
 * - myOverageCost: Calculate overage costs for billing
 * - myUsageLogs: Get detailed usage logs
 * - checkUploadEligibility: Pre-flight check for file uploads
 * - checkDeploymentEligibility: Pre-flight check for deployments
 */
export interface QueryValidateSubdomainArgs {
  subdomain: Scalars['String']['input'];
}

/**
 * Initiate domain renewal (Cameroon mobile money flow)
 *
 * Creates DomainRenewal record → User pays via MTN/Orange → Webhook completes renewal
 * Uses DomainRenewalService.initiate_renewal()
 */
export interface RenewDomain {
  __typename?: 'RenewDomain';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  paymentInstructions?: Maybe<Scalars['String']['output']>;
  renewal?: Maybe<DomainRenewalType>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for renewing a domain
 *
 * Used by renewDomain mutation
 */
export interface RenewDomainInput {
  /** CustomDomain ID to renew */
  domainId: Scalars['ID']['input'];
  /** Renewal period (1-10 years) */
  renewalPeriodYears?: InputMaybe<Scalars['Int']['input']>;
}

/**
 * Resource usage log entry
 *
 * Historical usage data for analytics and billing
 */
export interface ResourceUsageLogType extends Node {
  __typename?: 'ResourceUsageLogType';
  avgResponseTimeMs: Scalars['Int']['output'];
  bandwidthUsedGb: Scalars['Decimal']['output'];
  errorRatePercentage: Scalars['Decimal']['output'];
  estimatedCostUsd: Scalars['Decimal']['output'];
  hostingEnvironment: HostingEnvironmentType;
  id: Scalars['ID']['output'];
  recordedAt: Scalars['DateTime']['output'];
  requestsCount: Scalars['BigInt']['output'];
  storageUsedGb: Scalars['Decimal']['output'];
  workspace?: Maybe<WorkspaceType>;
}

/**
 * SEO settings for a deployed storefront
 *
 * Contains all SEO metadata used for:
 * - Search engine optimization (Google, Bing, etc.)
 * - Social media sharing (Facebook, Twitter, WhatsApp)
 * - Open Graph previews
 */
export interface SeoSettingsType {
  __typename?: 'SEOSettingsType';
  /** Meta description for search snippets (max 160 chars recommended) */
  description?: Maybe<Scalars['String']['output']>;
  /** Open Graph image URL for social sharing previews */
  imageUrl?: Maybe<Scalars['String']['output']>;
  /** Comma-separated keywords (optional, less important for modern SEO) */
  keywords?: Maybe<Scalars['String']['output']>;
  /** SEO title for search results (max 60 chars recommended) */
  title?: Maybe<Scalars['String']['output']>;
}

/**
 * Set or update storefront password protection
 *
 * Shopify pattern: "Infrastructure live, business not live"
 * Allows merchants to lock their storefront during development.
 *
 * Args:
 *     workspace_id: ID of workspace
 *     password: Plain text password (will be hashed)
 *              Set to None or empty string to disable protection
 *
 * Returns:
 *     success: Boolean
 *     message: Success/error message
 *     password_enabled: Whether password protection is now active
 *
 * Security:
 *     - Password is hashed using Django's PBKDF2 SHA256
 *     - Never stored in plain text
 *     - Requires workspace ownership (validated by middleware)
 *
 * Examples:
 *     # Enable password protection
 *     mutation {
 *       setStorefrontPassword(
 *         workspaceId: "uuid",
 *         password: "my-secret-password"
 *       ) {
 *         success
 *         message
 *         passwordEnabled
 *       }
 *     }
 *
 *     # Disable password protection
 *     mutation {
 *       setStorefrontPassword(
 *         workspaceId: "uuid",
 *         password: ""
 *       ) {
 *         success
 *         message
 *         passwordEnabled
 *       }
 *     }
 */
export interface SetStorefrontPassword {
  __typename?: 'SetStorefrontPassword';
  message?: Maybe<Scalars['String']['output']>;
  passwordEnabled?: Maybe<Scalars['Boolean']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for setting/updating storefront password
 *
 * Used by setStorefrontPassword mutation
 */
export interface SetStorefrontPasswordInput {
  description?: InputMaybe<Scalars['String']['input']>;
  enabled?: InputMaybe<Scalars['Boolean']['input']>;
  password?: InputMaybe<Scalars['String']['input']>;
  workspaceId: Scalars['ID']['input'];
}

/** Sites usage details */
export interface SitesUsageType {
  __typename?: 'SitesUsageType';
  activeCount: Scalars['Int']['output'];
  limit: Scalars['Int']['output'];
  percentage: Scalars['Float']['output'];
  remaining: Scalars['Int']['output'];
}

/** Storage usage details */
export interface StorageUsageType {
  __typename?: 'StorageUsageType';
  limitGb: Scalars['Float']['output'];
  percentage: Scalars['Float']['output'];
  remainingGb: Scalars['Float']['output'];
  usedGb: Scalars['Float']['output'];
}

/**
 * Storefront settings for UI forms
 *
 * Used by:
 * - SEO Settings page (edit SEO metadata)
 * - Password Settings page (edit password protection)
 * - Puck Editor (initial values for root.props)
 */
export interface StorefrontSettingsType {
  __typename?: 'StorefrontSettingsType';
  /** Current active domain (subdomain or custom) */
  assignedDomain: Scalars['String']['output'];
  /** Current password (plaintext, for merchant to share) */
  password?: Maybe<Scalars['String']['output']>;
  /** Custom message shown to visitors on password page (e.g., 'Store coming soon!') */
  passwordDescription?: Maybe<Scalars['String']['output']>;
  /** Whether password protection is enabled */
  passwordEnabled: Scalars['Boolean']['output'];
  /** Full preview URL for the storefront */
  previewUrl?: Maybe<Scalars['String']['output']>;
  /** SEO meta description (max 160 chars) */
  seoDescription?: Maybe<Scalars['String']['output']>;
  /** SEO social share image URL */
  seoImageUrl?: Maybe<Scalars['String']['output']>;
  /** SEO meta keywords (comma-separated) */
  seoKeywords?: Maybe<Scalars['String']['output']>;
  /** SEO title tag (max 60 chars) */
  seoTitle: Scalars['String']['output'];
  /** Store name for display */
  siteName?: Maybe<Scalars['String']['output']>;
}

/** Subdomain availability validation result */
export interface SubdomainValidationType {
  __typename?: 'SubdomainValidationType';
  available: Scalars['Boolean']['output'];
  errors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  fullDomain?: Maybe<Scalars['String']['output']>;
  subdomain?: Maybe<Scalars['String']['output']>;
}

/**
 * Update SEO settings for a deployed storefront
 *
 * Allows merchants to optimize their store for search engines and social sharing.
 * Fields are validated against Google's best practices:
 * - Title: Max 60 chars (Google truncates at ~60)
 * - Description: Max 160 chars (Google truncates at ~160)
 * - Keywords: Optional (less important for modern SEO)
 *
 * Args:
 *     workspace_id: ID of workspace
 *     seo_title: Page title for search results (max 60 chars recommended)
 *     seo_description: Meta description for search snippets (max 160 chars recommended)
 *     seo_keywords: Comma-separated keywords (optional)
 *     seo_image_url: Open Graph image URL for social sharing
 *
 * Returns:
 *     success: Boolean
 *     message: Success/error message
 *     warnings: List of SEO warnings (e.g., "title too long")
 *     seo_settings: Updated SEO settings object
 *
 * Examples:
 *     # Update all SEO fields
 *     mutation {
 *       updateStorefrontSEO(
 *         workspaceId: "uuid",
 *         seoTitle: "My Amazing Store - Quality Products",
 *         seoDescription: "Shop our curated collection of quality products at amazing prices. Free shipping on orders over $50.",
 *         seoKeywords: "online store, quality products, free shipping",
 *         seoImageUrl: "https://cdn.huzilerz.com/my-store/og-image.jpg"
 *       ) {
 *         success
 *         message
 *         warnings
 *         seoSettings {
 *           title
 *           description
 *           keywords
 *           imageUrl
 *         }
 *       }
 *     }
 *
 *     # Update only title and description
 *     mutation {
 *       updateStorefrontSEO(
 *         workspaceId: "uuid",
 *         seoTitle: "Best Shoes Online",
 *         seoDescription: "Find your perfect pair from our collection of premium footwear."
 *       ) {
 *         success
 *         message
 *       }
 *     }
 */
export interface UpdateStorefrontSeo {
  __typename?: 'UpdateStorefrontSEO';
  message?: Maybe<Scalars['String']['output']>;
  seoSettings?: Maybe<SeoSettingsType>;
  success?: Maybe<Scalars['Boolean']['output']>;
  warnings?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
}

/**
 * Input for updating storefront SEO settings
 *
 * Used by updateStorefrontSEO mutation
 */
export interface UpdateStorefrontSeoInput {
  seoDescription?: InputMaybe<Scalars['String']['input']>;
  seoImageUrl?: InputMaybe<Scalars['String']['input']>;
  seoKeywords?: InputMaybe<Scalars['String']['input']>;
  seoTitle?: InputMaybe<Scalars['String']['input']>;
  workspaceId: Scalars['ID']['input'];
}

/** Single data point in usage history */
export interface UsageDataPointType {
  __typename?: 'UsageDataPointType';
  avgResponseTimeMs?: Maybe<Scalars['Int']['output']>;
  bandwidthUsedGb: Scalars['Float']['output'];
  recordedAt: Scalars['DateTime']['output'];
  requestsCount?: Maybe<Scalars['Int']['output']>;
  storageUsedGb: Scalars['Float']['output'];
}

/** Usage history with time series data */
export interface UsageHistoryType {
  __typename?: 'UsageHistoryType';
  currentUsage: UsageSummaryType;
  dataPoints: Array<Maybe<UsageDataPointType>>;
  periodDays: Scalars['Int']['output'];
}

/** Complete usage summary with all resources */
export interface UsageSummaryType {
  __typename?: 'UsageSummaryType';
  bandwidth: BandwidthUsageType;
  customDomains: CustomDomainsUsageType;
  deploymentAllowed: Scalars['Boolean']['output'];
  sites: SitesUsageType;
  status: Scalars['String']['output'];
  storage: StorageUsageType;
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
 * Manually trigger domain verification
 *
 * Use case: User configured DNS and wants immediate verification
 * (instead of waiting for 15-min auto-verification Celery task)
 */
export interface VerifyCustomDomain {
  __typename?: 'VerifyCustomDomain';
  domain?: Maybe<CustomDomainType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  verified?: Maybe<Scalars['Boolean']['output']>;
}

/** An enumeration. */
export enum WorkspaceHostingCustomDomainRegistrarNameChoices {
  /** GoDaddy */
  Godaddy = 'GODADDY',
  /** Namecheap */
  Namecheap = 'NAMECHEAP'
}

/** An enumeration. */
export enum WorkspaceHostingCustomDomainStatusChoices {
  /** Active */
  Active = 'ACTIVE',
  /** Verification Failed */
  Failed = 'FAILED',
  /** Pending Verification */
  Pending = 'PENDING',
  /** Suspended */
  Suspended = 'SUSPENDED',
  /** Verified */
  Verified = 'VERIFIED'
}

/** An enumeration. */
export enum WorkspaceHostingDomainPurchasePaymentStatusChoices {
  /** Completed */
  Completed = 'COMPLETED',
  /** Failed */
  Failed = 'FAILED',
  /** Pending Payment */
  Pending = 'PENDING',
  /** Processing */
  Processing = 'PROCESSING',
  /** Refunded */
  Refunded = 'REFUNDED'
}

/** An enumeration. */
export enum WorkspaceHostingDomainRenewalRenewalStatusChoices {
  /** Completed */
  Completed = 'COMPLETED',
  /** Expired - Not Renewed */
  Expired = 'EXPIRED',
  /** Failed */
  Failed = 'FAILED',
  /** Payment Received */
  PaymentReceived = 'PAYMENT_RECEIVED',
  /** Pending Payment */
  PendingPayment = 'PENDING_PAYMENT',
  /** Processing Renewal */
  Processing = 'PROCESSING'
}

/** An enumeration. */
export enum WorkspaceHostingHostingEnvironmentStatusChoices {
  /** Active */
  Active = 'ACTIVE',
  /** Error */
  Error = 'ERROR',
  /** Grace Period */
  GracePeriod = 'GRACE_PERIOD',
  /** Initializing */
  Initializing = 'INITIALIZING',
  /** Suspended */
  Suspended = 'SUSPENDED'
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
