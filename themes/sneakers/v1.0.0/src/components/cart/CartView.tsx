'use client';

import { useCallback, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useQuery, useMutation } from '@apollo/client/react';
import { useSession } from '@/lib/session/SessionProvider';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { RemoveFromCartDocument } from '@/services/cart/__generated__/remove-from-cart.generated';
import { UpdateCartItemDocument } from '@/services/cart/__generated__/update-cart-item.generated';
import { ApplyDiscountToCartDocument } from '@/services/discounts/__generated__/apply-discount.generated';
import { RemoveDiscountFromCartDocument } from '@/services/discounts/__generated__/remove-discount.generated';
import { Button } from '@/components/shadcn-ui/button';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Loader2, Trash2, Minus, Plus, ArrowRight, X, Tag } from 'lucide-react';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { toast } from 'sonner';

// Cart Skeleton Component
function CartSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
            <Skeleton className="h-4 w-32 mb-8" />
            <Skeleton className="h-10 w-40 mb-8" />

            <div className="flex flex-col gap-12 lg:flex-row lg:items-start">
                {/* Cart Items Skeleton */}
                <div className="flex-1">
                    <div className="divide-y divide-border">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex gap-4 py-6">
                                <Skeleton className="h-28 w-24 flex-none" />
                                <div className="flex-1 space-y-3">
                                    <Skeleton className="h-5 w-32" />
                                    <Skeleton className="h-4 w-20" />
                                    <Skeleton className="h-4 w-24" />
                                    <div className="flex items-center gap-4 mt-4">
                                        <Skeleton className="h-8 w-24" />
                                        <Skeleton className="h-8 w-20" />
                                    </div>
                                </div>
                                <Skeleton className="h-5 w-16" />
                            </div>
                        ))}
                    </div>
                </div>

                {/* Summary Skeleton */}
                <div className="w-full lg:w-96">
                    <div className="border border-border bg-card p-6">
                        <Skeleton className="h-6 w-32 mb-6" />
                        <div className="space-y-4 pb-4">
                            <div className="flex justify-between">
                                <Skeleton className="h-4 w-16" />
                                <Skeleton className="h-4 w-20" />
                            </div>
                            <div className="flex justify-between">
                                <Skeleton className="h-4 w-20" />
                                <Skeleton className="h-4 w-24" />
                            </div>
                        </div>
                        <div className="py-4 border-t border-border">
                            <Skeleton className="h-4 w-24 mb-2" />
                            <div className="flex gap-2">
                                <Skeleton className="h-10 flex-1" />
                                <Skeleton className="h-10 w-16" />
                            </div>
                        </div>
                        <div className="py-4 border-t border-border">
                            <div className="flex justify-between">
                                <Skeleton className="h-5 w-12" />
                                <Skeleton className="h-5 w-20" />
                            </div>
                        </div>
                        <Skeleton className="h-12 w-full mt-6" />
                        <Skeleton className="h-4 w-32 mx-auto mt-4" />
                    </div>
                </div>
            </div>
        </div>
    );
}

