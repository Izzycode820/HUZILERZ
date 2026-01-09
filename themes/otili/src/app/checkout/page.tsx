import Link from 'next/link';
import Image from 'next/image';
import { CheckoutForm } from '@/components/checkout/CheckoutForm';
import { cartItems } from '@/lib/mock-data/cart';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

export default function CheckoutPage() {
    const subtotal = cartItems.reduce((acc, item) => acc + (item.product.price * item.quantity), 0);
    const total = subtotal; // Free shipping

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
            <Breadcrumbs
                items={[{ label: 'Cart', href: '/cart' }, { label: 'Checkout' }]}
                className="mb-8"
            />

            <h1 className="mb-8 text-3xl font-black tracking-tighter uppercase text-center md:text-left">Checkout</h1>

            <div className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:items-start">
                {/* Form */}
                <div className="lg:col-span-7">
                    <CheckoutForm />
                </div>

                {/* Order Summary (Sidebar on desktop) */}
                <div className="h-fit bg-muted/30 p-6 border border-border lg:col-span-5 lg:sticky lg:top-24">
                    <h2 className="text-lg font-bold mb-6 uppercase tracking-wide">Order Summary</h2>
                    <div className="space-y-4 divide-y divide-border">
                        {cartItems.map(item => (
                            <div key={item.id} className="flex gap-4 py-4 first:pt-0">
                                <div className="relative h-16 w-16 overflow-hidden bg-background border border-border">
                                    <Image
                                        src={item.product.images[0]?.url || '/placeholders/product.jpg'}
                                        alt={item.product.title}
                                        fill
                                        className="object-cover"
                                        unoptimized
                                    />
                                    <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-black text-xs text-white">
                                        {item.quantity}
                                    </span>
                                </div>
                                <div className="flex flex-1 justify-between">
                                    <div>
                                        <h3 className="text-sm font-semibold uppercase">{item.product.title}</h3>
                                        <p className="text-xs text-muted-foreground">{item.product.vendor}</p>
                                    </div>
                                    <p className="text-sm font-bold">${(item.product.price * item.quantity).toFixed(2)}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="border-t border-border pt-4 mt-4 space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Subtotal</span>
                            <span className="font-medium">${subtotal.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Shipping</span>
                            <span className="font-medium">Free</span>
                        </div>
                        <div className="flex justify-between border-t border-border pt-4 text-lg font-bold">
                            <span className="uppercase">Total</span>
                            <span>${total.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
