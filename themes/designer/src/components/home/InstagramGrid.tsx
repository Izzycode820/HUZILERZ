"use client";

import { Instagram } from "lucide-react";

const instaImages = [
    "/img/instagram/insta-1.jpg",
    "/img/instagram/insta-2.jpg",
    "/img/instagram/insta-3.jpg",
    "/img/instagram/insta-4.jpg",
    "/img/instagram/insta-5.jpg",
    "/img/instagram/insta-6.jpg",
];

export default function InstagramGrid() {
    return (
        <div className="flex flex-wrap">
            {instaImages.map((img, index) => (
                <div key={index} className="w-1/2 md:w-1/3 lg:w-1/6 relative group h-[320px]">
                    <div
                        className="absolute inset-0 bg-cover bg-center"
                        style={{ backgroundImage: `url(${img})` }}
                    />
                    <div className="absolute inset-0 bg-white/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col items-center justify-center text-center p-4">
                        <Instagram size={30} className="text-secondary mb-2" />
                        <p className="text-secondary font-medium">@ ashion_shop</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
