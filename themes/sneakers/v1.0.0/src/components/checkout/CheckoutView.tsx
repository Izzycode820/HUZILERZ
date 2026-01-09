'use client';

import { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@apollo/client/react';
import { useSession } from '@/lib/session/SessionProvider';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { GetAvailableRegionsDocument } from '@/services/checkout/__generated__/get-available-regions.generated';
import { CreateCodOrderDocument } from '@/services/checkout/__generated__/create-cod-order.generated';
import { CreateWhatsappOrderDocument } from '@/services/checkout/__generated__/create-whatsapp-order.generated';
import { GetStoreSettingsDocument } from '@/services/settings/__generated__/get-store-settings.generated';
import { GetAvailablePaymentMethodsDocument } from '@/services/checkout/__generated__/get-available-payment-methods.generated';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/shadcn-ui/radio-group';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Loader2, CheckCircle2, MessageCircle, Tag, MapPin, Truck, ArrowLeft, CreditCard, Wallet } from 'lucide-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

// Fallback WhatsApp number if store settings not available
const FALLBACK_WHATSAPP_NUMBER = '237699999999';

// Cameroon regions (10 administrative regions + major cities)
const CAMEROON_REGIONS = [
    // Administrative Regions
    'Adamawa',
    'Centre',
    'East',
    'Far North',
    'Littoral',
    'North',
    'North-West',
    'South',
    'South-West',
    'West',
    // Major Cities
    'Douala',
    'Yaoundé',
    'Buea',
    'Bamenda',
    'Bafoussam',
    'Limbe',
    'Kribi',
    'Garoua',
    'Maroua',
    'Bertoua',
];

// Skeleton Components
function CheckoutSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl animate-pulse">
            <Skeleton className="h-4 w-32 mb-8" />
            <Skeleton className="h-10 w-48 mb-12" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                {/* Form Skeleton */}
                <div className="lg:col-span-7 space-y-12">
                    {/* Contact Section */}
                    <div className="space-y-6">
                        <Skeleton className="h-8 w-40" />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Skeleton className="h-4 w-20" />
                                <Skeleton className="h-10 w-full" />
                            </div>
                            <div className="space-y-2">
                                <Skeleton className="h-4 w-24" />
                                <Skeleton className="h-10 w-full" />
                            </div>
                            <div className="space-y-2 md:col-span-2">
                                <Skeleton className="h-4 w-16" />
                                <Skeleton className="h-10 w-full" />
                            </div>
                        </div>
                    </div>

                    {/* Shipping Section */}
                    <div className="space-y-6">
                        <Skeleton className="h-8 w-48" />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Skeleton className="h-4 w-28" />
                                <Skeleton className="h-10 w-full" />
                            </div>
                            <div className="space-y-2">
                                <Skeleton className="h-4 w-20" />
                                <Skeleton className="h-10 w-full" />
                            </div>
                        </div>
                    </div>

                    {/* Payment Section */}
                    <div className="space-y-6">
                        <Skeleton className="h-8 w-40" />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Skeleton className="h-24 w-full" />
                            <Skeleton className="h-24 w-full" />
                        </div>
                    </div>
                </div>

                {/* Summary Skeleton */}
                <div className="lg:col-span-5">
                    <div className="border border-border bg-card p-6">
                        <Skeleton className="h-6 w-32 mb-6" />
                        <div className="space-y-4 mb-6">
                            {[1, 2].map(i => (
                                <div key={i} className="flex gap-4">
                                    <Skeleton className="h-16 w-16" />
                                    <div className="flex-1 space-y-2">
                                        <Skeleton className="h-4 w-24" />
                                        <Skeleton className="h-3 w-16" />
                                    </div>
                                    <Skeleton className="h-4 w-16" />
                                </div>
                            ))}
                        </div>
                        <div className="space-y-3 border-t border-border pt-4">
                            <div className="flex justify-between">
                                <Skeleton className="h-4 w-16" />
                                <Skeleton className="h-4 w-20" />
                            </div>
                            <div className="flex justify-between">
                                <Skeleton className="h-4 w-20" />
                                <Skeleton className="h-4 w-20" />
                            </div>
                        </div>
                        <div className="border-t border-border pt-4 mt-4">
                            <div className="flex justify-between">
                                <Skeleton className="h-6 w-12" />
                                <Skeleton className="h-6 w-24" />
                            </div>
                        </div>
                        <Skeleton className="h-14 w-full mt-6" />
                    </div>
                </div>
            </div>
        </div>
    );
}

