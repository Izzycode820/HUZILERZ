import React from "react";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

const CATEGORIES = [
    {
        id: 1,
        name: "Clothing & Bags",
        image: "https://placehold.co/400x400/FDE68A/000000/png?text=Clothing",
        color: "bg-yellow-100"
    },
    {
        id: 2,
        name: "Business Cards",
        image: "https://placehold.co/400x400/C084FC/FFFFFF/png?text=Cards",
        color: "bg-purple-100"
    },
    {
        id: 3,
        name: "Packaging",
        image: "https://placehold.co/400x400/FBCFE8/000000/png?text=Packaging",
        color: "bg-pink-100"
    },
    {
        id: 4,
        name: "Home & Living",
        image: "https://placehold.co/400x400/FB923C/FFFFFF/png?text=Home",
        color: "bg-orange-100"
    },
    {
        id: 5,
        name: "Celebrations Gifts",
        image: "https://placehold.co/400x400/60A5FA/FFFFFF/png?text=Gifts",
        color: "bg-blue-100"
    },
    {
        id: 6,
        name: "Accessories",
        image: "https://placehold.co/400x400/818CF8/FFFFFF/png?text=Accessories",
        color: "bg-indigo-100"
    }
];

export function ShopByCategory() {
    return (
        <section className="py-20 relative overflow-hidden">
            {/* Soft Gradient Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 opacity-80 -z-10" />

            <div className="container mx-auto px-4">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="flex items-center justify-center gap-2 mb-3">
                        <span className="w-5 h-5 rounded-full border border-red-500 flex items-center justify-center text-red-500 text-xs">A</span>
                        <span className="text-[#EB4335] font-bold text-xs tracking-widest uppercase">PRINT WITH APRIN</span>
                    </div>
                    <h2 className="text-4xl font-bold text-gray-900">SHOP BY CATEGORY</h2>
                </div>

                {/* Categories Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
                    {CATEGORIES.map((cat) => (
                        <div
                            key={cat.id}
                            className="group bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2"
                        >
                            {/* Image Area */}
                            <div className={cn("aspect-square overflow-hidden relative", cat.color)}>
                                <img
                                    src={cat.image}
                                    alt={cat.name}
                                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                />
                                {/* Overlay on hover */}
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors" />
                            </div>

                            {/* Text Area */}
                            <div className="p-4 flex items-center justify-between">
                                <span className="font-semibold text-gray-800 text-sm md:text-base whitespace-nowrap overflow-hidden text-ellipsis">
                                    {cat.name}
                                </span>
                                <ArrowUpRight className="w-4 h-4 text-gray-400 group-hover:text-[#EB4335] transition-colors" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
