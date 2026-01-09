/**
 * Subscription Types Barrel Export
 * Central export point for all subscription-related types
 */

// Core subscription management
export {
  SubscriptionStatus,
  PlanTier,
  SubscriptionCreateSchema,
  SubscriptionUpgradeSchema,
  requiresPayment,
  isOperational,
  type SubscriptionStatusType,
  type PlanTierType,
  type SubscriptionCreateRequest,
  type SubscriptionCreateResponse,
  type SubscriptionUpgradeRequest,
  type SubscriptionUpgradeResponse,
  type SubscriptionStatusResponse,
  type CancelSubscriptionRequest,
  type CancelSubscriptionResponse,
  canCancelSubscription,
  // Error types
  type PaidSubscriptionExistsError,
  type ActiveTrialExistsError,
  type PaymentExpiredRetryAvailableError,
  type CannotCancelActiveSubscriptionError,
  type SubscriptionError,
  isPaidSubscriptionExistsError,
  isActiveTrialExistsError,
  isPaymentExpiredRetryAvailableError,
  isCannotCancelActiveSubscriptionError,
} from './subscription';

// Payment processing
export {
  PaymentStatus,
  PaymentType,
  PaymentMethod,
  PhoneNumberSchema,
  PaymentInitiationSchema,
  isPaymentComplete,
  isPaymentFailed,
  isPaymentPending,
  type PaymentStatusType,
  type PaymentTypeType,
  type PaymentMethodType,
  type PaymentInitiationRequest,
  type PaymentInitiationResponse,
  type PaymentStatusResponse,
  type PaymentRecord,
  type CancelPaymentResponse,
  // Error types
  type CannotCancelCompletedPaymentError,
  type PaymentError,
  isCannotCancelCompletedPaymentError,
} from './payment';

// Trial system
export {
  TrialStatus,
  TrialTier,
  TrialCreateSchema,
  TrialUpgradeSchema,
  TrialPricing,
  calculateTrialUpgradeCost,
  isTrialActive,
  trialRequiresPayment,
  canUpgradeTrial,
  type TrialStatusType,
  type TrialTierType,
  type TrialCreateRequest,
  type TrialCreateResponse,
  type TrialUpgradeRequest,
  type TrialUpgradeResponse,
  type TrialStatusResponse,
} from './trials';

// Plans and pricing
export {
  PlanResources,
  PlanPricingValues,
  type PlanCapabilities,
  type PlanLimits,
  type PlanPricing,
  type PricingPlan,
  type PricingResponse,
  type PlanTierKey,
} from './plans';

// API Endpoints - Actual backend implementations
export {
  type UpgradePromptsResponse,
  type FeatureComparisonResponse,
  type PaymentMethodsResponse,
  type SubscriptionHistoryResponse,
  type HistoryEntry,
  type PaymentHistoryEntry,
  type TrialHistoryEntry,
  type RenewSubscriptionRequest,
  type RenewSubscriptionResponse,
  type ScheduleDowngradeRequest,
  type ScheduleDowngradeResponse,
  type ReactivateSubscriptionRequest,
  type ReactivateSubscriptionResponse,
  type BatchDiscountCalculationRequest,
  type BatchDiscountCalculationResponse,
  type BatchPaymentStatusCheckRequest,
  type BatchPaymentStatusCheckResponse,
  type BatchFeatureAvailabilityRequest,
  type BatchFeatureAvailabilityResponse,
  type BatchUsageAnalyticsRequest,
  type BatchUsageAnalyticsResponse,
  type BatchSubscriptionComparisonRequest,
  type BatchSubscriptionComparisonResponse,
} from './api-endpoints';

// API types
export {
  type SubscriptionApiResponse,
  type SubscriptionApiError,
  type PaginatedApiResponse,
  type PendingPaymentInfo,
} from './api-response';

// Discounts (keeping existing)
export {
  DISCOUNT_TYPES,
  DISCOUNT_LIMITS,
  DiscountCodeSchema,
  type DiscountType,
  type DiscountInfo,
  type DiscountDetail,
  type AppliedDiscount,
  type StackedDiscounts,
  type PricingCalculation,
  type DiscountValidationResult,
  type BulkDiscount,
  type PromotionalDiscount,
  type UserDiscountEligibility,
  type DiscountAnalytics,
} from './discounts';

// Features (keeping existing)
export {
  CORE_FEATURES,
  FEATURE_LIMITS,
  type CoreFeatureType,
  type FeatureAccessResult,
  type FeatureGateConfig,
  type BatchFeatureCheckRequest,
  type BatchFeatureCheckResponse,
  type FeatureUsageEvent,
  type FeatureAnalytics,
  type ConversionMessage,
  type FeatureFlag,
  type FeatureGateProps,
} from './features';

// Usage (keeping existing, removed BatchUsageAnalyticsRequest/Response - now in api-endpoints)
export {
  RESOURCE_TYPES,
  UsageAlertLevel,
  AlertNotificationChannel,
  type ResourceTypeType,
  type UsageRecord,
  type UsageAnalytics,
  type UsageLimit,
  type UsageAlert,
  type UsageHistory,
  type OptimizationSuggestion,
  type UsageBasedBilling,
  type RealTimeUsage,
  type UsageExport,
  type UsageAlertLevelType,
  type AlertNotificationChannelType,
  type UsageAlertConfig,
  type UsageAlertInstance,
  type UsageMonitoringEvent,
  type UsageSystemHealth,
} from './usage';

// WebSockets (keeping existing)
export {
  type WebSocketMessage,
  type PaymentStatusMessage,
  type SubscriptionStatusMessage,
  type UsageAlertMessage,
  type FeatureAccessMessage,
  type BillingUpdateMessage,
  type PromotionMessage,
  type SystemNotificationMessage,
  type WebSocketConnectionState,
  type WebSocketClientConfig,
  type WebSocketEventHandlers,
  type WebSocketClient,
  type HeartbeatMessage,
  type WebSocketError,
  type WebSocketMetrics,
} from './websockets';

// Invoices (keeping existing)
export {
  InvoiceStatus,
  CameroonRegion,
  type InvoiceStatusType,
  type CameroonRegionType,
  type Invoice,
  type InvoiceLineItem,
  type CameroonTaxDetails,
  type BillingAddress,
  type PaymentAllocation,
  type InvoiceGenerationRequest,
  type InvoiceGenerationResponse,
  type PaymentInstructions,
  type BulkInvoiceOperationRequest,
  type InvoiceFilterCriteria,
  type BulkInvoiceOperationResponse,
  type InvoiceAnalytics,
  type InvoiceSchedule,
  type InvoiceTemplate,
  type InvoiceLayoutConfig,
  type InvoiceBranding,
  type CreditNote,
  type InvoiceEventMessage,
  type InvoiceAccessLog,
} from './invoices';