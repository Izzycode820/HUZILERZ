"use client";

import React, { useState, useEffect } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Button } from '@/components/shadcn-ui/button';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';
import { Badge } from '@/components/shadcn-ui/badge';
import { PricingCard } from './PricingCard';
import { usePricing } from '@/hooks/subscription';
import { useSubscription } from '@/hooks/subscription';
import { useAuth } from '@/hooks/authentication/useAuth';
import { cn } from '@/lib/utils';

interface PricingTableProps {
  onPlanSelect?: (planTier: string, subscriptionType: 'standard' | 'trial', billingPeriod?: 'monthly' | 'yearly') => void;
  showFeatureComparison?: boolean;
  maxPlans?: number;
  className?: string;
  initialSubscriptionType?: 'standard' | 'trial';
  initialBillingPeriod?: 'monthly' | 'yearly';
}

/**
 * Pricing Table Component - Modern Version
 * Complete pricing display with Standard/Trial toggle and Monthly/Yearly billing
 * Cameroon market optimized with Mobile Money payment
 */
export function PricingTable({
  onPlanSelect,
  showFeatureComparison = true,
  maxPlans = 4,
  className,
  initialSubscriptionType = 'standard',
  initialBillingPeriod = 'monthly'
}: PricingTableProps) {
  // Hooks
  const router = useRouter();
  const { subscription, isLoading: subscriptionLoading } = useSubscription();
  const {
    standardPricing,
    trialPricing,
    isLoading: pricingLoading,
    error: pricingError,
    getStandardPricing,
    getTrialPricing
  } = usePricing();
  const { isAuthenticated, isTrialEligible, hasUsedTrial } = useAuth();

  // State (initialized with URL params if provided)
  const [subscriptionType, setSubscriptionType] = useState<'standard' | 'trial'>(initialSubscriptionType);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>(initialBillingPeriod);
  const [processingPlan, setProcessingPlan] = useState<string | null>(null);

  // Current user's plan tier
  const currentTier = subscription?.plan?.tier || 'free';

  // Trial eligibility check (from JWT for performance)
  const canStartTrial = isAuthenticated && isTrialEligible && !hasUsedTrial;

  // Load pricing data on mount (empty deps - run once only)
  useEffect(() => {
    getStandardPricing();
    getTrialPricing();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Get price for a specific plan tier based on subscription type and billing period
   */
  const getPriceForPlan = (tier: string): number => {
    if (tier === 'free') return 0;

    if (subscriptionType === 'trial') {
      const trialTier = tier as 'beginning' | 'pro' | 'enterprise';
      return trialPricing?.[trialTier]?.amount || 0;
    }

    const standardTier = tier as 'beginning' | 'pro' | 'enterprise';
    const plan = standardPricing?.[standardTier];

    if (!plan) return 0;

    if (billingPeriod === 'monthly') {
      return plan.pricing.monthly.base_price;
    }

    return plan.pricing.yearly.discounted_price;
  };

  /**
   * Get period label based on subscription type and billing period
   */
  const getPeriodLabel = (): string => {
    if (subscriptionType === 'trial') return '30 days';
    if (billingPeriod === 'monthly') return '/month';
    return '/month (billed annually)';
  };

  /**
   * Get savings amount for yearly billing
   */
  const getSavings = (tier: string): number | null => {
    if (tier === 'free' || subscriptionType === 'trial') return null;
    if (billingPeriod !== 'yearly') return null;

    const standardTier = tier as 'beginning' | 'pro' | 'enterprise';
    return standardPricing?.[standardTier]?.pricing.yearly.savings || null;
  };

  /**
   * Get plan features
   */
  const getPlanFeatures = (tier: string): string[] => {
    const tierKey = tier as 'free' | 'beginning' | 'pro' | 'enterprise';
    const plan = standardPricing?.[tierKey];

    if (!plan) return [];

    const features: string[] = [];

    // Add capabilities
    if (plan.capabilities.deployment_allowed) features.push('Deployment allowed');
    if (plan.capabilities.custom_domains_allowed) features.push('Custom domains');
    if (plan.capabilities.analytics_enabled) features.push('Advanced analytics');
    if (plan.capabilities.white_label_enabled) features.push('White label');
    if (plan.capabilities.api_access) features.push('API access');
    if (plan.capabilities.dedicated_support) features.push('Dedicated support');

    // Add limits
    features.push(`${plan.limits.storage_gb} GB storage`);
    features.push(`${plan.limits.bandwidth_gb} GB bandwidth`);
    if (plan.limits.deployed_sites > 0) {
      features.push(`${plan.limits.deployed_sites} deployed site${plan.limits.deployed_sites > 1 ? 's' : ''}`);
    }

    return features;
  };

  /**
   * Get plan name
   */
  const getPlanName = (tier: string): string => {
    const tierKey = tier as 'free' | 'beginning' | 'pro' | 'enterprise';
    return standardPricing?.[tierKey]?.name || tier;
  };

  /**
   * Get plan description
   */
  const getPlanDescription = (tier: string): string => {
    const tierKey = tier as 'free' | 'beginning' | 'pro' | 'enterprise';
    return standardPricing?.[tierKey]?.tagline || '';
  };

  /**
   * Get tier ordering for comparison
   */
  const getTierOrder = (tier: string): number => {
    const order = { free: 0, beginning: 1, pro: 2, enterprise: 3 };
    return order[tier as keyof typeof order] || 0;
  };

  /**
   * Handle plan selection with authentication gate
   */
  const handlePlanSelect = async (planTier: string) => {
    if (planTier === currentTier || processingPlan) return;

    // Authentication gate - redirect to signup if not authenticated (industry standard)
    if (!isAuthenticated) {
      const redirectUrl = `/billing/plans?tier=${planTier}&type=${subscriptionType}&period=${billingPeriod}`;
      router.push(`/auth/signup?redirect=${encodeURIComponent(redirectUrl)}`);
      return;
    }

    // UX-only trial eligibility check (backend has real validation)
    if (subscriptionType === 'trial' && !canStartTrial) {
      // Don't proceed - button should be disabled anyway
      return;
    }

    try {
      setProcessingPlan(planTier);
      onPlanSelect?.(planTier, subscriptionType, billingPeriod);
    } catch (err) {
      console.error('Failed to handle plan selection:', err);
    } finally {
      setProcessingPlan(null);
    }
  };

  // Determine which tiers to show
  const tiers = subscriptionType === 'trial'
    ? ['beginning', 'pro', 'enterprise']
    : ['free', 'beginning', 'pro', 'enterprise'];

  // Loading state
  const isLoading = pricingLoading || subscriptionLoading;

  if (isLoading) {
    return (
      <div className={cn('space-y-8', className)}>
        <Skeleton className="h-20 w-full mx-auto max-w-md" />
        <Skeleton className="h-12 w-full mx-auto max-w-sm" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: maxPlans }).map((_, i) => (
            <Skeleton key={i} className="h-96 w-full" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (pricingError) {
    return (
      <div className={cn('space-y-4', className)}>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {pricingError}
          </AlertDescription>
        </Alert>
        <Button
          onClick={() => {
            getStandardPricing();
            getTrialPricing();
          }}
          variant="outline"
          className="w-full"
        >
          Retry
        </Button>
      </div>
    );
  }

  // No pricing data state
  if (!standardPricing && !trialPricing) {
    return (
      <div className={cn('text-center py-12', className)}>
        <p className="text-muted-foreground">No pricing plans available.</p>
        <Button
          onClick={() => {
            getStandardPricing();
            getTrialPricing();
          }}
          variant="outline"
          className="mt-4"
        >
          Refresh
        </Button>
      </div>
    );
  }

  return (
    <div className={cn('space-y-8', className)}>
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-foreground">
          Pricing for the Cameroonian Market
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Flexible plans with Mobile Money payment to grow your business
        </p>
      </div>

      {/* Switchers Container */}
      <div className="flex flex-col items-center gap-4">
        {/* Level 1: Standard/Trial Switcher */}
        <Tabs
          value={subscriptionType}
          onValueChange={(v) => setSubscriptionType(v as 'standard' | 'trial')}
        >
          <TabsList className="grid w-[400px] grid-cols-2 bg-muted">
            <TabsTrigger value="standard" className="data-[state=active]:bg-background">
              Standard Plans
            </TabsTrigger>
            <TabsTrigger value="trial" className="data-[state=active]:bg-background">
              Trial (30 days)
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Level 2: Monthly/Yearly Switcher (only for Standard) */}
        <div
          className={cn(
            "transition-all duration-300 ease-in-out",
            subscriptionType === 'standard'
              ? 'opacity-100 max-h-20'
              : 'opacity-0 max-h-0 overflow-hidden'
          )}
        >
          {subscriptionType === 'standard' && (
            <Tabs
              value={billingPeriod}
              onValueChange={(v) => setBillingPeriod(v as 'monthly' | 'yearly')}
            >
              <TabsList className="grid w-[350px] grid-cols-2 bg-muted">
                <TabsTrigger value="monthly" className="data-[state=active]:bg-background">
                  Monthly
                </TabsTrigger>
                <TabsTrigger value="yearly" className="data-[state=active]:bg-background">
                  Yearly
                  <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800">
                    Save 15%
                  </Badge>
                </TabsTrigger>
              </TabsList>
            </Tabs>
          )}
        </div>
      </div>

      {/* Pricing cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
        {tiers.slice(0, maxPlans).map((tier) => {
          const price = getPriceForPlan(tier);
          const savings = getSavings(tier);

          // UX-only eligibility check (backend validates for real)
          const isButtonDisabled = currentTier === tier ||
            (subscriptionType === 'trial' && isAuthenticated && !canStartTrial);

          return (
            <PricingCard
              key={tier}
              plan={{
                tier: tier,
                name: getPlanName(tier),
                price: price,
                originalPrice: savings ? price + savings : undefined,
                description: getPlanDescription(tier),
                pricing: {
                  monthly: price,
                  quarterly: price * 3,
                  annually: price * 12
                },
                features: getPlanFeatures(tier),
                card_features: getPlanFeatures(tier).slice(0, 5),
                resources: {
                  deployed_sites: standardPricing?.[tier as 'free' | 'beginning' | 'pro' | 'enterprise']?.limits.deployed_sites || 0,
                  storage_gb: standardPricing?.[tier as 'free' | 'beginning' | 'pro' | 'enterprise']?.limits.storage_gb || 0,
                  bandwidth_gb: standardPricing?.[tier as 'free' | 'beginning' | 'pro' | 'enterprise']?.limits.bandwidth_gb || 0,
                  workspaces: standardPricing?.[tier as 'free' | 'beginning' | 'pro' | 'enterprise']?.limits.workspaces || 1
                },
                is_current_plan: currentTier === tier,
                is_upgrade: getTierOrder(tier) > getTierOrder(currentTier),
                is_downgrade: getTierOrder(tier) < getTierOrder(currentTier),
                is_popular: tier === 'beginning',
                discount_available: savings !== null
              }}
              onSelect={handlePlanSelect}
              loading={processingPlan === tier}
              disabled={isButtonDisabled}
              periodLabel={getPeriodLabel()}
              savings={savings}
              subscriptionType={subscriptionType}
            />
          );
        })}
      </div>

      {/* Feature comparison table */}
      {showFeatureComparison && tiers.length > 1 && (
        <div className="mt-16 max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-foreground">Compare Plans</h3>
            <p className="text-muted-foreground mt-2">
              Choose the perfect plan for your needs
            </p>
          </div>

          <div className="overflow-x-auto">
            <div className="min-w-full bg-background rounded-lg border border-border">
              <div className="grid grid-cols-5 gap-4 p-6 border-b border-border">
                <div className="font-semibold text-foreground">Features</div>
                {tiers.slice(0, 4).map(tier => (
                  <div key={tier} className="text-center font-semibold text-foreground">
                    {getPlanName(tier)}
                    {tier === 'beginning' && (
                      <Badge className="ml-2 bg-foreground text-background">
                        Popular
                      </Badge>
                    )}
                  </div>
                ))}
              </div>

              {/* Feature rows */}
              <div className="p-6 text-center text-muted-foreground">
                <div className="space-y-4">
                  <p>Detailed feature comparison coming soon</p>
                  <div className="text-xs">
                    All plans include support and Mobile Money integration
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trust indicators */}
      <div className="text-center mt-16 space-y-4">
        <p className="text-sm text-muted-foreground">
          Secure payment via Mobile Money • Local support
        </p>
        <div className="flex justify-center gap-6 items-center opacity-60">
          <span className="text-xs text-muted-foreground">MTN Mobile Money</span>
          <span className="text-xs text-muted-foreground">Orange Money</span>
          <span className="text-xs text-muted-foreground">Fapshi Secured</span>
        </div>
      </div>

      {/* Loading overlay */}
      {processingPlan && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-background p-6 rounded-lg shadow-lg border border-border flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-foreground" />
            <span className="text-foreground">Processing your selection...</span>
          </div>
        </div>
      )}
    </div>
  );
}