import { Button } from '../ui/Button';
import { Product } from '@/lib/mock-data/products';

interface MobileStickyBarProps {
    product: Product;
}

export function MobileStickyBar({ product }: MobileStickyBarProps) {
    return (
        <div className="fixed bottom-0 left-0 right-0 z-40 block border-t bg-background p-4 shadow-top md:hidden safe-area-bottom">
            <div className="flex gap-4">
                <div className="flex flex-col justify-center">
                    <span className="text-xs text-muted-foreground">{product.title}</span>
                    <span className="font-bold">${product.price.toFixed(2)}</span>
                </div>
                <Button className="flex-1">
                    Add to Cart
                </Button>
            </div>
        </div>
    );
}
