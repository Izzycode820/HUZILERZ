"use client"

import React from 'react';
import { useRouter } from 'next/navigation';
import { Crown, Zap, Users, Globe, TrendingUp, Lock, Database, Wifi, Box } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import { cn } from '@/lib/utils';
import { FEATURE_LIMITS } from '@/types/subscription';

// ============================================================================
// Types - Feature Context (Extensible)
// ============================================================================

export type FeatureContext =
  | 'workspace_limit'
  | 'deployment'
  | 'custom_domain'
  | 'analytics'
  | 'white_label'
  | 'api_access'
  | 'team_collaboration'
  | 'storage_limit'
  | 'bandwidth_limit'
  | 'sites_limit';

type PlanTier = 'free' | 'beginning' | 'pro' | 'enterprise';

// ============================================================================
// Smart Tier Gap Detection
// ============================================================================

interface TierGap {
  from: PlanTier;
  to: PlanTier;
  gapType: 'free_to_beginning' | 'beginning_to_pro' | 'pro_to_enterprise' | 'free_to_pro' | 'free_to_enterprise' | 'beginning_to_enterprise';
}

function detectTierGap(currentTier: PlanTier, requiredTier: PlanTier): TierGap {
  const tierOrder: Record<PlanTier, number> = { free: 0, beginning: 1, pro: 2, enterprise: 3 };
  const current = tierOrder[currentTier];
  const required = tierOrder[requiredTier];

  // Direct gaps
  if (current === 0 && required === 1) return { from: currentTier, to: requiredTier, gapType: 'free_to_beginning' };
  if (current === 1 && required === 2) return { from: currentTier, to: requiredTier, gapType: 'beginning_to_pro' };
  if (current === 2 && required === 3) return { from: currentTier, to: requiredTier, gapType: 'pro_to_enterprise' };

  // Multi-tier gaps
  if (current === 0 && required === 2) return { from: currentTier, to: requiredTier, gapType: 'free_to_pro' };
  if (current === 0 && required === 3) return { from: currentTier, to: requiredTier, gapType: 'free_to_enterprise' };
  if (current === 1 && required === 3) return { from: currentTier, to: requiredTier, gapType: 'beginning_to_enterprise' };

  return { from: currentTier, to: requiredTier, gapType: 'free_to_beginning' };
}

// ============================================================================
// Smart Required Tier Calculator
// ============================================================================

function calculateRequiredTier(feature: FeatureContext, currentUsage?: number): PlanTier {
  // Map feature to FEATURE_LIMITS key
  const featureToLimitKey: Record<FeatureContext, keyof typeof FEATURE_LIMITS.free> = {
    workspace_limit: 'workspaces',
    deployment: 'sites_per_workspace',
    storage_limit: 'storage_gb',
    bandwidth_limit: 'bandwidth_gb',
    custom_domain: 'custom_domains',
    team_collaboration: 'team_members',
    api_access: 'api_calls_per_month',
    sites_limit: 'sites_per_workspace',
    analytics: 'sites_per_workspace', // Available when you can deploy
    white_label: 'sites_per_workspace', // Enterprise feature
  };

  const limitKey = featureToLimitKey[feature];

  // Find the minimum tier that satisfies the requirement
  const tiers: PlanTier[] = ['beginning', 'pro', 'enterprise'];

  for (const tier of tiers) {
    const limit = FEATURE_LIMITS[tier][limitKey];

    // If limit is -1 (unlimited) or greater than current usage, this tier works
    if (limit === -1 || (currentUsage && limit > currentUsage) || limit > 0) {
      // Special cases
      if (feature === 'white_label') return 'enterprise';
      if (feature === 'analytics' && tier === 'beginning') continue; // Analytics needs Pro

      return tier;
    }
  }

  return 'beginning'; // Fallback
}

// ============================================================================
// Smart Messaging Generator (Achievement-Based)
// ============================================================================

interface SmartMessage {
  title: string;
  description: string;
  achievement?: string; // "You've created 1 workspace!"
  benefit: string; // "Upgrade to Pro for 3 workspaces"
  ctaText: string;
}

