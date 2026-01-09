import Breadcrumb from "@/components/ui/Breadcrumb";
import ProductGallery from "@/components/product/ProductGallery";
import ProductInfo from "@/components/product/ProductInfo";
import ProductTabs from "@/components/product/ProductTabs";
import ProductCard from "@/components/product/ProductCard";
import InstagramGrid from "@/components/home/InstagramGrid";

const relatedProducts = [
    { id: 1, title: "Buttons tweed blazer", price: 59.0, rating: 5, image: "/img/product/product-1.jpg" },
    { id: 2, title: "Flowy striped skirt", price: 49.0, rating: 4, image: "/img/product/product-2.jpg" },
    { id: 3, title: "Cotton T-Shirt", price: 59.0, rating: 5, image: "/img/product/product-3.jpg" },
    { id: 4, title: "Slim striped pocket shirt", price: 59.0, rating: 5, image: "/img/product/product-4.jpg" },
];

export default function ProductDetailsPage({ params }: { params: { id: string } }) {
    return (
        <main>
            <Breadcrumb title="Essential structured blazer" links={[{ label: "Shop", href: "/shop" }]} />

            <section className="py-20">
                <div className="container mx-auto px-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                        <ProductGallery />
                        <ProductInfo />
                    </div>

                    <ProductTabs />

                    <div className="mt-20">
                        <div className="title text-center mb-12">
                            <h4 className="text-2xl font-bold uppercase relative inline-block after:content-[''] after:absolute after:left-0 after:-bottom-1 after:w-full after:h-[2px] after:bg-primary">
                                Related Products
                            </h4>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                            {relatedProducts.map((product) => (
                                <ProductCard key={product.id} product={product as any} />
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            <InstagramGrid />
        </main>
    );
}
