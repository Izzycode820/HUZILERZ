import Link from 'next/link';
import { products } from '@/lib/mock-data/products';
import { ProductCard } from '../shared/ProductCard';
import { homeConfig } from '@/lib/mock-data/home';

export function TrendingProducts() {
    // Show first 4 products
    const trending = products.slice(0, 4);
    const { trending: config } = homeConfig;

    return (
        <section className="bg-secondary/30 py-16 md:py-24">
            <div className="container mx-auto px-4">
                <div className="mb-12 flex items-end justify-between">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight uppercase">{config.title}</h2>
                        <p className="mt-4 text-muted-foreground">{config.subtitle}</p>
                    </div>
                    <Link href="/shop" className="hidden text-sm font-medium text-primary hover:underline md:block">
                        {config.viewAllText} &rarr;
                    </Link>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    {trending.map((product) => (
                        <ProductCard key={product.id} product={product} />
                    ))}
                </div>

                <div className="mt-8 text-center md:hidden">
                    <Link href="/shop" className="text-sm font-medium text-primary hover:underline">
                        {config.viewAllText} &rarr;
                    </Link>
                </div>
            </div>
        </section>
    );
}
