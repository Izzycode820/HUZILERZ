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
  DateTime: { input: string; output: string; }
  Decimal: { input: string; output: string; }
  UUID: { input: string; output: string; }
}

/**
 * Billing overview type for billing page
 * Matches Shopify billing page structure - upcoming bill section only
 */
export interface BillingOverviewType {
  __typename?: 'BillingOverviewType';
  daysUntilBill?: Maybe<Scalars['Int']['output']>;
  lastPaymentMethod?: Maybe<Scalars['String']['output']>;
  lastPaymentPhoneNumber?: Maybe<Scalars['String']['output']>;
  nextBillDate?: Maybe<Scalars['DateTime']['output']>;
  upcomingBillAmount?: Maybe<Scalars['Float']['output']>;
}

/**
 * Billing profile type for billing profile page
 * Matches Shopify billing-profile page
 * Fields: primary payment method, payment number
 */
export interface BillingProfileType {
  __typename?: 'BillingProfileType';
  primaryPaymentMethod?: Maybe<Scalars['String']['output']>;
  userPhone?: Maybe<Scalars['String']['output']>;
}

/**
 * Charges table type
 * Matches Shopify billing-charging table page
 * Fields: bill number (reference), date, charge type, amount
 */
export interface ChargesType {
  __typename?: 'ChargesType';
  /** Amount in XAF */
  amount: Scalars['Decimal']['output'];
  /** Type of charge (derived from PaymentIntent.purpose) */
  chargeType: SubscriptionPaymentRecordChargeTypeChoices;
  createdAt: Scalars['DateTime']['output'];
  /** Payment reference */
  reference: Scalars['String']['output'];
}

/** Price breakdown for transparency */
export interface CheckoutBreakdown {
  __typename?: 'CheckoutBreakdown';
  /** Base plan price */
  basePrice?: Maybe<Scalars['Float']['output']>;
  /** Currency code (XAF) */
  currency?: Maybe<Scalars['String']['output']>;
  /** Discount amount (if intro) */
  discount?: Maybe<Scalars['Float']['output']>;
  /** Final amount to charge */
  finalAmount?: Maybe<Scalars['Float']['output']>;
}

/**
 * Subscription mutations
 *
 * Platform-level mutations (auth required, no workspace):
 * - prepareSubscriptionCheckout: Get authoritative pricing for checkout
 */
export interface Mutation {
  __typename?: 'Mutation';
  /**
   * Determine checkout action type based on user's current subscription state.
   *
   * Called by PricingPage BEFORE navigation to determine which flow to use.
   * This is the source of truth for action type - frontend doesn't guess.
   *
   * Returns one of:
   * - subscribe: No subscription or expired, go to checkout
   * - renew: Same tier, in renewal window, go to checkout
   * - upgrade: Higher tier selected, go to upgrade checkout
   * - downgrade: Lower tier selected, show confirmation modal (no checkout)
   * - already_on_plan: Same tier, not in renewal window
   */
  prepareIntent?: Maybe<PrepareIntent>;
  /**
   * Prepare renewal checkout - Returns AUTHORITATIVE PRICING for current plan
   *
   * Security:
   * - Verifies user has active subscription
   * - Validates renewal window (5 days)
   * - Returns price of CURRENT plan (no user input needed)
   */
  prepareRenewalCheckout?: Maybe<PrepareRenewalCheckout>;
  /**
   * Prepare subscription checkout - Returns AUTHORITATIVE PRICING
   *
   * SECURITY BOUNDARY: This mutation re-derives price from source of truth
   * Frontend passes INTENT only, backend computes final price
   *
   * Pattern: Shopify/Stripe checkout preparation
   *
   * Flow:
   * 1. Frontend: User selects plan → passes tier/cycle/requested_mode
   * 2. Backend: Validates eligibility, resolves final pricing_mode, computes amount
   * 3. Frontend: Displays returned amount (authoritative)
   * 4. Payment: Creates PaymentIntent with backend-computed amount
   */
  prepareSubscriptionCheckout?: Maybe<PrepareSubscriptionCheckout>;
  /**
   * Prepare upgrade checkout - Returns AUTHORITATIVE PRICING for upgrade
   *
   * Security:
   * - Verifies user has active subscription
   * - Validates target tier is higher than current
   * - Returns upgrade amount (future: could include proration)
   */
  prepareUpgradeCheckout?: Maybe<PrepareUpgradeCheckout>;
}


