import { ProductListing } from '@/components/shop/ProductListing';
import { products } from '@/lib/mock-data/products';

export default function ShopPage() {
    return (
        <ProductListing
            initialProducts={products}
            title="All Products"
            description="Explore our full collection of premium items."
        />
    );
}
