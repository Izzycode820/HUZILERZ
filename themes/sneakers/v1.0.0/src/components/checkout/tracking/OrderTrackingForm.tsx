'use client';

import { useState } from 'react';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Search, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface OrderTrackingFormProps {
    onTrack: (data: { orderNumber: string; phone: string }) => void;
    isLoading: boolean;
}

export function OrderTrackingForm({ onTrack, isLoading }: OrderTrackingFormProps) {
    const [orderNumber, setOrderNumber] = useState('');
    const [phone, setPhone] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!orderNumber.trim()) {
            toast.error('Please enter your order number');
            return;
        }

        if (!phone.trim()) {
            toast.error('Please enter your phone number');
            return;
        }

        onTrack({
            orderNumber: orderNumber.trim(),
            phone: phone.trim()
        });
    };

    return (
        <div className="w-full max-w-md mx-auto p-6 bg-card border border-border">
            <h2 className="text-2xl font-black uppercase tracking-tighter mb-6 text-center">
                Track Your Order
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                    <Label htmlFor="orderNumber" className="text-sm font-medium">
                        Order Number
                    </Label>
                    <Input
                        id="orderNumber"
                        placeholder="e.g. #12345"
                        value={orderNumber}
                        onChange={(e) => setOrderNumber(e.target.value)}
                        className="rounded-none h-12"
                        disabled={isLoading}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="phone" className="text-sm font-medium">
                        Phone Number
                    </Label>
                    <Input
                        id="phone"
                        type="tel"
                        placeholder="e.g. 677 000 000"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="rounded-none h-12"
                        disabled={isLoading}
                    />
                </div>

                <Button
                    type="submit"
                    className="w-full rounded-none h-12 font-bold uppercase tracking-wide"
                    disabled={isLoading}
                    size="lg"
                >
                    {isLoading ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Tracking...
                        </>
                    ) : (
                        <>
                            <Search className="mr-2 h-4 w-4" />
                            Track Order
                        </>
                    )}
                </Button>
            </form>
        </div>
    );
}
