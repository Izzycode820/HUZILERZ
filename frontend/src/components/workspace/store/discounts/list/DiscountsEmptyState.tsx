'use client';

import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent } from '@/components/shadcn-ui/card';

interface DiscountsEmptyStateProps {
  onAddDiscount: () => void;
}

export function DiscountsEmptyState({ onAddDiscount }: DiscountsEmptyStateProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-center space-y-4">
            <h3 className="text-lg font-semibold">No discounts yet</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Create discount codes and automatic discounts for your products and collections
            </p>
            <Button onClick={onAddDiscount} className="mt-4">
              Create discount
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
