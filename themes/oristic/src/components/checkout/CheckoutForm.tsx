'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

export function CheckoutForm() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        router.push('/checkout/success');
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-8">
            <div>
                <h2 className="text-lg font-medium">Contact Information</h2>
                <div className="mt-4 space-y-4">
                    <Input type="email" placeholder="Email address" required />
                    <div className="flex items-center gap-2">
                        <input type="checkbox" id="newsletter" className="rounded border-gray-300" />
                        <label htmlFor="newsletter" className="text-sm text-muted-foreground">Email me with news and offers</label>
                    </div>
                </div>
            </div>

            <div>
                <h2 className="text-lg font-medium">Shipping Address</h2>
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Input placeholder="First name" required />
                    <Input placeholder="Last name" required />
                    <Input placeholder="Address" className="sm:col-span-2" required />
                    <Input placeholder="Apartment, suite, etc. (optional)" className="sm:col-span-2" />
                    <Input placeholder="City" required />
                    <Input placeholder="Postal code" required />
                    <Input placeholder="Country" required />
                    <Input placeholder="Phone" />
                </div>
            </div>

            <div>
                <h2 className="text-lg font-medium">Payment</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                    All transactions are secure and encrypted.
                </p>
                <div className="mt-4 rounded-md border p-4 bg-muted/50">
                    <p className="text-sm font-medium">Credit Card (Simulated)</p>
                    <div className="mt-4 space-y-4">
                        <Input placeholder="Card number" />
                        <div className="grid grid-cols-2 gap-4">
                            <Input placeholder="Expiration (MM/YY)" />
                            <Input placeholder="Security code" />
                        </div>
                        <Input placeholder="Name on card" />
                    </div>
                </div>
            </div>

            <Button type="submit" size="lg" className="w-full" isLoading={isLoading}>
                Pay Now
            </Button>
        </form>
    );
}
