"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

const categories = [
    {
        id: 1,
        title: "Women’s fashion",
        text: "Sitamet, consectetur adipiscing elit, sed do eiusmod tempor incidid-unt labore edolore magna aliquapendisse ultrices gravida.",
        image: "/img/categories/category-1.jpg",
        link: "/shop?category=women",
        large: true,
    },
    {
        id: 2,
        title: "Men’s fashion",
        text: "358 items",
        image: "/img/categories/category-2.jpg",
        link: "/shop?category=men",
        large: false,
    },
    {
        id: 3,
        title: "Kid’s fashion",
        text: "273 items",
        image: "/img/categories/category-3.jpg",
        link: "/shop?category=kid",
        large: false,
    },
    {
        id: 4,
        title: "Cosmetics",
        text: "159 items",
        image: "/img/categories/category-4.jpg",
        link: "/shop?category=cosmetics",
        large: false,
    },
    {
        id: 5,
        title: "Accessories",
        text: "792 items",
        image: "/img/categories/category-5.jpg",
        link: "/shop?category=accessories",
        large: false,
    },
];

export default function CategoriesGrid() {
    const largeCategory = categories.find((c) => c.large);
    const smallCategories = categories.filter((c) => !c.large);

    return (
        <section className="grid grid-cols-1 lg:grid-cols-2 h-auto lg:h-[600px] gap-0">
            {/* Large Item (Left) */}
            <div
                className="relative group h-[500px] lg:h-full bg-cover bg-center overflow-hidden"
                style={{ backgroundImage: `url(${largeCategory?.image})` }}
            >
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-500" />
                <div className="absolute inset-0 flex flex-col justify-center p-12 lg:p-24">
                    <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold font-cookie text-secondary mb-4 leading-tight">
                        {largeCategory?.title}
                    </h1>
                    <p className="text-gray-600 mb-6 max-w-sm">
                        {largeCategory?.text}
                    </p>
                    <Link
                        href={largeCategory?.link || "#"}
                        className="inline-block uppercase font-bold text-sm text-secondary border-b-2 border-primary pb-1 hover:text-primary transition-colors w-max"
                    >
                        Shop now
                    </Link>
                </div>
            </div>

            {/* Small Items Grid (Right) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 h-full">
                {smallCategories.map((cat) => (
                    <div
                        key={cat.id}
                        className="relative group h-[300px] lg:h-[300px] bg-cover bg-center overflow-hidden"
                        style={{ backgroundImage: `url(${cat.image})` }}
                    >
                        <div className="absolute inset-0 flex flex-col justify-center px-8">
                            <h4 className="text-2xl font-bold font-montserrat text-secondary mb-2">
                                {cat.title}
                            </h4>
                            <p className="text-gray-600 text-sm mb-4">
                                {cat.text}
                            </p>
                            <Link
                                href={cat.link}
                                className="inline-block uppercase font-bold text-sm text-secondary border-b-2 border-primary pb-1 hover:text-primary transition-colors w-max"
                            >
                                Shop now
                            </Link>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
