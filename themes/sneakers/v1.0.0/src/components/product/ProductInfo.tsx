'use client';

import { useState } from 'react';
import { Button } from '@/components/shadcn-ui/button';
import { AccordionItem } from '@/components/ui/Accordion';
import { GetProductDetailsQuery } from '@/services/products/__generated__/get-product-details.generated';
import { Star } from 'lucide-react';
import { useSession } from '@/lib/session/SessionProvider';
import { useMutation } from '@apollo/client/react';
import { AddToCartDocument } from '@/services/cart/__generated__/add-to-cart.generated';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { CartAnimation } from '@/components/shared/CartAnimation';
import { cn } from '@/lib/utils';

type ProductType = NonNullable<GetProductDetailsQuery['product']>;

interface ProductInfoProps {
    product: ProductType;
    selectedVariant: any | null;
    setSelectedVariant: (variant: any | null) => void;
    onAddToCart: (pos: { x: number; y: number }) => void;
    isAdding: boolean;
}

export function ProductInfo({ product, selectedVariant, setSelectedVariant, onAddToCart, isAdding }: ProductInfoProps) {
    const price = parseFloat(product.price?.toString() || '0');
    const compareAtPrice = product.compareAtPrice ? parseFloat(product.compareAtPrice.toString()) : null;

    // Extract all unique options for rendering selectors
    const optionsMap: Record<string, Set<string>> = {};
    if (product.variants) {
        product.variants.forEach(v => {
            if (!v) return;
            ['option1', 'option2', 'option3'].forEach((optKey, idx) => {
                const optValue = (v as any)[optKey];
                if (optValue) {
                    const optName = `Option ${idx + 1}`;
                    if (!optionsMap[optName]) optionsMap[optName] = new Set();
                    optionsMap[optName].add(optValue);
                }
            });
        });
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('fr-CM', {
            style: 'currency',
            currency: 'XAF',
        }).format(amount);
    };

    const handleAddToCartClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        const rect = event.currentTarget.getBoundingClientRect();
        onAddToCart({
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2,
        });
    };

    // Mock rating
    const rating = 4.5;
    const reviewCount = 128;

    return (
        <div className="flex flex-col gap-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">{product.name}</h1>
                <div className="mt-4 flex items-center justify-between">
                    <div className="text-2xl font-bold">
                        {compareAtPrice && (
                            <span className="mr-3 text-muted-foreground line-through text-lg">{formatCurrency(compareAtPrice)}</span>
                        )}
                        {formatCurrency(price)}
                    </div>
                    {rating && (
                        <div className="flex items-center gap-1">
                            <div className="flex">
                                {[...Array(5)].map((_, i) => (
                                    <Star key={i} className={cn("h-4 w-4", i < Math.round(rating) ? "fill-primary text-primary" : "text-muted-foreground")} />
                                ))}
                            </div>
                            <span className="text-sm text-muted-foreground">({reviewCount})</span>
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
                            const isSelected = selectedVariant && Object.values(selectedVariant).includes(value);
                            return (
                                <button
                                    key={value}
                                    onClick={() => {
                                        const newVariant = product.variants?.find(v =>
                                            v && Object.values(v).includes(value)
                                        );
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
                <Button
                    size="lg"
                    className="w-full rounded-none h-12 uppercase font-bold tracking-wider"
                    id="main-add-to-cart"
                    onClick={handleAddToCartClick}
                    disabled={isAdding || !product.inStock}
                >
                    {isAdding ? 'Adding...' : !product.inStock ? 'Out of Stock' : 'Add into Cart'}
                </Button>
            </div>

            <div className="border-t pt-6">
                <AccordionItem title="Description" defaultOpen>
                    <div
                        className="prose prose-sm text-muted-foreground"
                        dangerouslySetInnerHTML={{ __html: product.description || '' }}
                    />
                </AccordionItem>
                <AccordionItem title="Shipping & Returns">
                    <div className="prose prose-sm text-muted-foreground">
                        <p>
                            We ship every where in Cameroon. Standard shipping takes 1-2 business days.
                            Express shipping options available at checkout.
                        </p>
                    </div>
                </AccordionItem>
            </div>
        </div>
    );
}

