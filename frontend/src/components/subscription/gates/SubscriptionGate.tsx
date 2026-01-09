"use client";

import React from 'react';
import { useSubscription } from '@/hooks/subscription';

interface SubscriptionGateProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requireActive?: boolean;
}

/**
 * Subscription Gate Component
 * Controls access based on subscription status
 */
export function SubscriptionGate({ 
  children, 
  fallback = null, 
  requireActive = true 
}: SubscriptionGateProps) {
  const { subscription, loading } = useSubscription();

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  const hasValidSubscription = subscription && 
    (requireActive ? subscription.is_active : true);

  if (!hasValidSubscription) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}