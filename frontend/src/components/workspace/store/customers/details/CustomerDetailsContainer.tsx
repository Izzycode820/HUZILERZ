'use client';

import { useQuery } from '@apollo/client/react';
import { GetCustomerDocument } from '@/services/graphql/admin-store/queries/customers/__generated__/GetCustomer.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { useRouter } from 'next/navigation';
import { formatDistanceToNow } from 'date-fns';
import { CustomerDetailsHeader } from './CustomerDetailsHeader';
import { CustomerStatsBar } from './CustomerStatsBar';
import { LastOrderCard } from './LastOrderCard';
import { CustomerTimeline } from './CustomerTimeline';
import { CustomerSidebar } from './CustomerSidebar';

interface CustomerDetailsContainerProps {
  customerId: string;
}

export default function CustomerDetailsContainer({ customerId }: CustomerDetailsContainerProps) {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const { data, loading, error } = useQuery(GetCustomerDocument, {
    variables: { id: customerId },
    skip: !currentWorkspace,
    fetchPolicy: 'cache-and-network',
  });

  const customer = data?.customer;

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading customer...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !customer) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-destructive">
          <p>Failed to load customer</p>
          <p className="text-sm text-muted-foreground">
            {error?.message || 'Customer not found'}
          </p>
        </div>
      </div>
    );
  }

  const customerSince = formatDistanceToNow(new Date(customer.createdAt), { addSuffix: false });
  const rfmGroup = customer.isHighValue ? 'Champions' : customer.isFrequentBuyer ? 'Loyal' : 'Prospects';

  const handleCreateOrder = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/orders/add?customer=${customer.id}`);
  };

  return (
    <div className="@container/main flex flex-1 flex-col gap-4">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <CustomerDetailsHeader customerName={customer.name} />

        {/* Stats Bar */}
        <CustomerStatsBar
          totalSpent={customer.totalSpent}
          totalOrders={customer.totalOrders}
          customerSince={customerSince}
          rfmGroup={rfmGroup}
        />

        {/* Main Content Grid */}
        <div className="px-4 lg:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Last Order Placed */}
              <LastOrderCard
                totalOrders={customer.totalOrders}
                lastOrderAt={customer.lastOrderAt}
                onCreateOrder={handleCreateOrder}
              />

              {/* Timeline */}
              <CustomerTimeline
                events={(customer.history || [])
                  .filter((event): event is NonNullable<typeof event> => event !== null)
                  .map(event => ({
                    id: event.id,
                    type: 'HISTORY', // generic type for now
                    message: event.displayMessage || 'Event occurred',
                    createdAt: event.createdAt,
                    author: event.performedBy ? {
                      name: `${event.performedBy.firstName || ''} ${event.performedBy.lastName || ''}`.trim() || event.performedBy.email,
                      initials: `${event.performedBy.firstName?.[0] || ''}${event.performedBy.lastName?.[0] || ''}`.toUpperCase() || 'U'
                    } : undefined,
                    metadata: event.details || {}
                  }))}
              />
            </div>

            {/* Right Column - Sidebar */}
            <CustomerSidebar customer={customer} />
          </div>
        </div>
      </div>
    </div>
  );
}