function generateSmartMessage(
  feature: FeatureContext,
  currentTier: PlanTier,
  requiredTier: PlanTier,
  currentUsage?: { current: number; limit: number }
): SmartMessage {
  const gap = detectTierGap(currentTier, requiredTier);
  const tierNames: Record<PlanTier, string> = {
    free: 'Free',
    beginning: 'Beginning',
    pro: 'Pro',
    enterprise: 'Enterprise'
  };

  // Achievement-based messaging (63% lift)
  const formatLimit = (num: number) => num === -1 ? 'unlimited' : num.toString();

  // Get upgrade benefit from FEATURE_LIMITS
  const getUpgradeBenefit = () => {
    const featureMap: Record<FeatureContext, keyof typeof FEATURE_LIMITS.free> = {
      workspace_limit: 'workspaces',
      storage_limit: 'storage_gb',
      bandwidth_limit: 'bandwidth_gb',
      deployment: 'sites_per_workspace',
      sites_limit: 'sites_per_workspace',
      custom_domain: 'custom_domains',
      team_collaboration: 'team_members',
      api_access: 'api_calls_per_month',
      analytics: 'sites_per_workspace',
      white_label: 'sites_per_workspace',
    };

    const key = featureMap[feature];
    const nextTierLimit = FEATURE_LIMITS[requiredTier][key];

    return formatLimit(nextTierLimit);
  };

  // Feature-specific messaging
  switch (feature) {
    case 'workspace_limit': {
      const benefit = getUpgradeBenefit();
      return {
        title: 'Workspace Limit Reached',
        achievement: currentUsage ? `You've created ${currentUsage.current} workspace${currentUsage.current > 1 ? 's' : ''}!` : undefined,
        description: `You've reached your workspace limit. Scale your business with more workspaces.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for ${benefit} workspace${benefit === 'unlimited' || parseInt(benefit) > 1 ? 's' : ''}`,
        ctaText: `Unlock ${benefit === 'unlimited' ? 'Unlimited' : benefit} Workspaces`
      };
    }

    case 'storage_limit': {
      const benefit = getUpgradeBenefit();
      return {
        title: 'Storage Limit Reached',
        achievement: currentUsage ? `You've used ${currentUsage.current} GB of storage!` : undefined,
        description: `You're out of storage space. Upgrade to store more content and media.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for ${benefit} GB storage`,
        ctaText: `Get ${benefit} GB Storage`
      };
    }

    case 'bandwidth_limit': {
      const benefit = getUpgradeBenefit();
      return {
        title: 'Bandwidth Limit Reached',
        achievement: currentUsage ? `You've used ${currentUsage.current} GB bandwidth!` : undefined,
        description: `You've reached your bandwidth limit. Upgrade to serve more visitors.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for ${benefit} GB monthly bandwidth`,
        ctaText: `Get ${benefit} GB Bandwidth`
      };
    }

    case 'deployment':
    case 'sites_limit': {
      return {
        title: 'Deployment Unlocks with Paid Plans',
        description: `You're currently on the Free plan (build-only). Deploy your workspace live to the web.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} to deploy your site`,
        ctaText: 'Deploy Live'
      };
    }

    case 'custom_domain': {
      const benefit = getUpgradeBenefit();
      return {
        title: 'Custom Domain Available on Paid Plans',
        description: `Connect your own domain name to build your brand.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for ${benefit} custom domain${benefit === 'unlimited' || parseInt(benefit) > 1 ? 's' : ''}`,
        ctaText: 'Connect Your Domain'
      };
    }

    case 'team_collaboration': {
      const benefit = getUpgradeBenefit();
      return {
        title: 'Team Collaboration',
        description: `Work together with your team. Invite members and assign roles.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for ${benefit} team member${benefit === 'unlimited' || parseInt(benefit) > 1 ? 's' : ''}`,
        ctaText: 'Invite Your Team'
      };
    }

    case 'api_access': {
      return {
        title: 'API Access Available on Paid Plans',
        description: `Programmatically access and manage your workspace data.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for API access`,
        ctaText: 'Unlock API Access'
      };
    }

    case 'analytics': {
      return {
        title: 'Advanced Analytics',
        description: `Get detailed insights, conversion tracking, and performance metrics.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} for advanced analytics`,
        ctaText: 'Unlock Analytics'
      };
    }

    case 'white_label': {
      return {
        title: 'White Label Branding',
        description: `Remove Huzilerz branding and use your own. Perfect for agencies.`,
        benefit: `Upgrade to Enterprise for white label`,
        ctaText: 'Go White Label'
      };
    }

    default:
      return {
        title: 'Premium Feature',
        description: `This feature is available on ${tierNames[requiredTier]} plan and above.`,
        benefit: `Upgrade to ${tierNames[requiredTier]} to unlock`,
        ctaText: 'Upgrade Now'
      };
  }
}

