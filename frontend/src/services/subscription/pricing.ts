/**
 * Pricing Service - Pricing plans and trial pricing
 * Backend: GET /api/subscriptions/pricing/ (plural 'subscriptions')
 */

import BaseService from '../base/BaseService'
import type { PricingResponse } from '../../types/subscription'
import { TrialPricing } from '../../types/subscription/trials'

// ============================================================================
// Pricing Service
// ============================================================================

export class PricingService extends BaseService {
  constructor() {
    super('subscriptions') // Note: plural 'subscriptions' for all subscription endpoints
  }

  /**
   * Get standard subscription pricing plans
   * Backend: GET /api/subscriptions/pricing/
   */
  async getPricing(): Promise<PricingResponse> {
    return this.get<PricingResponse>('/pricing/')
  }

  /**
   * Get trial pricing information
   * Returns trial pricing for all tiers (30-day period)
   */
  getTrialPricing() {
    return {
      beginning: {
        amount: TrialPricing.beginning,
        duration_days: 30,
        currency: 'FCFA' as const,
        period: '30 days' as const,
      },
      pro: {
        amount: TrialPricing.pro,
        duration_days: 30,
        currency: 'FCFA' as const,
        period: '30 days' as const,
      },
      enterprise: {
        amount: TrialPricing.enterprise,
        duration_days: 30,
        currency: 'FCFA' as const,
        period: '30 days' as const,
      },
    }
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const pricingService = new PricingService()
export default pricingService