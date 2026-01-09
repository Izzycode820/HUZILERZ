"use client";

import { useState } from "react";
import ProductCard from "@/components/product/ProductCard";
import { cn } from "@/lib/utils";

const items = [
    { id: 1, title: "Buttons tweed blazer", price: 59.0, rating: 5, image: "/img/product/product-1.jpg", category: "women", label: "New" },
    { id: 2, title: "Flowy striped skirt", price: 49.0, rating: 4, image: "/img/product/product-2.jpg", category: "men" },
    { id: 3, title: "Cotton T-Shirt", price: 59.0, rating: 5, image: "/img/product/product-3.jpg", category: "accessories", label: "Out of stock" },
    { id: 4, title: "Slim striped pocket shirt", price: 59.0, rating: 5, image: "/img/product/product-4.jpg", category: "cosmetic" },
    { id: 5, title: "Fit micro corduroy shirt", price: 59.0, rating: 4, image: "/img/product/product-5.jpg", category: "kid" },
    { id: 6, title: "Tropical Kimono", price: 59.0, salePrice: 49.0, rating: 5, image: "/img/product/product-6.jpg", category: "women", label: "Sale" },
    { id: 7, title: "Contrasting sunglasses", price: 59.0, rating: 5, image: "/img/product/product-7.jpg", category: "accessories" },
    { id: 8, title: "Water resistant backpack", price: 59.0, salePrice: 49.0, rating: 5, image: "/img/product/product-8.jpg", category: "men", label: "Sale" },
];

const filters = [
    { id: "*", label: "All" },
    { id: "women", label: "Women’s" },
    { id: "men", label: "Men’s" },
    { id: "kid", label: "Kid’s" },
    { id: "accessories", label: "Accessories" },
    { id: "cosmetic", label: "Cosmetics" },
];

export default function NewProductSection() {
    const [activeFilter, setActiveFilter] = useState("*");

    const filteredItems = activeFilter === "*"
        ? items
        : items.filter(item => item.category === activeFilter);

    return (
        <section className="py-20">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12 items-center">
                    <div className="title text-center md:text-left">
                        <h4 className="text-2xl font-bold uppercase relative inline-block after:content-[''] after:absolute after:left-0 after:-bottom-1 after:w-full after:h-[2px] after:bg-primary">
                            New product
                        </h4>
                    </div>
                    <div>
                        <ul className="flex flex-wrap justify-center md:justify-end gap-x-6 gap-y-2 text-sm text-secondary">
                            {filters.map((filter) => (
                                <li
                                    key={filter.id}
                                    className={cn(
                                        "cursor-pointer hover:text-primary transition-colors hover:underline",
                                        activeFilter === filter.id && "underline text-secondary font-bold"
                                    )}
                                    onClick={() => setActiveFilter(filter.id)}
                                >
                                    {filter.label}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {filteredItems.map((item) => (
                        <ProductCard key={item.id} product={item as any} />
                    ))}
                </div>
            </div>
        </section>
    );
}
