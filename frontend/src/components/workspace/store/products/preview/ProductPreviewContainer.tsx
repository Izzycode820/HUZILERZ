"use client";

import { GetProductQuery } from "@/services/graphql/admin-store/queries/products/__generated__/GetProduct.generated";
import { ProductImagesSection } from "./ProductImagesSection";
import { ProductSidebarSection } from "./ProductSidebarSection";

interface ProductPreviewContainerProps {
  product: NonNullable<GetProductQuery["product"]>;
}

export function ProductPreviewContainer({
  product,
}: ProductPreviewContainerProps) {
  // Extract images from mediaGallery
  const images =
    product.mediaGallery?.filter(
      (img): img is NonNullable<typeof img> => img !== null
    ) || [];

  // Extract variants
  const variants =
    product.variants?.filter(
      (variant): variant is NonNullable<typeof variant> => variant !== null
    ) || [];

  return (
    <div className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:gap-16">
        {/* Left: Images Section */}
        <div className="order-1">
          <ProductImagesSection images={images} productName={product.name} />
        </div>

        {/* Right: Sidebar Section */}
        <div className="order-2">
          <ProductSidebarSection
            name={product.name}
            description={product.description}
            price={product.price}
            compareAtPrice={product.compareAtPrice}
            isOnSale={product.isOnSale}
            salePercentage={product.salePercentage}
            hasVariants={product.hasVariants}
            variants={variants}
            options={product.options}
            brand={product.brand}
            vendor={product.vendor}
            tags={product.tags}
            isInStock={product.isInStock}
            totalStock={product.totalStock}
            requiresShipping={product.requiresShipping}
            weight={product.weight}
          />
        </div>
      </div>
    </div>
  );
}
