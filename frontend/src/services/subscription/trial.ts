/**
 * Trial Service - Trial subscription operations
 * Aligned with backend trial_views.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  TrialCreateRequest,
  TrialCreateResponse,
  TrialUpgradeRequest,
  TrialUpgradeResponse,
  TrialStatusResponse,
} from '../../types/subscription'

// ============================================================================
// Trial Service
// ============================================================================

export class TrialService extends BaseService {
  constructor() {
    super('subscriptions')
  }

  /**
   * Create new trial subscription
   * Backend: POST /api/subscriptions/trials/create/
   */
  async createTrial(request: TrialCreateRequest): Promise<TrialCreateResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['tier'])

    return this.post<TrialCreateResponse>('/trials/create/', request)
  }

  /**
   * Upgrade existing trial to higher tier
   * Backend: POST /api/subscriptions/trials/upgrade/
   */
  async upgradeTrial(request: TrialUpgradeRequest): Promise<TrialUpgradeResponse> {
    this.validateRequired(request as unknown as Record<string, unknown>, ['target_tier'])

    return this.post<TrialUpgradeResponse>('/trials/upgrade/', request)
  }

  /**
   * Get current trial status
   * Backend: GET /api/subscriptions/trials/status/
   */
  async getTrialStatus(): Promise<TrialStatusResponse> {
    return this.get<TrialStatusResponse>('/trials/status/')
  }

  /**
   * Get trial pricing information
   * Backend: GET /api/subscriptions/trials/pricing/
   */
  async getTrialPricing(): Promise<{
    beginning: { amount: number; duration_days: number };
    pro: { amount: number; duration_days: number };
    enterprise: { amount: number; duration_days: number };
  }> {
    return this.get('/trials/pricing/')
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const trialService = new TrialService()
export default trialService