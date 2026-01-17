'use client';

import { useQuery } from '@apollo/client/react';
import { Navigate } from 'react-router-dom';
import { GetProductDetailsDocument } from '@/services/products/__generated__/get-product-details.generated';
import { ProductGallery } from './ProductGallery';
import { ProductInfo } from './ProductInfo';
import { RelatedProducts } from './RelatedProducts';
import { MobileStickyBar } from './MobileStickyBar';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

import { useState } from 'react';
import { useSession } from '@/lib/session/SessionProvider';
import { useMutation } from '@apollo/client/react';
import { AddToCartDocument } from '@/services/cart/__generated__/add-to-cart.generated';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { triggerFlyToCartAnimation } from '@/lib/animations/flyToCart';
import { GetProductDetailsQuery } from '@/services/products/__generated__/get-product-details.generated';

interface ProductViewProps {
    slug: string;
}

type ProductType = NonNullable<GetProductDetailsQuery['product']>;

export function ProductView({ slug }: ProductViewProps) {
    // ALL HOOKS MUST BE AT THE TOP - before any conditional returns
    // State for variant selection only (animation is now pure DOM)
    const [selectedVariant, setSelectedVariant] = useState<any | null>(null);

    // Cart Logic - Optimistic UI for instant feedback
    const { guestSessionId, createGuestSession } = useSession();
    const [addToCart, { loading: adding }] = useMutation(AddToCartDocument, {
        optimisticResponse: (variables) => ({
            __typename: 'Mutation' as const,
            addToCart: {
                __typename: 'AddToCart' as const,
                cart: {
                    __typename: 'CartType' as const,
                    id: guestSessionId || 'temp-cart-id',
                    subtotal: '0',
                    discountCode: null,
                    discountAmount: null,
                    total: null,
                    hasDiscount: null,
                    appliedDiscount: null,
                    itemCount: null,
                    items: null
                }
            }
        }),
        update: (cache, { data }) => {
            if (data?.addToCart?.cart) {
                cache.writeQuery({
                    query: GetCartDocument,
                    variables: { sessionId: guestSessionId || '' },
                    data: {
                        __typename: 'Query',
                        cart: data.addToCart.cart
                    }
                });
            }
        },
        onError: (err) => {
            alert("Failed to add to cart: " + err.message);
        }
    });

    // Query AFTER hooks
    const { data, loading, error } = useQuery(GetProductDetailsDocument, {
        variables: { productSlug: slug },
    });

    // NOW we can do conditional returns
    if (loading) {
        return (
            <div className="container mx-auto px-4 py-20 min-h-[60vh] flex items-center justify-center">
                <div className="animate-pulse space-y-4 text-center">
                    <div className="h-8 w-48 bg-gray-200 mx-auto" />
                    <div className="text-muted-foreground">Loading product...</div>
                </div>
            </div>
        );
    }

    if (error || !data?.product) {
        return (
            <div className="container mx-auto px-4 py-20 text-center">
                <h1 className="text-2xl font-bold">Product not found</h1>
                <p className="text-muted-foreground">We couldn't find the product you're looking for.</p>
            </div>
        );
    }

    const { product } = data;

    // Initialize selectedVariant after we have product data
    if (!selectedVariant && product.variants && product.variants.length > 0) {
        setSelectedVariant(product.variants[0]);
    }

    const handleAddToCart = async (startPos: { x: number; y: number }) => {
        // Trigger animation immediately (pure DOM - no React state)
        triggerFlyToCartAnimation(startPos.x, startPos.y);

        try {
            let sessionId = guestSessionId;
            if (!sessionId) {
                sessionId = await createGuestSession();
            }

            if (!sessionId) {
                return;
            }

            const variantId = selectedVariant?.id || product.variants?.[0]?.id;

            await addToCart({
                variables: {
                    input: {
                        sessionId,
                        productId: product.id,
                        quantity: 1,
                        variantId: variantId || undefined,
                    }
                }
            });
        } catch (e) {
            console.error(e);
        }
    };

    const breadcrumbs = [
        { label: 'Shop', href: '/products' },
        ...(product.category ? [{ label: product.category.name, href: `/collections/${product.category.slug}` }] : []),
        { label: product.name },
    ];

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 pb-24 md:pb-12 max-w-6xl">
            <Breadcrumbs items={breadcrumbs} className="mb-8" />

            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:gap-16">
                <ProductGallery media={product.mediaUploads || []} />
                <ProductInfo
                    product={product}
                    selectedVariant={selectedVariant}
                    setSelectedVariant={setSelectedVariant}
                    onAddToCart={handleAddToCart}
                    isAdding={adding}
                />
            </div>

            {/* Related Products */}
            <RelatedProducts productId={product.id} />

            {/* Mobile Sticky Bar */}
            <MobileStickyBar
                product={product}
                onAddToCart={handleAddToCart}
            />

            <RelatedProducts productId={product.id} />
        </div>
    );
}
