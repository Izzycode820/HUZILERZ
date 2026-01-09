import Link from 'next/link';
import { Button } from '../ui/Button';

export function OrderSummary({ subtotal }: { subtotal: number }) {
    const shipping = 0; // Free for now
    const total = subtotal + shipping;

    return (
        <div className="rounded-lg bg-muted/50 p-6 md:p-8">
            <h2 className="text-lg font-medium">Order Summary</h2>

            <div className="mt-6 space-y-4">
                <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span>{shipping === 0 ? 'Free' : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className="flex justify-between border-t py-4 text-base font-medium">
                    <span>Total</span>
                    <span>${total.toFixed(2)}</span>
                </div>
            </div>

            <Link href="/checkout" className="block w-full">
                <Button size="lg" className="w-full mt-6">
                    Proceed to Checkout
                </Button>
            </Link>
        </div>
    );
}
