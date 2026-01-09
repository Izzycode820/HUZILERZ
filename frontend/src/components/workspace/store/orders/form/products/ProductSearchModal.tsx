import { useState, useMemo } from 'react';
import { Search, Check } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import { useQuery } from '@apollo/client/react';
import { SearchProductsForOrderDocument } from '@/services/graphql/admin-store/queries/products/__generated__/SearchProductsForOrder.generated';
import type { ProductSearchModalProps } from './types';

// Currency formatting utility
function formatCurrency(amount: string | number): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numAmount);
}

export function ProductSearchModal({
  open,
  onOpenChange,
  onAddProduct,
  selectedProductIds,
}: ProductSearchModalProps) {
  const [searchTerm, setSearchTerm] = useState('');

  // Query products with search - show initial products when modal opens
  const { data, loading } = useQuery(SearchProductsForOrderDocument, {
    variables: {
      search: searchTerm, // Empty string loads all products
      first: 50,
    },
    skip: !open,
  });

  const products = useMemo(() => {
    return (
      data?.products?.edges
        ?.map(edge => edge?.node)
        .filter((node): node is NonNullable<typeof node> => node != null) || []
    );
  }, [data]);

  const handleAddProduct = (product: any) => {
    onAddProduct(product);
    onOpenChange(false);
    setSearchTerm('');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Select products</DialogTitle>
        </DialogHeader>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
            autoFocus
          />
        </div>

        {/* Products Table */}
        <div className="flex-1 overflow-auto border rounded-md">
          <table className="w-full">
            <thead className="bg-muted/50 sticky top-0">
              <tr className="border-b">
                <th className="text-left p-3 text-sm font-medium">Product</th>
                <th className="text-right p-3 text-sm font-medium">Available</th>
                <th className="text-right p-3 text-sm font-medium">Price</th>
                <th className="w-20"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center p-8 text-muted-foreground">
                    Loading products...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center p-8 text-muted-foreground">
                    No products found
                  </td>
                </tr>
              ) : (
                products.map((product) => {
                  const isSelected = selectedProductIds.includes(product.id);
                  return (
                    <tr key={product.id} className="border-b hover:bg-muted/30">
                      <td className="p-3">
                        <div className="flex items-center gap-3">
                          {/* Product Image */}
                          <div className="flex-shrink-0 w-10 h-10 bg-muted rounded overflow-hidden">
                            {product.mediaGallery?.[0]?.thumbnailUrl ? (
                              <img
                                src={product.mediaGallery[0].thumbnailUrl}
                                alt={product.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{product.name}</p>
                            {product.sku && (
                              <p className="text-xs text-muted-foreground">
                                SKU: {product.sku}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="p-3 text-right text-sm">
                        {product.inventoryQuantity}
                      </td>
                      <td className="p-3 text-right text-sm font-medium">
                        FCFA {formatCurrency(product.price)}
                      </td>
                      <td className="p-3">
                        <Button
                          size="sm"
                          onClick={() => handleAddProduct(product)}
                          disabled={isSelected}
                          variant={isSelected ? 'outline' : 'default'}
                        >
                          {isSelected ? (
                            <>
                              <Check className="h-3 w-3 mr-1" />
                              Added
                            </>
                          ) : (
                            'Add'
                          )}
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t">
          <p className="text-sm text-muted-foreground">
            0/500 variants selected
          </p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
