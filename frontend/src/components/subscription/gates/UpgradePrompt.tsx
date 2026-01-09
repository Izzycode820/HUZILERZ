"use client";

import React, { useState } from 'react';
import { 
  Crown, 
  ArrowRight, 
  Star, 
  Check, 
  X, 
  Zap, 
  TrendingUp, 
  Users,
  Clock 
} from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { cn } from '@/lib/utils';
import type { CoreFeatureType } from '@/types/subscription';

interface UpgradePromptProps {
  title: string;
  description: string;
  currentTier: string;
  requiredTier: string;
  feature: CoreFeatureType;
  benefits: string[];
  onUpgrade?: () => void;
  onDismiss?: () => void;
  showDismiss?: boolean;
  urgency?: 'low' | 'medium' | 'high';
  psychology?: 'scarcity' | 'social_proof' | 'value_proposition' | 'loss_aversion';
  className?: string;
}

/**
 * Upgrade Prompt Component
 * Conversion-optimized upgrade prompts with psychology-driven messaging
 */
export function UpgradePrompt({
  title,
  description,
  currentTier,
  requiredTier,
  feature,
  benefits,
  onUpgrade,
  onDismiss,
  showDismiss = true,
  urgency = 'medium',
  psychology = 'value_proposition',
  className
}: UpgradePromptProps) {
  const [isDismissed, setIsDismissed] = useState(false);

  if (isDismissed) return null;

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  const handleUpgrade = () => {
    onUpgrade?.();
  };

  // Get tier display names
  const getTierDisplayName = (tier: string): string => {
    const names: Record<string, string> = {
      free: 'Free',
      beginning: 'Beginner',
      pro: 'Pro',
      enterprise: 'Enterprise'
    };
    return names[tier] || tier;
  };

  // Get psychology-driven messaging
  const getPsychologyContent = () => {
    switch (psychology) {
      case 'scarcity':
        return {
          badge: 'Limited Offer',
          badgeVariant: 'destructive' as const,
          subtitle: 'This promotion expires soon!',
          cta: `Upgrade to ${getTierDisplayName(requiredTier)} now`,
          urgencyText: 'Only a few spots remaining'
        };
      
      case 'social_proof':
        return {
          badge: 'Popular Choice',
          badgeVariant: 'default' as const,
          subtitle: '87% of our users choose this plan',
          cta: `Join ${getTierDisplayName(requiredTier)}`,
          urgencyText: '+1,200 companies trust us'
        };
        
      case 'loss_aversion':
        return {
          badge: 'Missing Feature',
          badgeVariant: 'secondary' as const,
          subtitle: 'Don\'t miss this growth opportunity',
          cta: `Unlock with ${getTierDisplayName(requiredTier)}`,
          urgencyText: 'Your competitors are already using these features'
        };
        
      default: // value_proposition
        return {
          badge: 'Premium Feature',
          badgeVariant: 'outline' as const,
          subtitle: 'Optimize your productivity',
          cta: `Upgrade to ${getTierDisplayName(requiredTier)}`,
          urgencyText: 'Guaranteed return on investment'
        };
    }
  };

  const psychologyContent = getPsychologyContent();

  // Get urgency styling
  const getUrgencyStyles = () => {
    switch (urgency) {
      case 'high':
        return {
          container: 'border-red-200 bg-gradient-to-br from-red-50 to-orange-50',
          header: 'text-red-900',
          icon: 'text-red-600',
        };
      case 'medium':
        return {
          container: 'border-blue-200 bg-gradient-to-br from-blue-50 to-purple-50',
          header: 'text-blue-900',
          icon: 'text-blue-600',
        };
      default:
        return {
          container: 'border-green-200 bg-gradient-to-br from-green-50 to-blue-50',
          header: 'text-green-900',
          icon: 'text-green-600',
        };
    }
  };

  const styles = getUrgencyStyles();

  // Get feature icon
  const getFeatureIcon = () => {
    const icons: Partial<Record<CoreFeatureType, React.ReactNode>> = {
      deployment: <Zap className="w-5 h-5" />,
      custom_domain: <Crown className="w-5 h-5" />,
      analytics: <TrendingUp className="w-5 h-5" />,
      analytics_advanced: <TrendingUp className="w-5 h-5" />,
      white_label: <Star className="w-5 h-5" />,
      dedicated_support: <Users className="w-5 h-5" />,
      team_collaboration: <Users className="w-5 h-5" />,
      api_access: <Zap className="w-5 h-5" />,
    };

    return icons[feature] || <Crown className="w-5 h-5" />;
  };

  return (
    <Card className={cn(
      'relative overflow-hidden transition-all duration-300 hover:shadow-lg',
      styles.container,
      className
    )}>
      {/* Dismiss button */}
      {showDismiss && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 h-6 w-6 z-10 hover:bg-white/20"
          onClick={handleDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      )}

      <CardHeader className="pb-4">
        <div className="flex items-start gap-3">
          <div className={cn('mt-1', styles.icon)}>
            {getFeatureIcon()}
          </div>
          
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <CardTitle className={cn('text-lg font-bold', styles.header)}>
                {title}
              </CardTitle>
              <Badge variant={psychologyContent.badgeVariant} className="text-xs">
                {psychologyContent.badge}
              </Badge>
            </div>
            
            <CardDescription className="text-sm">
              {description}
            </CardDescription>
            
            <p className="text-xs font-medium opacity-75">
              {psychologyContent.subtitle}
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current vs Required tier */}
        <div className="flex items-center justify-between p-3 bg-white/50 rounded-lg border">
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Current</div>
            <div className="font-semibold">{getTierDisplayName(currentTier)}</div>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground" />
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Required</div>
            <div className="font-semibold text-primary">{getTierDisplayName(requiredTier)}</div>
          </div>
        </div>

        {/* Benefits list */}
        <div className="space-y-2">
          <p className="text-sm font-medium">What you unlock:</p>
          <div className="grid gap-2 max-h-32 overflow-y-auto">
            {benefits.slice(0, 4).map((benefit, index) => (
              <div key={index} className="flex items-start gap-2">
                <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{benefit}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Psychology-driven urgency message */}
        <Alert className="border-current bg-white/30">
          <Clock className="h-4 w-4" />
          <AlertDescription className="text-xs">
            {psychologyContent.urgencyText}
          </AlertDescription>
        </Alert>

        {/* CTA Button */}
        <Button 
          onClick={handleUpgrade}
          className="w-full font-semibold"
          size="lg"
        >
          {psychologyContent.cta}
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>

        {/* Trust indicators */}
        <div className="text-center text-xs text-muted-foreground space-y-1">
          <p>Secure Mobile Money Payment</p>
          <p>Support available - No commitment</p>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Compact upgrade prompt for inline use
 */
interface CompactUpgradePromptProps {
  feature: CoreFeatureType;
  requiredTier: string;
  onUpgrade?: () => void;
  className?: string;
}

export function CompactUpgradePrompt({ 
  feature, 
  requiredTier, 
  onUpgrade,
  className 
}: CompactUpgradePromptProps) {
  const getTierDisplayName = (tier: string): string => {
    const names: Record<string, string> = {
      free: 'Free',
      beginning: 'Beginner', 
      pro: 'Pro',
      enterprise: 'Enterprise'
    };
    return names[tier] || tier;
  };

  return (
    <Alert className={cn('border-blue-200 bg-blue-50', className)}>
      <Crown className="h-4 w-4 text-blue-600" />
      <div className="flex items-center justify-between">
        <AlertDescription className="text-blue-800 text-sm">
          <strong>Premium Feature</strong> - Upgrade to {getTierDisplayName(requiredTier)} to unlock
        </AlertDescription>
        <Button size="sm" onClick={onUpgrade} className="ml-4">
          Explore
          <ArrowRight className="w-3 h-3 ml-1" />
        </Button>
      </div>
    </Alert>
  );
}

/**
 * Floating upgrade prompt for persistent display
 */
interface FloatingUpgradePromptProps {
  feature: CoreFeatureType;
  requiredTier: string;
  onUpgrade?: () => void;
  onDismiss?: () => void;
}

export function FloatingUpgradePrompt({ 
  feature, 
  requiredTier, 
  onUpgrade,
  onDismiss 
}: FloatingUpgradePromptProps) {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  const getTierDisplayName = (tier: string): string => {
    const names: Record<string, string> = {
      beginning: 'Beginner',
      pro: 'Pro', 
      enterprise: 'Enterprise'
    };
    return names[tier] || tier;
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 max-w-[calc(100vw-2rem)]">
      <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50 shadow-lg">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Crown className="w-4 h-4 text-blue-600" />
              <CardTitle className="text-sm">Premium Feature</CardTitle>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleDismiss}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-muted-foreground">
            Unlock this feature with {getTierDisplayName(requiredTier)} plan
          </p>
          <div className="flex gap-2">
            <Button size="sm" onClick={onUpgrade} className="flex-1">
              Explore
            </Button>
            <Button size="sm" variant="outline" onClick={handleDismiss}>
              Later
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}