"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

const SLIDES = [
    {
        id: 1,
        label: "SPECIAL OFFERS",
        title: "BRANDED PACKAGING",
        subtitle: "Get your business logo into more hands",
        cta: "Shop The Sale",
        link: "/catalog",
        bg: "bg-[#FFF5F5]",
        image: "/assets/hero/packaging.png",
        alignment: "left"
    },
    {
        id: 2,
        label: "NEW ARRIVALS",
        title: "CUSTOM APPAREL",
        subtitle: "Premium quality tees and hoodies for your brand",
        cta: "Customize Your Own",
        link: "/catalog",
        bg: "bg-[#F0F9FF]", // Light blue tint
        image: "/assets/hero/apparel.png",
        alignment: "left"
    },
    {
        id: 3,
        label: "BEST SELLERS",
        title: "PROMO PRODUCTS",
        subtitle: "Mugs, pens, and accessories that sell",
        cta: "View Catalog",
        link: "/catalog",
        bg: "bg-[#FFFBF0]", // Light yellow tint
        image: "/assets/hero/promo.png",
        alignment: "left"
    }
];

export function Hero() {
    const [currentSlide, setCurrentSlide] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentSlide((prev) => (prev + 1) % SLIDES.length);
        }, 5000);
        return () => clearInterval(timer);
    }, []);

    return (
        <section className="relative w-full h-[500px] md:h-[600px] overflow-hidden">
            {SLIDES.map((slide, index) => (
                <div
                    key={slide.id}
                    className={cn(
                        "absolute inset-0 w-full h-full transition-opacity duration-1000 ease-in-out flex items-center",
                        slide.bg,
                        index === currentSlide ? "opacity-100 z-10" : "opacity-0 z-0"
                    )}
                >
                    <div className="container mx-auto px-4 grid md:grid-cols-2 gap-8 items-center h-full">
                        {/* Text Content */}
                        <div className={cn(
                            "space-y-6 max-w-xl transition-all duration-700 delay-300 transform",
                            index === currentSlide ? "translate-x-0 opacity-100" : "-translate-x-10 opacity-0"
                        )}>
                            <span className="text-[#EB4335] font-bold tracking-widest text-sm uppercase">
                                {slide.label}
                            </span>
                            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 leading-tight">
                                {slide.title}
                            </h1>
                            <p className="text-gray-500 text-lg md:text-xl">
                                {slide.subtitle}
                            </p>
                            <div className="flex gap-4">
                                <Link href={slide.link || "/catalog"}>
                                    <button className="bg-[#EB4335] hover:bg-[#D33025] text-white px-8 py-4 rounded-full font-semibold flex items-center gap-2 transition-all transform hover:translate-x-1 shadow-lg group">
                                        {slide.cta}
                                        <ArrowRight className="w-5 h-5 group-hover:ml-1 transition-all" />
                                    </button>
                                </Link>
                            </div>
                        </div>

                        {/* Image Content (Placeholder simulation) */}
                        <div className={cn(
                            "relative h-full flex items-center justify-center transition-all duration-700 delay-500 transform",
                            index === currentSlide ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"
                        )}>
                            {/* This is where the product image would go - using a styled div/img placeholder */}
                            <div className="relative w-full aspect-square md:aspect-auto md:h-[80%] rounded-3xl overflow-hidden shadow-2xl bg-white/50 backdrop-blur-sm p-4">
                                <img
                                    src={slide.image}
                                    alt={slide.title}
                                    className="w-full h-full object-cover rounded-2xl"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            ))}

            {/* Dots Navigation */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex gap-3">
                {SLIDES.map((_, idx) => (
                    <button
                        key={idx}
                        onClick={() => setCurrentSlide(idx)}
                        className={cn(
                            "w-12 h-1 rounded-full transition-all duration-300",
                            idx === currentSlide ? "bg-[#EB4335]" : "bg-gray-300 hover:bg-gray-400"
                        )}
                        aria-label={`Go to slide ${idx + 1}`}
                    />
                ))}
            </div>
        </section>
    );
}
