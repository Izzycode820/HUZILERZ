"use client";

import React from 'react';
import { CreditCard, Calendar, Receipt, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Button } from '@/components/shadcn-ui/button';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { cn } from '@/lib/utils';
import { useSubscription, useBilling } from '@/hooks/subscription';

interface BillingOverviewProps {
  onManageSubscription?: () => void;
  onViewInvoices?: () => void;
  onUpdatePayment?: () => void;
  className?: string;
}

/**
 * Billing Overview Component
 * Shows current subscription status, next billing, and payment method
 */
export function BillingOverview({
  onManageSubscription,
  onViewInvoices,
  onUpdatePayment,
  className
}: BillingOverviewProps) {
  const { subscription, loading: subscriptionLoading } = useSubscription();
  const { currentInvoice, paymentMethod, loading: billingLoading } = useBilling();

  const loading = subscriptionLoading || billingLoading;

  if (loading) {
    return (
      <div className={cn('space-y-6', className)}>
        <Skeleton className="h-40 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <Alert className={className}>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No subscription information available. Please try refreshing the page.
        </AlertDescription>
      </Alert>
    );
  }

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('fr-CM', {
      style: 'currency',
      currency: 'XAF',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'suspended':
        return 'destructive';
      case 'cancelled':
        return 'secondary';
      case 'grace_period':
        return 'outline';
      case 'expired':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600';
      case 'suspended':
        return 'text-red-600';
      case 'cancelled':
        return 'text-gray-600';
      case 'grace_period':
        return 'text-blue-600';
      case 'expired':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Main subscription status card */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl">Current Subscription</CardTitle>
              <CardDescription>
                Manage your subscription and billing preferences
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {subscription.status === 'active' ? (
                <CheckCircle className={cn('w-5 h-5', getStatusColor(subscription.status))} />
              ) : (
                <AlertCircle className={cn('w-5 h-5', getStatusColor(subscription.status))} />
              )}
              <Badge variant={getStatusBadgeVariant(subscription.status)}>
                {subscription.status.replace('_', ' ').toUpperCase()}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Plan details */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div>
              <div className="font-semibold text-lg">{subscription.plan?.name}</div>
              <div className="text-sm text-muted-foreground">
                {subscription.plan?.description}
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold text-xl">
                {subscription.plan?.price?.monthly === 0
                  ? 'Free'
                  : formatCurrency(subscription.plan?.price?.monthly || 0)
                }
              </div>
              {(subscription.plan?.price?.monthly || 0) > 0 && (
                <div className="text-sm text-muted-foreground">per month</div>
              )}
            </div>
          </div>

          {/* Billing cycle info */}
          {subscription.status === 'active' && subscription.expires_at && (
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-muted-foreground">Next billing date:</span>
              <span className="font-medium">{formatDate(subscription.expires_at)}</span>
            </div>
          )}

          {/* Grace period info */}
          {subscription.status === 'grace_period' && subscription.expires_at && (
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-muted-foreground">Grace period ends:</span>
              <span className="font-medium">{formatDate(subscription.expires_at)}</span>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 pt-4">
            <Button onClick={onManageSubscription}>
              Manage Subscription
            </Button>
            {(subscription.plan?.price?.monthly || 0) > 0 && (
              <Button variant="outline" onClick={onViewInvoices}>
                <Receipt className="w-4 h-4 mr-2" />
                View Invoices
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Payment method and current invoice */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Payment method */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <CreditCard className="w-5 h-5" />
              Payment Method
            </CardTitle>
          </CardHeader>
          <CardContent>
            {paymentMethod ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Provider:</span>
                  <span className="font-medium">{paymentMethod.method_type === 'mtn_momo' ? 'MTN Mobile Money' : 'Orange Money'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Phone:</span>
                  <span className="font-medium">{paymentMethod.phone_number}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Status:</span>
                  <Badge variant={paymentMethod.is_verified ? 'default' : 'secondary'}>
                    {paymentMethod.is_verified ? 'Verified' : 'Pending'}
                  </Badge>
                </div>
                <Button variant="outline" size="sm" onClick={onUpdatePayment} className="w-full mt-3">
                  Update Payment Method
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground mb-3">
                  No payment method configured
                </p>
                <Button size="sm" onClick={onUpdatePayment}>
                  Add Payment Method
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current invoice */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Calendar className="w-5 h-5" />
              Current Invoice
            </CardTitle>
          </CardHeader>
          <CardContent>
            {currentInvoice ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Amount:</span>
                  <span className="font-medium">{formatCurrency(currentInvoice.amount)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Status:</span>
                  <Badge variant={currentInvoice.status === 'completed' ? 'default' : 'destructive'}>
                    {currentInvoice.status === 'completed' ? 'Paid' : 'Pending'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Due date:</span>
                  <span className="font-medium">{formatDate(currentInvoice.created_at)}</span>
                </div>
                <Button variant="outline" size="sm" onClick={onViewInvoices} className="w-full mt-3">
                  View Details
                </Button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground">
                  No current invoice
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Status alerts */}
      {subscription.status === 'suspended' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Your subscription is suspended. Please update your payment method to avoid service interruption.
          </AlertDescription>
        </Alert>
      )}

      {subscription.status === 'cancelled' && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Your subscription has been cancelled and will end on {formatDate(subscription.expires_at || null)}.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}