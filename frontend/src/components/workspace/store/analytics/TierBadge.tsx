'use client';

import * as React from 'react';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/shadcn-ui/popover';
import { Separator } from '@/components/shadcn-ui/separator';

type TierBadgeProps = {
    currentTier: 'none' | 'basic' | 'pro' | 'advanced';
};

const tierConfig = {
    basic: {
        color: 'bg-gray-400',
        label: 'Basic',
        current: [
            'Revenue and orders tracking',
            'Payment method breakdown',
            'Revenue chart',
        ],
        future: [],
    },
    pro: {
        color: 'bg-orange-500',
        label: 'Pro',
        current: [
            'All Basic features',
            'Conversion funnel',
            'Customer metrics',
            'Cart abandonment tracking',
        ],
        future: [
            'Extended date ranges',
            'Sales by traffic source',
        ],
    },
    advanced: {
        color: 'bg-green-500',
        label: 'Advanced',
        current: [
            'All Pro features',
            'Customer lifetime value',
            'Cohort analysis',
        ],
        future: [
            'Custom reports',
            'Profit margin tracking',
            'Multi-channel attribution',
        ],
    },
    none: {
        color: 'bg-gray-300',
        label: 'None',
        current: [],
        future: ['Upgrade to access analytics'],
    },
};

export function TierBadge({ currentTier }: TierBadgeProps) {
    const tiers = ['basic', 'pro', 'advanced'] as const;

    return (
        <div className="flex items-center gap-1">
            {tiers.map((tier) => {
                const config = tierConfig[tier];
                const isActive = currentTier === tier;
                const isUnlocked =
                    currentTier === 'advanced' ||
                    (currentTier === 'pro' && tier !== 'advanced') ||
                    (currentTier === 'basic' && tier === 'basic');

                return (
                    <Popover key={tier}>
                        <PopoverTrigger asChild>
                            <button
                                className={`h-2 w-2 rounded-full ${config.color} ${!isUnlocked ? 'opacity-30' : ''
                                    } transition-opacity hover:opacity-100`}
                                aria-label={`${config.label} tier`}
                            />
                        </PopoverTrigger>
                        <PopoverContent className="w-64 p-3" align="start">
                            <div className="space-y-2">
                                <div className="font-medium text-sm">{config.label} Tier</div>

                                {config.current.length > 0 && (
                                    <div className="text-xs space-y-1">
                                        <div className="text-muted-foreground">Current</div>
                                        {config.current.map((item, i) => (
                                            <div key={i} className="text-foreground">
                                                {item}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {config.future.length > 0 && (
                                    <>
                                        <Separator className="my-2" />
                                        <div className="text-xs space-y-1">
                                            <div className="text-muted-foreground">Coming Soon</div>
                                            {config.future.map((item, i) => (
                                                <div key={i} className="text-muted-foreground">
                                                    {item}
                                                </div>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        </PopoverContent>
                    </Popover>
                );
            })}
        </div>
    );
}
