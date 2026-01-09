'use client';

import { Button } from '../../shadcn-ui/button';
import { ArrowRight } from 'lucide-react';

interface Product {
    id: string;
    mediaUploads?: Array<{
        optimizedWebp?: string | null;
    }>;
}

interface Category {
    id: string;
    name: string;
    slug: string;
    image?: string | null;
    products?: Product[];
}

interface TwoColumnCollectionsProps {
    title?: string;
    collection1Slug?: string;
    collection2Slug?: string;
    // Resolved data
    categories?: Category[];
}

export default function TwoColumnCollections({
    title,
    collection1Slug,
    collection2Slug,
    categories = [],
}: TwoColumnCollectionsProps) {

    // Helper to find category by slug
    const findCategory = (slug?: string) => categories.find(c => c.slug === slug);

    // Default logic: Skip first 3 (assumed featured) and take next 2
    // Or if slugs provided, use them.
    let col1 = findCategory(collection1Slug);
    let col2 = findCategory(collection2Slug);

    if (!col1 && !collection1Slug) {
        // Default fallback
        col1 = categories[3]; // 4th item
    }
    if (!col2 && !collection2Slug) {
        col2 = categories[4]; // 5th item
    }

    // If we still don't have enough categories, just take what's available
    if (!col1 && categories.length > 0) col1 = categories[0];
    if (!col2 && categories.length > 1) col2 = categories[1];

    // If same category selected for both (or fallback collision), try to diversify
    if (col1?.id === col2?.id && categories.length > 2) {
        col2 = categories.find(c => c.id !== col1?.id) || col2;
    }

    const items = [col1, col2].filter(Boolean) as Category[];

    if (items.length === 0) return null;


    return (
        <section className="py-12 bg-background">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {title && <h2 className="text-2xl sm:text-3xl font-black mb-8 uppercase tracking-tighter text-foreground">{title}</h2>}

                <div className="grid grid-cols-2 gap-4 md:gap-8">
                    {items.map((cat, idx) => {
                        // Use category image, or first product image, or fallback
                        const bgImage = cat.image || cat.products?.[0]?.mediaUploads?.[0]?.optimizedWebp || "";

                        return (
                            <a
                                key={cat.id || idx}
                                href={`/products?collection=${cat.slug}`}
                                className="group relative h-[300px] md:h-[500px] overflow-hidden block border border-gray-100 dark:border-gray-800"
                            >
                                <div
                                    className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
                                    style={{ backgroundImage: `url(${bgImage})` }}
                                />
                                <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors" />

                                <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4 md:p-8">
                                    <h3 className="text-xl md:text-5xl font-black text-white uppercase tracking-tighter mb-4 transform translate-y-4 transition-transform duration-300 group-hover:translate-y-0 shadow-black drop-shadow-lg">
                                        {cat.name}
                                    </h3>
                                    <div className="opacity-0 transform translate-y-8 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
                                        <Button className="bg-white text-black hover:bg-gray-100 rounded-none uppercase tracking-wide font-bold h-8 text-xs md:h-10 md:text-sm px-4 md:px-8">
                                            Shop Now
                                        </Button>
                                    </div>
                                </div>
                            </a>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}
