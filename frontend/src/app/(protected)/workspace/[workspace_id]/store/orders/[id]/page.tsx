import OrderDetailsContainer from '@/components/workspace/store/orders/details/OrderDetailsContainer';

interface OrderDetailPageProps {
  params: Promise<{
    id: string;
    workspace_id: string;
  }>;
}

export default async function OrderDetailPage({ params }: OrderDetailPageProps) {
  const { id } = await params;
  return (
    <div className="@container/main flex flex-1 flex-col">
      <OrderDetailsContainer orderId={id} />
    </div>
  );
}
