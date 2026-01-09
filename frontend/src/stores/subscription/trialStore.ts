/**
 * Trial Store - Zustand 2024 Best Practices
 * Manages trial subscription state, creation, and upgrades
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type {
  TrialCreateRequest,
  TrialCreateResponse,
  TrialUpgradeRequest,
  TrialUpgradeResponse,
  TrialStatusResponse,
} from "../../types/subscription";
import trialService from "../../services/subscription/trial";

// ============================================================================
// Trial Store State Interface
// ============================================================================

interface TrialStoreState {
  // Trial Data
  trial: TrialStatusResponse["trial"] | null;
  currentTrial: TrialCreateResponse | null;
  upgradeInfo: TrialUpgradeResponse | null;
  pricing: {
    beginning: { amount: number; duration_days: number };
    pro: { amount: number; duration_days: number };
    enterprise: { amount: number; duration_days: number };
  } | null;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Actions - Trial Operations
  createTrial: (request: TrialCreateRequest) => Promise<TrialCreateResponse>;
  upgradeTrial: (request: TrialUpgradeRequest) => Promise<TrialUpgradeResponse>;
  getTrialStatus: () => Promise<void>;
  getTrialPricing: () => Promise<void>;

  // UI Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  clearTrial: () => void;

  // Computed/Helper Methods
  isActive: () => boolean;
  requiresPayment: () => boolean;
  daysRemaining: () => number | null;
  canUpgrade: () => boolean;
  isExpired: () => boolean;
  getNextTierOptions: () => string[];
  getUpgradeCost: (targetTier: string) => number | null;
}

// ============================================================================
// Create Trial Store
// ============================================================================

export const useTrialStore = create<TrialStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      trial: null,
      currentTrial: null,
      upgradeInfo: null,
      pricing: null,
      isLoading: false,
      error: null,

      // ========================================================================
      // Trial Actions
      // ========================================================================

      createTrial: async (request) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const response = await trialService.createTrial(request);

          set((state) => {
            state.currentTrial = response;
            state.isLoading = false;
          });

          // Refresh trial status after creation
          await get().getTrialStatus();

          return response;
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Operation failed';
            state.isLoading = false;
          });
          throw error;
        }
      },

      upgradeTrial: async (request) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const response = await trialService.upgradeTrial(request);

          set((state) => {
            state.upgradeInfo = response;
            state.isLoading = false;
          });

          // Refresh trial status after upgrade
          await get().getTrialStatus();

          return response;
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Operation failed';
            state.isLoading = false;
          });
          throw error;
        }
      },

      getTrialStatus: async () => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const response = await trialService.getTrialStatus();

          set((state) => {
            state.trial = response.trial;
            state.isLoading = false;
          });
        } catch (error) {
          const errorMessage =
            error instanceof Error
              ? error.message
              : "Failed to fetch trial status";
          set((state) => {
            state.error = errorMessage;
            state.isLoading = false;
          });
          throw error;
        }
      },

      getTrialPricing: async () => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const pricing = await trialService.getTrialPricing();

          set((state) => {
            state.pricing = pricing;
            state.isLoading = false;
          });
        } catch (error) {
          const errorMessage =
            error instanceof Error
              ? error.message
              : "Failed to fetch trial pricing";
          set((state) => {
            state.error = errorMessage;
            state.isLoading = false;
          });
          throw error;
        }
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

      clearTrial: () => {
        set((state) => {
          state.trial = null;
          state.currentTrial = null;
          state.upgradeInfo = null;
          state.error = null;
        });
      },

      // ========================================================================
      // Computed/Helper Methods
      // ========================================================================

      isActive: () => {
        const { trial } = get();
        return trial?.status === "active";
      },

      requiresPayment: () => {
        const { trial } = get();
        return trial?.status === "pending_payment";
      },

      daysRemaining: () => {
        const { trial } = get();
        return trial?.days_remaining ?? null;
      },

      canUpgrade: () => {
        const { trial } = get();
        return trial?.can_upgrade ?? false;
      },

      isExpired: () => {
        const { trial } = get();
        return trial?.status === "expired";
      },

      getNextTierOptions: () => {
        const { trial } = get();
        return trial?.next_tier_options ?? [];
      },

      getUpgradeCost: (targetTier) => {
        const { trial, pricing } = get();
        if (!trial || !pricing) return null;

        const currentTierAmount =
          pricing[trial.tier as keyof typeof pricing]?.amount ?? 0;
        const targetTierAmount =
          pricing[targetTier as keyof typeof pricing]?.amount ?? 0;

        return targetTierAmount - currentTierAmount;
      },
    })),
  ),
);

// ============================================================================
// Selectors for Performance
// ============================================================================

// Stable references for default values to prevent infinite loops
const EMPTY_ARRAY: never[] = [];

export const trialSelectors = {
  // Core selectors
  trial: (state: TrialStoreState) => state.trial,
  currentTrial: (state: TrialStoreState) => state.currentTrial,
  upgradeInfo: (state: TrialStoreState) => state.upgradeInfo,
  pricing: (state: TrialStoreState) => state.pricing,
  isLoading: (state: TrialStoreState) => state.isLoading,
  error: (state: TrialStoreState) => state.error,

  // Computed selectors
  isActive: (state: TrialStoreState) => state.trial?.status === "active",
  requiresPayment: (state: TrialStoreState) =>
    state.trial?.status === "pending_payment",
  isExpired: (state: TrialStoreState) => state.trial?.status === "expired",
  isConverted: (state: TrialStoreState) => state.trial?.status === "converted",
  tier: (state: TrialStoreState) => state.trial?.tier,
  daysRemaining: (state: TrialStoreState) => state.trial?.days_remaining,
  canUpgrade: (state: TrialStoreState) => state.trial?.can_upgrade ?? false,
  nextTierOptions: (state: TrialStoreState) =>
    state.trial?.next_tier_options || EMPTY_ARRAY,
  hasTrial: (state: TrialStoreState) => state.trial !== null,
  amountPaid: (state: TrialStoreState) => state.trial?.amount_paid ?? 0,
  upgradeHistory: (state: TrialStoreState) =>
    state.trial?.upgrade_history || EMPTY_ARRAY,

  // Action selectors (stable references)
  createTrial: (state: TrialStoreState) => state.createTrial,
  upgradeTrial: (state: TrialStoreState) => state.upgradeTrial,
  getTrialStatus: (state: TrialStoreState) => state.getTrialStatus,
  getTrialPricing: (state: TrialStoreState) => state.getTrialPricing,
  clearError: (state: TrialStoreState) => state.clearError,
  clearTrial: (state: TrialStoreState) => state.clearTrial,
  getUpgradeCost: (state: TrialStoreState) => state.getUpgradeCost,
  getNextTierOptions: (state: TrialStoreState) => state.getNextTierOptions,
};

// ============================================================================
// Export
// ============================================================================

export default useTrialStore;
