import Breadcrumb from "@/components/ui/Breadcrumb";
import ShopSidebar from "@/components/shop/ShopSidebar";
import ProductCard from "@/components/product/ProductCard";
import InstagramGridComp from "@/components/home/InstagramGrid";

const shopProducts = [
    { id: 1, title: "Buttons tweed blazer", price: 59.0, rating: 5, image: "/img/product/product-1.jpg" },
    { id: 2, title: "Flowy striped skirt", price: 49.0, rating: 4, image: "/img/product/product-2.jpg" },
    { id: 3, title: "Cotton T-Shirt", price: 59.0, rating: 5, image: "/img/product/product-3.jpg", label: "Out of stock" },
    { id: 4, title: "Slim striped pocket shirt", price: 59.0, rating: 5, image: "/img/product/product-4.jpg" },
    { id: 5, title: "Fit micro corduroy shirt", price: 59.0, rating: 4, image: "/img/product/product-5.jpg" },
    { id: 6, title: "Tropical Kimono", price: 59.0, salePrice: 49.0, rating: 5, image: "/img/product/product-6.jpg", label: "Sale" },
    { id: 7, title: "Contrasting sunglasses", price: 59.0, rating: 5, image: "/img/product/product-7.jpg" },
    { id: 8, title: "Water resistant backpack", price: 59.0, salePrice: 49.0, rating: 5, image: "/img/product/product-8.jpg", label: "Sale" },
    { id: 9, title: "Round leather bag", price: 59.0, rating: 4, image: "/img/product/product-9.jpg" },
];

export default function ShopPage() {
    return (
        <main>
            <Breadcrumb title="Shop" />

            <section className="py-20">
                <div className="container mx-auto px-4">
                    <div className="flex flex-col lg:flex-row">
                        {/* Sidebar */}
                        <div className="w-full lg:w-1/4 mb-12 lg:mb-0">
                            <ShopSidebar />
                        </div>

                        {/* Content */}
                        <div className="w-full lg:w-3/4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {shopProducts.map((product) => (
                                    <ProductCard key={product.id} product={product as any} />
                                ))}
                            </div>

                            {/* Pagination */}
                            <div className="flex justify-center mt-12 space-x-2">
                                {[1, 2, 3].map((page) => (
                                    <button
                                        key={page}
                                        className="w-10 h-10 border border-gray-200 rounded-full flex items-center justify-center text-secondary hover:bg-primary hover:text-white hover:border-primary transition-all font-semibold"
                                    >
                                        {page}
                                    </button>
                                ))}
                                <button
                                    className="w-10 h-10 border border-gray-200 rounded-full flex items-center justify-center text-secondary hover:bg-primary hover:text-white hover:border-primary transition-all font-semibold"
                                >
                                    &gt;
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <InstagramGridComp />
        </main>
    );
}
