import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Home, ChevronRight } from "lucide-react";
import { getCategory, getSubcategories } from "@/lib/registry/categories";
import { getProductsByCategory } from "@/lib/registry/products";
import { StarRating, PriceTag } from "@/components/ui";

export default async function CategoryPage(props: { params: Promise<{ category: string }> }) {
    const params = await props.params;
    const categoryId = params.category;
    const category = getCategory(categoryId);

    if (!category) {
        notFound();
    }

    const products = getProductsByCategory(categoryId);
    const subcategories = getSubcategories(categoryId);

    return (
        <div className="min-h-screen bg-white pb-20">
            {/* Breadcrumbs & Header */}
            <div className="bg-[#FDFCF7] border-b border-gray-200">
                <div className="container mx-auto px-4 py-8">
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
                        <Link href="/" className="hover:text-black flex items-center gap-1">
                            <Home className="w-4 h-4" /> Home
                        </Link>
                        <ChevronRight className="w-4 h-4" />
                        <Link href="/catalog" className="hover:text-black">
                            Catalog
                        </Link>
                        <ChevronRight className="w-4 h-4" />
                        <span className="font-semibold text-black">{category.label}</span>
                    </div>

                    <h1 className="text-4xl font-black text-gray-900 mb-2">{category.label}</h1>
                    {category.description && (
                        <p className="text-gray-600">{category.description}</p>
                    )}
                </div>
            </div>

            <div className="container mx-auto px-4 py-12 flex flex-col lg:flex-row gap-12">
                {/* Sidebar Filters (Simplified for MVP) */}
                <aside className="w-full lg:w-64 shrink-0 space-y-8">
                    <div className="bg-gray-50 p-6 rounded-xl border border-gray-200">
                        <h3 className="font-bold text-gray-900 mb-4">Categories</h3>
                        <ul className="space-y-2">
                            <li>
                                <Link href="/catalog" className="flex items-center gap-2 text-gray-600 hover:text-black">
                                    <ArrowLeft className="w-4 h-4" /> All Categories
                                </Link>
                            </li>
                            <div className="h-px bg-gray-200 my-2" />
                            {subcategories.map(sub => (
                                <li key={sub.id}>
                                    <Link href={`/catalog/${sub.id}`} className="text-gray-900 font-medium hover:text-[#EB4335]">
                                        {sub.label}
                                    </Link>
                                </li>
                            ))}
                            {subcategories.length === 0 && (
                                <li className="text-sm text-gray-400 italic">No subcategories</li>
                            )}
                        </ul>
                    </div>
                </aside>

                {/* Product Grid */}
                <main className="flex-1">
                    {products.length === 0 ? (
                        <div className="text-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-300">
                            <h3 className="text-xl font-bold text-gray-900 mb-2">No products found</h3>
                            <p className="text-gray-500">We are adding new items to {category.label} soon!</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                            {products.map((product) => (
                                <Link
                                    key={product.id}
                                    href={`/catalog/${category.id}/${product.id}`}
                                    className="group block border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-300"
                                >
                                    {/* Product Image */}
                                    <div className="aspect-[4/5] bg-gray-100 relative p-6">
                                        {product.isBestSeller && (
                                            <span className="absolute top-3 left-3 bg-[#EB4335] text-white text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider z-10">
                                                Best Seller
                                            </span>
                                        )}
                                        <div className="w-full h-full relative">
                                            {/* Show the preview image if available, else placeholder */}
                                            <img
                                                src={product.printAreas[0]?.baseImage || "https://placehold.co/400x500/F3F4F6/9CA3AF/png?text=No+Image"}
                                                alt={product.name}
                                                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-500"
                                            />
                                        </div>
                                    </div>

                                    {/* Product Info */}
                                    <div className="p-4 space-y-3">
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium mb-1">{product.brand}</p>
                                            <h3 className="font-bold text-gray-900 leading-tight group-hover:text-[#EB4335] transition-colors">
                                                {product.name}
                                            </h3>
                                        </div>

                                        <StarRating rating={product.rating || 0} count={product.reviewCount} />

                                        <div className="pt-3 border-t border-gray-100">
                                            <PriceTag price={product.basePrice} premiumPrice={product.premiumPrice} />
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
