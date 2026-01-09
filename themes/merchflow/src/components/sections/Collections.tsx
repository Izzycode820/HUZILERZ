"use client";

import React, { useRef } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";

const COLLECTIONS = [
    {
        id: 1,
        categoryId: "clothing-kids",
        title: "Kids & Babies",
        count: "7 products",
        image: "https://placehold.co/500x500/FDE68A/000000/png?text=Kids",
        bg: "bg-yellow-100"
    },
    {
        id: 2,
        categoryId: "stationery",
        title: "Paper, Stationery & Office",
        count: "7 products",
        image: "https://placehold.co/500x500/99F6E4/000000/png?text=Office",
        bg: "bg-teal-100"
    },
    {
        id: 3,
        categoryId: "electronics-phone",
        title: "Phone Cases & Accessories",
        count: "6 products",
        image: "https://placehold.co/500x500/E5E7EB/000000/png?text=Accessories",
        bg: "bg-gray-100"
    },
    {
        id: 4,
        categoryId: "clothing",
        title: "Sportswear",
        count: "4 products",
        image: "https://placehold.co/500x500/86EFAC/000000/png?text=Sports",
        bg: "bg-green-100"
    },
    // Duplicating for scroll effect
    {
        id: 5,
        categoryId: "clothing-tops",
        title: "Mens Clothing",
        count: "12 products",
        image: "https://placehold.co/500x500/93C5FD/000000/png?text=Mens",
        bg: "bg-blue-100"
    }
];

export function Collections() {
    const scrollRef = useRef<HTMLDivElement>(null);

    const scroll = (direction: "left" | "right") => {
        if (scrollRef.current) {
            const container = scrollRef.current;
            const scrollAmount = 400;
            if (direction === "left") {
                container.scrollBy({ left: -scrollAmount, behavior: "smooth" });
            } else {
                container.scrollBy({ left: scrollAmount, behavior: "smooth" });
            }
        }
    };

    return (
        <section className="py-20 bg-[#FDFCF7]">
            <div className="container mx-auto px-4">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-end mb-12 gap-6">
                    <div className="max-w-2xl">
                        <span className="text-gray-500 text-sm font-semibold mb-2 block">Create a collection</span>
                        <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
                            Let's start creating, what do you want to create for?
                        </h2>
                        <p className="text-gray-600">
                            Product collections help you create multiple products that will help you succeed.
                        </p>
                    </div>
                    <Link href="/catalog" className="flex items-center gap-2 font-bold text-gray-900 hover:text-[#EB4335] transition-colors whitespace-nowrap">
                        <ExternalLink className="w-5 h-5" />
                        View Catalog
                    </Link>
                </div>

                {/* Carousel Container */}
                <div className="relative group/carousel">
                    {/* Navigation Buttons */}
                    <button
                        onClick={() => scroll("left")}
                        className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:bg-gray-50 transition-colors opacity-0 group-hover/carousel:opacity-100 duration-300"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>

                    <button
                        onClick={() => scroll("right")}
                        className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center text-gray-700 hover:bg-gray-50 transition-colors opacity-0 group-hover/carousel:opacity-100 duration-300"
                    >
                        <ChevronRight className="w-6 h-6" />
                    </button>

                    {/* Scrollable Area */}
                    <div
                        ref={scrollRef}
                        className="flex gap-6 overflow-x-auto pb-12 snap-x snap-mandatory scrollbar-hide no-scrollbar"
                        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                    >
                        {COLLECTIONS.map((item) => (
                            <Link
                                key={item.id}
                                href={`/catalog/${item.categoryId}`}
                                className="min-w-[300px] md:min-w-[400px] snap-start group cursor-pointer block"
                            >
                                <div className={`aspect-square rounded-xl overflow-hidden mb-4 relative ${item.bg}`}>
                                    <img
                                        src={item.image}
                                        alt={item.title}
                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                    />
                                    {/* Overlay */}
                                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-gray-900">{item.title}</h3>
                                    <p className="text-gray-500 text-sm">{item.count}</p>
                                </div>
                            </Link>
                        ))}
                    </div>

                    {/* Custom Scrollbar Indicator (Static representation for visual style) */}
                    <div className="h-2 bg-gray-200 rounded-full w-full max-w-4xl mx-auto overflow-hidden">
                        <div className="h-full bg-gray-500 w-1/3 rounded-full" />
                    </div>
                </div>
            </div>
        </section>
    );
}
