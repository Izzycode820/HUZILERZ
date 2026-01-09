"use client";

import useEmblaCarousel from "embla-carousel-react";
import Autoplay from "embla-carousel-autoplay";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const slides = [
    {
        image: "/img/banner/banner-1.jpg",
        subtitle: "The Chloe Collection",
        title: "The Project Jacket",
    },
    {
        image: "/img/banner/banner-1.jpg", // Using banner-1 as placeholder if banner-2/3 missing or same style
        subtitle: "The Chloe Collection",
        title: "The Project Jacket",
    },
    {
        image: "/img/banner/banner-1.jpg",
        subtitle: "The Chloe Collection",
        title: "The Project Jacket",
    },
];

export default function BannerSlider() {
    const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true }, [Autoplay({ delay: 5000 })]);
    const [selectedIndex, setSelectedIndex] = useState(0);

    const onSelect = useCallback(() => {
        if (!emblaApi) return;
        setSelectedIndex(emblaApi.selectedScrollSnap());
    }, [emblaApi]);

    useEffect(() => {
        if (!emblaApi) return;
        onSelect();
        emblaApi.on("select", onSelect);
    }, [emblaApi, onSelect]);

    const scrollTo = useCallback(
        (index: number) => emblaApi && emblaApi.scrollTo(index),
        [emblaApi]
    );

    return (
        <section className="py-20">
            <div className="container mx-auto px-4">
                <div className="relative h-[500px] overflow-hidden rounded-lg">
                    <div className="absolute inset-0" ref={emblaRef}>
                        <div className="flex h-full">
                            {slides.map((slide, index) => (
                                <div key={index} className="flex-[0_0_100%] min-w-0 relative h-full">
                                    <div
                                        className="absolute inset-0 bg-cover bg-center"
                                        style={{ backgroundImage: `url(${slide.image})` }}
                                    />
                                    <div className="absolute inset-0 flex items-center justify-center text-center">
                                        <div className="max-w-xl px-4">
                                            <span className="text-lg text-primary uppercase font-medium tracking-wide block mb-2">
                                                {slide.subtitle}
                                            </span>
                                            <h1 className="text-6xl md:text-7xl font-cookie text-secondary mb-6">
                                                {slide.title}
                                            </h1>
                                            <Link
                                                href="/shop"
                                                className="inline-block uppercase font-bold text-sm text-secondary border-b-2 border-primary pb-1 hover:text-primary transition-colors"
                                            >
                                                Shop now
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Dots */}
                    <div className="absolute bottom-8 left-0 right-0 flex justify-center space-x-2">
                        {slides.map((_, index) => (
                            <button
                                key={index}
                                className={cn(
                                    "w-3 h-3 rounded-full transition-colors",
                                    index === selectedIndex ? "bg-primary" : "bg-gray-400 hover:bg-gray-600"
                                )}
                                onClick={() => scrollTo(index)}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
