"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

const images = [
    "/img/product/details/product-1.jpg",
    "/img/product/details/thumb-1.jpg",
    "/img/product/details/thumb-2.jpg",
    "/img/product/details/thumb-3.jpg",
    "/img/product/details/thumb-4.jpg",
];

export default function ProductGallery() {
    const [selectedImage, setSelectedImage] = useState(images[0]);

    return (
        <div className="flex gap-4">
            {/* Thumbnails (Left) */}
            <div className="flex flex-col gap-4 w-[100px]">
                {images.slice(1).map((img, i) => (
                    <div
                        key={i}
                        className={cn(
                            "w-full h-[120px] bg-cover bg-center cursor-pointer border border-transparent hover:border-primary transition-all",
                            selectedImage === img && "border-primary"
                        )}
                        style={{ backgroundImage: `url(${img})` }}
                        onClick={() => setSelectedImage(img)}
                        onMouseEnter={() => setSelectedImage(img)}
                    />
                ))}
            </div>

            {/* Main Image */}
            <div className="flex-1 h-[550px] relative overflow-hidden bg-gray-100">
                <img src={selectedImage} alt="Product" className="w-full h-full object-cover" />
                <div className="absolute top-4 left-4 bg-green-500 text-white text-xs font-bold uppercase px-3 py-1">New</div>
                <button className="absolute top-4 right-4 bg-white p-2 rounded-full shadow-md hover:scale-110 transition-transform">
                    <span className="sr-only">Zoom</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21 21-4.3-4.3" /><path d="M11 8a3 3 0 1 0 0 6 3 3 0 0 0 0-6" /><path d="M19 19a10 10 0 1 1-10-10" /></svg>
                </button>
            </div>
        </div>
    );
}
