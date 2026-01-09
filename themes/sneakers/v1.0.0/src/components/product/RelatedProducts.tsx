'use client';

import { useQuery } from '@apollo/client/react';
import { GetRelatedProductsDocument } from '@/services/products/__generated__/get-related-products.generated';
import ProductCard from '@/components/shared/ProductCard';

interface RelatedProductsProps {
    productId: string;
}

export function RelatedProducts({ productId }: RelatedProductsProps) {
    const { data, loading } = useQuery(GetRelatedProductsDocument, {
        variables: { productId, limit: 4 },
        skip: !productId,
    });

    const products = data?.relatedProducts || [];

    if (loading) return <div className="py-12 text-center text-muted-foreground">Loading related products...</div>;
    if (products.length === 0) return null;

    return (
        <div className="mt-24">
            <h2 className="text-2xl font-bold tracking-tight mb-8">You May Also Like</h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {products.filter((p): p is NonNullable<typeof p> => !!p).map((product) => (
                    <ProductCard
                        key={product.id}
                        id={product.id}
                        name={product.name}
                        slug={product.slug}
                        price={product.price}
                        imageUrl={product.mediaUploads?.[0]?.thumbnailWebp || product.mediaUploads?.[0]?.optimizedWebp || ''}
                    />
                ))}
            </div>
        </div>
    );
}