/**
 * Subscription mutations
 *
 * Platform-level mutations (auth required, no workspace):
 * - prepareSubscriptionCheckout: Get authoritative pricing for checkout
 */
export interface MutationPrepareIntentArgs {
  intentData: PrepareIntentInput;
}


/**
 * Subscription mutations
 *
 * Platform-level mutations (auth required, no workspace):
 * - prepareSubscriptionCheckout: Get authoritative pricing for checkout
 */
export interface MutationPrepareSubscriptionCheckoutArgs {
  checkoutData: PrepareCheckoutInput;
}


/**
 * Subscription mutations
 *
 * Platform-level mutations (auth required, no workspace):
 * - prepareSubscriptionCheckout: Get authoritative pricing for checkout
 */
export interface MutationPrepareUpgradeCheckoutArgs {
  upgradeData: PrepareUpgradeInput;
}

/** An object with an ID */
export interface Node {
  /** The ID of the object */
  id: Scalars['ID']['output'];
}

/**
 * Badge display for plan cards (e.g., "Most popular", "Best value")
 * Loaded from plans_showcase.yaml
 */
export interface PlanBadgeType {
  __typename?: 'PlanBadgeType';
  text?: Maybe<Scalars['String']['output']>;
  tone?: Maybe<Scalars['String']['output']>;
}

/**
 * Call-to-action button text configuration
 * Changes based on whether it's the current plan
 */
export interface PlanCtaType {
  __typename?: 'PlanCTAType';
  currentPlan?: Maybe<Scalars['String']['output']>;
  default?: Maybe<Scalars['String']['output']>;
}

/**
 * Plan capabilities/features from YAML
 * Matches plans.yaml structure exactly
 */
export interface PlanCapabilitiesType {
  __typename?: 'PlanCapabilitiesType';
  analytics?: Maybe<Scalars['String']['output']>;
  apiAccess?: Maybe<Scalars['String']['output']>;
  automation?: Maybe<Scalars['String']['output']>;
  customDomain?: Maybe<Scalars['Boolean']['output']>;
  dedicatedSupport?: Maybe<Scalars['Boolean']['output']>;
  deploymentAllowed?: Maybe<Scalars['Boolean']['output']>;
  paymentProcessing?: Maybe<Scalars['Boolean']['output']>;
  productLimit?: Maybe<Scalars['Int']['output']>;
  staffLimit?: Maybe<Scalars['Int']['output']>;
  storageGb?: Maybe<Scalars['Float']['output']>;
  themeLibraryLimit?: Maybe<Scalars['Int']['output']>;
  workspaceLimit?: Maybe<Scalars['Int']['output']>;
}

/**
 * Pricing display configuration for plan cards
 * Controls how pricing is shown (intro, standard, starting_at, free)
 */
