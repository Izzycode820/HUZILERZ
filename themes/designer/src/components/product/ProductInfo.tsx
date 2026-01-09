"use client";

import { Star, Heart } from "lucide-react";
import { useState } from "react";

export default function ProductInfo() {
    const [quantity, setQuantity] = useState(1);

    return (
        <div>
            <div className="flex justify-between items-start mb-4">
                <h3 className="text-3xl font-semibold text-secondary">Essential structured blazer</h3>
                <span className="text-gray-400 text-sm">Brand: SKMEIMore Men Watches from SKMEI</span>
            </div>

            <div className="flex items-center mb-6">
                <div className="flex text-yellow-400 text-xs mr-2">
                    {[...Array(5)].map((_, i) => (
                        <Star key={i} size={14} fill="currentColor" />
                    ))}
                </div>
                <span className="text-sm text-gray-500">( 138 reviews )</span>
            </div>

            <div className="text-3xl font-bold text-primary mb-6">
                $ 75.0 <span className="text-lg text-gray-400 line-through font-normal ml-2">$ 83.0</span>
            </div>

            <p className="text-gray-600 mb-8 leading-relaxed">
                Nemo enim ipsam voluptatem quia aspernatur aut odit aut loret fugit, sed quia consequuntur magni lores eos qui ratione voluptatem sequi nesciunt.
            </p>

            {/* Selectors */}
            <div className="flex gap-8 mb-8">
                <div>
                    <h6 className="text-secondary font-bold uppercase text-sm mb-2">Available Color</h6>
                    <div className="flex gap-2">
                        <label className="cursor-pointer">
                            <input type="radio" name="color" className="peer sr-only" />
                            <div className="w-4 h-4 rounded-full bg-black peer-checked:ring-2 peer-checked:ring-offset-2 peer-checked:ring-primary"></div>
                        </label>
                        <label className="cursor-pointer">
                            <input type="radio" name="color" className="peer sr-only" />
                            <div className="w-4 h-4 rounded-full bg-blue-500 peer-checked:ring-2 peer-checked:ring-offset-2 peer-checked:ring-primary"></div>
                        </label>
                        <label className="cursor-pointer">
                            <input type="radio" name="color" className="peer sr-only" />
                            <div className="w-4 h-4 rounded-full bg-red-500 peer-checked:ring-2 peer-checked:ring-offset-2 peer-checked:ring-primary"></div>
                        </label>
                    </div>
                </div>
                <div>
                    <h6 className="text-secondary font-bold uppercase text-sm mb-2">Available Size</h6>
                    <div className="flex gap-2 text-sm uppercase text-secondary">
                        {["s", "m", "l", "xl"].map(size => (
                            <label key={size} className="cursor-pointer">
                                <input type="radio" name="size" className="peer sr-only" />
                                <div className="w-8 h-8 flex items-center justify-center border border-gray-200 peer-checked:bg-primary peer-checked:text-white peer-checked:border-primary transition-all rounded-sm hover:border-primary">
                                    {size}
                                </div>
                            </label>
                        ))}
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4 border-t border-gray-100 pt-8">
                <div className="flex items-center border border-gray-200 rounded-full overflow-hidden h-12 w-32">
                    <button
                        onClick={() => setQuantity(q => Math.max(1, q - 1))}
                        className="w-10 h-full flex items-center justify-center text-secondary hover:text-primary"
                    >-</button>
                    <input
                        type="text"
                        value={quantity}
                        readOnly
                        className="w-12 text-center border-none focus:ring-0 text-secondary font-semibold"
                    />
                    <button
                        onClick={() => setQuantity(q => q + 1)}
                        className="w-10 h-full flex items-center justify-center text-secondary hover:text-primary"
                    >+</button>
                </div>
                <button className="bg-primary text-white font-bold uppercase px-8 h-12 rounded-full hover:bg-black transition-colors">
                    Add to cart
                </button>
                <button className="h-12 w-12 border border-gray-200 rounded-full flex items-center justify-center text-secondary hover:bg-primary hover:text-white hover:border-primary transition-all">
                    <Heart size={20} />
                </button>
            </div>

            <div className="flex gap-6 mt-8 text-sm text-secondary font-medium">
                <span>Availability: <span className="text-gray-500 font-normal">In Stock</span></span>
                <div className="flex items-center">
                    <span className="mr-2">Share on:</span>
                    <div className="flex gap-2 text-gray-400">
                        <a href="#" className="hover:text-primary"><i className="fa-brands fa-facebook-f"></i></a>
                        <a href="#" className="hover:text-primary"><i className="fa-brands fa-twitter"></i></a>
                        <a href="#" className="hover:text-primary"><i className="fa-brands fa-pinterest"></i></a>
                    </div>
                </div>
            </div>

        </div>
    );
}
