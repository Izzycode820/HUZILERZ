import { notFound } from 'next/navigation';
import { ProductListing } from '@/components/shop/ProductListing';
import { products } from '@/lib/mock-data/products';
import { categories } from '@/lib/mock-data/categories';

interface PageProps {
    params: Promise<{ slug: string }>;
}

export default async function CategoryPage({ params }: PageProps) {
    const { slug } = await params;
    const category = categories.find((c) => c.slug === slug);

    if (!category) {
        notFound();
    }

    // Filter products by category (mock logic)
    // Recursively find children categories if complex, but simple match for now
    const categoryProducts = products.filter(p => p.category_id === category.id);

    // If no products found for demo category, just show some random ones to fill the UI
    // In real app, this would just be empty
    const displayProducts = categoryProducts.length > 0 ? categoryProducts : products.slice(0, 3);

    return (
        <ProductListing
            initialProducts={displayProducts}
            title={category.name}
            description={category.description}
        />
    );
}
