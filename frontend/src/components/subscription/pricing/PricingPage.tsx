'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client/react';
import { useRouter } from 'next/navigation';
import { useAuthWithRedirect } from '@/hooks/authentication/useAuthWithRedirect';
import { buildPathWithParams } from '@/utils/redirect-with-intent';
import { GetPlansDocument } from '@/services/graphql/subscription/queries/pricing/__generated__/get-plans.generated';
import { GetCurrentPlanDocument } from '@/services/graphql/subscription/queries/plan/__generated__/get-current-plan.generated';
import { PrepareIntentDocument } from '@/services/graphql/subscription/mutations/pricing/__generated__/prepare-intent.generated';
import { Tabs, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Badge } from '@/components/shadcn-ui/badge';
import { AlertCircle, Smartphone, Check, Calendar } from 'lucide-react';
import { PricingCard } from './PricingCard';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/shadcn-ui/dialog';
import { Button } from '@/components/shadcn-ui/button';
import { toast } from 'sonner';

interface PricingPageProps {
  className?: string;
}

export function PricingPage({ className }: PricingPageProps) {
  const router = useRouter();
  const { requireAuth, isAuthenticated } = useAuthWithRedirect();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [selectedTier, setSelectedTier] = useState<string | null>(null);
  const [downgradeDialog, setDowngradeDialog] = useState<{
    open: boolean;
    planName: string;
    currentPlan: string;
    scheduleDate: string;
  }>({ open: false, planName: '', currentPlan: '', scheduleDate: '' });

  // Query all plans
  const { data: plansData, loading: plansLoading, error: plansError } = useQuery(GetPlansDocument);

  // Query current plan (for highlighting current plan)
  const { data: currentPlanData, loading: currentPlanLoading } = useQuery(GetCurrentPlanDocument);

  // PrepareIntent mutation - determines action type from backend
  const [prepareIntent, { loading: intentLoading }] = useMutation(PrepareIntentDocument);

  const plans = plansData?.plans || [];
  const currentTier = currentPlanData?.currentPlan?.plan?.name?.toLowerCase();

  /**
   * Intro Pricing Eligibility Logic 
   *
   * isIntroPricingEligible from backend:
   * - true  = User authenticated AND eligible (never used intro)
   * - false = User authenticated AND already used intro
   * - null  = User NOT authenticated (public visitor)
   *
   * Frontend display logic:
   * - null or true  → Show intro pricing (unauth or eligible)
   * - false         → Show regular pricing (already used)
   */
  const isIntroPricingEligible = plansData?.isIntroPricingEligible;
  const shouldShowIntroPrice = isIntroPricingEligible === null || isIntroPricingEligible === true;

  /**
   * Handle plan selection with PrepareIntent (backend source of truth)
   *
   * Flow:
   * 1. If unauthenticated → old flow (redirect to checkout, auth gate handles)
   * 2. If authenticated → call prepareIntent to determine action type
   * 3. Based on action: subscribe/renew/upgrade → checkout, downgrade → confirmation modal
   */
  const handlePlanSelect = async (tier: string) => {
    setSelectedTier(tier);

    // Map frontend tier names to backend (beginner -> beginning)
    const backendTier = tier.toLowerCase() === 'beginner' ? 'beginning' : tier.toLowerCase();

    // For unauthenticated users, use old flow (auth gate will redirect)
    if (!isAuthenticated) {
      const selectedPlan = plans.find(p => p?.tier?.toLowerCase() === tier.toLowerCase());
      const hasIntroDiscount = selectedPlan?.showcase?.pricingDisplay?.hasIntroDiscount;
      const requestedMode = (shouldShowIntroPrice && hasIntroDiscount) ? 'intro' : 'regular';

      const checkoutPath = buildPathWithParams('/checkout', {
        tier: backendTier,
        cycle: billingCycle,
        mode: requestedMode
      });

      requireAuth(checkoutPath, () => {
        router.push(checkoutPath);
      });
      return;
    }

    // For authenticated users, call prepareIntent to get action type
    try {
      const result = await prepareIntent({
        variables: {
          intentData: {
            tier: backendTier,
            cycle: billingCycle
          }
        }
      });

      const intent = result.data?.prepareIntent;

      if (!intent?.success) {
        toast.error(intent?.error || 'Failed to determine action');
        setSelectedTier(null);
        return;
      }

      const action = intent.action;

      // Route based on action type
      switch (action) {
        case 'subscribe':
          // New subscription - go to checkout
          router.push(buildPathWithParams('/checkout', {
            tier: backendTier,
            cycle: billingCycle,
            mode: intent.pricingMode || 'regular',
            action: 'subscribe'
          }));
          break;

        case 'renew':
          // Renewal - go to checkout with renew action
          router.push(buildPathWithParams('/checkout', {
            tier: backendTier,
            cycle: billingCycle,
            mode: 'regular',
            action: 'renew'
          }));
          break;

        case 'upgrade':
          // Upgrade - go to checkout with upgrade action
          router.push(buildPathWithParams('/checkout', {
            tier: backendTier,
            cycle: billingCycle,
            mode: 'regular',
            action: 'upgrade'
          }));
          break;

        case 'downgrade':
          // Downgrade - show confirmation modal (no checkout)
          setDowngradeDialog({
            open: true,
            planName: intent.planName || tier,
            currentPlan: intent.currentPlanName || 'Current Plan',
            scheduleDate: intent.scheduleDate?.split('T')[0] || 'end of billing cycle'
          });
          break;

        case 'already_on_plan':
          // User is on this plan, not in renewal window
          toast.info(intent.message || `You're already on ${intent.planName}`);
          break;

        default:
          toast.error('Unknown action type');
      }
    } catch (error) {
      console.error('PrepareIntent failed:', error);
      toast.error('Failed to process plan selection');
    } finally {
      setSelectedTier(null);
    }
  };

  // Handle downgrade confirmation
  const handleConfirmDowngrade = async () => {
    try {
      // Call schedule-downgrade REST endpoint
      const response = await fetch('/api/subscriptions/schedule-downgrade/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_plan_tier: selectedTier?.toLowerCase() === 'beginner' ? 'beginning' : selectedTier?.toLowerCase()
        }),
        credentials: 'include'
      });

      if (response.ok) {
        toast.success(`Downgrade scheduled for ${downgradeDialog.scheduleDate}`);
        setDowngradeDialog({ open: false, planName: '', currentPlan: '', scheduleDate: '' });
        // Refresh the page to update UI
        router.refresh();
      } else {
        const error = await response.json();
        toast.error(error.error || 'Failed to schedule downgrade');
      }
    } catch (error) {
      console.error('Downgrade failed:', error);
      toast.error('Failed to schedule downgrade');
    }
  };

  // Calculate yearly savings for badge
  const calculateYearlySavings = () => {
    const proMonthly = plans.find(p => p?.tier === 'PRO')?.regularPriceMonthly ?? 0;
    const proYearly = plans.find(p => p?.tier === 'PRO')?.regularPriceYearly ?? 0;
    if (proMonthly > 0 && proYearly > 0) {
      const monthlyCost = proMonthly * 12;
      const savings = monthlyCost - proYearly;
      return savings > 0 ? Math.round((savings / monthlyCost) * 100) : 0;
    }
    return 0;
  };

  const savingsPercent = calculateYearlySavings();

  // Loading state
  if (plansLoading || currentPlanLoading) {
    return (
      <div className={cn('space-y-8', className)}>
        <div className="text-center space-y-4">
          <Skeleton className="h-12 w-96 mx-auto" />
          <Skeleton className="h-6 w-[500px] mx-auto" />
        </div>
        <Skeleton className="h-12 w-[400px] mx-auto" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[400px] w-full" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (plansError) {
    return (
      <div className={cn('space-y-4', className)}>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load pricing plans. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Sort plans by showcase order
  const sortedPlans = [...plans].sort((a, b) => {
    const orderA = a?.showcase?.order ?? 999;
    const orderB = b?.showcase?.order ?? 999;
    return orderA - orderB;
  });

  return (
    <div className={cn('space-y-8', className)}>
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Choose Your Perfect Plan
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Flexible pricing with Mobile Money payment to grow your business
        </p>
      </div>

      {/* Billing Cycle Toggle */}
      <div className="flex justify-center">
        <Tabs value={billingCycle} onValueChange={(v) => setBillingCycle(v as 'monthly' | 'yearly')}>
          <TabsList className="grid w-[350px] grid-cols-2 bg-muted">
            <TabsTrigger value="monthly" className="data-[state=active]:bg-background">
              Monthly
            </TabsTrigger>
            <TabsTrigger value="yearly" className="data-[state=active]:bg-background">
              Yearly
              {savingsPercent > 0 && (
                <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800">
                  Save {savingsPercent}%
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
        {sortedPlans.map((plan) => {
          if (!plan) return null;

          const isCurrentPlan = plan.tier === currentTier?.toUpperCase();
          const isLoading = intentLoading && selectedTier?.toLowerCase() === plan.tier?.toLowerCase();

          return (
            <PricingCard
              key={plan.id}
              plan={plan}
              billingCycle={billingCycle}
              isCurrentPlan={isCurrentPlan}
              onSelect={handlePlanSelect}
              loading={isLoading}
              showIntroPrice={shouldShowIntroPrice}
            />
          );
        })}
      </div>

      {/* Mobile Money Footer */}
      <div className="text-center space-y-4 mt-12">
        <div className="flex items-center justify-center gap-2 text-muted-foreground">
          <Smartphone className="w-4 h-4" />
          <span className="text-sm">
            Secure payment via MTN Mobile Money, Orange Money, and Fapshi
          </span>
        </div>

        <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground flex-wrap">
          <div className="flex items-center gap-1">
            <Check className="w-3 h-3 text-green-600" />
            <span>Cancel anytime</span>
          </div>
          <div className="flex items-center gap-1">
            <Check className="w-3 h-3 text-green-600" />
            <span>24/7 Support</span>
          </div>
          <div className="flex items-center gap-1">
            <Check className="w-3 h-3 text-green-600" />
            <span>No hidden fees</span>
          </div>
        </div>
      </div>

      {/* Downgrade Confirmation Dialog */}
      <Dialog open={downgradeDialog.open} onOpenChange={(open) => !open && setDowngradeDialog({ ...downgradeDialog, open: false })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Schedule Downgrade
            </DialogTitle>
            <DialogDescription>
              You are about to schedule a downgrade from <strong>{downgradeDialog.currentPlan}</strong> to <strong>{downgradeDialog.planName}</strong>.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Your current plan features will remain active until <strong>{downgradeDialog.scheduleDate}</strong>.
                After this date, your plan will automatically switch to {downgradeDialog.planName}.
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setDowngradeDialog({ ...downgradeDialog, open: false })}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDowngrade}
            >
              Confirm Downgrade
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
