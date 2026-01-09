"use client"

import OrdersListContainer from '@/components/workspace/store/orders/list/OrdersListContainer';

export default function OrdersPage() {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <OrdersListContainer />
      </div>
    </div>
  );
}
