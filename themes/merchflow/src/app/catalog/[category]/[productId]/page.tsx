import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Home, ChevronRight, Check, Info, Palette, Ruler, Truck } from "lucide-react";
import { getProduct, getCategory } from "@/lib/registry"; // Simplified import via barrel
import { StarRating, PriceTag } from "@/components/ui";

export default async function ProductDetailsPage(props: { params: Promise<{ category: string, productId: string }> }) {
    const params = await props.params;
    const { category: categoryId, productId } = params;
    const product = getProduct(productId);
    const category = getCategory(categoryId);

    if (!product || !category) {
        notFound();
    }

    return (
        <div className="min-h-screen bg-white pb-20">
            {/* Breadcrumbs */}
            <div className="border-b border-gray-200 bg-white sticky top-0 z-20">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Link href="/catalog" className="hover:text-black">Catalog</Link>
                        <ChevronRight className="w-4 h-4" />
                        <Link href={`/catalog/${category.id}`} className="hover:text-black">{category.label}</Link>
                        <ChevronRight className="w-4 h-4" />
                        <span className="font-semibold text-black truncate max-w-[200px]">{product.name}</span>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-8 flex flex-col lg:flex-row gap-12">

                {/* Left Column: Images (Simplified Gallery for MVP) */}
                <div className="w-full lg:w-1/2 space-y-4">
                    <div className="aspect-square bg-[#F9FAFB] rounded-2xl overflow-hidden border border-gray-100 sticky top-24">
                        <img
                            src={product.printAreas[0]?.baseImage}
                            alt={product.name}
                            className="w-full h-full object-contain p-8"
                        />
                    </div>
                    {/* Thumbnails to be added later */}
                </div>

                {/* Right Column: Details & Actions */}
                <div className="w-full lg:w-1/2 space-y-8">
                    {/* Header Info */}
                    <div>
                        <h1 className="text-3xl md:text-4xl font-black text-gray-900 mb-2">{product.name}</h1>
                        <div className="flex items-center gap-4 mb-4">
                            <div className="bg-gray-100 text-gray-600 px-3 py-1 rounded text-sm font-medium">
                                {product.brand}
                            </div>
                            <StarRating rating={product.rating || 0} count={product.reviewCount} />
                        </div>
                    </div>

                    {/* Pricing Card */}
                    <div className="bg-[#FDFCF7] border border-gray-200 rounded-xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                        <PriceTag price={product.basePrice} premiumPrice={product.premiumPrice} />

                        <Link
                            href={`/editor?product=${product.id}`}
                            className="w-full sm:w-auto px-8 py-3 bg-[#008060] hover:bg-[#006e52] text-white font-bold rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 transform hover:-translate-y-0.5"
                        >
                            Start Designing
                            <ArrowLeft className="w-4 h-4 rotate-180" />
                        </Link>
                    </div>

                    {/* Description */}
                    <div>
                        <h3 className="font-bold text-gray-900 text-lg mb-3">About the product</h3>
                        <p className="text-gray-600 leading-relaxed text-lg">
                            {product.description}
                        </p>
                    </div>

                    {/* Key Features Grid (Ref: details 2.PNG) */}
                    {product.features && (
                        <div>
                            <h3 className="font-bold text-gray-900 text-lg mb-4">Key features</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                {product.features.map((feature, i) => (
                                    <div key={i} className="flex gap-4">
                                        {/* Icon Placeholder - In real app we map string to Lucide Icon */}
                                        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center shrink-0 text-gray-700">
                                            <Check className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-gray-900">{feature.title}</h4>
                                            <p className="text-sm text-gray-500 mt-1">{feature.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Size Guide (Ref: details 3.PNG) */}
                    {product.sizes && (
                        <div className="border-t border-gray-200 pt-8">
                            <div className="flex items-center gap-2 mb-4">
                                <Ruler className="w-5 h-5 text-gray-400" />
                                <h3 className="font-bold text-gray-900 text-lg">Size Guide</h3>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
                                        <tr>
                                            <th className="px-4 py-3">Size</th>
                                            {Object.keys(product.sizes[0].dims).map(key => (
                                                <th key={key} className="px-4 py-3 capitalize">{key}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {product.sizes.map((size) => (
                                            <tr key={size.label} className="hover:bg-gray-50">
                                                <td className="px-4 py-3 font-bold text-gray-900">{size.label}</td>
                                                {Object.values(size.dims).map((val, i) => (
                                                    <td key={i} className="px-4 py-3 text-gray-600">{val}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Care Instructions */}
                    {product.careInstructions && (
                        <div className="border-t border-gray-200 pt-8">
                            <h3 className="font-bold text-gray-900 text-lg mb-4">Care instructions</h3>
                            <ul className="space-y-2">
                                {product.careInstructions.map((inst, i) => (
                                    <li key={i} className="flex items-center gap-3 text-gray-600">
                                        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
                                        {inst}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
