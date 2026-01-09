'use client';

import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/shadcn-ui/input';
import { OrderCard } from './OrderCard';
import { OrdersFilterChips } from './OrdersFilterChips';
import { MobileOrdersActionBar } from './MobileOrdersActionBar';
import type { GetOrdersQuery } from '@/services/graphql/admin-store/queries/orders/__generated__/getOrders.generated';

type OrderNode = NonNullable<
    NonNullable<
        NonNullable<GetOrdersQuery['orders']>['edges'][number]
    >['node']
>;

interface FilterChip {
    value: string;
    label: string;
    count?: number;
}

interface MobileOrdersListProps {
    orders: OrderNode[];
    workspaceId: string;
    // Search
    searchTerm: string;
    onSearchChange: (value: string) => void;
    // Filter chips
    chips: FilterChip[];
    activeChip: string;
    onChipChange: (value: string) => void;
    // Selection
    selectedOrders: string[];
    onSelectOrder: (orderId: string) => void;
    onLongPressOrder: (orderId: string) => void;
    onClearSelection: () => void;
    // Bulk actions
    onBulkArchive: () => void;
    onBulkMarkAsPaid: () => void;
    onBulkCancel: () => void;
    onBulkMarkAsShipped?: () => void;
    onBulkMarkAsDelivered?: () => void;
    // Loading
    isLoading?: boolean;
}

export function MobileOrdersList({
    orders,
    workspaceId,
    searchTerm,
    onSearchChange,
    chips,
    activeChip,
    onChipChange,
    selectedOrders,
    onSelectOrder,
    onLongPressOrder,
    onClearSelection,
    onBulkArchive,
    onBulkMarkAsPaid,
    onBulkCancel,
    onBulkMarkAsShipped,
    onBulkMarkAsDelivered,
    isLoading,
}: MobileOrdersListProps) {
    const isSelectionMode = selectedOrders.length > 0;

    return (
        <div className="flex flex-col gap-4 pb-32">
            {/* Search Bar */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
                <Input
                    placeholder="Search orders..."
                    value={searchTerm}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10 h-12 rounded-xl border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
                />
            </div>

            {/* Filter Chips */}
            <OrdersFilterChips
                chips={chips}
                activeChip={activeChip}
                onChipChange={onChipChange}
            />

            {/* Orders List */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
                </div>
            ) : orders.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <p className="text-zinc-500 dark:text-zinc-400">No orders found</p>
                    <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-1">
                        Try adjusting your filters
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-3">
                    {orders.map((order) => (
                        <OrderCard
                            key={order.id}
                            order={order}
                            workspaceId={workspaceId}
                            isSelected={selectedOrders.includes(order.id)}
                            isSelectionMode={selectedOrders.length > 0}
                            onSelect={onSelectOrder}
                            onLongPress={onLongPressOrder}
                        />
                    ))}
                </div>
            )}

            {/* Mobile Action Bar (fixed position) */}
            <MobileOrdersActionBar
                selectedCount={selectedOrders.length}
                onCancel={onClearSelection}
                onArchive={onBulkArchive}
                onMarkAsPaid={onBulkMarkAsPaid}
                onBulkCancel={onBulkCancel}
                onMarkAsShipped={onBulkMarkAsShipped}
                onMarkAsDelivered={onBulkMarkAsDelivered}
            />
        </div>
    );
}