// ============================================================================
// Icon Mapping
// ============================================================================

function getFeatureIcon(feature: FeatureContext): React.ReactNode {
  const iconMap: Record<FeatureContext, React.ReactNode> = {
    workspace_limit: <Users className="w-6 h-6" />,
    deployment: <Zap className="w-6 h-6" />,
    custom_domain: <Globe className="w-6 h-6" />,
    analytics: <TrendingUp className="w-6 h-6" />,
    white_label: <Crown className="w-6 h-6" />,
    api_access: <Zap className="w-6 h-6" />,
    team_collaboration: <Users className="w-6 h-6" />,
    storage_limit: <Database className="w-6 h-6" />,
    bandwidth_limit: <Wifi className="w-6 h-6" />,
    sites_limit: <Box className="w-6 h-6" />,
  };

  return iconMap[feature] || <Lock className="w-6 h-6" />;
}

// ============================================================================
// Component Props
// ============================================================================

interface FeatureGateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  feature: FeatureContext;
  currentTier: PlanTier;
  currentUsage?: string; // e.g., "1/1 workspaces" for badge
  usageData?: { current: number; limit: number }; // For achievement messaging
  className?: string;
}

// ============================================================================
// FeatureGateModal Component - Smart, Achievement-Based
// ============================================================================

export function FeatureGateModal({
  open,
  onOpenChange,
  feature,
  currentTier,
  currentUsage,
  usageData,
  className
}: FeatureGateModalProps) {
  const router = useRouter();

  // Smart calculations
  const requiredTier = calculateRequiredTier(feature, usageData?.current);
  const message = generateSmartMessage(feature, currentTier, requiredTier, usageData);

  const handleUpgrade = () => {
    onOpenChange(false);
    // Navigate to pricing with context (conversion optimization)
    router.push(`/billing/plans?feature=${feature}&from=${currentTier}&to=${requiredTier}`);
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          // Premium glassmorphism effect
          'bg-background/95 backdrop-blur-lg',
          // Elegant spacing
          'sm:max-w-md',
          // Smooth animations
          'data-[state=open]:animate-in data-[state=closed]:animate-out',
          'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
          'data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
          // Premium shadow
          'shadow-2xl border-muted',
          className
        )}
      >
        <DialogHeader className="space-y-4">
          {/* Feature Icon with Usage Badge */}
          <div className="flex flex-col items-center gap-3 pt-2">
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 text-primary">
              {getFeatureIcon(feature)}
            </div>

            {currentUsage && (
              <Badge variant="secondary" className="text-xs font-medium">
                {currentUsage}
              </Badge>
            )}
          </div>

          {/* Achievement + Messaging - 350% better conversion */}
          <div className="text-center space-y-3">
            {message.achievement && (
              <div className="px-4 py-2 bg-primary/5 rounded-lg border border-primary/10">
                <p className="text-sm font-medium text-primary">
                  ✓ {message.achievement}
                </p>
              </div>
            )}

            <DialogTitle className="text-xl font-semibold">
              {message.title}
            </DialogTitle>

            <DialogDescription className="text-sm text-muted-foreground leading-relaxed">
              {message.description}
            </DialogDescription>

            {/* Specific Benefit - 63% lift */}
            <div className="px-4 py-3 bg-muted/50 rounded-lg border">
              <p className="text-sm font-medium text-foreground">
                {message.benefit}
              </p>
            </div>
          </div>
        </DialogHeader>

        {/* Clean Action Buttons - Coda Pattern */}
        <DialogFooter className="sm:justify-center gap-3 pt-2">
          <Button
            variant="outline"
            onClick={handleCancel}
            className="flex-1 sm:flex-none min-w-[100px]"
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpgrade}
            className="flex-1 sm:flex-none min-w-[120px]"
          >
            {message.ctaText}
          </Button>
        </DialogFooter>

        {/* Minimal Trust Indicator */}
        <p className="text-center text-xs text-muted-foreground pb-2">
          Mobile Money • Cancel Anytime
        </p>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Export
// ============================================================================

export default FeatureGateModal;
