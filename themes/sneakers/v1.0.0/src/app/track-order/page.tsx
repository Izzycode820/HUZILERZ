'use client';

import { useState } from 'react';
import { useLazyQuery } from '@apollo/client/react';
import { TrackOrderDocument, type TrackOrderQuery } from '@/services/checkout/__generated__/track-order.generated';
import { OrderTrackingForm } from '@/components/checkout/tracking/OrderTrackingForm';
import { OrderTrackingResult } from '@/components/checkout/tracking/OrderTrackingResult';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { toast } from 'sonner';

export default function TrackOrderPage() {
    const [searched, setSearched] = useState(false);

    const [trackOrder, { data, loading }] = useLazyQuery(TrackOrderDocument, {
        fetchPolicy: 'network-only',
    });

    const handleTrack = async (formData: { orderNumber: string; phone: string }) => {
        try {
            const result = await trackOrder({
                variables: {
                    orderNumber: formData.orderNumber,
                    phone: formData.phone
                }
            });

            // Handle success
            if (result.data?.trackOrder) {
                setSearched(true);
            } else {
                toast.error('Order not found. Please check your details.');
                setSearched(false);
            }
        } catch (err: any) {
            // Handle error
            console.error('Tracking error:', err);
            toast.error(err.message || 'Failed to track order. Please try again.');
            setSearched(false);
        }
    };

    const handleReset = () => {
        setSearched(false);
        // Optional: clear data if needed, but not strictly necessary with new search
    };

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 min-h-[60vh]">
            <Breadcrumbs
                items={[
                    { label: 'Home', href: '/' },
                    { label: 'Track Order' }
                ]}
                className="mb-8"
            />

            <div className="flex flex-col items-center justify-center gap-12">
                <div className="text-center space-y-4 max-w-2xl">
                    <h1 className="text-4xl md:text-5xl font-black uppercase tracking-tighter">
                        Track Your Order
                    </h1>
                    {!searched && (
                        <p className="text-muted-foreground text-lg">
                            Enter your order details below to check the current status of your shipment.
                        </p>
                    )}
                </div>

                <div className="w-full">
                    {searched && data?.trackOrder ? (
                        <OrderTrackingResult
                            order={data.trackOrder}
                            onBack={handleReset}
                        />
                    ) : (
                        <OrderTrackingForm
                            onTrack={handleTrack}
                            isLoading={loading}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
