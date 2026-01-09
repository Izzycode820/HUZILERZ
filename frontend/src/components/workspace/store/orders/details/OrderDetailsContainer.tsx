'use client';

import { useQuery, useMutation } from '@apollo/client/react';
import { GetOrderDocument } from '@/services/graphql/admin-store/queries/orders/__generated__/getOrder.generated';
import { CancelOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/CancelOrder.generated';
import { ArchiveOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/ArchiveOrder.generated';
import { UnarchiveOrderDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/UnarchiveOrder.generated';
import { UpdateOrderStatusDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/UpdateOrderStatus.generated';
import { MarkOrderAsPaidDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/MarkOrderAsPaid.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { OrderDetailsHeader } from './OrderDetailsHeader';
import { UnfulfillmentCard } from './UnfulfillmentCard';
import { PaymentCard } from './PaymentCard';
import { TimelineSection } from './TimelineSection';
import { OrderSidebar } from './OrderSidebar';
import { toast } from 'sonner';

interface OrderDetailsContainerProps {
  orderId: string;
}

export default function OrderDetailsContainer({ orderId }: OrderDetailsContainerProps) {
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const { data, loading, error, refetch } = useQuery(GetOrderDocument, {
    variables: { id: orderId },
    skip: !currentWorkspace,
  });

  const [cancelOrder] = useMutation(CancelOrderDocument, {
    refetchQueries: ['GetOrder', 'GetOrders'],
    awaitRefetchQueries: true,
  });

  const [archiveOrder] = useMutation(ArchiveOrderDocument, {
    refetchQueries: ['GetOrder', 'GetOrders'],
    awaitRefetchQueries: true,
  });

  const [unarchiveOrder] = useMutation(UnarchiveOrderDocument, {
    refetchQueries: ['GetOrder', 'GetOrders'],
    awaitRefetchQueries: true,
  });

  const [updateOrderStatus] = useMutation(UpdateOrderStatusDocument, {
    refetchQueries: ['GetOrder', 'GetOrders'],
    awaitRefetchQueries: true,
  });

  const [markOrderAsPaid] = useMutation(MarkOrderAsPaidDocument, {
    refetchQueries: ['GetOrder', 'GetOrders'],
    awaitRefetchQueries: true,
  });

  const order = data?.order;

  const handleEdit = () => {
    toast.info('Edit order functionality coming soon!');
  };

  const handleRefund = () => {
    toast.info('Refund functionality coming soon!');
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this order?')) return;

    try {
      const result = await cancelOrder({ variables: { orderId } });
      if (result.data?.cancelOrder?.success) {
        toast.success('Order cancelled successfully');
      } else {
        toast.error(result.data?.cancelOrder?.error || 'Failed to cancel order');
      }
    } catch (e) {
      toast.error('An error occurred');
    }
  };

  const handleArchive = async () => {
    try {
      const result = await archiveOrder({ variables: { orderId } });
      if (result.data?.archiveOrder?.success) {
        toast.success('Order archived successfully');
      } else {
        toast.error(result.data?.archiveOrder?.error || 'Failed to archive order');
      }
    } catch (e) {
      toast.error('An error occurred');
    }
  };

  const handleUnarchive = async () => {
    try {
      const result = await unarchiveOrder({ variables: { orderId } });
      if (result.data?.unarchiveOrder?.success) {
        toast.success('Order unarchived successfully');
      } else {
        toast.error(result.data?.unarchiveOrder?.error || 'Failed to unarchive order');
      }
    } catch (e) {
      toast.error('An error occurred');
    }
  };

  const handleMarkAsFulfilled = async () => {
    try {
      const result = await updateOrderStatus({
        variables: {
          orderId,
          newStatus: 'fulfilled',
        },
      });

      if (result.data?.updateOrderStatus?.success) {
        toast.success('Order marked as fulfilled');
      } else {
        toast.error(result.data?.updateOrderStatus?.error || 'Failed to mark order as fulfilled');
      }
    } catch (e) {
      toast.error('An error occurred');
      console.error('Fulfill order error:', e);
    }
  };

  const handleMarkAsPaid = async () => {
    try {
      const result = await markOrderAsPaid({ variables: { orderId } });
      if (result.data?.markOrderAsPaid?.success) {
        toast.success('Order marked as paid');
      } else {
        toast.error(result.data?.markOrderAsPaid?.error || 'Failed to mark order as paid');
      }
    } catch (e) {
      toast.error('An error occurred');
      console.error('Mark as paid error:', e);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading order...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error || !order) {
    return (
      <div className="px-4 lg:px-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>Failed to load order</p>
              <p className="text-sm text-muted-foreground">
                {error?.message || 'Order not found'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <OrderDetailsHeader
        orderNumber={order.orderNumber}
        status={order.status}
        paymentStatus={order.paymentStatus}
        createdAt={order.createdAt}
        orderSource={order.orderSource}
        workspaceId={currentWorkspace?.id || ''}
        onEdit={handleEdit}
        onRefund={handleRefund}
        onCancel={handleCancel}
        onArchive={handleArchive}
        onUnarchive={handleUnarchive}
        canBeCancelled={order.canBeCancelled ?? false}
        canBeRefunded={order.canBeRefunded ?? false}
        canBeArchived={order.canBeArchived ?? false}
        canBeUnarchived={order.canBeUnarchived ?? false}
        canMarkAsPaid={order.canMarkAsPaid ?? false}
        onMarkAsPaid={handleMarkAsPaid}
      />

      {/* Main Content */}
      <div className="px-4 lg:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Unfulfillment Card */}
            <UnfulfillmentCard
              status={order.status}
              items={order.items?.filter((item): item is NonNullable<typeof item> => item !== null).map(item => ({
                id: item.id,
                productName: item.productName,
                productSku: item.productSku,
                quantity: item.quantity,
                unitPrice: String(item.unitPrice),
                totalPrice: String(item.totalPrice ?? 0),
                productData: item.productData
              })) || []}
              onMarkAsFulfilled={handleMarkAsFulfilled}
            />

            {/* Payment Card */}
            <PaymentCard
              paymentStatus={order.paymentStatus}
              paymentMethod={order.paymentMethod}
              subtotal={order.subtotal}
              shippingCost={order.shippingCost}
              taxAmount={order.taxAmount}
              discountAmount={order.discountAmount}
              totalAmount={order.totalAmount}
              currency={order.currency}
              itemCount={order.itemCount ?? 0}
            />

            {/* Timeline */}
            <TimelineSection
              orderId={order.id}
              events={(order.timeline || [])
                .filter((event): event is NonNullable<typeof event> => event !== null)
                .map(event => ({
                  id: event.id,
                  type: event.type as 'COMMENT' | 'STATUS_CHANGE' | 'NOTIFICATION' | 'ORDER_CREATED',
                  message: event.message,
                  createdAt: event.createdAt,
                  author: event.author ? {
                    name: `${event.author.firstName} ${event.author.lastName}`.trim() || event.author.email,
                    initials: `${event.author.firstName?.[0] || ''}${event.author.lastName?.[0] || ''}`.toUpperCase() || 'U'
                  } : undefined,
                  metadata: event.metadata || {},
                  isInternal: event.isInternal ?? true
                }))}
              onCommentAdded={() => refetch()}
            />
          </div>

          {/* Right Column - Sidebar */}
          <div className="lg:col-span-1">
            <OrderSidebar
              orderId={order.id}
              notes={order.notes}
              customer={order.customer}
              customerName={order.customerName}
              customerPhone={order.customerPhone}
              customerEmail={order.customerEmail}
              shippingAddress={order.shippingAddress}
              billingAddress={order.billingAddress}
              shippingRegion={order.shippingRegion}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
