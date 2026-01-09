"use client";

import React from 'react';
import { Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { cn } from '@/lib/utils';

interface PaymentFormProps {
  planName: string;
  amount: number;
  phoneNumber: string;
  onPhoneNumberChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  error?: string | null;
  className?: string;
  children?: React.ReactNode; // For PaymentMethodSelector
}

/**
 * Payment Form Component
 * Minimal shadcn form for phone input only
 * Clean, no verbose text or guidance
 */
export function PaymentForm({
  planName,
  amount,
  phoneNumber,
  onPhoneNumberChange,
  onSubmit,
  onCancel,
  isSubmitting = false,
  error = null,
  className,
  children
}: PaymentFormProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <Card className={cn('max-w-md mx-auto', className)}>
      <CardHeader>
        <CardTitle>Payment Method</CardTitle>
        <CardDescription>
          Complete your {planName} subscription
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={onSubmit} className="space-y-6">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}

          {/* Payment Method Selector (passed as children) */}
          {children}

          {/* Phone Number */}
          <div className="space-y-2">
            <Label htmlFor="phone">Phone number</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="670123456"
              value={phoneNumber}
              onChange={(e) => onPhoneNumberChange(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {/* Amount Display */}
          <div className="flex items-center justify-between py-4 border-t">
            <span className="text-sm text-muted-foreground">Total</span>
            <span className="text-2xl font-bold">{formatCurrency(amount)} FCFA</span>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !phoneNumber}
              className="flex-1"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing
                </>
              ) : (
                'Pay'
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
