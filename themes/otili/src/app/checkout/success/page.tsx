import Link from 'next/link';
import { Check, ShoppingBag, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function CheckoutSuccessPage() {
    return (
        <div className="container mx-auto px-4 py-12 md:py-24 flex flex-col items-center justify-center min-h-[60vh] text-center">

            <div className="mb-8 relative">
                <div className="h-24 w-24 bg-green-500 rounded-none flex items-center justify-center animate-in zoom-in duration-300">
                    <Check className="h-12 w-12 text-white" />
                </div>
                {/* Decorative Elements */}
                <div className="absolute -top-4 -right-4 h-8 w-8 border-2 border-black" />
                <div className="absolute -bottom-4 -left-4 h-8 w-8 bg-black/10" />
            </div>

            <h1 className="text-4xl md:text-5xl font-black uppercase tracking-tighter mb-4">
                Order Confirmed!
            </h1>

            <p className="text-lg text-muted-foreground max-w-md mb-2">
                Thank you for your purchase. Your order <span className="font-bold text-foreground">#ORD-10293</span> has been received.
            </p>
            <p className="text-sm text-muted-foreground max-w-md mb-12">
                We've sent a confirmation email to your inbox with all the details.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 w-full max-w-sm">
                <Link href="/shop" className="w-full">
                    <Button className="w-full h-12 rounded-none uppercase font-bold tracking-wider group">
                        Continue Shopping
                        <ShoppingBag className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                </Link>
                <Link href="/account" className="w-full">
                    <Button variant="outline" className="w-full h-12 rounded-none uppercase font-bold tracking-wider group border-black hover:bg-black hover:text-white">
                        View Order
                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Button>
                </Link>
            </div>
        </div>
    );
}
