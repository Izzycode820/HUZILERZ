'use client';

/**
 * Store Analytics Dashboard Container (Smart Component)
 * 
 * Industry Standard Pattern:
 * - Container handles analytics data fetching (GraphQL)
 * - Presentational components handle UI (SectionCards, ChartAreaInteractive)
 * - Clean separation of concerns
 */

import React from 'react';
import { useQuery } from '@apollo/client/react';
import { GetStoreAnalyticsDocument } from '@/services/graphql/admin-store/queries/analytics/__generated__/getStoreAnalytics.generated';
import { SectionCards } from './section-cards';
import { ChartAreaInteractive } from './chart-area-interactive';
import { Card, CardContent } from '@/components/shadcn-ui/card';

export function DashboardContainer() {
    // Fetch analytics data (workspace auto-scoped via JWT middleware)
    const { data, loading, error } = useQuery(GetStoreAnalyticsDocument, {
        variables: {
            days: 30, // Last 30 days
        },
    });

    const analytics = data?.storeAnalytics;

    // Loading state
    if (loading) {
        return (
            <div className="@container/main flex flex-1 flex-col gap-2 relative">
                <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                    <Card>
                        <CardContent className="pt-6">
                            <div className="text-center py-12">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                                <p className="text-muted-foreground">Loading analytics...</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // Error state
    if (error || !analytics) {
        return (
            <div className="@container/main flex flex-1 flex-col gap-2 relative">
                <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                    <Card>
                        <CardContent className="pt-6">
                            <div className="text-center text-destructive">
                                <p>Failed to load analytics</p>
                                <p className="text-sm text-muted-foreground">
                                    {error?.message || 'Unknown error occurred'}
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // No access state (free tier)
    if (!analytics.hasAccess) {
        return (
            <div className="@container/main flex flex-1 flex-col gap-2 relative">
                <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                    <Card>
                        <CardContent className="pt-6">
                            <div className="text-center py-12">
                                <p className="text-lg font-semibold mb-2">Analytics Not Available</p>
                                <p className="text-muted-foreground mb-4">
                                    {analytics.error || `Analytics is not available for your current plan.`}
                                </p>
                                {analytics.requiredPlan && (
                                    <p className="text-sm text-muted-foreground">
                                        Upgrade to <span className="font-semibold">{analytics.requiredPlan}</span> to unlock analytics
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div className="@container/main flex flex-1 flex-col gap-2 relative pb-24 md:pb-0">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                {/* Cards Section - BASIC tier */}
                <SectionCards cards={analytics.cards || []} />

                {/* Chart Section - BASIC tier */}
                <div className="px-4 lg:px-6">
                    <ChartAreaInteractive chartData={analytics.chart} />
                </div>
            </div>
        </div>
    );
}
