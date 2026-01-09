import Link from "next/link";
import { ArrowRight, ChevronRight, Home } from "lucide-react";
import { getRootCategories, getSubcategories } from "@/lib/registry/categories";

export default function CatalogPage() {
    const rootCategories = getRootCategories();

    return (
        <div className="min-h-screen bg-white pb-20">
            {/* Catalog Header */}
            <div className="bg-[#FDFCF7] border-b border-gray-200">
                <div className="container mx-auto px-4 py-12">
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
                        <Link href="/" className="hover:text-black flex items-center gap-1">
                            <Home className="w-4 h-4" /> Home
                        </Link>
                        <ChevronRight className="w-4 h-4" />
                        <span className="font-semibold text-black">Catalog</span>
                    </div>

                    <h1 className="text-4xl font-black text-gray-900 mb-4">Product Catalog</h1>
                    <p className="text-xl text-gray-600 max-w-2xl">
                        Choose from our wide selection of premium products to customize and sell.
                    </p>
                </div>
            </div>

            {/* Categories Grid */}
            <div className="container mx-auto px-4 py-12">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {rootCategories.map((category) => {
                        const subcategories = getSubcategories(category.id);

                        return (
                            <article key={category.id} className="group border border-gray-200 rounded-2xl overflow-hidden hover:shadow-xl transition-all duration-300">
                                {/* Category Card Header */}
                                <div className="h-48 bg-gray-100 relative overflow-hidden">
                                    {/* Placeholder for Category Image - We would use category.image here */}
                                    <div className={`absolute inset-0 bg-gradient-to-br from-gray-100 to-gray-200 group-hover:scale-105 transition-transform duration-700`} />
                                    <div className="absolute bottom-4 left-4">
                                        <h2 className="text-2xl font-bold text-gray-900">{category.label}</h2>
                                    </div>
                                </div>

                                {/* Subcategories List */}
                                <div className="p-6 bg-white">
                                    <ul className="space-y-3 mb-6">
                                        {subcategories.map((sub) => (
                                            <li key={sub.id}>
                                                <Link
                                                    href={`/catalog/${sub.id}`}
                                                    className="flex items-center justify-between text-gray-600 hover:text-[#EB4335] group/link"
                                                >
                                                    <span className="font-medium">{sub.label}</span>
                                                    <ChevronRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover/link:opacity-100 group-hover/link:translate-x-0 transition-all" />
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>

                                    <Link
                                        href={`/catalog/${category.id}`}
                                        className="inline-flex items-center gap-2 font-bold text-[#EB4335] hover:gap-3 transition-all"
                                    >
                                        View all {category.label}
                                        <ArrowRight className="w-4 h-4" />
                                    </Link>
                                </div>
                            </article>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
