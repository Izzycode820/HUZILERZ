'use client';

import { Link } from 'react-router-dom';

import { Heart, ShoppingBag } from 'lucide-react';
import { Button } from '../shadcn-ui/button';
import { cn } from '@/lib/utils';

interface ProductCardProps {
  id: string;
  name: string;
  slug: string;
  price: number | string;
  compareAtPrice?: number | string;
  imageUrl?: string;
  badge?: string;
  vendor?: string;
  onAddToCart?: (id: string, startPos?: { x: number; y: number }) => void;
  isSkeleton?: boolean;
}

export default function ProductCard({
  id,
  name,
  slug,
  price,
  compareAtPrice,
  imageUrl,
  badge,
  vendor,
  onAddToCart,
  isSkeleton = false,
}: ProductCardProps) {
  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    const startPos = {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2,
    };
    if (!isSkeleton) onAddToCart?.(id, startPos);
  };

  const formatPrice = (amount: number | string) => {
    const numPrice = typeof amount === 'number' ? amount : parseFloat(amount.toString());
    return `$${numPrice.toFixed(2)}`;
  };

  if (isSkeleton) {
    return (
      <div className="group relative block aspect-[3/4] overflow-hidden bg-muted pointer-events-none">
        <div className="absolute inset-0 bg-muted animate-pulse" />
      </div>
    );
  }

  return (
    <div className="group relative flex flex-col overflow-hidden bg-card transition-all hover:shadow-lg">
      <Link to={`/products/${slug}`} className="relative aspect-[3/4] overflow-hidden bg-muted">
        {imageUrl ? (
          <Image
            src={imageUrl}
            alt={name}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            unoptimized
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground bg-muted">
            No Image
          </div>
        )}

        {badge && (
          <span className="absolute left-2 top-2 rounded bg-destructive px-2 py-1 text-xs font-medium text-destructive-foreground">
            {badge}
          </span>
        )}

        {/* Action Buttons - Mobile: Always Visible, Desktop: Hover Only */}
        <div className="absolute right-2 top-2 z-10 flex flex-col gap-2 opacity-100 transition-opacity duration-300 md:opacity-0 md:group-hover:opacity-100">
          <Button
            size="icon"
            variant="secondary"
            className="h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm hover:bg-background hover:text-foreground transition-colors shadow-sm border border-border/50"
            aria-label="Add to wishlist"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
          >
            <Heart className="h-4 w-4 stroke-[1.5px]" />
          </Button>
          <Button
            size="icon"
            variant="secondary"
            className="h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm hover:bg-background hover:text-foreground transition-colors shadow-sm border border-border/50"
            aria-label="Add to cart"
            onClick={handleAddToCart}
          >
            <ShoppingBag className="h-4 w-4 stroke-[1.5px]" />
          </Button>
        </div>

      </Link>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="text-sm font-medium text-foreground">
          <Link to={`/products/${slug}`}>
            <span aria-hidden="true" className="absolute inset-0" />
            {name}
          </Link>
        </h3>
        {vendor && <p className="mt-1 text-sm text-muted-foreground">{vendor}</p>}
        <div className="mt-auto flex items-center justify-between pt-4">
          <div className="flex flex-col text-sm">
            {compareAtPrice ? (
              <div className="flex gap-2">
                <span className="font-bold text-destructive">{formatPrice(price)}</span>
                <span className="text-muted-foreground line-through">{formatPrice(compareAtPrice)}</span>
              </div>
            ) : (
              <span className="font-bold text-foreground">{formatPrice(price)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