// Debounce utility to prevent spam
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout | null = null;
    return function executedFunction(...args: Parameters<T>) {
        const later = () => {
            timeout = null;
            func(...args);
        };
        if (timeout) clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

export function CartView() {
    const { guestSessionId } = useSession();
    const [discountCode, setDiscountCode] = useState('');

    // Fetch Cart
    const { data, loading, refetch } = useQuery(GetCartDocument, {
        variables: { sessionId: guestSessionId || '' },
        skip: !guestSessionId,
        fetchPolicy: 'network-only',
    });

    // Mutations - removeItem uses refetch (infrequent action), updateItem uses cache (frequent)
    const [removeItem, { loading: removing }] = useMutation(RemoveFromCartDocument, {
        refetchQueries: [{ query: GetCartDocument, variables: { sessionId: guestSessionId || '' } }],
        awaitRefetchQueries: true
    });

    // Discount mutations - use refetch for immediate visibility
    const [applyDiscount, { loading: applyingDiscount }] = useMutation(ApplyDiscountToCartDocument, {
        refetchQueries: [{ query: GetCartDocument, variables: { sessionId: guestSessionId || '' } }],
        awaitRefetchQueries: true
    });

    const [removeDiscount, { loading: removingDiscount }] = useMutation(RemoveDiscountFromCartDocument, {
        refetchQueries: [{ query: GetCartDocument, variables: { sessionId: guestSessionId || '' } }],
        awaitRefetchQueries: true
    });

    const [updateItemMutation] = useMutation(UpdateCartItemDocument, {
        // Update cache directly after mutation completes - still very fast!
        update: (cache, { data }) => {
            if (data?.updateCartItem?.cart) {
                // Merge the updated cart data into cache
                const newCart = data.updateCartItem.cart;

                cache.writeQuery({
                    query: GetCartDocument,
                    variables: { sessionId: guestSessionId || '' },
                    data: {
                        __typename: 'Query',
                        cart: {
                            ...newCart,
                            // Preserve fields from GetCart that aren't in UpdateCartItem
                            items: newCart.items?.map((item, idx) => {
                                const existingItem = cart?.items?.[idx];
                                return item ? {
                                    ...item,
                                    product: item.product ? {
                                        ...item.product,
                                        // Preserve mediaUploads from existing cache
                                        mediaUploads: existingItem?.product?.mediaUploads || null
                                    } : null
                                } : null;
                            }) || null
                        }
                    }
                });
            }
        }
    });

    // Debounce to prevent spam when user clicks rapidly
    const updateItemDebounced = useCallback(
        debounce((productId: string, variantId: string | null | undefined, quantity: number) => {
            if (!guestSessionId) return;
            updateItemMutation({
                variables: {
                    input: {
                        sessionId: guestSessionId,
                        productId,
                        quantity,
                        variantId: variantId || undefined
                    }
                }
            });
        }, 300), // Wait 300ms after last click before sending request
        [guestSessionId, updateItemMutation]
    );

    const cart = data?.cart;
    const isEmpty = !guestSessionId || !cart || !cart.items || cart.items.length === 0;

    // Handlers
    const handleRemove = async (productId: string, variantId?: string | null) => {
        if (!guestSessionId) return;
        await removeItem({
            variables: {
                input: {
                    sessionId: guestSessionId,
                    productId: productId,
                    variantId: variantId || undefined
                }
            }
        });
    };

    const handleUpdateQuantity = (productId: string, variantId: string | null | undefined, currentQty: number, delta: number) => {
        const newQty = currentQty + delta;
        if (newQty < 1) return; // Prevent going below 1

        // Call debounced mutation - batches rapid clicks
        updateItemDebounced(productId, variantId, newQty);
    };

    const handleApplyDiscount = async () => {
        if (!guestSessionId || !discountCode.trim()) return;

        const result = await applyDiscount({
            variables: {
                input: {
                    sessionId: guestSessionId,
                    discountCode: discountCode.trim()
                }
            }
        });

        const response = result.data?.applyDiscountToCart;

        if (response?.success) {
            toast.success(response.message || 'Discount applied successfully!');
            setDiscountCode(''); // Clear input on success
        } else if (response?.error) {
            toast.error(response.error);
        }
    };

    const handleRemoveDiscount = async () => {
        if (!guestSessionId) return;

        const result = await removeDiscount({
            variables: {
                input: {
                    sessionId: guestSessionId
                }
            }
        });

        const response = result.data?.removeDiscountFromCart;

        if (response?.success) {
            toast.success(response.message || 'Discount removed');
        } else if (response?.error) {
            toast.error(response.error);
        }
    };

    // Format currency
    const formatPrice = (amount: number | string) => {
        const num = typeof amount === 'string' ? parseFloat(amount) : amount;
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'XAF',
        }).format(num);
    };

    if (loading && !cart) {
        return <CartSkeleton />;
    }

    if (isEmpty) {
        return (
            <div className="container mx-auto px-4 py-20 min-h-[50vh] flex flex-col items-center justify-center text-center gap-6">
                <h1 className="text-3xl font-black uppercase tracking-tighter">Your Cart is Empty</h1>
                <p className="text-muted-foreground">Looks like you haven't added anything yet.</p>
                <Button asChild size="lg" className="rounded-none uppercase font-bold tracking-wide">
                    <Link href="/products">
                        Continue Shopping
                    </Link>
                </Button>
            </div>
        );
    }

    const subtotal = parseFloat(cart?.subtotal?.toString() || '0');
    const discountAmount = parseFloat(cart?.discountAmount?.toString() || '0');
    const total = parseFloat(cart?.total?.toString() || '0');

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
            <Breadcrumbs
                items={[{ label: 'Shopping Cart' }]}
                className="mb-8"
            />

            <h1 className="mb-8 text-3xl font-black uppercase tracking-tighter">Your Bag</h1>

            <div className="flex flex-col gap-12 lg:flex-row lg:items-start">
                {/* Cart Items */}
                <div className="flex-1">
                    <div className="divide-y divide-border">
                        {cart?.items?.map((item) => {
                            if (!item || !item.product) return null;
                            return (
                                <div key={item.id} className="flex gap-4 py-6 border-b border-border last:border-0">
                                    {/* Product Image */}
                                    <div className="relative h-28 w-24 flex-none overflow-hidden bg-muted">
                                        {item.product.mediaUploads?.[0]?.thumbnailWebp && (
                                            <Image
                                                src={item.product.mediaUploads[0].thumbnailWebp}
                                                alt={item.product.name}
                                                fill
                                                className="object-cover"
                                                unoptimized
                                            />
                                        )}
                                    </div>

                                    {/* Product Details */}
                                    <div className="flex flex-1 flex-col justify-between">
                                        <div className="flex justify-between gap-4">
                                            <div>
                                                <h3 className="text-base font-semibold uppercase tracking-wide">
                                                    {item.product.name}
                                                </h3>
                                                <p className="mt-1 text-sm text-muted-foreground">
                                                    {item.product.price ? formatPrice(item.product.price) : '-'}
                                                </p>
                                                {/* Variant Options */}
                                                {(item.variant?.option1 || item.variant?.option2) && (
                                                    <p className="mt-1 text-xs text-muted-foreground uppercase">
                                                        {[item.variant.option1, item.variant.option2, item.variant.option3]
                                                            .filter(Boolean)
                                                            .join(' / ')}
                                                    </p>
                                                )}
                                            </div>
                                            <p className="text-sm font-bold">
                                                {item.totalPrice ? formatPrice(item.totalPrice) : '-'}
                                            </p>
                                        </div>

                                        {/* Quantity & Remove */}
                                        <div className="flex items-center justify-between mt-4">
                                            <div className="flex items-center gap-4">
                                                <div className="flex items-center border border-border">
                                                    <button
                                                        onClick={() => handleUpdateQuantity(item.product!.id, item.variant?.id, item.quantity, -1)}
                                                        disabled={item.quantity <= 1}
                                                        className="p-2 hover:bg-accent transition-colors disabled:opacity-50"
                                                    >
                                                        <Minus className="h-3 w-3" />
                                                    </button>
                                                    <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                                                    <button
                                                        onClick={() => handleUpdateQuantity(item.product!.id, item.variant?.id, item.quantity, 1)}
                                                        className="p-2 hover:bg-accent transition-colors"
                                                    >
                                                        <Plus className="h-3 w-3" />
                                                    </button>
                                                </div>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleRemove(item.product!.id, item.variant?.id)}
                                                disabled={removing}
                                                className="text-destructive hover:text-destructive"
                                            >
                                                <Trash2 className="mr-2 h-4 w-4" /> Remove
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Order Summary */}
                <div className="w-full lg:w-96">
                    <div className="border border-border bg-card p-6">
                        <h2 className="mb-6 text-xl font-black uppercase tracking-wide">Order Summary</h2>

                        <div className="space-y-4 border-b border-border pb-4">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Subtotal</span>
                                <span className="font-medium">{formatPrice(subtotal)}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Shipping</span>
                                <span className="text-sm">Calculated at checkout</span>
                            </div>
                        </div>

                        {/* Discount Section */}
                        <div className="py-4 border-b border-border">
                            {cart?.hasDiscount ? (
                                // Show applied discount
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <div className="flex items-center gap-2">
                                            <Tag className="h-4 w-4 text-green-600" />
                                            <span className="font-medium text-green-600">
                                                {cart.discountCode}
                                            </span>
                                        </div>
                                        <button
                                            onClick={handleRemoveDiscount}
                                            disabled={removingDiscount}
                                            className="text-muted-foreground hover:text-foreground disabled:opacity-50"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Discount</span>
                                        <span className="font-medium text-green-600">-{formatPrice(discountAmount)}</span>
                                    </div>
                                </div>
                            ) : (
                                // Show discount input
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Discount Code</label>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={discountCode}
                                            onChange={(e) => setDiscountCode(e.target.value.toUpperCase())}
                                            onKeyDown={(e) => e.key === 'Enter' && handleApplyDiscount()}
                                            placeholder="ENTER CODE"
                                            className="flex-1 px-3 py-2 text-sm border border-border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                                            disabled={applyingDiscount}
                                        />
                                        <Button
                                            onClick={handleApplyDiscount}
                                            disabled={applyingDiscount || !discountCode.trim()}
                                            size="sm"
                                            className="rounded-none uppercase font-bold px-4"
                                        >
                                            {applyingDiscount ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Apply'}
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="py-4 border-b border-border">
                            <div className="flex justify-between text-base font-bold">
                                <span>Total</span>
                                <span>{formatPrice(total)}</span>
                            </div>
                        </div>

                        <Button className="mt-6 w-full rounded-none uppercase font-bold tracking-wide h-12" asChild>
                            <Link href="/checkout">
                                Checkout <ArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                        </Button>

                        <div className="mt-4 text-center">
                            <Link href="/products" className="text-sm font-medium text-muted-foreground hover:text-foreground underline transition-colors">
                                Continue Shopping
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
