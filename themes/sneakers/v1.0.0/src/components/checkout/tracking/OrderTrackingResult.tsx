'use client';

import { CheckCircle2, Clock, Package, Truck, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { cn } from '@/lib/utils';
import { Link } from 'react-router-dom';

interface OrderTrackingResultProps {
    order: {
        __typename?: 'OrderTrackingType';
        orderNumber: string | null;
        status: string | null;
        totalAmount: string | null;  // Decimal comes as string from backend
        createdAt: string | null;
        trackingNumber: string | null;
    };
    onBack: () => void;
}

export function OrderTrackingResult({ order, onBack }: OrderTrackingResultProps) {
    // Format currency
    const formatPrice = (amount: string | null) => {
        if (!amount) return '-';
        const numAmount = parseFloat(amount);
        return new Intl.NumberFormat('fr-CM', {
            style: 'currency',
            currency: 'XAF',
            minimumFractionDigits: 0,
        }).format(numAmount);
    };

    // Format date
    const formatDate = (dateString: string | null) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Helper to get status color/icon
    const getStatusConfig = (status: string | null) => {
        const s = status?.toLowerCase() || '';
        if (s.includes('delivered') || s.includes('completed')) {
            return {
                icon: CheckCircle2,
                color: 'text-green-600',
                bg: 'bg-green-100',
                label: 'Delivered'
            };
        }
        if (s.includes('shipping') || s.includes('transit')) {
            return {
                icon: Truck,
                color: 'text-blue-600',
                bg: 'bg-blue-100',
                label: 'On The Way'
            };
        }
        if (s.includes('processing') || s.includes('pending')) {
            return {
                icon: Package,
                color: 'text-orange-600',
                bg: 'bg-orange-100',
                label: 'Processing'
            };
        }
        return {
            icon: Clock,
            color: 'text-muted-foreground',
            bg: 'bg-muted',
            label: status || 'Unknown'
        };
    };

    const statusConfig = getStatusConfig(order.status);
    const StatusIcon = statusConfig.icon;

    return (
        <div className="w-full max-w-2xl mx-auto space-y-8">
            <Button
                variant="ghost"
                onClick={onBack}
                className="pl-0 hover:pl-2 transition-all"
            >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Track Another Order
            </Button>

            <div className="bg-card border border-border p-8">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6 mb-8 border-b border-border pb-8">
                    <div>
                        <h2 className="text-3xl font-black uppercase tracking-tighter mb-2">
                            Order #{order.orderNumber}
                        </h2>
                        <p className="text-muted-foreground">
                            Placed on {formatDate(order.createdAt)}
                        </p>
                    </div>

                    <div className={cn("inline-flex items-center gap-2 px-4 py-2 rounded-full", statusConfig.bg, statusConfig.color)}>
                        <StatusIcon className="h-5 w-5" />
                        <span className="font-bold uppercase text-sm tracking-wide">
                            {statusConfig.label}
                        </span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                        <div>
                            <p className="text-sm text-muted-foreground uppercase tracking-wider font-medium mb-1">
                                Order Status
                            </p>
                            <p className="font-medium text-lg capitalize">
                                {order.status}
                            </p>
                        </div>

                        {order.trackingNumber && (
                            <div>
                                <p className="text-sm text-muted-foreground uppercase tracking-wider font-medium mb-1">
                                    Tracking Number
                                </p>
                                <p className="font-mono text-lg">
                                    {order.trackingNumber}
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="space-y-4">
                        <div>
                            <p className="text-sm text-muted-foreground uppercase tracking-wider font-medium mb-1">
                                Total Amount
                            </p>
                            <p className="font-bold text-2xl">
                                {formatPrice(order.totalAmount)}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="mt-12 pt-8 border-t border-border">
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Button asChild variant="default" size="lg" className="rounded-none font-bold uppercase tracking-wide">
                            <Link to="/products">
                                Continue Shopping
                            </Link>
                        </Button>
                        <Button asChild variant="outline" size="lg" className="rounded-none font-bold uppercase tracking-wide">
                            <Link to="/">
                                Return Home
                            </Link>
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
