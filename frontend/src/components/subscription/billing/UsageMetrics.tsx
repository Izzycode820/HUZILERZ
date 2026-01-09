"use client";

import React, { useMemo } from 'react';
import { TrendingUp, Database, Globe, BarChart3, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Progress } from '@/components/shadcn-ui/progress';
import { Badge } from '@/components/shadcn-ui/badge';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { cn } from '@/lib/utils';
import { useSubscription, useUsageMetrics } from '@/hooks/subscription';

interface UsageMetricsProps {
  onUpgrade?: () => void;
  className?: string;
  showUpgradePrompts?: boolean;
}

interface MetricCardProps {
  title: string;
  current: number;
  limit: number | 'unlimited';
  unit: string;
  icon: React.ReactNode;
  description: string;
  warningThreshold?: number;
}

/**
 * Usage Metrics Component
 * Displays current resource usage against subscription limits
 */
export function UsageMetrics({ 
  onUpgrade, 
  className, 
  showUpgradePrompts = true 
}: UsageMetricsProps) {
  const { subscription, loading: subscriptionLoading } = useSubscription();
  const { usage, loading: usageLoading } = useUsageMetrics();

  const loading = subscriptionLoading || usageLoading;

  const MetricCard = ({ 
    title, 
    current, 
    limit, 
    unit, 
    icon, 
    description,
    warningThreshold = 0.8 
  }: MetricCardProps) => {
    const isUnlimited = limit === 'unlimited';
    const percentage = isUnlimited ? 0 : Math.min((current / limit) * 100, 100);
    const isWarning = !isUnlimited && percentage >= warningThreshold * 100;
    const isAtLimit = !isUnlimited && current >= limit;

    const getProgressColor = () => {
      if (isAtLimit) return 'bg-red-500';
      if (isWarning) return 'bg-yellow-500';
      return 'bg-primary';
    };

    const formatNumber = (num: number): string => {
      if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
      if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
      return num.toString();
    };

    return (
      <Card className={cn(isAtLimit && 'border-red-200 bg-red-50/50')}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={cn('p-2 rounded-lg', isAtLimit ? 'bg-red-100' : 'bg-muted')}>
                <div className={cn('w-4 h-4', isAtLimit ? 'text-red-600' : 'text-muted-foreground')}>
                  {icon}
                </div>
              </div>
              <div>
                <CardTitle className="text-base font-medium">{title}</CardTitle>
                <CardDescription className="text-xs">{description}</CardDescription>
              </div>
            </div>
            {isAtLimit && (
              <AlertTriangle className="w-4 h-4 text-red-500" />
            )}
          </div>
        </CardHeader>
        
        <CardContent className="space-y-3">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-2xl font-bold">
                {formatNumber(current)}
              </div>
              <div className="text-xs text-muted-foreground">
                of {isUnlimited ? 'unlimited' : formatNumber(limit)} {unit}
              </div>
            </div>
            {!isUnlimited && (
              <Badge variant={isAtLimit ? 'destructive' : isWarning ? 'secondary' : 'outline'}>
                {percentage.toFixed(0)}%
              </Badge>
            )}
          </div>
          
          {!isUnlimited && (
            <Progress 
              value={percentage} 
              className="h-2"
            />
          )}
          
          {isAtLimit && showUpgradePrompts && (
            <div className="text-xs text-red-600 font-medium">
              Limit reached - Upgrade to continue
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      </div>
    );
  }

  if (!subscription || !usage) {
    return (
      <Alert className={className}>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Unable to load usage metrics. Please try refreshing the page.
        </AlertDescription>
      </Alert>
    );
  }

  const plan = subscription.plan;
  const hasLimitWarnings = useMemo(() => {
    const warnings = [];
    
    const sitesLimit = typeof plan.resources?.deployed_sites === 'number' ? plan.resources.deployed_sites : 0;
    const workspacesLimit = typeof plan.resources?.workspaces === 'number' ? plan.resources.workspaces : 0;
    const storageLimit = plan.resources?.storage_gb || 0;
    const bandwidthLimit = plan.resources?.bandwidth_gb || 0;

    if (sitesLimit > 0 && usage.sites_used >= sitesLimit) {
      warnings.push('sites');
    }
    if (workspacesLimit > 0 && usage.workspaces_used >= workspacesLimit) {
      warnings.push('workspaces');
    }
    if (storageLimit > 0 && usage.storage_used_gb >= storageLimit) {
      warnings.push('storage');
    }
    if (bandwidthLimit > 0 && usage.bandwidth_used_gb >= bandwidthLimit) {
      warnings.push('bandwidth');
    }
    
    return warnings;
  }, [plan, usage]);

  return (
    <div className={cn('space-y-6', className)}>
      {/* Usage overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Deployed Sites"
          current={usage.sites_used}
          limit={typeof plan.resources?.deployed_sites === 'number' && plan.resources.deployed_sites > 0 ? plan.resources.deployed_sites : 'unlimited'}
          unit="sites"
          icon={<Globe />}
          description="Active website deployments"
        />
        
        <MetricCard
          title="Workspaces"
          current={usage.workspaces_used}
          limit={typeof plan.resources?.workspaces === 'number' && plan.resources.workspaces > 0 ? plan.resources.workspaces : 'unlimited'}
          unit="workspaces"
          icon={<BarChart3 />}
          description="Project workspaces in use"
        />
        
        <MetricCard
          title="Storage Used"
          current={usage.storage_used_gb}
          limit={plan.resources?.storage_gb && plan.resources.storage_gb > 0 ? plan.resources.storage_gb : 'unlimited'}
          unit="GB"
          icon={<Database />}
          description="Total storage across all sites"
        />
        
        <MetricCard
          title="Bandwidth"
          current={usage.bandwidth_used_gb}
          limit={plan.resources?.bandwidth_gb && plan.resources.bandwidth_gb > 0 ? plan.resources.bandwidth_gb : 'unlimited'}
          unit="GB"
          icon={<TrendingUp />}
          description="Data transfer this month"
        />
      </div>

      {/* Usage warnings */}
      {hasLimitWarnings.length > 0 && showUpgradePrompts && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <div className="font-medium">Resource limits reached</div>
              <div className="text-sm">
                You've reached your limit for: {hasLimitWarnings.join(', ')}. 
                Upgrade your plan to continue using these resources.
              </div>
              {onUpgrade && (
                <button
                  onClick={onUpgrade}
                  className="text-sm font-medium underline hover:no-underline"
                >
                  Upgrade now
                </button>
              )}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Usage summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Current Plan: {plan.name}
          </CardTitle>
          <CardDescription>
            Your resource usage for this billing period
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-sm text-muted-foreground mb-1">Sites</div>
              <div className="font-medium">
                {usage.sites_used} / {typeof plan.resources?.deployed_sites === 'number' && plan.resources.deployed_sites > 0 ? plan.resources.deployed_sites : '∞'}
              </div>
            </div>
            
            <div>
              <div className="text-sm text-muted-foreground mb-1">Workspaces</div>
              <div className="font-medium">
                {usage.workspaces_used} / {typeof plan.resources?.workspaces === 'number' && plan.resources.workspaces > 0 ? plan.resources.workspaces : '∞'}
              </div>
            </div>
            
            <div>
              <div className="text-sm text-muted-foreground mb-1">Storage</div>
              <div className="font-medium">
                {usage.storage_used_gb}GB / {plan.resources?.storage_gb && plan.resources.storage_gb > 0 ? `${plan.resources.storage_gb}GB` : '∞'}
              </div>
            </div>
            
            <div>
              <div className="text-sm text-muted-foreground mb-1">Bandwidth</div>
              <div className="font-medium">
                {usage.bandwidth_used_gb}GB / {plan.resources?.bandwidth_gb && plan.resources.bandwidth_gb > 0 ? `${plan.resources.bandwidth_gb}GB` : '∞'}
              </div>
            </div>
          </div>
          
          <div className="mt-4 text-xs text-muted-foreground text-center">
            Usage resets on your next billing date: {
              subscription.expires_at
                ? new Date(subscription.expires_at).toLocaleDateString()
                : 'N/A'
            }
          </div>
        </CardContent>
      </Card>
    </div>
  );
}