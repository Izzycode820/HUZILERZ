import { notFound } from 'next/navigation';
import { products } from '@/lib/mock-data/products';
import { ProductGallery } from '@/components/product/ProductGallery';
import { ProductInfo } from '@/components/product/ProductInfo';
import { MobileStickyBar } from '@/components/product/MobileStickyBar';
import { ProductCard } from '@/components/shared/ProductCard';

interface PageProps {
    params: Promise<{ slug: string }>;
}

export default async function ProductPage({ params }: PageProps) {
    const { slug } = await params;
    const product = products.find((p) => p.slug === slug);

    if (!product) {
        notFound();
    }

    // Mock related products
    const relatedProducts = products.filter(p => p.id !== product.id).slice(0, 4);

    return (
        <div className="container mx-auto px-4 py-8 md:py-12 pb-24 md:pb-12">
            <nav className="mb-8 text-sm text-muted-foreground">
                Home / Shop / {product.title}
            </nav>

            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:gap-16">
                <ProductGallery images={product.images} />
                <ProductInfo product={product} />
            </div>

            {/* Related Products */}
            <div className="mt-24">
                <h2 className="text-2xl font-bold tracking-tight mb-8">You May Also Like</h2>
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    {relatedProducts.map(p => (
                        <ProductCard key={p.id} product={p} />
                    ))}
                </div>
            </div>

            <MobileStickyBar product={product} />
        </div>
    );
}
