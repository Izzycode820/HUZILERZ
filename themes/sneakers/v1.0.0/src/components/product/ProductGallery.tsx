'use client';

import { useState } from 'react';

import { cn } from '@/lib/utils';
import { GetProductDetailsQuery } from '@/services/products/__generated__/get-product-details.generated';

// Extract the Media type helper
type ProductMediaType = NonNullable<NonNullable<GetProductDetailsQuery['product']>['mediaUploads']>[number];

interface ProductGalleryProps {
    media: ProductMediaType[];
}

export function ProductGallery({ media }: ProductGalleryProps) {
    const [selectedImage, setSelectedImage] = useState(media?.[0]);

    // Filter out nulls and ensure we have valid images
    const validMedia = media?.filter((m): m is NonNullable<typeof m> => !!(m?.url || m?.optimizedWebp)) || [];

    // If no images, use placeholder
    const displayImages = validMedia.length > 0 ? validMedia : [];

    if (displayImages.length === 0) {
        return (
            <div className="aspect-square w-full bg-muted flex items-center justify-center text-muted-foreground">
                No Image Available
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4">
            {/* Main Image */}
            <div className="relative aspect-[3/4] overflow-hidden bg-muted sm:aspect-square md:aspect-[3/4] lg:aspect-square">
                <Image
                    src={selectedImage?.optimizedWebp || selectedImage?.url || displayImages[0].optimizedWebp || displayImages[0].url || ''}
                    alt="Product image"
                    fill
                    className="object-cover"
                    priority
                    unoptimized
                />
            </div>

            {/* Thumbnails (Desktop Grid / Mobile Scroll) */}
            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                {displayImages.map((image, index) => (
                    <button
                        key={index}
                        onClick={() => setSelectedImage(image)}
                        className={cn(
                            "relative h-20 w-20 flex-none overflow-hidden border-2 bg-muted transition-all",
                            selectedImage?.url === image.url || selectedImage?.optimizedWebp === image.optimizedWebp
                                ? "border-primary"
                                : "border-transparent hover:border-primary/50"
                        )}
                    >

                        <Image
                            src={image.optimizedWebp || image.url || ''}
                            alt={`Thumbnail ${index + 1}`}
                            fill
                            className="object-cover"
                            sizes="80px"
                            unoptimized
                        />
                    </button>
                ))}
            </div>
        </div>
    );
}
