import { cartItems } from '@/lib/mock-data/cart';
import { CartItem } from '@/components/cart/CartItem';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

export default function CartPage() {
    const subtotal = cartItems.reduce((acc, item) => acc + (item.product.price * item.quantity), 0);

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
            <Breadcrumbs
                items={[{ label: 'Shopping Cart' }]}
                className="mb-8"
            />

            <h1 className="mb-8 text-3xl font-black uppercase tracking-tighter">Your Bag</h1>

            <div className="flex flex-col gap-12 lg:flex-row lg:items-start">
                <div className="flex-1">
                    {cartItems.length > 0 ? (
                        <div className="divide-y divide-border">
                            {cartItems.map((item) => (
                                <CartItem key={item.id} item={item} />
                            ))}
                        </div>
                    ) : (
                        <p className="py-12 text-center text-muted-foreground">Your cart is empty.</p>
                    )}
                </div>

                <div className="w-full lg:w-96">
                    <OrderSummary subtotal={subtotal} />
                </div>
            </div>
        </div>
    );
}
