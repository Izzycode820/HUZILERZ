import OrderDetailsContainer from '@/components/workspace/store/orders/details/OrderDetailsContainer';

interface OrderDetailPageProps {
  params: {
    id: string;
    workspace_id: string;
  };
}

export default function OrderDetailPage({ params }: OrderDetailPageProps) {
  return (
    <div className="@container/main flex flex-1 flex-col">
      <OrderDetailsContainer orderId={params.id} />
    </div>
  );
}
