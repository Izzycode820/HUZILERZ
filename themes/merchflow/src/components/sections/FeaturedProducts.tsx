"use client";

import React, { useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = ["BEST SELLER", "NEW ARRIVALS", "SALES"];

const PRODUCTS = [
    {
        id: 1,
        name: "Awesome Wooden Plate",
        price: "$420.42",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Plate",
        isNew: true,
        category: "NEW ARRIVALS"
    },
    {
        id: 2,
        name: "Incredible Paper Shoes",
        price: "$100.41",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Shoes",
        isNew: false,
        category: "BEST SELLER"
    },
    {
        id: 3,
        name: "Synergistic Copper Bag",
        price: "$78.14",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Bag",
        isNew: false,
        category: "SALES"
    },
    {
        id: 4,
        name: "Enormous Silk Gloves",
        price: "$387.22",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Gloves",
        isNew: true,
        category: "NEW ARRIVALS"
    },
    {
        id: 5,
        name: "Awesome Aluminum Watch",
        price: "$29.29",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Cap",
        isNew: true,
        category: "SALES"
    },
    {
        id: 6,
        name: "Ergonomic Cotton Gloves",
        price: "$220.15",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Mug",
        isNew: false,
        category: "BEST SELLER"
    },
    {
        id: 7,
        name: "Rustic Concrete Case",
        price: "$15.99",
        rating: 5,
        reviews: 5,
        image: "https://placehold.co/300x300/F3F4F6/000000/png?text=Case",
        isNew: true,
        category: "SALES"
    }
];

export function FeaturedProducts() {
    const [activeTab, setActiveTab] = useState("SALES");

    // For demo purposes, we might want to show all products or filter.
    // The image showed a grid that seemed to be for "SALES" specifically or a mix.
    // I will just show all spread out for now, or filter if I had enough data.
    // Let's filter to simulate the interaction, but since I have limited dummy data, 
    // I'll randomize/shim it so it looks populated for any tab.
    const displayProducts = PRODUCTS;

    return (
        <section className="py-20 bg-white">
            <div className="container mx-auto px-4">
                {/* Tabs Headers */}
                <div className="flex flex-wrap justify-center gap-8 mb-12 text-xl md:text-2xl font-bold text-gray-400 uppercase tracking-wide">
                    {TABS.map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                                "transition-colors duration-300 pb-2 border-b-2 border-transparent hover:text-gray-600",
                                activeTab === tab ? "text-black border-black scale-105" : "hover:border-gray-200"
                            )}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* Product Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
                    {displayProducts.map((product) => (
                        <div key={product.id} className="group cursor-pointer">
                            {/* Image Card */}
                            <div className="bg-[#F3F4F6] rounded-3xl p-6 relative aspect-square mb-4 transition-transform duration-300 group-hover:-translate-y-2 group-hover:shadow-lg overflow-hidden">
                                {product.isNew && (
                                    <span className="absolute top-4 left-4 bg-blue-500 text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase">
                                        New
                                    </span>
                                )}
                                <img
                                    src={product.image}
                                    alt={product.name}
                                    className="w-full h-full object-contain mix-blend-multiply group-hover:scale-110 transition-transform duration-500"
                                />
                            </div>

                            {/* Details */}
                            <div className="text-center space-y-1">
                                <h3 className="text-sm font-semibold text-gray-900 truncate px-2">{product.name}</h3>
                                <div className="flex items-center justify-center gap-1">
                                    {[...Array(5)].map((_, i) => (
                                        <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                    ))}
                                    <span className="text-xs text-gray-400">({product.reviews})</span>
                                </div>
                                <div className="font-bold text-gray-900">{product.price}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
