/**
 * Payment Service - Payment retry and status polling
 * Aligned with backend payments/views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  RetryPaymentRequest,
  RetryPaymentResponse,
} from '../../types/subscription/subscription'
import type {
  PaymentStatusResponse,
  PlatformPaymentMethodsResponse
} from '../../types/payment/payment'

// ============================================================================
// Payment Service
// ============================================================================

export class PaymentService extends BaseService {
  constructor() {
    super('payments')
  }

  /**
   * Retry payment for existing subscription/domain/etc
   * Backend: POST /api/payments/retry/
   *
   * Handles retry for any purpose (subscription, domain, theme, checkout)
   */
  async retryPayment(request: RetryPaymentRequest): Promise<RetryPaymentResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['purpose', 'reference_id', 'workspace_id'])

    return this.post<RetryPaymentResponse>('/retry/', request)
  }

  /**
   * Check payment status
   * Backend: GET /api/payments/status/{payment_intent_id}/
   *
   * Used for polling payment status after creation
   * Backend automatically queries provider API if payment is not in final state
   */
  async checkPaymentStatus(paymentIntentId: string): Promise<PaymentStatusResponse> {
    if (!paymentIntentId) {
      throw new Error('payment_intent_id is required')
    }

    return this.get<PaymentStatusResponse>(`/status/${paymentIntentId}/`)
  }

  /**
   * Get platform-level payment methods (NO workspace required)
   * Backend: GET /api/payments/platform-methods/?purpose=subscription
   *
   * Used for subscription checkout, domain purchases, and other platform-level payments
   * Returns cached response from Redis (1 hour TTL)
   * Rate limited: 100 requests/minute per IP
   *
   * @param purpose - Payment purpose (subscription, domain, theme) - defaults to 'subscription'
   */
  async getPlatformPaymentMethods(purpose: string = 'subscription'): Promise<PlatformPaymentMethodsResponse> {
    return this.get<PlatformPaymentMethodsResponse>(`/platform-methods/`, { purpose })
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const paymentService = new PaymentService()
export default paymentService
