"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { PaymentMethodSelector } from './PaymentMethodSelector';
import { PaymentForm } from './PaymentForm';
import { PaymentProcessor } from './PaymentProcessor';
import { usePlatformPaymentMethods } from '@/hooks/payment/usePayment';
import { useAuth } from '@/hooks/authentication/useAuth';
import { useCurrentWorkspace } from '@/hooks/authentication/useWorkspace';
import subscriptionService from '@/services/subscription/subscription';
import type { SubscriptionTier, BillingCycle, PricingMode } from '@/types/subscription/subscription';

interface PaymentResult {
  success: boolean;
  payment_intent_id?: string;
  subscription_id?: string;
  error?: string;
}

interface PaymentWizardProps {
  planTier?: SubscriptionTier; // Made optional - can come from URL params
  planName: string;
  amount: number;
  billingPeriod?: BillingCycle; // Made optional - can come from URL params
  pricingMode?: PricingMode; // NEW: Made optional - can come from URL params
  onSuccess: (result: PaymentResult) => void;
  onCancel: () => void;
  className?: string;
}

/**
 * Payment Wizard Component - Refactored
 * Orchestrates subscription payment flow:
 * 1. Read URL params (tier, cycle, mode) from pricing page
 * 2. Auto-select recommended payment method (Fapshi)
 * 3. Compose PaymentMethodSelector + PaymentForm for input
 * 4. Call subscription service with complete payload
 * 5. Switch to PaymentProcessor for polling
 * 6. Handle redirecting on success/failure
 */
