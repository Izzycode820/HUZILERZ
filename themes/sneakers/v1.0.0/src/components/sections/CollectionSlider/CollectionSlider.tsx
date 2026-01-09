'use client';

import { useState, useEffect } from 'react';
import { Button } from '../../shadcn-ui/button';
import { ArrowRight } from 'lucide-react';

interface Category {
    id: string;
    name: string;
    slug: string;
    image?: string | null;
}

interface CollectionSliderProps {
    title: string;
    limit?: number;
    viewMoreText?: string;
    // Resolved data
    categories?: Category[];
}

export default function CollectionSlider({
    title = "Shop by Collection",
    limit = 6, // Default to 6 to allow 2 sets of 3
    viewMoreText = "See all collections",
    categories = [],
}: CollectionSliderProps) {
    // If no categories (e.g. editor mode), show skeletons
    const showSkeletons = categories.length === 0;

    // Use actual data or 6 placeholders to fill 2 slides
    const effectiveCategories = showSkeletons
        ? Array.from({ length: 6 }).map((_, i) => ({
            id: `skeleton-${i}`,
            name: "Collection Name",
            slug: "#",
            image: null,
            isSkeleton: true
        }))
        : categories;

    const featuredCollections = effectiveCategories.slice(0, limit);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [mobileIndex, setMobileIndex] = useState(0);

    // Desktop Carousel Logic (Slides of 3)
    useEffect(() => {
        if (featuredCollections.length <= 3) return;

        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 3 >= featuredCollections.length ? 0 : prev + 3));
        }, 5000); // 5 seconds per slide

        return () => clearInterval(interval);
    }, [featuredCollections.length]);

    // Mobile Slideshow Logic (One by one)
    useEffect(() => {
        if (featuredCollections.length <= 1) return;

        const interval = setInterval(() => {
            setMobileIndex((prev) => (prev + 1 >= featuredCollections.length ? 0 : prev + 1));
        }, 4000); // 4 seconds per slide (manual swipe feel)

        return () => clearInterval(interval);
    }, [featuredCollections.length]);

    // Current visible desktop items
    const desktopVisibleItems = featuredCollections.slice(currentIndex, currentIndex + 3);

    // Current visible mobile item
    const mobileItem = featuredCollections[mobileIndex];

    return (
        <section className="py-16 bg-background overflow-hidden relative">
            {/* Empty State Overlay */}
            {showSkeletons && (
                <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
                    <div className="bg-background/80 backdrop-blur-sm border border-border p-6 rounded-lg shadow-lg text-center">
                        <p className="text-lg font-bold uppercase tracking-wide text-muted-foreground">
                            No Collections Found
                        </p>
                    </div>
                </div>
            )}

            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="flex items-center justify-between mb-8 border-b border-gray-100 pb-4 dark:border-gray-800">
                    <h2 className="text-2xl sm:text-3xl font-black uppercase tracking-tighter text-foreground">{title}</h2>
                    <Button variant="link" asChild className="gap-2 uppercase tracking-wide font-bold text-foreground hover:no-underline">
                        <a href="/collections">
                            {viewMoreText}
                            <ArrowRight className="h-4 w-4" />
                        </a>
                    </Button>
                </div>

                {/* Desktop: Masonry Grid with Auto-Slide (Carousel of 3) */}
                <div className="hidden lg:block relative min-h-[450px]">
                    {/* Render current set of 3 items */}
                    {desktopVisibleItems.length > 0 && (
                        <div key={currentIndex} className="grid grid-cols-12 gap-4 h-[450px] animate-in fade-in slide-in-from-right-4 duration-700">
                            {/* Left: Big Item (1st item) */}
                            <div className="col-span-7 h-full">
                                {desktopVisibleItems[0] ? (
                                    <div className="h-full w-full">
                                        <CollectionCard
                                            category={desktopVisibleItems[0]}
                                            isSkeleton={(desktopVisibleItems[0] as any).isSkeleton}
                                            variant="large"
                                        />
                                    </div>
                                ) : <div className="h-full bg-gray-100" />}
                            </div>

                            {/* Right: Stacked Items (2nd and 3rd items) */}
                            <div className="col-span-5 flex flex-col gap-4 h-full">
                                {/* Top Right */}
                                <div className="flex-1">
                                    {desktopVisibleItems[1] ? (
                                        <div className="h-full w-full">
                                            <CollectionCard
                                                category={desktopVisibleItems[1]}
                                                isSkeleton={(desktopVisibleItems[1] as any).isSkeleton}
                                                variant="small"
                                            />
                                        </div>
                                    ) : <div className="h-full bg-gray-100" />}
                                </div>
                                {/* Bottom Right */}
                                <div className="flex-1">
                                    {desktopVisibleItems[2] ? (
                                        <div className="h-full w-full">
                                            <CollectionCard
                                                category={desktopVisibleItems[2]}
                                                isSkeleton={(desktopVisibleItems[2] as any).isSkeleton}
                                                variant="small"
                                            />
                                        </div>
                                    ) : <div className="h-full bg-gray-100" />}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Mobile: One-by-One Slideshow */}
                <div className="lg:hidden relative w-full h-[500px] overflow-hidden">
                    {mobileItem && (
                        <div key={mobileIndex} className="w-full h-full animate-in fade-in slide-in-from-right-8 duration-500">
                            <CollectionCard
                                category={mobileItem}
                                isSkeleton={(mobileItem as any).isSkeleton}
                                variant="large"
                            />
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}

function CollectionCard({ category, isSkeleton = false, variant = 'mobile' }: { category: Category, isSkeleton?: boolean, variant?: 'large' | 'small' | 'mobile' }) {
    if (isSkeleton) {
        return (
            <div className="group relative block h-full w-full overflow-hidden bg-gray-200 pointer-events-none">
                {/* No image, just gray bg */}

                {/* Skeleton Content */}
                <div className={`absolute bottom-6 left-6 right-6 space-y-3 opacity-50`}>
                    {/* Title Bar */}
                    <div className={`bg-black/10 rounded-none ${variant === 'large' ? 'h-10 w-3/4' : 'h-8 w-2/3'}`} />
                    {/* Button/Link Bar */}
                    <div className="h-4 bg-black/10 w-1/2 rounded-none translate-y-0 opacity-100" />
                </div>
            </div>
        )
    }

    return (
        <a href={`/products?collection=${category.slug}`} className="group relative block h-full w-full overflow-hidden bg-gray-100">
            {category.image ? (
                <div
                    className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
                    style={{ backgroundImage: `url(${category.image})` }}
                />
            ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-300">
                    <span className="text-6xl font-black opacity-10">{category.name[0]}</span>
                </div>
            )}

            {/* Overlay */}
            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/40 transition-colors duration-500" />

            <div className={`absolute bottom-0 left-0 right-0 p-6 sm:p-8 transform transition-transform duration-500`}>
                <h3 className={`font-black text-white uppercase tracking-tighter mb-2 drop-shadow-lg leading-none ${variant === 'large' ? 'text-4xl sm:text-6xl' : 'text-3xl'}`}>
                    {category.name}
                </h3>
                <span className="inline-flex items-center text-sm font-bold text-white uppercase tracking-widest opacity-0 transform translate-y-4 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
                    Expected Drop <ArrowRight className="ml-2 h-4 w-4" />
                </span>
            </div>
        </a>
    )
}

