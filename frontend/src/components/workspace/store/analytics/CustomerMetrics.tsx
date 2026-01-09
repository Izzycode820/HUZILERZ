'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';

type CustomerMetricsProps = {
    data: {
        newCustomers: number | null;
        returningCustomers: number | null;
        total: number | null;
        newRate: number | null;
    } | null;
};

export function CustomerMetrics({ data }: CustomerMetricsProps) {
    if (!data) {
        return null;
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Customer Metrics</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    {data.newCustomers !== null && (
                        <div>
                            <div className="text-muted-foreground">New Customers</div>
                            <div className="text-2xl font-semibold">{data.newCustomers}</div>
                        </div>
                    )}
                    {data.returningCustomers !== null && (
                        <div>
                            <div className="text-muted-foreground">Returning</div>
                            <div className="text-2xl font-semibold">{data.returningCustomers}</div>
                        </div>
                    )}
                    {data.total !== null && (
                        <div>
                            <div className="text-muted-foreground">Total</div>
                            <div className="text-2xl font-semibold">{data.total}</div>
                        </div>
                    )}
                    {data.newRate !== null && (
                        <div>
                            <div className="text-muted-foreground">New Customer Rate</div>
                            <div className="text-2xl font-semibold">{data.newRate.toFixed(1)}%</div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
