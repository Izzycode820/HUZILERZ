import Link from 'next/link';
import { Button } from '../ui/Button';

export function OrderSummary({ subtotal }: { subtotal: number }) {
    const shipping: number = 0; // Free for now
    const total = subtotal + shipping;

    return (
        <div className="bg-muted/30 p-6 md:p-8 border border-border">
            <h2 className="text-lg font-bold uppercase tracking-wide">Order Summary</h2>

            <div className="mt-6 space-y-4">
                <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="font-medium">${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className="font-medium">{shipping === 0 ? 'Free' : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className="pt-4 border-t border-border">
                    <div className="flex justify-between items-baseline">
                        <span className="text-base font-bold uppercase">Total</span>
                        <span className="text-xl font-bold">${total.toFixed(2)}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">Taxes calculated at checkout</p>
                </div>
            </div>

            <Link href="/checkout" className="block w-full mt-8">
                <Button size="lg" className="w-full h-12 rounded-none bg-black text-white hover:bg-black/90 uppercase tracking-widest font-bold text-sm">
                    Proceed to Checkout
                </Button>
            </Link>
        </div>
    );
}
