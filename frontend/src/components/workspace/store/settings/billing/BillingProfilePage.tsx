'use client';

import React from 'react';
import { useQuery } from '@apollo/client/react';
import { useRouter } from 'next/navigation';
import { GetBillingProfileDocument } from '@/services/graphql/subscription/queries/billing/__generated__/get-billing-profile.generated';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Separator } from '@/components/shadcn-ui/separator';
import {
  ArrowLeft,
  Plus,
  MapPin,
  DollarSign,
  Info,
  MoreHorizontal
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';

export function BillingProfilePage() {
  const router = useRouter();

  // Query for billing profile
  const { data, loading } = useQuery(GetBillingProfileDocument);

  const billingProfile = data?.billingProfile;

  const handleAddPaymentMethod = () => {
    // Coming soon placeholder
    alert('Coming soon! Payment method management will be available soon.');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Billing profile</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Your payment methods, billing currency and store address
          </p>
        </div>
      </div>

      {/* Payment Methods Section */}
      <Card>
        <CardHeader>
          <CardTitle>Payment methods</CardTitle>
          <p className="text-sm text-muted-foreground">
            For purchases and bills in Huzilerz
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <>
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-10 w-48" />
            </>
          ) : (
            <>
              {/* Primary Payment Method */}
              {billingProfile?.primaryPaymentMethod ? (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-12 h-8 bg-blue-600 rounded text-white font-bold text-sm">
                        {billingProfile.primaryPaymentMethod === 'MTN' ? 'MTN' :
                         billingProfile.primaryPaymentMethod === 'Orange' ? 'OM' :
                         billingProfile.primaryPaymentMethod}
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">
                          {billingProfile.primaryPaymentMethod}{' '}
                          {billingProfile.userPhone
                            ? `•••• ${billingProfile.userPhone.slice(-4)}`
                            : ''}
                        </p>
                        <Badge variant="secondary" className="bg-blue-50 text-blue-700 hover:bg-blue-50">
                          Primary
                        </Badge>
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={handleAddPaymentMethod}>
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={handleAddPaymentMethod}>
                          Remove
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No payment method added yet</p>
                </div>
              )}

              {/* Add Payment Method Button */}
              <Button
                variant="outline"
                className="gap-2"
                onClick={handleAddPaymentMethod}
              >
                <Plus className="h-4 w-4" />
                Add payment method
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Address and Currency Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CardTitle>Address and currency</CardTitle>
            <Info className="h-4 w-4 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground">
            The options for your billing currency are determined by your billing address
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Store Address */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="font-medium text-sm text-muted-foreground mb-1">
                  Store address
                </p>
                <p className="font-medium">Bonabéri, Cameroon</p>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Manage
            </Button>
          </div>

          <Separator />

          {/* Currency */}
          <div className="flex items-start gap-3">
            <DollarSign className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="font-medium text-sm text-muted-foreground mb-1">
                Currency
              </p>
              <p className="font-medium">XAF (Central African CFA franc)</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
