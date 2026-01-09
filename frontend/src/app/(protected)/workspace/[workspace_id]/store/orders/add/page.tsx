'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { OrderForm, type OrderFormData } from '@/components/workspace/store/orders/form/OrderForm';
import { Button } from '@/components/shadcn-ui/button';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useMutation } from '@apollo/client/react';
import { CreateOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/CreateOrder.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';

export default function AddOrderPage() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const [createOrder, { loading }] = useMutation(CreateOrderDocument, {
    // Refetch orders list after creating an order to update cache
    refetchQueries: ['GetOrders'],
    awaitRefetchQueries: true,
    onCompleted: async (data) => {
      if (data.createOrder?.success && data.createOrder?.order) {
        toast.success(`Order ${data.createOrder.order.orderNumber} has been created successfully.`);

        // Add small delay to ensure cache is fully updated before navigation
        // This prevents stale data from showing when the orders list loads
        await new Promise(resolve => setTimeout(resolve, 100));

        // Navigate to orders list - fresh data will be displayed from cache
        router.push(`/workspace/${currentWorkspace?.id}/store/orders`);
      } else {
        toast.error(data.createOrder?.error || "Failed to create order");

        // Show unavailable items if any
        if (data.createOrder?.unavailableItems && data.createOrder.unavailableItems.length > 0) {
          toast.error(`Unavailable items: ${data.createOrder.unavailableItems.join(', ')}`);
        }
      }
    },
    onError: (error) => {
      toast.error(error.message || "An unexpected error occurred");
    },
  });

  const handleSubmit = async (data: OrderFormData) => {
    // Validate that we have items
    if (data.items.length === 0) {
      toast.error("Please add at least one product to the order");
      return;
    }

    // Validate that we have a customer (customerId is required)
    if (!data.customer_id) {
      toast.error("Please select a customer");
      return;
    }

    await createOrder({
      variables: {
        orderData: {
          // Customer info (required)
          customerId: data.customer_id,

          // Order items (snake_case to camelCase)
          items: data.items.map(item => ({
            productId: item.product_id,
            variantId: item.variant_id || undefined,
            quantity: item.quantity,
            unitPrice: item.unit_price,
          })),

          // Payment info (snake_case to camelCase)
          paymentMethod: data.payment_method,

          // Additional costs (snake_case to camelCase)
          shippingCost: data.shipping_cost,
          taxAmount: data.tax_amount,
          discountAmount: data.discount_amount,

          // Shipping address (required field - correct AddressInput fields)
          shippingAddress: {
            address: '', // Street/physical address
            city: '',
            region: '',
          },

          // Notes
          notes: data.notes || undefined,

          // Order source (manual entry from admin panel)
          orderSource: 'manual',
        },
      },
    });
  };

  const handleSaveDraft = async (data: OrderFormData) => {
    toast.info("Save draft functionality coming soon!");
    // TODO: Implement draft functionality when backend supports it
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
            <Link href={`/workspace/${currentWorkspace.id}/store/orders`}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <h1 className="text-2xl font-bold">Create order</h1>
          </div>
          <p className="text-muted-foreground">
            Create a new order for your store
          </p>
        </div>

        {/* Main Form */}
        <div className="px-4 lg:px-6">
          <OrderForm
            onSubmit={handleSubmit}
            onSaveDraft={handleSaveDraft}
            isEditing={false}
            isLoading={loading}
          />
        </div>
      </div>
    </div>
  );
}
