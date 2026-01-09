"use client";

import { useQuery } from "@apollo/client/react";
import { ProductListing } from "@/components/shop/ProductListing";
import { GetProductsPaginatedDocument } from "@/services/products/__generated__/get-products-paginated.generated";
import { useStoreSlug } from "@/lib/utils/store-identifier";
import { FilterProvider } from "@/contexts/FilterContext";

export default function ProductsPage() {
  const storeSlug = useStoreSlug();

  const { data, loading, error } = useQuery(GetProductsPaginatedDocument, {
    variables: {
      storeSlug,
      first: 24,
    },
  });

  const products = data?.products?.edges?.map(edge => {
    const node = edge?.node;
    if (!node) return null;

    return {
      id: node.id,
      name: node.name,
      slug: node.slug,
      price: typeof node.price === 'number' ? node.price : parseFloat(node.price?.toString() || '0'),
      compareAtPrice: node.compareAtPrice ? (typeof node.compareAtPrice === 'number' ? node.compareAtPrice : parseFloat(node.compareAtPrice.toString())) : null,
      vendor: node.vendor || undefined,
      mediaUploads: node.mediaUploads,
    };
  }).filter((node): node is NonNullable<typeof node> => Boolean(node)) || [];

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 min-h-[60vh] flex items-center justify-center">
        <div className="animate-pulse space-y-4 text-center">
          <div className="h-8 w-48 bg-gray-200 mx-auto" />
          <div className="text-muted-foreground">Loading products...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold">Error loading products</h1>
        <p className="text-muted-foreground mt-2">Please try again later.</p>
      </div>
    );
  }

  return (
    <FilterProvider>
      <ProductListing
        initialProducts={products}
        title="All Products"
        description="Browse our complete collection"
      />
    </FilterProvider>
  );
}

