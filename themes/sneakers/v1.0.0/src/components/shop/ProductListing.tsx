'use client';

import { useState } from 'react';
import { Filter, X } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { FilterSidebar } from './FilterSidebar';
import ProductCard from '@/components/shared/ProductCard';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { useSession } from '@/lib/session/SessionProvider';
import { useMutation } from '@apollo/client/react';
import { AddToCartDocument } from '@/services/cart/__generated__/add-to-cart.generated';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { triggerFlyToCartAnimation } from '@/lib/animations/flyToCart';
import { useFilters } from '@/contexts/FilterContext';
import { SortDropdown } from '../filters/SortDropdown';
import { ActiveFilters } from '../filters/ActiveFilters';


type Product = {
    id: string;
    name: string;
    slug: string;
    price: number;
    compareAtPrice?: number;
    vendor?: string;
    mediaUploads?: Array<{
        thumbnailWebp?: string | null;
        optimizedWebp?: string | null;
    } | null> | null;
};

interface ProductListingProps {
    initialProducts: Product[];
    title?: string;
    description?: string;
}

export function ProductListing({ initialProducts, title = "All Products", description }: ProductListingProps) {
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [products] = useState(initialProducts);
    const { hasActiveFilters } = useFilters();

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
        onCompleted: (data) => {
            // Animation is triggered immediately on click, no need to wait for network
        },
        onError: (err) => {
            alert("Failed to add to cart: " + err.message);
        }
    });

    const handleAddToCart = async (productId: string, startPos?: { x: number; y: number }) => {
        // Trigger animation immediately (pure DOM - no React state)
        if (startPos) {
            triggerFlyToCartAnimation(startPos.x, startPos.y);
        }

        try {
            let sessionId = guestSessionId;
            if (!sessionId) {
                sessionId = await createGuestSession();
            }

            if (!sessionId || !sessionId) {
                // Handle session creation failure silently or user notice
                return;
            }

            // Default variant logic would go here if needed, but for listing we assume simple product or default var
            // For now, listing usually adds default/first variant
            await addToCart({
                variables: {
                    input: {
                        sessionId,
                        productId: productId,
                        quantity: 1,
                    }
                }
            });
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 md:py-12">
            {/* Header */}
            <div className="mb-8 space-y-4">
                <Breadcrumbs
                    items={[{ label: 'Shop', href: '/products' }, { label: title }]}
                    className="mb-4"
                />

                <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                    <div>
                        <h1 className="text-3xl font-black uppercase tracking-tighter">{title}</h1>
                        {description && <p className="mt-2 text-muted-foreground">{description}</p>}
                    </div>

                    <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground hidden md:inline-block">
                            {products.length} Products
                        </span>
                        <Button
                            variant="outline"
                            size="sm"
                            className="md:hidden rounded-none uppercase font-bold"
                            onClick={() => setIsFilterOpen(true)}
                        >
                            <Filter className="mr-2 h-4 w-4" />
                            Filters {hasActiveFilters && <span className="ml-1 px-1.5 py-0.5 bg-primary text-primary-foreground text-xs rounded-full">•</span>}
                        </Button>
                        <SortDropdown />
                    </div>
                </div>
            </div>

            {/* Active Filters */}
            <ActiveFilters />

            <div className="flex flex-col gap-8 md:flex-row">
                {/* Desktop Sidebar */}
                <aside className="hidden w-64 flex-none md:block">
                    <FilterSidebar />
                </aside>

                {/* Mobile Filter Drawer */}
                {isFilterOpen && (
                    <div className="fixed inset-0 z-50 flex md:hidden">
                        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setIsFilterOpen(false)} />
                        <div className="relative ml-auto flex h-full w-[85%] flex-col overflow-y-auto bg-background p-6 shadow-xl animate-in slide-in-from-right sm:max-w-sm border-l border-border text-foreground">
                            <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
                                <h2 className="text-lg font-black uppercase tracking-wide">Filters</h2>
                                <Button variant="ghost" size="icon" onClick={() => setIsFilterOpen(false)}>
                                    <X className="h-5 w-5" />
                                </Button>
                            </div>
                            <FilterSidebar />
                            <div className="mt-8 pt-4 border-t border-border sticky bottom-0 bg-background">
                                <Button className="w-full rounded-none uppercase font-bold" onClick={() => setIsFilterOpen(false)}>
                                    Show {products.length} {products.length === 1 ? 'Result' : 'Results'}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Product Grid */}
                <div className="flex-1">
                    {products.length === 0 ? (
                        <div className="flex h-64 items-center justify-center text-muted-foreground">
                            No products found.
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 gap-4 sm:gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                            {products.map((product) => (
                                <ProductCard
                                    key={product.id}
                                    id={product.id}
                                    name={product.name}
                                    slug={product.slug}
                                    price={product.price}
                                    compareAtPrice={product.compareAtPrice || undefined}
                                    imageUrl={product.mediaUploads?.[0]?.optimizedWebp || product.mediaUploads?.[0]?.thumbnailWebp || undefined}
                                    vendor={product.vendor}
                                    onAddToCart={handleAddToCart}
                                />
                            ))}
                        </div>
                    )}

                    {/* Pagination Placeholder */}
                    {products.length > 0 && (
                        <div className="mt-12 flex justify-center gap-2">
                            <Button variant="outline" size="sm" disabled>Previous</Button>
                            <Button variant="outline" size="sm" className="bg-primary text-primary-foreground">1</Button>
                            <Button variant="outline" size="sm">2</Button>
                            <Button variant="outline" size="sm">3</Button>
                            <Button variant="outline" size="sm">Next</Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
