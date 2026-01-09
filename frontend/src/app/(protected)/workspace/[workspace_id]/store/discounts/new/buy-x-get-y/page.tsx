'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/shadcn-ui/button';
import { ArrowLeft } from 'lucide-react';
import { useMutation } from '@apollo/client/react';
import { CreateDiscountDocument } from '@/services/graphql/admin-store/mutations/discounts/__generated__/CreateDiscount.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';
import { BuyXGetYForm, type BuyXGetYFormData } from '@/components/workspace/store/discounts/create/buy-x-get-y/BuyXGetYForm';
import * as Types from '@/types/workspace/store/graphql-base';

export default function AddBuyXGetYDiscountPage() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const [createDiscount, { loading }] = useMutation(CreateDiscountDocument, {
    onCompleted: (data) => {
      if (data.createDiscount?.success && data.createDiscount?.discount) {
        toast.success(`Discount "${data.createDiscount.discount.code}" created successfully`);
        router.push(`/workspace/${currentWorkspace?.id}/store/discounts`);
      } else {
        toast.error(data.createDiscount?.error || 'Failed to create discount');
      }
    },
    onError: (error) => {
      toast.error(error.message || 'An unexpected error occurred');
    },
  });

  const handleSubmit = async (data: BuyXGetYFormData) => {
    await createDiscount({
      variables: {
        input: {
          code: data.code,
          name: data.name || data.code,
          method: data.method,
          discountType: Types.WorkspaceStoreDiscountDiscountTypeChoices.BuyXGetY,
          customerBuysType: data.customerBuysType,
          customerBuysQuantity: data.customerBuysQuantity,
          customerBuysValue: data.customerBuysValue?.toString(),
          customerBuysProductIds: data.customerBuysProductIds || [],
          customerGetsQuantity: data.customerGetsQuantity,
          customerGetsProductIds: data.customerGetsProductIds || [],
          bxgyDiscountType: data.bxgyDiscountType,
          bxgyValue: data.bxgyValue?.toString(),
          maxUsesPerOrder: data.maxUsesPerOrder,
          startsAt: data.startsAt,
          endsAt: data.endsAt,
          minimumRequirementType: data.minimumRequirementType,
          minimumPurchaseAmount: data.minimumPurchaseAmount?.toString(),
          minimumQuantityItems: data.minimumQuantityItems,
          usageLimit: data.limitTotalUses ? data.usageLimit : undefined,
          limitOnePerCustomer: data.limitOnePerCustomer,
          canCombineWithProductDiscounts: data.canCombineWithProductDiscounts,
          canCombineWithOrderDiscounts: data.canCombineWithOrderDiscounts,
          appliesToAllCustomers: data.appliesToAllCustomers,
          status: Types.WorkspaceStoreDiscountStatusChoices.Active,
        },
      },
    });
  };

  const handleDiscard = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/discounts`);
  };

  const handleBackClick = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/discounts`);
  };

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

 
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <div className="px-4 lg:px-6">
          <div className="flex items-center gap-4 mb-4">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={handleBackClick}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold">Create discount</h1>
          </div>
          <p className="text-muted-foreground">
            Buy X get Y
          </p>
        </div>

        {/* Main Form */}
        <div className="px-4 lg:px-6">
          <BuyXGetYForm
            onSubmit={handleSubmit}
            onDiscard={handleDiscard}
            isLoading={loading}
          />
        </div>
      </div>
    </div>
  );
}
