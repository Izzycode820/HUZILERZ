"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Filter, ArrowRight, Star, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

const FILTERS = [
    "Fast Sellers", "Home & Living", "Clothing & Apparel", "Drinkware & Kitchen",
    "Kids & Babies", "Paper, Stationery & Office", "Phone Cases & Accessories"
];

const PRODUCTS = [
    {
        id: 1,
        name: "Tote Bag (AOP)",
        brand: "Generic brand",
        image: "https://placehold.co/400x400/E5E7EB/000000/png?text=Tote",
        price: "12.38",
        premiumPrice: "9.25"
    },
    {
        id: 2,
        name: "Tough Phone Cases",
        brand: "Generic brand",
        image: "https://placehold.co/400x400/D1D5DB/000000/png?text=Case",
        price: "12.62",
        premiumPrice: "9.57"
    },
    {
        id: 3,
        name: "Cotton Canvas Tote Bag",
        brand: "Liberty Bags - OAD113",
        image: "https://placehold.co/400x400/F3F4F6/000000/png?text=Canvas+Tote",
        price: "9.48",
        premiumPrice: "6.97"
    },
    {
        id: 4,
        name: "Bumper Stickers",
        brand: "Generic brand",
        image: "https://placehold.co/400x400/E5E7EB/000000/png?text=Sticker",
        price: "4.35",
        premiumPrice: "3.15"
    }
];

export function ProductSelector() {
    const [activeFilter, setActiveFilter] = useState("Phone Cases & Accessories");
    const [selectedCount, setSelectedCount] = useState(0);

    return (
        <section className="py-20 bg-[#FDFCF7] border-t border-gray-200">
            <div className="container mx-auto px-4">
                {/* Header Section */}
                <div className="flex items-center justify-between mb-8">
                    <button className="flex items-center gap-2 text-gray-500 hover:text-black">
                        <ChevronLeft className="w-5 h-5" />
                        Back to collections
                    </button>
                    <button className="flex items-center gap-2 font-bold text-gray-900 hover:text-[#EB4335] transition-colors">
                        <ExternalLink className="w-5 h-5" />
                        View Printify Catalog
                    </button>
                </div>

                <h2 className="text-3xl font-bold text-gray-900 mb-8 max-w-4xl">
                    Let's start designing the best products for <span className="underline decoration-[#EB4335] underline-offset-4">{activeFilter}</span>
                </h2>

                {/* Filters */}
                <div className="flex gap-3 overflow-x-auto pb-6 scrollbar-hide">
                    {FILTERS.map((filter) => (
                        <button
                            key={filter}
                            onClick={() => setActiveFilter(filter)}
                            className={cn(
                                "px-4 py-2 rounded-full whitespace-nowrap text-sm font-semibold transition-colors border",
                                activeFilter === filter
                                    ? "bg-[#485346] text-white border-[#485346]"
                                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
                            )}
                        >
                            {filter}
                        </button>
                    ))}
                </div>

                {/* Product Grid (Simulated Carousel) */}
                <div className="relative mt-8">
                    <button className="absolute -left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center z-10 text-gray-400 hover:text-black hover:scale-110 transition-all">
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <button className="absolute -right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center z-10 text-gray-400 hover:text-black hover:scale-110 transition-all">
                        <ChevronRight className="w-6 h-6" />
                    </button>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {PRODUCTS.map((product) => (
                            <div key={product.id} className="group cursor-pointer">
                                <div className="aspect-square bg-[#F5F5F0] mb-4">
                                    <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
                                </div>
                                <h3 className="font-bold text-gray-900 text-lg">{product.name}</h3>
                                <p className="text-gray-500 text-sm mb-2">By {product.brand}</p>
                                <div className="space-y-1">
                                    <p className="font-bold text-gray-900">From USD {product.price}</p>
                                    <p className="text-[#008060] text-xs font-semibold">
                                        From USD {product.premiumPrice} with Printify Premium
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Sticky Bottom Bar */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4 mt-12 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
                <div className="container mx-auto flex items-center justify-between">
                    <span className="text-gray-600 font-medium">
                        {selectedCount} of 5 products created
                    </span>
                    <Link
                        href="/catalog"
                        className={cn(
                            "flex items-center gap-2 px-6 py-3 rounded font-bold transition-colors bg-green-600 text-white hover:bg-green-700"
                        )}
                    >
                        Start Designing
                        <ArrowRight className="w-5 h-5" />
                    </Link>
                </div>
            </div>
        </section>
    );
}
