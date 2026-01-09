'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMutation } from '@apollo/client/react';
import { PaymentWizard } from '@/components/subscription/payment/PaymentWizard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/shadcn-ui/card';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { CheckCircle, AlertCircle, Loader2, Info } from 'lucide-react';
import { PrepareSubscriptionCheckoutDocument } from '@/services/graphql/subscription/mutations/pricing/__generated__/prepare-checkout.generated';
import { PrepareRenewalCheckoutDocument } from '@/services/graphql/subscription/mutations/pricing/__generated__/prepare-renewal.generated';
import { PrepareUpgradeCheckoutDocument } from '@/services/graphql/subscription/mutations/pricing/__generated__/prepare-upgrade.generated';
import type { SubscriptionTier, BillingCycle, PricingMode } from '@/types/subscription/subscription';

/**
 * Checkout Flow Component - Handles subscription checkout with authoritative pricing
 *
 * Flow (SECURITY BOUNDARY):
 * 1. Reads URL params (?tier=pro&cycle=monthly&mode=intro&action=subscribe|renew|upgrade)
 * 2. Calls backend mutation based on action to get AUTHORITATIVE PRICING
 * 3. Displays backend-computed price
 * 4. PaymentWizard processes payment with authoritative amount
 * 5. Success → Redirect to workspace
 *
 * Actions:
 * - subscribe: New subscription (PrepareSubscriptionCheckout)
 * - renew: Renewal of current plan (PrepareRenewalCheckout)
 * - upgrade: Upgrade to higher tier (PrepareUpgradeCheckout)
 */
