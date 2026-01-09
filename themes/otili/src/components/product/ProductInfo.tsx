'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';
import { Button } from '../ui/Button';
import { AccordionItem } from '../ui/Accordion';
import { Product, ProductVariant } from '@/lib/mock-data/products';
import { cn } from '../ui/Button';

interface ProductInfoProps {
    product: Product;
}

export function ProductInfo({ product }: ProductInfoProps) {
    const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(
        product.variants.length > 0 ? product.variants[0] : null
    );

    // Extract all unique options for rendering selectors (e.g. all available sizes)
    // This is a simplified logic. In real apps, options are often derived from a separate options definition.
    const optionsMap: Record<string, Set<string>> = {};
    product.variants.forEach(v => {
        Object.entries(v.options).forEach(([key, value]) => {
            if (!optionsMap[key]) optionsMap[key] = new Set();
            optionsMap[key].add(value);
        });
    });

    return (
        <div className="flex flex-col gap-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">{product.title}</h1>
                <div className="mt-4 flex items-center justify-between">
                    <div className="text-2xl font-bold">
                        {product.compare_at_price && (
                            <span className="mr-3 text-muted-foreground line-through text-lg">${product.compare_at_price.toFixed(2)}</span>
                        )}
                        ${product.price.toFixed(2)}
                    </div>
                    {product.rating && (
                        <div className="flex items-center gap-1">
                            <div className="flex">
                                {[...Array(5)].map((_, i) => (
                                    <Star key={i} className={cn("h-4 w-4", i < Math.round(product.rating!) ? "fill-primary text-primary" : "text-muted-foreground")} />
                                ))}
                            </div>
                            <span className="text-sm text-muted-foreground">({product.review_count})</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Variant Selectors */}
            {Object.entries(optionsMap).map(([optionName, valuesSet]) => (
                <div key={optionName}>
                    <h3 className="mb-2 text-sm font-medium">{optionName}</h3>
                    <div className="flex flex-wrap gap-2">
                        {Array.from(valuesSet).map((value) => {
                            const isSelected = selectedVariant?.options[optionName] === value;
                            return (
                                <button
                                    key={value}
                                    onClick={() => {
                                        // Find variant with this option value + keeping other current selections if possible
                                        // Simplified: just find first variant with this value
                                        const newVariant = product.variants.find(v => v.options[optionName] === value);
                                        if (newVariant) setSelectedVariant(newVariant);
                                    }}
                                    className={cn(
                                        "flex min-w-[3rem] items-center justify-center border px-3 py-2 text-sm transition-all hover:border-foreground hover:bg-accent",
                                        isSelected ? "border-foreground bg-foreground text-background" : "border-input bg-background"
                                    )}
                                >
                                    {value}
                                </button>
                            );
                        })}
                    </div>
                </div>
            ))}

            <div className="flex flex-col gap-4 pt-4">
                <Button size="lg" className="w-full rounded-none h-12 uppercase font-bold tracking-wider" id="main-add-to-cart">
                    Add into Cart
                </Button>
                <p className="text-center text-xs text-muted-foreground">
                    Free shipping on orders over $100. Returns accepted within 30 days.
                </p>
            </div>

            <div className="border-t pt-6">
                <AccordionItem title="Description" defaultOpen>
                    <div className="prose prose-sm text-muted-foreground">
                        <p>{product.description}</p>
                    </div>
                </AccordionItem>
                <AccordionItem title="Shipping & Returns">
                    <div className="prose prose-sm text-muted-foreground">
                        <p>
                            We ship worldwide. Standard shipping takes 3-5 business days.
                            Express shipping options available at checkout.
                        </p>
                    </div>
                </AccordionItem>
            </div>
        </div>
    );
}
