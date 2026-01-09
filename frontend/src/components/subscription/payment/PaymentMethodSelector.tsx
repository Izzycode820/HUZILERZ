"use client";

import React from 'react';
import { Smartphone, Loader2, AlertCircle } from 'lucide-react';
import { Label } from '@/components/shadcn-ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/shadcn-ui/radio-group';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Badge } from '@/components/shadcn-ui/badge';
import { cn } from '@/lib/utils';
import { usePaymentMethodsList } from '@/hooks/payment/usePayment';

interface PaymentMethodSelectorProps {
  value: string; // Changed from 'mtn' | 'orange' to string (dynamic provider)
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Payment Method Selector Component - Refactored
 * Dynamic selector that fetches available payment providers from platform-methods endpoint
 * Auto-loads from Redis-cached backend (sub-millisecond response)
 * Supports any provider (Fapshi, MTN, Orange, future providers)
 */
export function PaymentMethodSelector({
  value,
  onChange,
  disabled = false,
  className
}: PaymentMethodSelectorProps) {
  // Fetch platform payment methods dynamically
  const {
    platformMethods,
    isLoadingMethods,
    methodsError,
    hasPaymentMethods,
    recommendedMethod
  } = usePaymentMethodsList();

  // Loading state
  if (isLoadingMethods) {
    return (
      <div className={cn('space-y-3', className)}>
        <Label>Select provider</Label>
        <div className="grid grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-28 w-full rounded-md" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (methodsError) {
    return (
      <div className={cn('space-y-3', className)}>
        <Label>Select provider</Label>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load payment methods. Please refresh the page.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // No methods available
  if (!hasPaymentMethods) {
    return (
      <div className={cn('space-y-3', className)}>
        <Label>Select provider</Label>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No payment methods available. Please contact support.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Helper to get provider icon/color based on provider name
  const getProviderDisplay = (providerName: string) => {
    const lower = providerName.toLowerCase();

    if (lower.includes('fapshi')) {
      return {
        icon: <Smartphone className="w-6 h-6 text-white" />,
        bgColor: 'bg-gradient-to-br from-blue-500 to-blue-600',
        textColor: 'text-white'
      };
    }
    if (lower.includes('mtn')) {
      return {
        icon: <Smartphone className="w-6 h-6 text-black" />,
        bgColor: 'bg-yellow-400',
        textColor: 'text-black'
      };
    }
    if (lower.includes('orange')) {
      return {
        icon: <Smartphone className="w-6 h-6 text-white" />,
        bgColor: 'bg-orange-500',
        textColor: 'text-white'
      };
    }

    // Default for unknown providers
    return {
      icon: <Smartphone className="w-6 h-6 text-white" />,
      bgColor: 'bg-gray-500',
      textColor: 'text-white'
    };
  };

  return (
    <div className={cn('space-y-3', className)}>
      <Label>Select provider</Label>
      <RadioGroup
        value={value}
        onValueChange={(v: string) => onChange(v)}
        disabled={disabled}
      >
        <div className={cn(
          "grid gap-4",
          platformMethods.length === 1 ? "grid-cols-1" : "grid-cols-2"
        )}>
          {platformMethods.map((method) => {
            const display = getProviderDisplay(method.provider);
            const isSelected = value === method.provider;
            const isRecommended = method.recommended;

            return (
              <Label
                key={method.provider}
                htmlFor={method.provider}
                className={cn(
                  "relative flex flex-col items-center justify-between rounded-md border-2 border-muted bg-transparent p-4 hover:bg-accent hover:text-accent-foreground cursor-pointer transition-all",
                  isSelected && "border-primary shadow-md",
                  disabled && "opacity-50 cursor-not-allowed"
                )}
              >
                <RadioGroupItem
                  value={method.provider}
                  id={method.provider}
                  className="sr-only"
                />

                {/* Recommended badge */}
                {isRecommended && (
                  <Badge
                    variant="secondary"
                    className="absolute top-2 right-2 text-xs bg-primary text-primary-foreground"
                  >
                    Recommended
                  </Badge>
                )}

                {/* Provider icon */}
                <div className={cn(
                  "w-12 h-12 rounded-full flex items-center justify-center mb-2",
                  display.bgColor
                )}>
                  {display.icon}
                </div>

                {/* Provider name */}
                <span className="text-sm font-medium text-center">
                  {method.display_name}
                </span>

                {/* Description */}
                {method.description && (
                  <span className="text-xs text-muted-foreground text-center mt-1">
                    {method.description}
                  </span>
                )}
              </Label>
            );
          })}
        </div>
      </RadioGroup>
    </div>
  );
}
