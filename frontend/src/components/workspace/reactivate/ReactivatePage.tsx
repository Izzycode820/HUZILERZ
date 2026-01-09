'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSubscription } from '@/hooks/subscription/useSubscription';
import { useQuery } from '@apollo/client/react';
import { GetBillingProfileDocument } from '@/services/graphql/subscription/queries/billing/__generated__/get-billing-profile.generated';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { AlertCircle, RefreshCw, ShoppingCart } from 'lucide-react';

export function ReactivatePage() {
  const router = useRouter();
  const [isReactivating, setIsReactivating] = useState(false);

  const { tier, renewSubscription } = useSubscription();
  const { data: profileData } = useQuery(GetBillingProfileDocument);

  // Redirect to checkout for reactivation
  // User completes full checkout flow - backend is source of truth
  const handleReactivate = () => {
    router.push('/checkout?action=reactivate');
  };

  const handleChooseDifferentPlan = () => {
    router.push('/billing');
  };

  const tierName = tier ? tier.charAt(0).toUpperCase() + tier.slice(1) : 'Unknown';

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-2xl mx-4">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-100 rounded-full">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-2xl">Subscription Suspended</CardTitle>
              <p className="text-muted-foreground mt-1">
                Your {tierName} plan is currently suspended
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Info Message */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Your subscription has been suspended due to non-payment.
              Reactivate your {tierName} plan to restore access to all features,
              or choose a different plan that better suits your needs.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            {/* Reactivate Same Tier */}
            <Button
              onClick={handleReactivate}
              disabled={isReactivating}
              className="w-full h-12 text-base gap-2"
              size="lg"
            >
              <RefreshCw className={`h-5 w-5 ${isReactivating ? 'animate-spin' : ''}`} />
              {isReactivating ? 'Processing...' : `Reactivate ${tierName} Plan`}
            </Button>

            {/* Choose Different Plan */}
            <Button
              onClick={handleChooseDifferentPlan}
              variant="outline"
              className="w-full h-12 text-base gap-2"
              size="lg"
            >
              <ShoppingCart className="h-5 w-5" />
              Choose Different Plan
            </Button>
          </div>

          {/* Footer Note */}
          <div className="text-center pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              All your data and workspace content has been preserved.
              Reactivating will restore immediate access.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