export interface PlanPricingDisplayType {
  __typename?: 'PlanPricingDisplayType';
  hasIntroDiscount?: Maybe<Scalars['Boolean']['output']>;
  introLabel?: Maybe<Scalars['String']['output']>;
  introSuffix?: Maybe<Scalars['String']['output']>;
  mode?: Maybe<Scalars['String']['output']>;
  startingLabel?: Maybe<Scalars['String']['output']>;
  supportsYearlyBilling?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Complete showcase/presentation configuration for a plan
 * Separates UI concerns from pricing/capability data
 * Based on Shopify pricing page pattern
 */
export interface PlanShowcaseType {
  __typename?: 'PlanShowcaseType';
  badge?: Maybe<PlanBadgeType>;
  cta?: Maybe<PlanCtaType>;
  highlightedFeatures?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  nameOverride?: Maybe<Scalars['String']['output']>;
  order?: Maybe<Scalars['Int']['output']>;
  pricingDisplay?: Maybe<PlanPricingDisplayType>;
  tagline?: Maybe<Scalars['String']['output']>;
}

/**
 * Public plan type for plan listing/browsing
 *
 * Contains pricing and basic info
 * Features loaded dynamically from YAML
 */
export interface PlanType extends Node {
  __typename?: 'PlanType';
  capabilities?: Maybe<PlanCapabilitiesType>;
  createdAt: Scalars['DateTime']['output'];
  /** Plan description for pricing page */
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  introDurationDays?: Maybe<Scalars['Int']['output']>;
  introPrice?: Maybe<Scalars['Float']['output']>;
  isActive: Scalars['Boolean']['output'];
  isFree?: Maybe<Scalars['Boolean']['output']>;
  isPaid?: Maybe<Scalars['Boolean']['output']>;
  name: Scalars['String']['output'];
  regularPriceMonthly?: Maybe<Scalars['Float']['output']>;
  regularPriceYearly?: Maybe<Scalars['Float']['output']>;
  showcase?: Maybe<PlanShowcaseType>;
  targetMarketDescription?: Maybe<Scalars['String']['output']>;
  tier: SubscriptionSubscriptionPlanTierChoices;
  updatedAt: Scalars['DateTime']['output'];
}

/**
 * Input for checkout preparation
 * Represents USER INTENT only (not authoritative pricing)
 */
export interface PrepareCheckoutInput {
  /** Billing cycle (monthly, yearly) */
  cycle: Scalars['String']['input'];
  /** Requested pricing mode (intro, regular) */
  requestedMode: Scalars['String']['input'];
  /** Plan tier (beginning, pro, enterprise) */
  tier: Scalars['String']['input'];
}

/**
 * Determine checkout action type based on user's current subscription state.
 *
 * Called by PricingPage BEFORE navigation to determine which flow to use.
 * This is the source of truth for action type - frontend doesn't guess.
 *
 * Returns one of:
 * - subscribe: No subscription or expired, go to checkout
 * - renew: Same tier, in renewal window, go to checkout
 * - upgrade: Higher tier selected, go to upgrade checkout
 * - downgrade: Lower tier selected, show confirmation modal (no checkout)
 * - already_on_plan: Same tier, not in renewal window
 */
export interface PrepareIntent {
  __typename?: 'PrepareIntent';
  /** Action type: subscribe, renew, upgrade, downgrade, already_on_plan */
  action?: Maybe<Scalars['String']['output']>;
  /** Expected amount (for display) */
  amount?: Maybe<Scalars['Float']['output']>;
  /** Currency code */
  currency?: Maybe<Scalars['String']['output']>;
  /** Current plan name (for downgrade confirmation) */
  currentPlanName?: Maybe<Scalars['String']['output']>;
  /** Days until renewal window opens */
  daysUntilRenewal?: Maybe<Scalars['Int']['output']>;
  /** Error message if any */
  error?: Maybe<Scalars['String']['output']>;
  /** Error code */
  errorCode?: Maybe<Scalars['String']['output']>;
  /** User-friendly message */
  message?: Maybe<Scalars['String']['output']>;
  /** Target plan display name */
  planName?: Maybe<Scalars['String']['output']>;
  /** intro or regular */
  pricingMode?: Maybe<Scalars['String']['output']>;
  /** When downgrade takes effect (ISO date) */
  scheduleDate?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Input for intent preparation - just the target tier */
export interface PrepareIntentInput {
  /** Billing cycle (monthly, yearly), defaults to monthly */
  cycle?: InputMaybe<Scalars['String']['input']>;
  /** Target plan tier (beginning, pro, enterprise) */
  tier: Scalars['String']['input'];
}

/**
 * Prepare renewal checkout - Returns AUTHORITATIVE PRICING for current plan
 *
 * Security:
 * - Verifies user has active subscription
 * - Validates renewal window (5 days)
 * - Returns price of CURRENT plan (no user input needed)
 */
export interface PrepareRenewalCheckout {
  __typename?: 'PrepareRenewalCheckout';
  /** Authoritative renewal amount */
  amount?: Maybe<Scalars['Float']['output']>;
  /** Price breakdown */
  breakdown?: Maybe<CheckoutBreakdown>;
  /** Currency code */
  currency?: Maybe<Scalars['String']['output']>;
  /** Billing cycle duration */
  cycleDurationDays?: Maybe<Scalars['Int']['output']>;
  /** Error message if any */
  error?: Maybe<Scalars['String']['output']>;
  /** Error code */
  errorCode?: Maybe<Scalars['String']['output']>;
  /** User-friendly message */
  message?: Maybe<Scalars['String']['output']>;
  /** Plan display name */
  planName?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Prepare subscription checkout - Returns AUTHORITATIVE PRICING
 *
 * SECURITY BOUNDARY: This mutation re-derives price from source of truth
 * Frontend passes INTENT only, backend computes final price
 *
 * Pattern: Shopify/Stripe checkout preparation
 *
 * Flow:
 * 1. Frontend: User selects plan → passes tier/cycle/requested_mode
 * 2. Backend: Validates eligibility, resolves final pricing_mode, computes amount
 * 3. Frontend: Displays returned amount (authoritative)
 * 4. Payment: Creates PaymentIntent with backend-computed amount
 */
export interface PrepareSubscriptionCheckout {
  __typename?: 'PrepareSubscriptionCheckout';
  /** Authoritative amount to charge */
  amount?: Maybe<Scalars['Float']['output']>;
  /** Price breakdown */
  breakdown?: Maybe<CheckoutBreakdown>;
  /** Currency code */
  currency?: Maybe<Scalars['String']['output']>;
  /** Billing cycle duration */
  cycleDurationDays?: Maybe<Scalars['Int']['output']>;
  /** Resolved pricing mode (intro or regular) */
  effectiveMode?: Maybe<Scalars['String']['output']>;
  /** Error message if any */
  error?: Maybe<Scalars['String']['output']>;
  /** Error code for programmatic handling */
  errorCode?: Maybe<Scalars['String']['output']>;
  /** Intro period duration (if applicable) */
  introDurationDays?: Maybe<Scalars['Int']['output']>;
  /** User-friendly message */
  message?: Maybe<Scalars['String']['output']>;
  /** Plan display name */
  planName?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Prepare upgrade checkout - Returns AUTHORITATIVE PRICING for upgrade
 *
 * Security:
 * - Verifies user has active subscription
 * - Validates target tier is higher than current
 * - Returns upgrade amount (future: could include proration)
 */
export interface PrepareUpgradeCheckout {
  __typename?: 'PrepareUpgradeCheckout';
  /** Authoritative upgrade amount */
  amount?: Maybe<Scalars['Float']['output']>;
  /** Price breakdown */
  breakdown?: Maybe<CheckoutBreakdown>;
  /** Currency code */
  currency?: Maybe<Scalars['String']['output']>;
  /** Current plan name */
  currentPlanName?: Maybe<Scalars['String']['output']>;
  /** Billing cycle duration */
  cycleDurationDays?: Maybe<Scalars['Int']['output']>;
  /** Error message if any */
  error?: Maybe<Scalars['String']['output']>;
  /** Error code */
  errorCode?: Maybe<Scalars['String']['output']>;
  /** User-friendly message */
  message?: Maybe<Scalars['String']['output']>;
  /** Target plan display name */
  planName?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Input for upgrade checkout preparation */
export interface PrepareUpgradeInput {
  /** Billing cycle (monthly, yearly) */
  cycle?: InputMaybe<Scalars['String']['input']>;
  /** Target plan tier (pro, enterprise) */
  tier: Scalars['String']['input'];
}

/**
 * Combined subscription queries
 *
 * Public queries (no auth):
 * - plans: Browse available subscription plans
 * - planDetails: View single plan details
 * - trialPricing: Get trial pricing info
 *
 * Authenticated queries (requires workspace):
 * - billingOverview: Billing page data (upcoming bill + past bills)
 * - paymentRecords: Charges table (payment history)
 * - billingProfile: Billing profile page (payment methods + user info)
 * - currentPlan: Current subscription/plan details
 * - myTrial: Trial status (eligibility check)
 */
export interface Query {
  __typename?: 'Query';
  /** Get billing overview for main billing page (upcoming bill + past bills) */
  billingOverview?: Maybe<BillingOverviewType>;
  /** Get billing profile (payment methods, currency, address) */
  billingProfile?: Maybe<BillingProfileType>;
  /** Get charges for charges table page */
  charges?: Maybe<Array<Maybe<ChargesType>>>;
  /** Get user's current subscription/plan */
  currentPlan?: Maybe<SubscriptionType>;
  /** Check if current user is eligible for intro pricing (returns null if not authenticated) */
  isIntroPricingEligible?: Maybe<Scalars['Boolean']['output']>;
  /** Get past bills with filters and sorting */
  pastBills?: Maybe<Array<Maybe<SubscriptionHistoryType>>>;
  /** Get detailed plan information by tier (PUBLIC) */
  planDetails?: Maybe<PlanType>;
  /** Browse all available subscription plans (PUBLIC) */
  plans?: Maybe<Array<Maybe<PlanType>>>;
}


/**
 * Combined subscription queries
 *
 * Public queries (no auth):
 * - plans: Browse available subscription plans
 * - planDetails: View single plan details
 * - trialPricing: Get trial pricing info
 *
 * Authenticated queries (requires workspace):
 * - billingOverview: Billing page data (upcoming bill + past bills)
 * - paymentRecords: Charges table (payment history)
 * - billingProfile: Billing profile page (payment methods + user info)
 * - currentPlan: Current subscription/plan details
 * - myTrial: Trial status (eligibility check)
 */
export interface QueryChargesArgs {
  chargeType?: InputMaybe<Scalars['String']['input']>;
  dateFrom?: InputMaybe<Scalars['DateTime']['input']>;
  dateTo?: InputMaybe<Scalars['DateTime']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Combined subscription queries
 *
 * Public queries (no auth):
 * - plans: Browse available subscription plans
 * - planDetails: View single plan details
 * - trialPricing: Get trial pricing info
 *
 * Authenticated queries (requires workspace):
 * - billingOverview: Billing page data (upcoming bill + past bills)
 * - paymentRecords: Charges table (payment history)
 * - billingProfile: Billing profile page (payment methods + user info)
 * - currentPlan: Current subscription/plan details
 * - myTrial: Trial status (eligibility check)
 */
export interface QueryPastBillsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  sortOrder?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Combined subscription queries
 *
 * Public queries (no auth):
 * - plans: Browse available subscription plans
 * - planDetails: View single plan details
 * - trialPricing: Get trial pricing info
 *
 * Authenticated queries (requires workspace):
 * - billingOverview: Billing page data (upcoming bill + past bills)
 * - paymentRecords: Charges table (payment history)
 * - billingProfile: Billing profile page (payment methods + user info)
 * - currentPlan: Current subscription/plan details
 * - myTrial: Trial status (eligibility check)
 */
export interface QueryPlanDetailsArgs {
  tier: Scalars['String']['input'];
}

/**
 * Subscription history type for past bills
 * Matches Shopify billing page past bills section
 */
export interface SubscriptionHistoryType {
  __typename?: 'SubscriptionHistoryType';
  action: SubscriptionSubscriptionHistoryActionChoices;
  amountPaid?: Maybe<Scalars['Decimal']['output']>;
  /** Human-readable bill number (e.g., #452157574) */
  billNumber: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Payment status of this bill */
  status: SubscriptionSubscriptionHistoryStatusChoices;
}

/** An enumeration. */
export enum SubscriptionPaymentRecordChargeTypeChoices {
  /** Add-on */
  Addon = 'ADDON',
  /** Checkout */
  Checkout = 'CHECKOUT',
  /** Domain */
  Domain = 'DOMAIN',
  /** Domain Renewal */
  DomainRenewal = 'DOMAIN_RENEWAL',
  /** Other */
  Other = 'OTHER',
  /** Subscription */
  Subscription = 'SUBSCRIPTION',
  /** Subscription Renewal */
  SubscriptionRenewal = 'SUBSCRIPTION_RENEWAL',
  /** Subscription Upgrade */
  SubscriptionUpgrade = 'SUBSCRIPTION_UPGRADE',
  /** Theme */
  Theme = 'THEME'
}

/** Plan type for authenticated subscription context */
export interface SubscriptionPlanType {
  __typename?: 'SubscriptionPlanType';
  /** Plan description for pricing page */
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  introDurationDays?: Maybe<Scalars['Int']['output']>;
  introPrice?: Maybe<Scalars['Float']['output']>;
  isFree?: Maybe<Scalars['Boolean']['output']>;
  isPaid?: Maybe<Scalars['Boolean']['output']>;
  name: Scalars['String']['output'];
  regularPriceMonthly?: Maybe<Scalars['Float']['output']>;
  regularPriceYearly?: Maybe<Scalars['Float']['output']>;
  tier: SubscriptionSubscriptionPlanTierChoices;
}

/** An enumeration. */
export enum SubscriptionSubscriptionHistoryActionChoices {
  /** Cancelled */
  Cancelled = 'CANCELLED',
  /** Converted */
  Converted = 'CONVERTED',
  /** Created */
  Created = 'CREATED',
  /** Downgraded */
  Downgraded = 'DOWNGRADED',
  /** Reactivated */
  Reactivated = 'REACTIVATED',
  /** Renewed */
  Renewed = 'RENEWED',
  /** Suspended */
  Suspended = 'SUSPENDED',
  /** Upgraded */
  Upgraded = 'UPGRADED'
}

/** An enumeration. */
export enum SubscriptionSubscriptionHistoryStatusChoices {
  /** Paid */
  Paid = 'PAID',
  /** Pending */
  Pending = 'PENDING',
  /** Unpaid */
  Unpaid = 'UNPAID'
}

/** An enumeration. */
export enum SubscriptionSubscriptionPlanTierChoices {
  /** Beginning */
  Beginning = 'BEGINNING',
  /** Enterprise */
  Enterprise = 'ENTERPRISE',
  /** Free */
  Free = 'FREE',
  /** Pro */
  Pro = 'PRO'
}

/** An enumeration. */
export enum SubscriptionSubscriptionStatusChoices {
  /** Active */
  Active = 'ACTIVE',
  /** Cancelled */
  Cancelled = 'CANCELLED',
  /** Change Pending */
  ChangePending = 'CHANGE_PENDING',
  /** Expired */
  Expired = 'EXPIRED',
  /** Grace Period */
  GracePeriod = 'GRACE_PERIOD',
  /** Pending Payment */
  PendingPayment = 'PENDING_PAYMENT',
  /** Restricted */
  Restricted = 'RESTRICTED',
  /** Suspended */
  Suspended = 'SUSPENDED'
}

/** User's subscription type for current plan page */
export interface SubscriptionType {
  __typename?: 'SubscriptionType';
  billingCycle?: Maybe<Scalars['String']['output']>;
  expiresAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['UUID']['output'];
  introEndsAt?: Maybe<Scalars['DateTime']['output']>;
  isOnIntroPricing?: Maybe<Scalars['Boolean']['output']>;
  plan?: Maybe<SubscriptionPlanType>;
  status: SubscriptionSubscriptionStatusChoices;
}
