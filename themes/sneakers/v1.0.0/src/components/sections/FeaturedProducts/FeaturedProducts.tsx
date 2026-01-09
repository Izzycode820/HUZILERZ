'use client';
import { useState, useEffect } from 'react';

import ProductCard from '../../shared/ProductCard';
import { Button } from '../../shadcn-ui/button';
import { ScrollArea, ScrollBar } from '../../shadcn-ui/scroll-area';
import { ArrowRight } from 'lucide-react';

interface Product {
    id: string;
    name: string;
    slug: string;
    price: string;
    compareAtPrice?: string | null;
    mediaUploads?: Array<{
        optimizedWebp?: string | null;
        thumbnailWebp?: string | null;
    }>;
}

interface FeaturedProductsProps {
    title: string;
    categorySlug: string;
    limit?: number;
    viewMoreText?: string;
    // Resolved data
    products?: Product[];
}

export default function FeaturedProducts({
    title = "Featured Products",
    categorySlug = "featured",
    limit = 10,
    viewMoreText = "View all",
    products = [],
}: FeaturedProductsProps) {

    // Display up to 10 products (2 rows of 5 on desktop)
    const effectiveProducts = products.slice(0, 10);
    // If no products (e.g. editor mode), show placeholders to maintain size/layout
    const showPlaceholders = effectiveProducts.length === 0;

    const itemsToRender = showPlaceholders ? Array.from({ length: 5 }).map((_, i) => ({
        id: `placeholder-${i}`,
        name: "Featured Product",
        slug: "#",
        price: "0 XAF",
        mediaUploads: [],
        isPlaceholder: true
    })) : effectiveProducts;

    const [mobileIndex, setMobileIndex] = useState(0);

    // Mobile Slideshow Logic (One by one)
    useEffect(() => {
        if (effectiveProducts.length <= 1) return;

        const interval = setInterval(() => {
            setMobileIndex((prev) => (prev + 1 >= effectiveProducts.length ? 0 : prev + 1));
        }, 4000); // 4 seconds per slide to simulate manual swipe

        return () => clearInterval(interval);
    }, [effectiveProducts.length]);

    // Current visible mobile item
    const mobileItem = effectiveProducts[mobileIndex];

    return (
        <section className="py-12 bg-background dark:bg-background relative">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="flex items-center justify-between mb-8 border-b border-gray-100 pb-4 dark:border-gray-800">
                    <h2 className="text-2xl sm:text-3xl font-black uppercase tracking-tighter text-foreground">{title}</h2>

                    <Button variant="link" asChild className="hidden sm:inline-flex gap-2 uppercase tracking-wide font-bold text-foreground hover:no-underline">
                        <a href={`/products?collection=${categorySlug}`}>
                            {viewMoreText}
                            <ArrowRight className="h-4 w-4" />
                        </a>
                    </Button>
                </div>

                {/* Empty State Message Overlay */}
                {showPlaceholders && (
                    <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
                        <div className="bg-background/80 backdrop-blur-sm border border-border p-6 rounded-lg shadow-lg text-center">
                            <p className="text-lg font-bold uppercase tracking-wide text-muted-foreground">
                                No Products Found
                            </p>
                            <p className="text-sm text-muted-foreground">
                                Collection: {categorySlug}
                            </p>
                        </div>
                    </div>
                )}

                {/* DESKTOP: 5-Column Grid */}
                <div className="hidden lg:grid grid-cols-5 gap-6">
                    {itemsToRender.map((product: any) => (
                        <div key={product.id}>
                            <ProductCard
                                id={product.id}
                                name={product.name}
                                slug={product.slug}
                                price={product.price}
                                imageUrl={
                                    product.mediaUploads?.[0]?.optimizedWebp ||
                                    product.mediaUploads?.[0]?.thumbnailWebp ||
                                    undefined
                                }
                                isSkeleton={product.isPlaceholder}
                            />
                        </div>
                    ))}
                </div>

                {/* MOBILE: One-by-One Slideshow */}
                <div className="lg:hidden relative w-full h-[500px] overflow-hidden">
                    {mobileItem && (
                        <div key={mobileIndex} className="w-full h-full animate-in fade-in slide-in-from-right-8 duration-500">
                            <ProductCard
                                id={mobileItem.id}
                                name={mobileItem.name}
                                slug={mobileItem.slug}
                                price={mobileItem.price}
                                imageUrl={
                                    (mobileItem as any).mediaUploads?.[0]?.optimizedWebp ||
                                    (mobileItem as any).mediaUploads?.[0]?.thumbnailWebp ||
                                    undefined
                                }
                                isSkeleton={(mobileItem as any).isPlaceholder}
                            />
                        </div>
                    )}
                </div>

                <div className="mt-8 text-center sm:hidden">
                    <Button asChild className="w-full uppercase tracking-wide font-bold">
                        <a href={`/products?collection=${categorySlug}`}>
                            {viewMoreText}
                        </a>
                    </Button>
                </div>
            </div>
        </section>
    );
}
