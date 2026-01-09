'use client';

import React from 'react';
import NumberFlow from '@number-flow/react';
import { Check, Star } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/shadcn-ui/card';
import { cn } from '@/lib/utils';
import type { GetPlansQuery } from '@/services/graphql/subscription/queries/pricing/__generated__/get-plans.generated';

type PlanData = NonNullable<NonNullable<GetPlansQuery['plans']>[number]>;

interface PricingCardProps {
  plan: PlanData;
  billingCycle: 'monthly' | 'yearly';
  isCurrentPlan: boolean;
  onSelect: (tier: string) => void;
  loading?: boolean;
  showIntroPrice?: boolean; // User hasn't used intro yet
}

export function PricingCard({
  plan,
  billingCycle,
  isCurrentPlan,
  onSelect,
  loading = false,
  showIntroPrice = false,
}: PricingCardProps) {
  const showcase = plan.showcase;

  // Determine price to show
  const getCurrentPrice = () => {
    // Show intro price if user is eligible and plan has intro discount
    if (showIntroPrice && showcase?.pricingDisplay?.hasIntroDiscount && plan.introPrice) {
      return plan.introPrice;
    }

    // Otherwise show regular price based on billing cycle
    if (billingCycle === 'yearly') {
      return plan.regularPriceYearly ?? 0;
    }
    return plan.regularPriceMonthly ?? 0;
  };

  const currentPrice = getCurrentPrice();
  const isOnIntro = showIntroPrice && showcase?.pricingDisplay?.hasIntroDiscount;


  // Get badge configuration
  const badgeConfig = showcase?.badge;
  const isPopular = badgeConfig?.tone === 'highlight';

  // Get CTA text based on intro eligibility
  const ctaText = isCurrentPlan
    ? (showcase?.cta?.currentPlan || 'Current Plan')
    : showIntroPrice
    ? 'Start promo'
    : (showcase?.cta?.default || 'Choose plan');

  // Format price
  const formatPrice = (amount: number): string => {
    if (amount === 0) return 'Free';
    return new Intl.NumberFormat('en-US', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Card
      className={cn(
        'relative transition-all duration-300',
        {
          'animate-background-shine bg-white dark:bg-[linear-gradient(110deg,#0c0a09,45%,#1c1917,55%,#0c0a09)] bg-[length:200%_100%]': isPopular,
          'hover:scale-105 hover:shadow-lg': !isCurrentPlan,
          'border-foreground shadow-lg': isPopular,
          'border-foreground/30 bg-muted/20': isCurrentPlan,
        }
      )}
    >
      {/* Floating Badge */}
      {badgeConfig?.text && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 z-10">
          <Badge
            className={cn(
              'px-3 py-1 flex items-center gap-1',
              {
                'bg-foreground text-background': badgeConfig.tone === 'highlight',
                'bg-green-600 text-white': badgeConfig.tone === 'neutral',
                'bg-yellow-600 text-white': badgeConfig.tone === 'warning',
              }
            )}
          >
            {badgeConfig.tone === 'highlight' && <Star className="w-3 h-3" />}
            {badgeConfig.text}
          </Badge>
        </div>
      )}

      <CardHeader className="text-center pb-4 pt-6">
        {/* Plan Name */}
        <h3 className="text-2xl font-bold text-foreground mb-2">
          {showcase?.nameOverride || plan.name}
        </h3>

        {/* Tagline */}
        {showcase?.tagline && (
          <p className="text-sm text-muted-foreground mb-4">
            {showcase.tagline}
          </p>
        )}

        {/* Pricing with NumberFlow */}
        <div className="space-y-2 mt-4">
          <div className="flex items-baseline justify-center gap-2">
            {currentPrice === 0 ? (
              <span className="text-4xl font-bold text-foreground">Free</span>
            ) : (
              <>
                {/* Show strikethrough regular price if on intro */}
                {isOnIntro && (
                  <div className="flex items-baseline gap-1">
                    <span className="line-through text-lg text-muted-foreground">
                      {formatPrice(billingCycle === 'yearly' ? (plan.regularPriceYearly ?? 0) : (plan.regularPriceMonthly ?? 0))}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      /{billingCycle === 'yearly' ? 'year' : 'month'}
                    </span>
                  </div>
                )}

                <NumberFlow
                  value={currentPrice}
                  format={{
                    style: 'decimal',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                  }}
                  transformTiming={{
                    duration: 400,
                    easing: 'ease-out'
                  }}
                  className="text-4xl font-bold text-foreground"
                />
                <span className="text-sm text-muted-foreground">XAF</span>
              </>
            )}
          </div>

          {/* Intro price label */}
          {isOnIntro && showcase?.pricingDisplay?.introLabel && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {showcase.pricingDisplay.introLabel}
              {showcase.pricingDisplay.introSuffix && ` ${showcase.pricingDisplay.introSuffix}`}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pb-6">
        {/* Highlighted Features */}
        {showcase?.highlightedFeatures && showcase.highlightedFeatures.length > 0 && (
          <div className="space-y-3">
            {showcase.highlightedFeatures.map((feature, index) => (
              <div key={index} className="flex items-start gap-3">
                <Check className="w-4 h-4 text-foreground mt-0.5 flex-shrink-0" />
                <span className="text-sm text-muted-foreground leading-relaxed">
                  {feature}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex flex-col gap-3">
        {/* CTA Button */}
        <Button
          onClick={() => onSelect(plan.tier)}
          disabled={isCurrentPlan || loading}
          size="lg"
          className={cn(
            'relative inline-flex w-full items-center justify-center rounded-md px-6 font-medium transition-all duration-200',
            {
              'bg-muted text-muted-foreground cursor-not-allowed': isCurrentPlan,
              'bg-foreground text-background hover:bg-foreground/90': !isCurrentPlan,
            }
          )}
        >
          {!isCurrentPlan && (
            <div className="absolute -inset-0.5 -z-10 rounded-lg bg-foreground/10 opacity-0 hover:opacity-100 transition-opacity duration-200 blur" />
          )}

          {loading ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              Processing...
            </div>
          ) : (
            ctaText
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
