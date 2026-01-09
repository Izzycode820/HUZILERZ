import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { ShoppingCart } from 'lucide-react';
import { format } from 'date-fns';

interface LastOrderCardProps {
  totalOrders: number;
  lastOrderAt?: string | null;
  onCreateOrder: () => void;
}

export function LastOrderCard({
  totalOrders,
  lastOrderAt,
  onCreateOrder,
}: LastOrderCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Last order placed</CardTitle>
      </CardHeader>
      <CardContent>
        {totalOrders === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="mb-4">
              <div className="h-24 w-24 rounded-full bg-gradient-to-br from-blue-100 to-teal-100 flex items-center justify-center">
                <ShoppingCart className="h-12 w-12 text-blue-600" />
              </div>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              This customer hasn't placed any orders yet
            </p>
            <Button variant="outline" size="sm" onClick={onCreateOrder}>
              Create order
            </Button>
          </div>
        ) : (
          <div>
            <p className="text-sm text-muted-foreground mb-2">
              Last order: {lastOrderAt && format(new Date(lastOrderAt), 'MMM d, yyyy')}
            </p>
            <Button variant="outline" size="sm" onClick={onCreateOrder}>
              Create order
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
