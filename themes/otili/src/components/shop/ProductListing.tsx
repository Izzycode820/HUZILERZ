'use client';

import { useState } from 'react';
import { Filter, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { FilterSidebar } from './FilterSidebar';
import { ProductCard } from '../shared/ProductCard';
import { Product } from '@/lib/mock-data/products';

interface ProductListingProps {
    initialProducts: Product[];
    title?: string;
    description?: string;
}

import { Breadcrumbs } from '../shared/Breadcrumbs';

// ... (imports)

export function ProductListing({ initialProducts, title = "All Products", description }: ProductListingProps) {
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [products] = useState(initialProducts);

    return (
        <div className="container mx-auto px-4 py-8 md:py-12">
            {/* Header */}
            <div className="mb-8 space-y-4">
                <Breadcrumbs
                    items={[{ label: 'Shop', href: '/shop' }, { label: title }]}
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
                        <Button variant="outline" size="sm" className="md:hidden rounded-none uppercase font-bold" onClick={() => setIsFilterOpen(true)}>
                            <Filter className="mr-2 h-4 w-4" /> Filters
                        </Button>
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-bold uppercase hidden sm:inline">Sort by:</span>
                            <select className="h-9 rounded-none border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring cursor-pointer">
                                <option className="bg-background text-foreground">Featured</option>
                                <option className="bg-background text-foreground">Price: Low to High</option>
                                <option className="bg-background text-foreground">Price: High to Low</option>
                                <option className="bg-background text-foreground">Newest</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

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
                                    Show {products.length} Results
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
                                <ProductCard key={product.id} product={product} />
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
