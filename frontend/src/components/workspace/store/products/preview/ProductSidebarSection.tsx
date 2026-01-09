"use client";

import { useState } from "react";
import { Button } from "@/components/shadcn-ui/button";
import { Badge } from "@/components/shadcn-ui/badge";
import { Star, Package, Truck } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = {
  id: string;
  option1: string;
  option2: string;
  price: any | null;
  compareAtPrice: any | null;
  isAvailable: boolean | null;
  totalStock: number | null;
};

interface ProductSidebarSectionProps {
  name: string;
  description: string;
  price: any;
  compareAtPrice: any | null;
  isOnSale: boolean | null;
  salePercentage: number | null;
  hasVariants: boolean;
  variants: Variant[] | null;
  options: any;
  brand: string;
  vendor: string;
  tags: any;
  isInStock: boolean | null;
  totalStock: number | null;
  requiresShipping: boolean;
  weight: any | null;
}

export function ProductSidebarSection({
  name,
  description,
  price,
  compareAtPrice,
  isOnSale,
  salePercentage,
  hasVariants,
  variants,
  options,
  brand,
  vendor,
  tags,
  isInStock,
  totalStock,
  requiresShipping,
  weight,
}: ProductSidebarSectionProps) {
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});

  // Parse options if it's a JSON array
  const parsedOptions = Array.isArray(options) ? options : [];

  // Get unique option values
  const getOptionValues = (optionName: string) => {
    if (!variants) return [];
    const values = new Set<string>();
    variants.forEach((v) => {
      if (optionName === parsedOptions[0]?.name && v.option1) values.add(v.option1);
      if (optionName === parsedOptions[1]?.name && v.option2) values.add(v.option2);
    });
    return Array.from(values).filter(Boolean);
  };

  // Format currency - matching sneaker theme
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("fr-CM", {
      style: "currency",
      currency: "XAF",
    }).format(amount);
  };

  // Mock rating - matching sneaker theme
  const rating = 4.5;
  const reviewCount = 128;

  return (
    <div className="flex flex-col gap-6">
      {/* Product Name & Rating - matching sneaker theme */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">{name}</h1>
        <div className="mt-4 flex items-center justify-between">
          <div className="text-2xl font-bold">
            {compareAtPrice && Number(compareAtPrice) > Number(price) && (
              <span className="mr-3 text-muted-foreground line-through text-lg">
                {formatCurrency(Number(compareAtPrice))}
              </span>
            )}
            {formatCurrency(Number(price))}
          </div>
          {rating && (
            <div className="flex items-center gap-1">
              <div className="flex">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={cn(
                      "h-4 w-4",
                      i < Math.round(rating) ? "fill-primary text-primary" : "text-muted-foreground"
                    )}
                  />
                ))}
              </div>
              <span className="text-sm text-muted-foreground">({reviewCount})</span>
            </div>
          )}
        </div>
      </div>

      {/* Variants/Options - matching sneaker theme button style */}
      {hasVariants && parsedOptions.length > 0 && (
        <div className="flex flex-col gap-4">
          {parsedOptions.map((option: any) => {
            const values = getOptionValues(option.name);
            if (values.length === 0) return null;

            return (
              <div key={option.name}>
                <h3 className="mb-2 text-sm font-medium">{option.name}</h3>
                <div className="flex gap-2 flex-wrap">
                  {values.map((value) => {
                    const isSelected = (selectedOptions[option.name] || values[0]) === value;
                    return (
                      <button
                        key={value}
                        onClick={() =>
                          setSelectedOptions((prev) => ({
                            ...prev,
                            [option.name]: value,
                          }))
                        }
                        className={cn(
                          "flex min-w-[3rem] items-center justify-center border px-3 py-2 text-sm transition-all hover:border-foreground hover:bg-accent",
                          isSelected
                            ? "border-foreground bg-foreground text-background"
                            : "border-input bg-background"
                        )}
                      >
                        {value}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add to Cart - matching sneaker theme */}
      <div className="flex flex-col gap-4 pt-4">
        <Button
          size="lg"
          className="w-full rounded-none h-12 uppercase font-bold tracking-wider"
          disabled
        >
          Add into Cart
        </Button>
      </div>

      {/* Stock & Shipping Info */}
      <div className="flex flex-col gap-2 text-sm">
        {/* Stock Status */}
        <div className="flex items-center gap-2">
          {isInStock ? (
            <>
              <Package className="h-4 w-4 text-green-600" />
              <span className="text-green-600 font-medium">Available</span>
              {totalStock !== null && totalStock > 0 && (
                <span className="text-muted-foreground">
                  ({totalStock} in stock)
                </span>
              )}
            </>
          ) : (
            <>
              <Package className="h-4 w-4 text-destructive" />
              <span className="text-destructive font-medium">Out of stock</span>
            </>
          )}
        </div>

        {/* Shipping */}
        {requiresShipping && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Truck className="h-4 w-4" />
            <span>Shipping within 3-4 days</span>
          </div>
        )}
      </div>

      {/* Description - matching sneaker theme accordion style */}
      {description && (
        <div className="border-t pt-6">
          <h3 className="font-semibold mb-2">Description</h3>
          <div className="prose prose-sm max-w-none">
            <p className="text-muted-foreground whitespace-pre-wrap">{description}</p>
          </div>
        </div>
      )}

      {/* Shipping & Returns */}
      <div className="border-t pt-6">
        <h3 className="font-semibold mb-2">Shipping & Returns</h3>
        <div className="prose prose-sm text-muted-foreground">
          <p>
            We ship every where in Cameroon. Standard shipping takes 1-2 business days.
            Express shipping options available at checkout.
          </p>
        </div>
      </div>

      {/* Brand/Vendor - Show if available */}
      {(brand || vendor) && (
        <div className="border-t pt-4 flex flex-col gap-2 text-sm">
          {brand && (
            <div className="flex gap-2">
              <span className="text-muted-foreground">Brand:</span>
              <span className="font-medium">{brand}</span>
            </div>
          )}
          {vendor && (
            <div className="flex gap-2">
              <span className="text-muted-foreground">Vendor:</span>
              <span className="font-medium">{vendor}</span>
            </div>
          )}
        </div>
      )}

      {/* Tags - Show if available */}
      {tags && Array.isArray(tags) && tags.length > 0 && (
        <div className="border-t pt-4">
          <span className="text-sm text-muted-foreground mb-2 block">Tags:</span>
          <div className="flex gap-2 flex-wrap">
            {tags.map((tag: string, index: number) => (
              <Badge key={index} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
