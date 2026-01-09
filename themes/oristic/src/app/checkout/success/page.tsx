import Link from 'next/link';
import { CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function CheckoutSuccessPage() {
    return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-600">
                <CheckCircle className="h-8 w-8" />
            </div>
            <h1 className="mt-8 text-3xl font-bold tracking-tight">Order Confirmed!</h1>
            <p className="mt-4 max-w-md text-muted-foreground">
                Thank you for your purchase. We have sent an email confirmation to your inbox.
                Your order number is #MERCH-10293.
            </p>
            <div className="mt-8 flex gap-4">
                <Link href="/">
                    <Button>Continue Shopping</Button>
                </Link>
                <Link href="/account/orders">
                    <Button variant="outline">View Order</Button>
                </Link>
            </div>
        </div>
    );
}
