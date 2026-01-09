'use client';

import { useState } from 'react';
import Image from 'next/image';
import { cn } from '../ui/Button';
import { ProductImage } from '@/lib/mock-data/products';

interface ProductGalleryProps {
    images: ProductImage[];
}

export function ProductGallery({ images }: ProductGalleryProps) {
    const [selectedImage, setSelectedImage] = useState(images[0]);

    // If no images, use placeholder
    const displayImages = images.length > 0 ? images : [{ id: 'placeholder', url: '/placeholders/product.jpg', alt: 'Product image' }];

    return (
        <div className="flex flex-col gap-4">
            {/* Main Image */}
            <div className="relative aspect-[3/4] overflow-hidden rounded-lg bg-muted sm:aspect-square md:aspect-[3/4] lg:aspect-square">
                <Image
                    src={selectedImage?.url || displayImages[0].url}
                    alt={selectedImage?.alt || 'Product image'}
                    fill
                    className="object-cover"
                    priority
                    unoptimized
                />
            </div>

            {/* Thumbnails (Desktop Grid / Mobile Scroll) */}
            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                {displayImages.map((image) => (
                    <button
                        key={image.id}
                        onClick={() => setSelectedImage(image)}
                        className={cn(
                            "relative h-20 w-20 flex-none overflow-hidden rounded-md border-2 bg-muted transition-all",
                            selectedImage?.id === image.id ? "border-primary" : "border-transparent hover:border-primary/50"
                        )}
                    >
                        <Image
                            src={image.url}
                            alt={image.alt}
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
