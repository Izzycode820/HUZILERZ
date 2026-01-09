"use client";

import { useQuery } from "@apollo/client/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ProductCard from "@/components/shared/ProductCard";
import { GetCategoryProductsDocument } from "@/services/categories/__generated__/get-category-products.generated";
import { useStoreSlug } from "@/lib/utils/store-identifier";

export default function CollectionPage() {
  const params = useParams();
  const categorySlug = params.slug as string;
  const storeSlug = useStoreSlug();

  const { data, loading, error } = useQuery(GetCategoryProductsDocument, {
    variables: {
      storeSlug,
      categorySlug,
      limit: 50,
    },
  });

  const products = data?.categoryProducts || [];

  return (
    <div className="min-h-screen bg-white">
      {/* Breadcrumb & Header */}
      <div className="border-b border-gray-200 bg-gray-50 px-8 py-8">
        <div className="container mx-auto max-w-7xl">
          <nav className="mb-4 flex items-center gap-2 text-sm text-gray-600">
            <Link href="/products" className="hover:text-gray-900">
              All Products
            </Link>
            <span>›</span>
            <span className="capitalize text-gray-900">{categorySlug.replace(/-/g, " ")}</span>
          </nav>
          <h1 className="text-3xl font-bold capitalize text-gray-900">
            {categorySlug.replace(/-/g, " ")}
          </h1>
          <p className="mt-2 text-gray-600">
            {products.length} {products.length === 1 ? "product" : "products"}
          </p>
        </div>
      </div>

      {/* Products Grid */}
      <div className="container mx-auto max-w-7xl px-8 py-12">
        {loading && (
          <div className="flex justify-center py-12">
            <p className="text-gray-600">Loading products...</p>
          </div>
        )}

        {error && (
          <div className="flex justify-center py-12">
            <p className="text-red-600">Error loading products. Please try again later.</p>
          </div>
        )}

        {!loading && !error && products.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="mb-4 text-gray-600">No products found in this collection.</p>
            <Link href="/products" className="text-blue-600 hover:underline">
              Browse all products
            </Link>
          </div>
        )}

        {!loading && !error && products.length > 0 && (
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {products.map((product) => (
              <ProductCard
                key={product?.id}
                image={product?.mediaUploads?.[0]?.optimizedWebp || product?.mediaUploads?.[0]?.thumbnailWebp || ""}
                title={product?.name || ""}
                description={product?.slug || ""}
                price={product?.price?.toString() || "0"}
                rating="four"
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