export function CheckoutView() {
    const { guestSessionId } = useSession();
    const [paymentMethod, setPaymentMethod] = useState<'whatsapp' | 'cod' | 'fapshi'>('whatsapp');
    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        email: '',
        customerRegion: '',  // Customer's location (Cameroon region)
        shippingRegion: '',  // Selected shipping zone (from available)
        address: '',
    });
    const [orderSuccess, setOrderSuccess] = useState<{
        id: string;
        orderNumber?: string | null;
        message?: string | null;
        whatsappLink?: string | null;
    } | null>(null);

    // Fetch Cart with discount data
    const { data: cartData, loading: cartLoading } = useQuery(GetCartDocument, {
        variables: { sessionId: guestSessionId || '' },
        skip: !guestSessionId,
        fetchPolicy: 'cache-first',
    });

    // Fetch store settings (WhatsApp number, etc.)
    const { data: storeSettingsData } = useQuery(GetStoreSettingsDocument, {
        fetchPolicy: 'cache-first',
    });

    // Fetch available shipping regions
    const { data: regionsData, loading: regionsLoading } = useQuery(GetAvailableRegionsDocument, {
        variables: { sessionId: guestSessionId || '' },
        skip: !guestSessionId,
    });

    // Fetch available payment methods
    const { data: paymentMethodsData } = useQuery(GetAvailablePaymentMethodsDocument, {
        fetchPolicy: 'cache-first',
    });

    const cart = cartData?.cart;
    const regions = regionsData?.availableShippingRegions?.regions || [];
    const storeSettings = storeSettingsData?.storeSettings;
    const storeWhatsAppNumber = storeSettings?.whatsappNumber || FALLBACK_WHATSAPP_NUMBER;
    const paymentMethods = paymentMethodsData?.availablePaymentMethods || [];
    const fapshiMethod = paymentMethods.find(m => m?.provider === 'fapshi');

    // Mutations
    const [createCodOrder, { loading: codLoading }] = useMutation(CreateCodOrderDocument);
    const [createWhatsappOrder, { loading: whatsappLoading }] = useMutation(CreateWhatsappOrderDocument);

    const loadingOrder = codLoading || whatsappLoading;

    // Calculate totals
    const totals = useMemo(() => {
        const subtotal = parseFloat(cart?.subtotal?.toString() || '0');
        const discountAmount = parseFloat(cart?.discountAmount?.toString() || '0');
        const cartTotal = parseFloat(cart?.total?.toString() || '0');
        const discountCode = cart?.discountCode;
        const hasDiscount = cart?.hasDiscount;

        // Find selected region
        const selectedRegion = regions.find(r => r?.name === formData.shippingRegion);
        const shippingCost = parseFloat(selectedRegion?.price?.toString() || '0');

        // Check if customer's region has a matching shipping zone (case-insensitive)
        const customerRegionLower = formData.customerRegion.toLowerCase();
        const hasShippingForCustomerRegion = regions.some(
            r => r?.name?.toLowerCase() === customerRegionLower
        );

        // Final total
        const finalTotal = cartTotal + shippingCost;

        return {
            subtotal,
            discountAmount,
            discountCode,
            hasDiscount,
            cartTotal,
            shippingCost,
            finalTotal,
            estimatedDays: selectedRegion?.estimatedDays,
            hasShippingForCustomerRegion,
        };
    }, [cart, regions, formData.shippingRegion, formData.customerRegion]);

    // Format currency
    const formatPrice = (amount: number) => {
        return new Intl.NumberFormat('fr-CM', {
            style: 'currency',
            currency: 'XAF',
            minimumFractionDigits: 0,
        }).format(amount);
    };

    // Handlers
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!guestSessionId) {
            toast.error('Session expired. Please refresh the page.');
            return;
        }

        if (!formData.name.trim()) {
            toast.error('Please enter your name');
            return;
        }

        if (!formData.phone.trim()) {
            toast.error('Please enter your phone number');
            return;
        }

        if (!formData.customerRegion) {
            toast.error('Please select your location');
            return;
        }

        if (!formData.shippingRegion) {
            toast.error('Please select a shipping region');
            return;
        }

        const customerInfo = {
            name: formData.name.trim(),
            phone: formData.phone.trim(),
            email: formData.email.trim() || undefined,
            address: formData.address.trim() || undefined,
            region: formData.customerRegion,  // Include customer region
        };

        try {
            if (paymentMethod === 'whatsapp') {
                const { data } = await createWhatsappOrder({
                    variables: {
                        sessionId: guestSessionId,
                        whatsappNumber: storeWhatsAppNumber,
                        customerInfo,
                        shippingRegion: formData.shippingRegion,
                    }
                });

                const result = data?.createWhatsappOrder;

                if (result?.success && result.whatsappLink) {
                    toast.success('Order created! Redirecting to WhatsApp...');
                    setOrderSuccess({
                        id: result.orderId || '',
                        orderNumber: result.orderNumber,
                        message: result.message,
                        whatsappLink: result.whatsappLink,
                    });
                    // Small delay before redirect
                    setTimeout(() => {
                        window.location.href = result.whatsappLink!;
                    }, 1500);
                } else {
                    toast.error(result?.error || 'Failed to create order');
                }
            } else if (paymentMethod === 'fapshi') {
                // Fapshi Mobile Money - redirect to checkout URL
                if (!fapshiMethod?.checkoutUrl) {
                    toast.error('Mobile Money payment not available');
                    return;
                }

                // Build the checkout URL with order info as query params
                const checkoutUrl = new URL(fapshiMethod.checkoutUrl);
                checkoutUrl.searchParams.set('amount', totals.finalTotal.toString());
                checkoutUrl.searchParams.set('name', customerInfo.name);
                checkoutUrl.searchParams.set('phone', customerInfo.phone);
                if (customerInfo.email) {
                    checkoutUrl.searchParams.set('email', customerInfo.email);
                }
                checkoutUrl.searchParams.set('message', `Order from ${storeSettings?.storeName || 'Store'}`);

                toast.success('Redirecting to payment...');
                // Redirect to Fapshi checkout
                window.location.href = checkoutUrl.toString();
            } else {
                // COD
                const { data } = await createCodOrder({
                    variables: {
                        sessionId: guestSessionId,
                        customerInfo,
                        shippingRegion: formData.shippingRegion,
                    }
                });

                const result = data?.createCodOrder;

                if (result?.success) {
                    toast.success('Order placed successfully!');
                    setOrderSuccess({
                        id: result.orderId || '',
                        orderNumber: result.orderNumber,
                        message: result.message,
                    });
                } else {
                    toast.error(result?.error || 'Failed to place order');
                }
            }
        } catch (err: any) {
            console.error('Checkout error:', err);
            toast.error(err.message || 'An error occurred during checkout');
        }
    };

    // --- Render States ---

    // Order Success
    if (orderSuccess) {
        return (
            <div className="container mx-auto px-4 py-20 min-h-[60vh] flex flex-col items-center justify-center text-center max-w-md">
                <div className="bg-green-100 p-4 rounded-full mb-6">
                    <CheckCircle2 className="h-12 w-12 text-green-600" />
                </div>
                <h1 className="text-3xl font-black uppercase tracking-tighter mb-2">Order Placed!</h1>
                <p className="text-muted-foreground mb-2">
                    Order #{orderSuccess.orderNumber || orderSuccess.id}
                </p>
                {orderSuccess.message && (
                    <p className="text-sm text-muted-foreground mb-8">{orderSuccess.message}</p>
                )}
                {orderSuccess.whatsappLink && (
                    <p className="text-sm text-green-600 mb-8">Redirecting to WhatsApp...</p>
                )}
                <div className="flex gap-4 w-full">
                    <Button asChild variant="outline" className="flex-1 rounded-none">
                        <Link href="/products">Continue Shopping</Link>
                    </Button>
                </div>
            </div>
        );
    }

    // Loading State
    if (cartLoading && !cart) {
        return <CheckoutSkeleton />;
    }

    // Empty Cart
    if (!cart || !cart.items || cart.items.length === 0) {
        return (
            <div className="container mx-auto px-4 py-20 min-h-[50vh] flex flex-col items-center justify-center text-center gap-6">
                <h1 className="text-3xl font-black uppercase tracking-tighter">Your Cart is Empty</h1>
                <p className="text-muted-foreground">Add some items before checking out.</p>
                <Button asChild size="lg" className="rounded-none uppercase font-bold tracking-wide">
                    <Link href="/products">Browse Products</Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
            <Breadcrumbs
                items={[
                    { label: 'Cart', href: '/cart' },
                    { label: 'Checkout' }
                ]}
                className="mb-8"
            />

            <div className="flex items-center gap-4 mb-12">
                <Link href="/cart" className="text-muted-foreground hover:text-foreground transition-colors">
                    <ArrowLeft className="h-5 w-5" />
                </Link>
                <h1 className="text-3xl md:text-4xl font-black uppercase tracking-tighter">
                    Checkout
                </h1>
            </div>

            <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">

                    {/* Form Section */}
                    <div className="lg:col-span-7 space-y-12">

                        {/* 1. Contact Info */}
                        <div className="space-y-6">
                            <h2 className="text-xl font-black uppercase tracking-wide border-b border-border pb-2">
                                1. Contact Information
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name" className="text-sm font-medium">Full Name *</Label>
                                    <Input
                                        id="name"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleInputChange}
                                        placeholder="John Doe"
                                        className="rounded-none"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="phone" className="text-sm font-medium">Phone Number *</Label>
                                    <Input
                                        id="phone"
                                        name="phone"
                                        value={formData.phone}
                                        onChange={handleInputChange}
                                        placeholder="677 000 000"
                                        className="rounded-none"
                                        required
                                    />
                                </div>
                                <div className="space-y-2 md:col-span-2">
                                    <Label htmlFor="email" className="text-sm font-medium">Email (Optional)</Label>
                                    <Input
                                        id="email"
                                        name="email"
                                        type="email"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                        placeholder="john@example.com"
                                        className="rounded-none"
                                    />
                                </div>
                                <div className="space-y-3 md:col-span-2">
                                    <Label className="text-sm font-medium flex items-center gap-2">
                                        <MapPin className="h-4 w-4" />
                                        Your Location *
                                    </Label>
                                    <div className="flex flex-wrap gap-2">
                                        {CAMEROON_REGIONS.map(region => (
                                            <button
                                                key={region}
                                                type="button"
                                                onClick={() => setFormData(prev => ({ ...prev, customerRegion: region }))}
                                                className={cn(
                                                    "px-3 py-1.5 text-xs font-medium border transition-all",
                                                    formData.customerRegion === region
                                                        ? "border-foreground bg-foreground text-background"
                                                        : "border-border bg-background hover:border-foreground/50"
                                                )}
                                            >
                                                {region}
                                            </button>
                                        ))}
                                    </div>
                                    {/* Warning when customer region has no shipping rate */}
                                    {formData.customerRegion && !totals.hasShippingForCustomerRegion && (
                                        <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 border border-amber-200">
                                            ⚠️ Shipping to {formData.customerRegion} not available. Different rates may apply.
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* 2. Shipping */}
                        <div className="space-y-6">
                            <h2 className="text-xl font-black uppercase tracking-wide border-b border-border pb-2">
                                2. Shipping
                            </h2>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="shippingRegion" className="text-sm font-medium flex items-center gap-2">
                                        <MapPin className="h-4 w-4" />
                                        Delivery Region *
                                    </Label>
                                    {regionsLoading ? (
                                        <Skeleton className="h-12 w-full" />
                                    ) : regions.length > 0 ? (
                                        <select
                                            id="shippingRegion"
                                            name="shippingRegion"
                                            value={formData.shippingRegion}
                                            onChange={handleInputChange}
                                            className="w-full h-12 md:h-10 px-3 border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring appearance-none cursor-pointer"
                                            required
                                            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.75rem center', backgroundSize: '1rem' }}
                                        >
                                            <option value="">Select delivery zone</option>
                                            {regions.map(region => region && (
                                                <option key={region.name} value={region.name}>
                                                    {region.name} — {formatPrice(region.price || 0)} ({region.estimatedDays})
                                                </option>
                                            ))}
                                        </select>
                                    ) : (
                                        <p className="text-sm text-muted-foreground">
                                            No shipping regions available for your cart items.
                                        </p>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="address" className="text-sm font-medium">
                                        Delivery Address (Optional)
                                    </Label>
                                    <Input
                                        id="address"
                                        name="address"
                                        value={formData.address}
                                        onChange={handleInputChange}
                                        placeholder="e.g. Bastos, near Total station"
                                        className="rounded-none"
                                    />
                                </div>
                            </div>

                            {/* Shipping Info */}
                            {formData.shippingRegion && totals.estimatedDays && (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 p-3">
                                    <Truck className="h-4 w-4" />
                                    <span>Estimated delivery: {totals.estimatedDays}</span>
                                </div>
                            )}
                        </div>

                        {/* 3. Payment Method */}
                        <div className="space-y-6">
                            <h2 className="text-xl font-black uppercase tracking-wide border-b border-border pb-2">
                                3. Payment Method
                            </h2>
                            <RadioGroup
                                value={paymentMethod}
                                onValueChange={(val: 'whatsapp' | 'cod' | 'fapshi') => setPaymentMethod(val)}
                                className="grid grid-cols-1 md:grid-cols-2 gap-4"
                            >
                                <Label
                                    htmlFor="pm-whatsapp"
                                    className={cn(
                                        "flex flex-col gap-2 border-2 p-4 cursor-pointer transition-all",
                                        paymentMethod === 'whatsapp'
                                            ? "border-foreground bg-accent"
                                            : "border-border hover:border-foreground/50"
                                    )}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-bold flex items-center gap-2">
                                            <MessageCircle className="h-5 w-5 text-green-600" />
                                            WhatsApp Order
                                        </span>
                                        <RadioGroupItem value="whatsapp" id="pm-whatsapp" />
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Confirm your order via WhatsApp chat.
                                    </p>
                                </Label>

                                <Label
                                    htmlFor="pm-cod"
                                    className={cn(
                                        "flex flex-col gap-2 border-2 p-4 cursor-pointer transition-all",
                                        paymentMethod === 'cod'
                                            ? "border-foreground bg-accent"
                                            : "border-border hover:border-foreground/50"
                                    )}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-bold flex items-center gap-2">
                                            <Wallet className="h-5 w-5" />
                                            Cash on Delivery
                                        </span>
                                        <RadioGroupItem value="cod" id="pm-cod" />
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Pay when you receive your order.
                                    </p>
                                </Label>

                                {/* Fapshi Mobile Money - only show if enabled */}
                                {fapshiMethod && (
                                    <Label
                                        htmlFor="pm-fapshi"
                                        className={cn(
                                            "flex flex-col gap-2 border-2 p-4 cursor-pointer transition-all md:col-span-2",
                                            paymentMethod === 'fapshi'
                                                ? "border-foreground bg-accent"
                                                : "border-border hover:border-foreground/50"
                                        )}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="font-bold flex items-center gap-2">
                                                <CreditCard className="h-5 w-5 text-orange-500" />
                                                {fapshiMethod.displayName || 'Mobile Money'}
                                            </span>
                                            <RadioGroupItem value="fapshi" id="pm-fapshi" />
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            {fapshiMethod.description || 'Pay with MTN MoMo or Orange Money'}
                                        </p>
                                    </Label>
                                )}
                            </RadioGroup>
                        </div>
                    </div>

                    {/* Order Summary */}
                    <div className="lg:col-span-5">
                        <div className="border border-border bg-card p-6 sticky top-24">
                            <h3 className="text-xl font-black uppercase tracking-wide mb-6">Order Summary</h3>

                            {/* Cart Items */}
                            <div className="space-y-4 mb-6 max-h-[300px] overflow-y-auto">
                                {cart.items?.map((item) => {
                                    if (!item || !item.product) return null;
                                    return (
                                        <div key={item.id} className="flex gap-3">
                                            <div className="relative h-16 w-16 flex-none bg-muted overflow-hidden">
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
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{item.product.name}</p>
                                                <p className="text-xs text-muted-foreground">Qty: {item.quantity}</p>
                                                {item.variant?.option1 && (
                                                    <p className="text-xs text-muted-foreground">
                                                        {[item.variant.option1, item.variant.option2].filter(Boolean).join(' / ')}
                                                    </p>
                                                )}
                                            </div>
                                            <p className="text-sm font-medium">
                                                {item.totalPrice ? formatPrice(item.totalPrice) : '-'}
                                            </p>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Totals */}
                            <div className="space-y-3 border-t border-border pt-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Subtotal</span>
                                    <span className="font-medium">{formatPrice(totals.subtotal)}</span>
                                </div>

                                {/* Discount */}
                                {totals.hasDiscount && totals.discountCode && (
                                    <div className="flex justify-between text-sm">
                                        <span className="flex items-center gap-2 text-green-600">
                                            <Tag className="h-3 w-3" />
                                            {totals.discountCode}
                                        </span>
                                        <span className="font-medium text-green-600">
                                            -{formatPrice(totals.discountAmount)}
                                        </span>
                                    </div>
                                )}

                                {/* Shipping */}
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Shipping</span>
                                    {formData.shippingRegion ? (
                                        <span className="font-medium">{formatPrice(totals.shippingCost)}</span>
                                    ) : (
                                        <span className="text-xs italic">Select region</span>
                                    )}
                                </div>
                            </div>

                            {/* Total */}
                            <div className="border-t border-border pt-4 mt-4">
                                <div className="flex justify-between items-center text-lg font-bold">
                                    <span>Total</span>
                                    <span>{formatPrice(totals.finalTotal)}</span>
                                </div>
                            </div>

                            {/* Submit Button */}
                            <Button
                                type="submit"
                                size="lg"
                                className="w-full h-14 mt-6 text-base font-bold uppercase tracking-wide rounded-none"
                                disabled={loadingOrder || !formData.shippingRegion}
                            >
                                {loadingOrder ? (
                                    <>
                                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                        Processing...
                                    </>
                                ) : paymentMethod === 'whatsapp' ? (
                                    <>
                                        <MessageCircle className="mr-2 h-5 w-5" />
                                        Order on WhatsApp
                                    </>
                                ) : (
                                    'Place Order'
                                )}
                            </Button>

                            <p className="mt-4 text-xs text-center text-muted-foreground">
                                By placing your order, you agree to our Terms of Service.
                            </p>

                            {/* Back to Cart */}
                            <div className="mt-4 text-center">
                                <Link
                                    href="/cart"
                                    className="text-sm font-medium text-muted-foreground hover:text-foreground underline transition-colors"
                                >
                                    ← Back to Cart
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    );
}
