'use client';

import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { ChevronRight, Tag, Gift, ShoppingCart, Truck } from 'lucide-react';

interface SelectDiscountTypeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SelectDiscountTypeModal({ open, onOpenChange }: SelectDiscountTypeModalProps) {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const handleSelectType = (type: string) => {
    if (type === 'amount_off_product' || type === 'buy_x_get_y') {
      router.push(`/workspace/${currentWorkspace?.id}/store/discounts/new/${type.replace(/_/g, '-')}`);
      onOpenChange(false);
    }
  };

  const discountTypes = [
    {
      id: 'amount_off_product',
      icon: Tag,
      title: 'Amount off products',
      description: 'Discount specific products or collections of products',
      available: true,
    },
    {
      id: 'buy_x_get_y',
      icon: Gift,
      title: 'Buy X get Y',
      description: 'Discount specific products or collections of products',
      available: true,
    },
    {
      id: 'amount_off_order',
      icon: ShoppingCart,
      title: 'Amount off order',
      description: 'Discount the total order amount',
      available: false,
    },
    {
      id: 'free_shipping',
      icon: Truck,
      title: 'Free shipping',
      description: 'Offer free shipping on an order',
      available: false,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Select discount type</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          {discountTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => handleSelectType(type.id)}
              disabled={!type.available}
              className={`w-full flex items-center justify-between p-4 rounded-lg border transition-colors ${
                type.available
                  ? 'hover:bg-accent cursor-pointer'
                  : 'opacity-50 cursor-not-allowed bg-muted'
              }`}
            >
              <div className="flex items-start gap-3 flex-1 text-left">
                <type.icon className="h-5 w-5 mt-0.5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="font-medium flex items-center gap-2">
                    {type.title}
                    {!type.available && (
                      <span className="text-xs text-muted-foreground font-normal">Coming soon</span>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">{type.description}</div>
                </div>
              </div>
              {type.available && <ChevronRight className="h-5 w-5 text-muted-foreground" />}
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
