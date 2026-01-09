/**
 * Payment Store - Zustand 2024 Best Practices
 * Manages payment state, initiation, and status tracking
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type {
  PaymentInitiationRequest,
  PaymentInitiationResponse,
  PaymentStatusResponse,
  PaymentMethodsResponse,
} from "../../types/subscription";
import paymentService from "../../services/subscription/payment";

// ============================================================================
// Payment Store State Interface
// ============================================================================

interface PaymentStoreState {
  // Payment Data
  currentPayment: PaymentInitiationResponse | null;
  paymentStatus: PaymentStatusResponse | null;
  paymentMethods: PaymentMethodsResponse | null;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Actions - Payment Operations
  initiatePayment: (
    request: PaymentInitiationRequest,
  ) => Promise<PaymentInitiationResponse>;
  checkPaymentStatus: (paymentId: string) => Promise<void>;
  getPaymentMethods: () => Promise<void>;
  pollPaymentStatus: (
    paymentId: string,
    maxAttempts?: number,
  ) => Promise<PaymentStatusResponse>;

  // UI Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  clearPayment: () => void;

  // Computed/Helper Methods
  isPaymentPending: () => boolean;
  isPaymentComplete: () => boolean;
  isPaymentFailed: () => boolean;
}

// ============================================================================
// Create Payment Store
// ============================================================================

export const usePaymentStore = create<PaymentStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      currentPayment: null,
      paymentStatus: null,
      paymentMethods: null,
      isLoading: false,
      error: null,

      // ========================================================================
      // Payment Actions
      // ========================================================================

      initiatePayment: async (request) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const response = await paymentService.initiatePayment(request);

          set((state) => {
            state.currentPayment = response;
            state.isLoading = false;
          });

          return response;
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Operation failed';
            state.isLoading = false;
          });
          throw error;
        }
      },

      checkPaymentStatus: async (paymentId) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const status = await paymentService.checkPaymentStatus(paymentId);

          set((state) => {
            state.paymentStatus = status;
            state.isLoading = false;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Operation failed';
            state.isLoading = false;
          });
          throw error;
        }
      },

      getPaymentMethods: async () => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const methods = await paymentService.getPaymentMethods();

          set((state) => {
            state.paymentMethods = methods;
            state.isLoading = false;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Operation failed';
            state.isLoading = false;
          });
          throw error;
        }
      },

      pollPaymentStatus: async (paymentId, maxAttempts = 20) => {
        const poll = async (
          attempt: number = 1,
        ): Promise<PaymentStatusResponse> => {
          if (attempt > maxAttempts) {
            throw new Error("Payment status check timeout");
          }

          await get().checkPaymentStatus(paymentId);
          const status = get().paymentStatus;

          if (!status) {
            throw new Error("Failed to get payment status");
          }

          // Payment complete or failed
          if (
            status.status === "completed" ||
            status.status === "successful" ||
            status.status === "failed"
          ) {
            return status;
          }

          // Wait 3 seconds before next poll
          await new Promise((resolve) => setTimeout(resolve, 3000));
          return poll(attempt + 1);
        };

        return poll();
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

      clearPayment: () => {
        set((state) => {
          state.currentPayment = null;
          state.paymentStatus = null;
          state.error = null;
        });
      },

      // ========================================================================
      // Computed/Helper Methods
      // ========================================================================

      isPaymentPending: () => {
        const { paymentStatus } = get();
        return (
          paymentStatus?.status === "pending" ||
          paymentStatus?.status === "processing"
        );
      },

      isPaymentComplete: () => {
        const { paymentStatus } = get();
        return (
          paymentStatus?.status === "completed" ||
          paymentStatus?.status === "successful"
        );
      },

      isPaymentFailed: () => {
        const { paymentStatus } = get();
        return (
          paymentStatus?.status === "failed" ||
          paymentStatus?.status === "cancelled"
        );
      },
    })),
  ),
);

// ============================================================================
// Selectors for Performance
// ============================================================================

export const paymentSelectors = {
  // Core selectors
  currentPayment: (state: PaymentStoreState) => state.currentPayment,
  paymentStatus: (state: PaymentStoreState) => state.paymentStatus,
  paymentMethods: (state: PaymentStoreState) => state.paymentMethods,
  isLoading: (state: PaymentStoreState) => state.isLoading,
  error: (state: PaymentStoreState) => state.error,

  // Computed selectors
  hasPaymentInProgress: (state: PaymentStoreState) =>
    state.currentPayment !== null,
  paymentId: (state: PaymentStoreState) => state.currentPayment?.payment_id,
  paymentReference: (state: PaymentStoreState) =>
    state.currentPayment?.payment_reference,
  paymentAmount: (state: PaymentStoreState) => state.currentPayment?.amount,
  paymentLink: (state: PaymentStoreState) => state.currentPayment?.payment_link,
};

// ============================================================================
// Export
// ============================================================================

export default usePaymentStore;
