import Link from 'next/link';
import Image from 'next/image';
import { Heart, ShoppingBag } from 'lucide-react';
import { Product } from '@/lib/mock-data/products';
import { Button } from '../ui/Button';

interface ProductCardProps {
    product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
    const mainImage = product.images.find(img => img.is_thumbnail) || product.images[0];

    return (
        <div className="group relative flex flex-col overflow-hidden bg-card transition-all hover:shadow-lg">
            <Link href={`/product/${product.slug}`} className="relative aspect-[3/4] overflow-hidden bg-muted">
                {/* Since we are using mock data with external URLs, we use standard img tag or configured Next Image. 
             For simplicity with random URLs, unoptimized Image or standard img recommended if domains not in config. 
             Ideally configure domains next.config.ts but for now utilizing unoptimized for external demo data */}
                <Image
                    src={mainImage?.url || '/placeholders/product-placeholder.jpg'}
                    alt={mainImage?.alt || product.title}
                    fill
                    className="object-cover transition-transform duration-300 group-hover:scale-105"
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    unoptimized
                />
                {product.compare_at_price && (
                    <span className="absolute left-2 top-2 rounded bg-destructive px-2 py-1 text-xs font-medium text-destructive-foreground">
                        Sale
                    </span>
                )}

                {/* Action Buttons - Mobile: Always Visible, Desktop: Hover Only */}
                <div className="absolute right-2 top-2 z-10 flex flex-col gap-2 opacity-100 transition-opacity duration-300 md:opacity-0 md:group-hover:opacity-100">
                    <Button
                        size="icon"
                        variant="secondary"
                        className="h-8 w-8 rounded-full bg-white/80 backdrop-blur-sm hover:bg-white hover:text-black transition-colors shadow-sm"
                        aria-label="Add to wishlist"
                    >
                        <Heart className="h-4 w-4 stroke-[1.5px]" />
                    </Button>
                    <Button
                        size="icon"
                        variant="secondary"
                        className="h-8 w-8 rounded-full bg-white/80 backdrop-blur-sm hover:bg-white hover:text-black transition-colors shadow-sm"
                        aria-label="Add to cart"
                    >
                        <ShoppingBag className="h-4 w-4 stroke-[1.5px]" />
                    </Button>
                </div>
            </Link>
            <div className="flex flex-1 flex-col p-4">
                <h3 className="text-sm font-medium text-foreground">
                    <Link href={`/product/${product.slug}`}>
                        <span aria-hidden="true" className="absolute inset-0" />
                        {product.title}
                    </Link>
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">{product.vendor}</p>
                <div className="mt-auto flex items-center justify-between pt-4">
                    <div className="flex flex-col text-sm">
                        {product.compare_at_price ? (
                            <div className="flex gap-2">
                                <span className="font-bold text-destructive">${product.price.toFixed(2)}</span>
                                <span className="text-muted-foreground line-through">${product.compare_at_price.toFixed(2)}</span>
                            </div>
                        ) : (
                            <span className="font-bold text-foreground">${product.price.toFixed(2)}</span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