export function CheckoutFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showSuccess, setShowSuccess] = useState(false);

  // Extract URL params (USER INTENT - not authoritative)
  const tier = (searchParams?.get('tier') || 'pro') as SubscriptionTier;
  const cycle = (searchParams?.get('cycle') || 'monthly') as BillingCycle;
  const requestedMode = (searchParams?.get('mode') || 'regular') as PricingMode;
  const action = searchParams?.get('action') || 'subscribe'; // subscribe | renew | upgrade

  // Map frontend tier to backend tier (frontend: 'beginner', backend: 'beginning')
  const backendTier = tier === 'beginner' ? 'beginning' : tier;

  // Determine flow type
  const isRenewal = action === 'renew' || action === 'reactivate';
  const isUpgrade = action === 'upgrade';

  // MUTATION 1: Standard Checkout (New Subscriptions)
  const [prepareCheckout, { data: standardData, loading: standardLoading, error: standardError }] = useMutation(PrepareSubscriptionCheckoutDocument);

  // MUTATION 2: Renewal Checkout (Existing Subscriptions)
  const [prepareRenewal, { data: renewalData, loading: renewalLoading, error: renewalError }] = useMutation(PrepareRenewalCheckoutDocument);

  // MUTATION 3: Upgrade Checkout (Plan Upgrades)
  const [prepareUpgrade, { data: upgradeData, loading: upgradeLoading, error: upgradeError }] = useMutation(PrepareUpgradeCheckoutDocument);

  // Call appropriate mutation on mount (SECURITY BOUNDARY)
  useEffect(() => {
    if (isUpgrade) {
      // For upgrades, get authoritative upgrade pricing
      prepareUpgrade({
        variables: {
          upgradeData: {
            tier: backendTier,
            cycle
          }
        }
      }).catch((err) => {
        console.error('Upgrade preparation failed:', err);
      });
    } else if (isRenewal) {
      // For renewals, get authoritative price for CURRENT plan
      prepareRenewal().catch((err) => {
        console.error('Renewal preparation failed:', err);
      });
    } else {
      // For new subscriptions, validate requested plan/tier
      prepareCheckout({
        variables: {
          checkoutData: {
            tier: backendTier,
            cycle,
            requestedMode
          }
        }
      }).catch((err) => {
        console.error('Checkout preparation failed:', err);
      });
    }
  }, [backendTier, cycle, requestedMode, prepareCheckout, prepareRenewal, prepareUpgrade, isRenewal, isUpgrade]);

  // Extract authoritative data (Unified)
  const standardResult = standardData?.prepareSubscriptionCheckout;
  const renewalResult = renewalData?.prepareRenewalCheckout;
  const upgradeResult = upgradeData?.prepareUpgradeCheckout;

  // Active result based on flow type
  const activeResult = isUpgrade ? upgradeResult : isRenewal ? renewalResult : standardResult;

  const loading = isUpgrade ? upgradeLoading : isRenewal ? renewalLoading : standardLoading;
  const error = isUpgrade ? upgradeError : isRenewal ? renewalError : standardError;

  const effectiveMode = (activeResult as any)?.effectiveMode || 'regular';
  const authoritativeAmount = activeResult?.amount || 0;
  const planName = activeResult?.planName || (isUpgrade ? 'Upgrade' : isRenewal ? 'Current Plan' : 'Pro');
  const breakdown = activeResult?.breakdown;
  const message = activeResult?.message;

  const handlePaymentSuccess = (result: { success: boolean; payment_intent_id?: string; subscription_id?: string; error?: string }) => {
    if (result.success) {
      setShowSuccess(true);

      // Redirect to workspace after 2 seconds
      setTimeout(() => {
        router.push('/workspace');
      }, 2000);
    }
  };

  const handleCancel = () => {
    // Go back to billing/pricing page
    router.push('/billing');
  };

  // Loading state - Fetching authoritative price from backend
  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto py-16 px-6">
          <div className="max-w-2xl mx-auto mb-8 text-center">
            <h1 className="text-3xl font-bold mb-2">Preparing Checkout</h1>
            <p className="text-muted-foreground">
              Validating pricing and eligibility...
            </p>
          </div>

          <Card className="max-w-md mx-auto">
            <CardContent className="py-8">
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <div className="space-y-2 w-full">
                  <Skeleton className="h-4 w-3/4 mx-auto" />
                  <Skeleton className="h-4 w-1/2 mx-auto" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Error state - Backend validation failed
  if (error || (activeResult && !activeResult.success)) {
    const errorMessage = activeResult?.error || error?.message || 'Failed to prepare checkout';
    const errorCode = activeResult?.errorCode;

    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-10 h-10 text-red-600" />
            </div>
            <CardTitle className="text-2xl">Checkout Error</CardTitle>
            <CardDescription>{errorMessage}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {errorCode === 'INTRO_ALREADY_USED' && (
              <Alert>
                <AlertDescription>
                  You've already used the introductory pricing offer. You can still subscribe at the regular price.
                </AlertDescription>
              </Alert>
            )}
            <button
              onClick={() => router.push('/billing')}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Back to Pricing
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Success state (payment completed)
  if (showSuccess) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <CardTitle className="text-2xl">Payment Successful!</CardTitle>
            <CardDescription>
              Your {planName} subscription has been activated
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-muted-foreground">
              Redirecting to your workspace...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Checkout state - Display with AUTHORITATIVE PRICING from backend
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-16 px-6">
        {/* Header */}
        <div className="max-w-2xl mx-auto mb-8 text-center">
          <h1 className="text-3xl font-bold mb-2">Complete Your Subscription</h1>
          <p className="text-muted-foreground">
            {planName} - {cycle === 'monthly' ? 'Monthly' : 'Yearly'} billing
            {effectiveMode === 'intro' && ' (Introductory pricing)'}
          </p>
          {message && (
            <p className="text-sm text-muted-foreground mt-2">
              {message}
            </p>
          )}
        </div>

        {/* Price Breakdown (if intro discount applied) */}
        {breakdown && breakdown.discount && breakdown.discount > 0 && (
          <div className="max-w-md mx-auto mb-6">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Regular Price:</span>
                    <span className="line-through">{breakdown.basePrice?.toLocaleString()} XAF</span>
                  </div>
                  <div className="flex justify-between text-green-600 font-medium">
                    <span>Intro Discount:</span>
                    <span>-{breakdown.discount?.toLocaleString()} XAF</span>
                  </div>
                  <div className="flex justify-between font-bold border-t pt-1">
                    <span>You Pay:</span>
                    <span>{breakdown.finalAmount?.toLocaleString()} XAF</span>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Payment Wizard with AUTHORITATIVE AMOUNT */}
        <PaymentWizard
          planTier={tier}
          planName={planName}
          amount={authoritativeAmount}
          billingPeriod={cycle}
          pricingMode={effectiveMode as PricingMode}
          onSuccess={handlePaymentSuccess}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
}
