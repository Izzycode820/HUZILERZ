/**
 * Subscription Service - Core subscription management
 * Aligned with backend subscription_views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  CreateSubscriptionRequest,
  CreateSubscriptionResponse,
  RenewSubscriptionRequest,
  RenewSubscriptionResponse,
  UpgradeSubscriptionRequest,
  UpgradeSubscriptionResponse,
  ScheduleDowngradeRequest,
  ScheduleDowngradeResponse,
  CancelSubscriptionRequest,
  CancelSubscriptionResponse,
  ResumeSubscriptionResponse,
  VoidPendingPaymentResponse,
  ReactivateSubscriptionResponse,
  RetrySubscriptionPaymentRequest,
  RetrySubscriptionPaymentResponse,
} from '../../types/subscription/subscription'

// ============================================================================
// Subscription Service
// ============================================================================

export class SubscriptionService extends BaseService {
  constructor() {
    super('subscriptions')
  }

  /**
   * Create new subscription
   * Backend: POST /api/subscriptions/create/
   */
  async createSubscription(request: CreateSubscriptionRequest): Promise<CreateSubscriptionResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['plan_tier', 'phone_number'])

    return this.post<CreateSubscriptionResponse>('/create/', request)
  }

  /**
   * Renew subscription manually
   * Backend: POST /api/subscriptions/renew/
   */
  async renewSubscription(request: RenewSubscriptionRequest): Promise<RenewSubscriptionResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['phone_number'])

    return this.post<RenewSubscriptionResponse>('/renew/', request)
  }

  /**
   * Upgrade existing subscription
   * Backend: POST /api/subscriptions/upgrade/
   */
  async upgradeSubscription(request: UpgradeSubscriptionRequest): Promise<UpgradeSubscriptionResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['new_plan_tier', 'phone_number'])

    return this.post<UpgradeSubscriptionResponse>('/upgrade/', request)
  }

  /**
   * Schedule downgrade for next billing cycle
   * Backend: POST /api/subscriptions/schedule-downgrade/
   */
  async scheduleDowngrade(request: ScheduleDowngradeRequest): Promise<ScheduleDowngradeResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['new_plan_tier'])

    return this.post<ScheduleDowngradeResponse>('/schedule-downgrade/', request)
  }

  /**
   * Cancel active subscription - downgrade to free immediately
   * Backend: POST /api/subscriptions/cancel/
   */
  async cancelActiveSubscription(request?: CancelSubscriptionRequest): Promise<CancelSubscriptionResponse> {
    return this.post<CancelSubscriptionResponse>('/cancel/', request || {})
  }

  /**
   * Resume cancelled subscription before expiry (Shopify/Stripe pattern)
   * Backend: POST /api/subscriptions/resume/
   */
  async resumeSubscription(): Promise<ResumeSubscriptionResponse> {
    return this.post<ResumeSubscriptionResponse>('/resume/')
  }

  /**
   * Void pending payment subscription (Stripe PaymentIntent cancel pattern)
   * Only works for pending_payment, failed, or expired subscriptions
   * Backend: POST /api/subscriptions/void/{subscription_id}/
   */
  async voidPendingPayment(subscriptionId: string): Promise<VoidPendingPaymentResponse> {
    if (!subscriptionId) {
      throw new Error('Subscription ID is required')
    }

    return this.post<VoidPendingPaymentResponse>(`/void/${subscriptionId}/`)
  }

  /**
   * Reactivate suspended subscription
   * Backend: POST /api/subscriptions/reactivate/
   */
  async reactivateSubscription(): Promise<ReactivateSubscriptionResponse> {
    return this.post<ReactivateSubscriptionResponse>('/reactivate/')
  }

  /**
   * Get full capabilities for current tier
   * Backend: GET /api/subscriptions/me/capabilities/
   *
   * Industry Standard: Stripe/GitHub/Vercel approach
   * JWT contains minimal claims + version hash
   * Full capabilities fetched separately for dynamic updates
   */
  async getCapabilities(): Promise<import('../../types/authentication/auth').CapabilitiesResponse> {
    return this.get<import('../../types/authentication/auth').CapabilitiesResponse>('/me/capabilities/')
  }

  /**
   * Retry payment for pending_payment subscription
   * Backend: POST /api/subscriptions/retry-payment/
   *
   * Use cases:
   * - User's USSD session expired
   * - User closed app without completing payment
   * - Network error during payment
   *
   * Logic:
   * - If active PaymentIntent exists -> returns it (resume)
   * - If expired -> creates new PaymentIntent (retry)
   * - NEVER recreates subscription (preserves intent)
   */
  async retrySubscriptionPayment(request: RetrySubscriptionPaymentRequest): Promise<RetrySubscriptionPaymentResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['phone_number'])

    return this.post<RetrySubscriptionPaymentResponse>('/retry-payment/', request)
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const subscriptionService = new SubscriptionService()
export default subscriptionService
