/**
 * Pricing Store - Zustand 2024 Best Practices
 * Manages standard and trial pricing data
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { PricingResponse } from "../../types/subscription";
import pricingService from "../../services/subscription/pricing";

// ============================================================================
// Pricing Store State Interface
// ============================================================================

interface TrialPricingData {
  beginning: {
    amount: number;
    duration_days: number;
    currency: "FCFA";
    period: "30 days";
  };
  pro: {
    amount: number;
    duration_days: number;
    currency: "FCFA";
    period: "30 days";
  };
  enterprise: {
    amount: number;
    duration_days: number;
    currency: "FCFA";
    period: "30 days";
  };
}

interface PricingStoreState {
  // Pricing Data
  standardPricing: PricingResponse | null;
  trialPricing: TrialPricingData | null;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Actions - Pricing Operations
  getStandardPricing: () => Promise<void>;
  getTrialPricing: () => void;

  // UI Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  clearPricing: () => void;

  // Helper methods
  hasStandardPricing: () => boolean;
  hasTrialPricing: () => boolean;
}

// ============================================================================
// Create Pricing Store
// ============================================================================

export const usePricingStore = create<PricingStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      standardPricing: null,
      trialPricing: null,
      isLoading: false,
      error: null,

      // ========================================================================
      // Pricing Actions
      // ========================================================================

      getStandardPricing: async () => {
        // Skip if already loading or data exists
        const { isLoading, standardPricing } = get();
        if (isLoading || standardPricing) return;

        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const pricing = await pricingService.getPricing();

          set((state) => {
            state.standardPricing = pricing;
            state.isLoading = false;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch pricing';
            state.isLoading = false;
          });
          throw error;
        }
      },

      getTrialPricing: () => {
        // Skip if data already exists
        const { trialPricing } = get();
        if (trialPricing) return;

        set((state) => {
          state.trialPricing = pricingService.getTrialPricing();
        });
      },

      // ========================================================================
      // UI State Actions
      // ========================================================================

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading;
        });
      },

      setError: (error) => {
        set((state) => {
          state.error = error;
          if (error) {
            state.isLoading = false;
          }
        });
      },

      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },

      clearPricing: () => {
        set((state) => {
          state.standardPricing = null;
          state.trialPricing = null;
          state.error = null;
        });
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      hasStandardPricing: () => {
        const { standardPricing } = get();
        return standardPricing !== null;
      },

      hasTrialPricing: () => {
        const { trialPricing } = get();
        return trialPricing !== null;
      },
    })),
  ),
);

// ============================================================================
// Selectors for Performance
// ============================================================================

export const pricingSelectors = {
  // Core selectors
  standardPricing: (state: PricingStoreState) => state.standardPricing,
  trialPricing: (state: PricingStoreState) => state.trialPricing,
  isLoading: (state: PricingStoreState) => state.isLoading,
  error: (state: PricingStoreState) => state.error,

  // Computed selectors
  hasStandardPricing: (state: PricingStoreState) =>
    state.standardPricing !== null,
  hasTrialPricing: (state: PricingStoreState) => state.trialPricing !== null,
  hasPricing: (state: PricingStoreState) =>
    state.standardPricing !== null || state.trialPricing !== null,

  // Plan selectors
  freePlan: (state: PricingStoreState) => state.standardPricing?.free,
  beginningPlan: (state: PricingStoreState) => state.standardPricing?.beginning,
  proPlan: (state: PricingStoreState) => state.standardPricing?.pro,
  enterprisePlan: (state: PricingStoreState) =>
    state.standardPricing?.enterprise,

  // Trial pricing selectors
  beginningTrialPrice: (state: PricingStoreState) =>
    state.trialPricing?.beginning.amount,
  proTrialPrice: (state: PricingStoreState) => state.trialPricing?.pro.amount,
  enterpriseTrialPrice: (state: PricingStoreState) =>
    state.trialPricing?.enterprise.amount,

  // Action selectors (stable references)
  getStandardPricing: (state: PricingStoreState) => state.getStandardPricing,
  getTrialPricing: (state: PricingStoreState) => state.getTrialPricing,
  clearError: (state: PricingStoreState) => state.clearError,
  clearPricing: (state: PricingStoreState) => state.clearPricing,
  hasStandardPricingFn: (state: PricingStoreState) => state.hasStandardPricing,
  hasTrialPricingFn: (state: PricingStoreState) => state.hasTrialPricing,
};

// ============================================================================
// Export
// ============================================================================

export default usePricingStore;
