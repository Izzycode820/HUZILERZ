"use client";

import { useState } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

type MediaImage = {
  id: string;
  url: string | null;
  thumbnailUrl: string | null;
  optimizedUrl: string | null;
  width: number | null;
  height: number | null;
};

interface ProductImagesSectionProps {
  images: MediaImage[];
  productName: string;
}

export function ProductImagesSection({
  images,
  productName,
}: ProductImagesSectionProps) {
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  // Filter out null images and images without URLs
  const validImages = images.filter((img) => img && img.url);

  if (validImages.length === 0) {
    return (
      <div className="flex flex-col gap-4">
        <div className="aspect-square w-full bg-muted flex items-center justify-center text-muted-foreground">
          No image available
        </div>
      </div>
    );
  }

  const selectedImage = validImages[selectedImageIndex];

  return (
    <div className="flex flex-col gap-4">
      {/* Main Image - matching sneaker theme aspect ratio */}
      <div className="relative aspect-[3/4] overflow-hidden bg-muted sm:aspect-square md:aspect-[3/4] lg:aspect-square">
        <Image
          src={selectedImage.optimizedUrl || selectedImage.url || ""}
          alt={productName}
          fill
          className="object-cover"
          priority
        />
      </div>

      {/* Thumbnails - matching sneaker theme scrollable row with h-20 w-20 */}
      {validImages.length > 1 && (
        <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
          {validImages.map((image, index) => (
            <button
              key={image.id}
              onClick={() => setSelectedImageIndex(index)}
              className={cn(
                "relative h-20 w-20 flex-none overflow-hidden border-2 bg-muted transition-all",
                selectedImageIndex === index
                  ? "border-primary"
                  : "border-transparent hover:border-primary/50"
              )}
            >
              <Image
                src={image.thumbnailUrl || image.url || ""}
                alt={`${productName} thumbnail ${index + 1}`}
                fill
                className="object-cover"
                sizes="80px"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
