import { CheckoutForm } from '@/components/checkout/CheckoutForm';
import { cartItems } from '@/lib/mock-data/cart';

export default function CheckoutPage() {
    const subtotal = cartItems.reduce((acc, item) => acc + (item.product.price * item.quantity), 0);
    const total = subtotal; // Free shipping

    return (
        <div className="container mx-auto px-4 py-8 md:py-12">
            <h1 className="mb-8 text-3xl font-bold tracking-tight text-center">Checkout</h1>

            <div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
                {/* Form */}
                <div>
                    <CheckoutForm />
                </div>

                {/* Order Summary (Sidebar on desktop) */}
                <div className="h-fit rounded-lg bg-muted/30 p-6 lg:sticky lg:top-24">
                    <h2 className="text-lg font-medium mb-4">Order Summary</h2>
                    <div className="space-y-4 divide-y">
                        {cartItems.map(item => (
                            <div key={item.id} className="flex gap-4 py-4 first:pt-0">
                                <div className="relative h-16 w-16 overflow-hidden rounded bg-background">
                                    {/* Image would go here, simplified for checkout view */}
                                    <div className="flex h-full w-full items-center justify-center text-xs text-muted-foreground">Img</div>
                                    <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                                        {item.quantity}
                                    </span>
                                </div>
                                <div className="flex flex-1 justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium">{item.product.title}</h3>
                                        <p className="text-xs text-muted-foreground">{item.product.vendor}</p>
                                    </div>
                                    <p className="text-sm font-medium">${(item.product.price * item.quantity).toFixed(2)}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="border-t pt-4 mt-4 space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>Subtotal</span>
                            <span>${subtotal.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Shipping</span>
                            <span>Free</span>
                        </div>
                        <div className="flex justify-between border-t pt-4 text-lg font-bold">
                            <span>Total</span>
                            <span>${total.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
