"use client";

import { Star } from "lucide-react";

interface TrendItemProps {
    image: string;
    title: string;
    price: number;
    rating: number;
}

function TrendItem({ image, title, price, rating }: TrendItemProps) {
    return (
        <div className="flex items-center mb-8">
            <div className="w-[90px] h-[90px] flex-shrink-0 overflow-hidden rounded-md mr-4">
                <img src={image} alt={title} className="w-full h-full object-cover" />
            </div>
            <div>
                <h6 className="text-secondary font-medium mb-1 text-sm">{title}</h6>
                <div className="flex text-yellow-400 mb-1 text-xs">
                    {[...Array(5)].map((_, i) => (
                        <Star key={i} size={10} fill={i < rating ? "currentColor" : "none"} className={i >= rating ? "text-gray-300" : ""} />
                    ))}
                </div>
                <div className="font-semibold text-secondary text-sm">${price.toFixed(1)}</div>
            </div>
        </div>
    );
}

export default function TrendSection() {
    const trendData = {
        "Hot Trend": [
            { image: "/img/trend/ht-1.jpg", title: "Chain bucket bag", price: 59.0, rating: 5 },
            { image: "/img/trend/ht-2.jpg", title: "Pendant earrings", price: 59.0, rating: 5 },
            { image: "/img/trend/ht-3.jpg", title: "Cotton T-Shirt", price: 59.0, rating: 5 },
        ],
        "Best Seller": [
            { image: "/img/trend/bs-1.jpg", title: "Cotton T-Shirt", price: 59.0, rating: 5 },
            { image: "/img/trend/bs-2.jpg", title: "Zip-pockets pebbled tote briefcase", price: 59.0, rating: 5 },
            { image: "/img/trend/bs-3.jpg", title: "Round leather bag", price: 59.0, rating: 5 },
        ],
        "Feature": [
            { image: "/img/trend/f-1.jpg", title: "Bow wrap skirt", price: 59.0, rating: 5 },
            { image: "/img/trend/f-2.jpg", title: "Metallic earrings", price: 59.0, rating: 5 },
            { image: "/img/trend/f-3.jpg", title: "Flap cross-body bag", price: 59.0, rating: 5 },
        ],
    };

    return (
        <section className="py-20">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {Object.entries(trendData).map(([category, items]) => (
                        <div key={category}>
                            <div className="mb-8">
                                <h4 className="text-xl font-bold uppercase relative inline-block after:content-[''] after:absolute after:left-0 after:-bottom-1 after:w-full after:h-[2px] after:bg-primary">
                                    {category}
                                </h4>
                            </div>
                            <div>
                                {items.map((item, index) => (
                                    <TrendItem key={index} {...item} />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
