"use client";

import Link from "next/link";
import { Heart, ShoppingBag, Maximize2, Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProductProps {
    id: number;
    title: string;
    price: number;
    image: string;
    rating: number;
    label?: "New" | "Sale" | "Out of stock";
    salePrice?: number;
}

export default function ProductCard({ product }: { product: ProductProps }) {
    return (
        <div className="group">
            <div
                className="relative h-[360px] bg-cover bg-center overflow-hidden"
                style={{ backgroundImage: `url(${product.image})` }}
            >
                {/* Label */}
                {product.label && (
                    <div className={cn(
                        "absolute top-2 left-0 px-3 py-1 text-white text-xs font-bold uppercase",
                        product.label === "New" && "bg-green-500",
                        product.label === "Sale" && "bg-primary",
                        product.label === "Out of stock" && "bg-black"
                    )}>
                        {product.label}
                    </div>
                )}

                {/* Hover Actions */}
                <div className="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <ul className="absolute bottom-4 left-0 right-0 flex justify-center space-x-2 translate-y-4 group-hover:translate-y-0 transition-transform duration-300 delay-75">
                        <li>
                            <button className="bg-white p-3 rounded-full hover:bg-primary hover:text-white transition-colors shadow-lg transform hover:rotate-90">
                                <Maximize2 size={18} />
                            </button>
                        </li>
                        <li>
                            <button className="bg-white p-3 rounded-full hover:bg-primary hover:text-white transition-colors shadow-lg">
                                <Heart size={18} />
                            </button>
                        </li>
                        <li>
                            <button className="bg-white p-3 rounded-full hover:bg-primary hover:text-white transition-colors shadow-lg">
                                <ShoppingBag size={18} />
                            </button>
                        </li>
                    </ul>
                </div>
            </div>

            <div className="pt-4 text-center">
                <h6 className="text-secondary font-medium mb-1 hover:text-primary transition-colors cursor-pointer">
                    <Link href={`/product/${product.id}`}>{product.title}</Link>
                </h6>
                <div className="flex justify-center text-yellow-400 mb-2 text-xs">
                    {[...Array(5)].map((_, i) => (
                        <Star key={i} size={12} fill={i < product.rating ? "currentColor" : "none"} className={i >= product.rating ? "text-gray-300" : ""} />
                    ))}
                </div>
                <div className="font-semibold text-secondary">
                    {product.salePrice ? (
                        <>
                            <span className="text-primary mr-2">${product.salePrice}</span>
                            <span className="text-gray-400 line-through font-normal">${product.price}</span>
                        </>
                    ) : (
                        <>${product.price}</>
                    )}
                </div>
            </div>
        </div>
    );
}
