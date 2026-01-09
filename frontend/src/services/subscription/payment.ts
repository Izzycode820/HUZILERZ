/**
 * Payment Service - Payment processing operations
 * Aligned with backend payment_views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  PaymentInitiationRequest,
  PaymentInitiationResponse,
  PaymentStatusResponse,
  PaymentMethodsResponse,
  CancelPaymentResponse,
} from '../../types/subscription'

// ============================================================================
// Payment Service
// ============================================================================

export class PaymentService extends BaseService {
  constructor() {
    super('subscriptions')
  }

  /**
   * Initiate payment for subscription or trial
   * Backend: POST /api/subscriptions/payment/initiate/
   */
  async initiatePayment(request: PaymentInitiationRequest): Promise<PaymentInitiationResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['payment_type', 'plan_tier', 'phone_number', 'payment_method', 'amount'])

    return this.post<PaymentInitiationResponse>('/payment/initiate/', request)
  }

  /**
   * Check payment status
   * Backend: GET /api/subscriptions/payment/status/{payment_id}/
   */
  async checkPaymentStatus(paymentId: string): Promise<PaymentStatusResponse> {
    if (!paymentId) {
      throw new Error('Payment ID is required')
    }

    return this.get<PaymentStatusResponse>(`/payment/status/${paymentId}/`)
  }

  /**
   * Get user's payment methods
   * Backend: GET /api/subscriptions/payment/methods/
   */
  async getPaymentMethods(): Promise<PaymentMethodsResponse> {
    return this.get<PaymentMethodsResponse>('/payment/methods/')
  }

  /**
   * Cancel pending payment session
   * Backend: POST /api/subscriptions/payment/cancel/{payment_id}/
   */
  async cancelPayment(paymentId: string, reason?: string): Promise<CancelPaymentResponse> {
    if (!paymentId) {
      throw new Error('Payment ID is required')
    }

    return this.post<CancelPaymentResponse>(`/payment/cancel/${paymentId}/`, {
      reason: reason || 'User requested cancellation',
    })
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const paymentService = new PaymentService()
export default paymentService