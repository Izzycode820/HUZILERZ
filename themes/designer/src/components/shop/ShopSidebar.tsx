"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight } from "lucide-react";

export default function ShopSidebar() {
    const [expanded, setExpanded] = useState<Record<string, boolean>>({
        categories: true,
        price: true,
        size: true,
        color: true
    });

    const toggle = (section: string) => {
        setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
    };

    return (
        <aside className="w-full pr-8">
            {/* Categories */}
            <div className="mb-8">
                <h4 className="uppercase font-bold text-secondary mb-4 flex justify-between cursor-pointer" onClick={() => toggle("categories")}>
                    Categories
                    <ChevronDown size={16} className={cn("transition-transform", !expanded.categories && "-rotate-90")} />
                </h4>
                {expanded.categories && (
                    <ul className="space-y-2 text-gray-500 text-sm">
                        {["Women", "Men", "Kids", "Accessories", "Cosmetic"].map((cat) => (
                            <li key={cat} className="hover:text-primary cursor-pointer transition-colors">
                                {cat}
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Price */}
            <div className="mb-8 p-1">
                <h4 className="uppercase font-bold text-secondary mb-4 flex justify-between cursor-pointer" onClick={() => toggle("price")}>
                    Shop by Price
                    <ChevronDown size={16} className={cn("transition-transform", !expanded.price && "-rotate-90")} />
                </h4>
                {expanded.price && (
                    <div className="space-y-2 text-sm text-gray-500">
                        {["$ 0.0 - $ 50.0", "$ 50.0 - $ 100.0", "$ 100.0 - $ 150.0", "$ 150.0 - $ 200.0", "$ 200.0+"].map((price) => (
                            <div key={price} className="flex items-center">
                                <input type="checkbox" className="mr-2" />
                                <span>{price}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Size */}
            <div className="mb-8">
                <h4 className="uppercase font-bold text-secondary mb-4 flex justify-between cursor-pointer" onClick={() => toggle("size")}>
                    Shop by Size
                    <ChevronDown size={16} className={cn("transition-transform", !expanded.size && "-rotate-90")} />
                </h4>
                {expanded.size && (
                    <div className="flex flex-wrap gap-2">
                        {["XXS", "XS", "S", "M", "L", "XL", "XXL"].map((size) => (
                            <div key={size} className="border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:bg-primary hover:text-white cursor-pointer uppercase transition-colors">
                                {size}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Color */}
            <div className="mb-8">
                <h4 className="uppercase font-bold text-secondary mb-4 flex justify-between cursor-pointer" onClick={() => toggle("color")}>
                    Shop by Color
                    <ChevronDown size={16} className={cn("transition-transform", !expanded.color && "-rotate-90")} />
                </h4>
                {expanded.color && (
                    <div className="flex flex-wrap gap-2 text-xs uppercase text-gray-500">
                        {["Black", "White", "Reds", "Greys", "Blue", "Beige", "Greens", "Yellows"].map((color) => (
                            <div key={color} className="flex items-center mr-2 mb-2 cursor-pointer hover:text-primary">
                                <span
                                    className="w-3 h-3 rounded-full mr-1 border border-gray-200"
                                    style={{ backgroundColor: color.toLowerCase().replace("s", "") }} // simple heuristic
                                />
                                {color}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </aside>
    );
}