export function PaymentWizard({
  planTier: propPlanTier,
  planName,
  amount,
  billingPeriod: propBillingPeriod,
  pricingMode: propPricingMode,
  onSuccess,
  onCancel,
  className
}: PaymentWizardProps) {
  // Read URL params (from pricing page navigation)
  const searchParams = useSearchParams();

  // Extract URL params with fallbacks to props
  const urlPlanTier = searchParams?.get('tier') as SubscriptionTier;
  const urlBillingCycle = searchParams?.get('cycle') as BillingCycle;
  const urlPricingMode = searchParams?.get('mode') as PricingMode;

  const planTier = urlPlanTier || propPlanTier || 'pro'; // Default to pro
  const billingCycle = urlBillingCycle || propBillingPeriod || 'monthly';
  const pricingMode = urlPricingMode || propPricingMode || 'regular'; // Default to regular

  // Check for renewal/reactivate action from URL
  const action = searchParams?.get('action'); // 'renew' | 'reactivate' | null
  const isRenewal = action === 'renew' || action === 'reactivate';

  // Component state
  const [stage, setStage] = useState<'input' | 'processing'>('input');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null);
  const [currentIdempotencyKey, setCurrentIdempotencyKey] = useState<string | null>(null);

  // Platform payment methods hook (auto-fetches and auto-selects recommended)
  const {
    selectedPaymentMethod,
    selectPaymentMethod,
    hasPaymentMethods
  } = usePlatformPaymentMethods(true, 'subscription');

  const { isAuthenticated, user } = useAuth();
  const { currentWorkspaceId } = useCurrentWorkspace();

  // SessionStorage keys for persistence
  const IDEMPOTENCY_KEY_STORAGE = `payment-idempotency-${planTier}`;
  const PAYMENT_INTENT_STORAGE = `payment-intent-${planTier}`;

  // Generate idempotency key (prevents double-click submissions)
  const generateIdempotencyKey = () => {
    return `${user?.id || 'anon'}-${planTier}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
  };

  // Get or create idempotency key with sessionStorage persistence
  const getOrCreateIdempotencyKey = () => {
    // Check if we have a stored key (for retry scenario)
    const storedKey = sessionStorage.getItem(IDEMPOTENCY_KEY_STORAGE);
    if (storedKey) {
      return storedKey;
    }

    // Generate new key and persist
    const newKey = generateIdempotencyKey();
    sessionStorage.setItem(IDEMPOTENCY_KEY_STORAGE, newKey);
    return newKey;
  };

  // Clear idempotency key (on success or cancel)
  const clearIdempotencyKey = () => {
    sessionStorage.removeItem(IDEMPOTENCY_KEY_STORAGE);
    sessionStorage.removeItem(PAYMENT_INTENT_STORAGE);
    setCurrentIdempotencyKey(null);
  };

  // Get client context (browser info for fraud detection)
  const getClientContext = () => {
    return {
      user_agent: navigator.userAgent,
      language: navigator.language,
      screen_resolution: `${window.screen.width}x${window.screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
  };

  const validatePhone = (phone: string): boolean => {
    const cleaned = phone.replace(/\s+/g, '');
    const regex = /^6[0-9]{8}$/;
    return regex.test(cleaned);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validatePhone(phoneNumber)) {
      setError('Invalid phone number format. Use Cameroonian number (e.g., 670123456)');
      return;
    }

    if (!isAuthenticated) {
      setError('You must be logged in to subscribe');
      onCancel();
      return;
    }

    // NOTE: Workspace is optional for subscriptions - they are user-level, not workspace-scoped

    if (!selectedPaymentMethod) {
      setError('Please select a payment method');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // Get or reuse idempotency key (critical for retry logic)
      const idempotencyKey = getOrCreateIdempotencyKey();
      setCurrentIdempotencyKey(idempotencyKey);

      let response;

      if (isRenewal) {
        // RENEWAL FLOW: Call renewal endpoint (user already has active subscription)
        // Renewal only needs phone_number and provider - backend uses current plan
        const renewPayload = {
          phone_number: phoneNumber.replace(/\s+/g, ''),
          provider: selectedPaymentMethod.provider,
          idempotency_key: idempotencyKey,
        };

        console.log('[PaymentWizard] Renewing subscription with payload:', renewPayload);
        response = await subscriptionService.renewSubscription(renewPayload);
      } else {
        // CREATE FLOW: Standard subscription creation
        // NOTE: workspace_id is optional - subscriptions are user-level, not workspace-level
        const createPayload = {
          plan_tier: planTier,
          phone_number: phoneNumber.replace(/\s+/g, ''),
          provider: selectedPaymentMethod.provider,
          billing_cycle: billingCycle,
          pricing_mode: pricingMode,
          idempotency_key: idempotencyKey,
          client_context: getClientContext(),
          ...(currentWorkspaceId && { workspace_id: currentWorkspaceId }),
        };

        console.log('[PaymentWizard] Creating subscription with payload:', {
          ...createPayload,
          client_context: '...'
        });
        response = await subscriptionService.createSubscription(createPayload);
      }

      if (!response.success) {
        throw new Error(response.error || 'Subscription creation failed');
      }

      // Check if already processed (idempotent response)
      if (response.already_processed) {
        console.log('[PaymentWizard] Payment already processed (idempotent response)');
      }

      // Store payment intent ID for polling
      if (response.payment_intent_id) {
        setPaymentIntentId(response.payment_intent_id);
        // Persist to sessionStorage for page refresh recovery
        sessionStorage.setItem(PAYMENT_INTENT_STORAGE, response.payment_intent_id);
        setStage('processing');
      } else {
        throw new Error('No payment intent ID returned');
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.error || err.message || 'Subscription failed';
      setError(errorMessage);
      console.error('[PaymentWizard] Subscription error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePaymentComplete = useCallback((result: PaymentResult) => {
    if (result.success) {
      // Payment succeeded - clear idempotency key and navigate to workspace
      clearIdempotencyKey();
      onSuccess({
        ...result,
        payment_intent_id: paymentIntentId || result.payment_intent_id
      });
    } else {
      // Payment failed - keep idempotency key for potential retry
      // But clear payment intent to allow fresh retry
      setError(result.error || 'Payment failed');
      setStage('input');
      setPaymentIntentId(null);
      sessionStorage.removeItem(PAYMENT_INTENT_STORAGE);
      // Note: We keep the idempotency key so retry can check if payment actually succeeded
    }
  }, [paymentIntentId, onSuccess]);

  // Handle retry - reuse idempotency key to check backend for existing payment
  const handleRetry = useCallback(() => {
    setStage('input');
    setPaymentIntentId(null);
    setError(null);
    sessionStorage.removeItem(PAYMENT_INTENT_STORAGE);
    // Keep idempotency key - backend will return existing result if already processed
  }, []);

  // Handle cancel - clear everything
  const handleCancel = useCallback(() => {
    clearIdempotencyKey();
    onCancel();
  }, [onCancel]);

  // Stage 2: Processing - Poll payment status and redirect
  if (stage === 'processing' && paymentIntentId) {
    return (
      <div className={className}>
        <PaymentProcessor
          paymentId={paymentIntentId}
          amount={amount}
          phoneNumber={phoneNumber}
          operator={selectedPaymentMethod?.displayName || 'Mobile Money'}
          onComplete={handlePaymentComplete}
          onRetry={handleRetry}
        />
      </div>
    );
  }

  // Stage 1: Input - Compose PaymentMethodSelector + PaymentForm
  return (
    <PaymentForm
      planName={planName}
      amount={amount}
      phoneNumber={phoneNumber}
      onPhoneNumberChange={setPhoneNumber}
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isSubmitting={isSubmitting || !hasPaymentMethods}
      error={error}
      className={className}
    >
      <PaymentMethodSelector
        value={selectedPaymentMethod?.provider || ''}
        onChange={(provider) => {
          const method = {
            provider,
            displayName: provider,
            mode: 'ussd' as const
          };
          selectPaymentMethod(method);
        }}
        disabled={isSubmitting}
      />
    </PaymentForm>
  );
}
