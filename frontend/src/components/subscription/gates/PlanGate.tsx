"use client";

import React from 'react';
import { useSubscription } from '@/hooks/subscription';
type SubscriptionTier = 'free' | 'beginning' | 'pro' | 'enterprise';

interface PlanGateProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requiredTier: SubscriptionTier;
  allowHigher?: boolean;
}

/**
 * Plan Gate Component
 * Controls access based on subscription plan tier
 */
export function PlanGate({ 
  children, 
  fallback = null, 
  requiredTier,
  allowHigher = true
}: PlanGateProps) {
  const { subscription, loading } = useSubscription();

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (!subscription || !subscription.is_active) {
    return <>{fallback}</>;
  }

  const tierOrder = { free: 0, beginning: 1, pro: 2, enterprise: 3 };
  const userTierOrder = tierOrder[subscription.plan.tier as keyof typeof tierOrder] || 0;
  const requiredTierOrder = tierOrder[requiredTier] || 0;

  const hasAccess = allowHigher 
    ? userTierOrder >= requiredTierOrder
    : userTierOrder === requiredTierOrder;

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}