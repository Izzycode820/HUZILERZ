import { Package } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Separator } from '@/components/shadcn-ui/separator';
import { formatCurrency } from '@/utils/currency';

interface OrderItem {
  id: string;
  productName: string;
  productSku: string;
  quantity: number;
  unitPrice: string;
  totalPrice: string;
  productData?: string;
}

interface UnfulfillmentCardProps {
  status: string;
  items: OrderItem[];
  onMarkAsFulfilled: () => void;
}

export function UnfulfillmentCard({
  status,
  items,
  onMarkAsFulfilled,
}: UnfulfillmentCardProps) {
  const isFulfilled = status?.toLowerCase() === 'fulfilled';

  return (
    <Card>
      <CardHeader className="bg-yellow-50 dark:bg-yellow-900/10 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded">
              <Package className="h-4 w-4 text-yellow-700 dark:text-yellow-400" />
            </div>
            <CardTitle className="text-base">
              {isFulfilled ? 'Fulfilled' : 'Unfulfilled'}
            </CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="p-4 space-y-1">
          <p className="text-sm font-medium">Shipping</p>
        </div>

        <Separator />

        {/* Products List */}
        <div className="divide-y">
          {items.map((item) => {
            let productImage = null;
            try {
              const productData = item.productData ? JSON.parse(item.productData) : null;
              if (productData?.images && Array.isArray(productData.images) && productData.images.length > 0) {
                productImage = productData.images[0].url;
              }
            } catch (e) {
              // Ignore parse errors
            }

            return (
              <div key={item.id} className="p-4 flex items-center gap-4">
                {/* Product Image */}
                <div className="w-12 h-12 flex-shrink-0">
                  {productImage ? (
                    <img
                      src={productImage}
                      alt={item.productName}
                      className="w-full h-full rounded-md object-cover border"
                    />
                  ) : (
                    <div className="w-full h-full rounded-md bg-muted flex items-center justify-center border">
                      <span className="text-[10px] text-muted-foreground">No image</span>
                    </div>
                  )}
                </div>

                {/* Product Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{item.productName}</p>
                  {item.productSku && (
                    <p className="text-xs text-muted-foreground">SKU: {item.productSku}</p>
                  )}
                </div>

                {/* Price and Quantity */}
                <div className="text-right">
                  <p className="text-sm">
                    FCFA {formatCurrency(item.unitPrice)} × {item.quantity}
                  </p>
                  <p className="text-sm font-medium">
                    FCFA {formatCurrency(item.totalPrice)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Button */}
        {!isFulfilled && (
          <div className="p-4 border-t">
            <Button onClick={onMarkAsFulfilled} size="sm">
              Mark as fulfilled
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
