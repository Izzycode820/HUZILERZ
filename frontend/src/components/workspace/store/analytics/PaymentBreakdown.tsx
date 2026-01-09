'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';

type PaymentBreakdownProps = {
    data: {
        mobileMoney: number | null;
        cashOnDelivery: number | null;
        card: number | null;
        whatsapp: number | null;
        bankTransfer: number | null;
    } | null;
};

export function PaymentBreakdown({ data }: PaymentBreakdownProps) {
    if (!data) {
        return null;
    }

    const methods = [
        { label: 'Mobile Money', value: data.mobileMoney },
        { label: 'Cash on Delivery', value: data.cashOnDelivery },
        { label: 'Card', value: data.card },
        { label: 'WhatsApp', value: data.whatsapp },
        { label: 'Bank Transfer', value: data.bankTransfer },
    ].filter(m => m.value !== null);

    return (
        <Card className="h-full flex flex-col">
            <CardHeader>
                <CardTitle>Payment Methods</CardTitle>
            </CardHeader>
            <CardContent className="flex-1">
                <div className="flex flex-col justify-between h-full text-sm">
                    {methods.map((method, index) => (
                        <div key={index} className="flex justify-between">
                            <span className="text-muted-foreground">{method.label}</span>
                            <span className="font-medium">{method.value}%</span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
