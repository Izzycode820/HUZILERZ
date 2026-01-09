import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import { Button } from '@/components/shadcn-ui/button';
import { MoreHorizontal, Archive, ArchiveRestore } from 'lucide-react';
import { OrderStatusBadge } from './OrderStatusBadge';
import { formatCurrency } from '@/utils/currency';
import type { GetOrdersQuery } from '@/services/graphql/admin-store/queries/orders/__generated__/getOrders.generated';

type OrderNode = NonNullable<
  NonNullable<
    NonNullable<GetOrdersQuery['orders']>['edges'][number]
  >['node']
>;

interface OrdersTableProps {
  orders: OrderNode[];
  selectedOrders: string[];
  onSelectOrder: (orderId: string) => void;
  onSelectAll: (selected: boolean) => void;
  workspaceId: string;
  onArchiveOrder?: (orderId: string) => void;
  onUnarchiveOrder?: (orderId: string) => void;
}

export function OrdersTable({
  orders,
  selectedOrders,
  onSelectOrder,
  onSelectAll,
  workspaceId,
  onArchiveOrder,
  onUnarchiveOrder,
}: OrdersTableProps) {
  const allSelected = orders.length > 0 && selectedOrders.length === orders.length;
  const someSelected = selectedOrders.length > 0 && selectedOrders.length < orders.length;

  const getChannelBadge = (orderSource: string) => {
    switch (orderSource?.toLowerCase()) {
      case 'whatsapp':
        return <span className="text-xs text-green-600 font-medium">WhatsApp</span>;
      case 'admin':
        return <span className="text-xs text-gray-600 font-medium">Admin</span>;
      case 'web':
        return <span className="text-xs text-blue-600 font-medium">Online Store</span>;
      default:
        return <span className="text-xs text-gray-600 font-medium">{orderSource}</span>;
    }
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="w-12">
              <Checkbox
                checked={allSelected}
                onCheckedChange={onSelectAll}
                aria-label="Select all orders"
                className={someSelected ? 'data-[state=checked]:bg-primary' : ''}
              />
            </TableHead>
            <TableHead>Order</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Channel</TableHead>
            <TableHead className="text-right">Total</TableHead>
            <TableHead>Payment status</TableHead>
            <TableHead>Fulfillment status</TableHead>
            <TableHead className="text-right">Items</TableHead>
            <TableHead>Delivery method</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.length === 0 ? (
            <TableRow>
              <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                No orders found
              </TableCell>
            </TableRow>
          ) : (
            orders.map((order) => (
              <TableRow key={order.id} className="hover:bg-muted/50">
                <TableCell>
                  <Checkbox
                    checked={selectedOrders.includes(order.id)}
                    onCheckedChange={() => onSelectOrder(order.id)}
                    aria-label={`Select order ${order.orderNumber}`}
                  />
                </TableCell>
                <TableCell>
                  <Link
                    href={`/workspace/${workspaceId}/store/orders/${order.id}`}
                    className="font-medium text-blue-600 hover:underline"
                  >
                    #{order.orderNumber}
                  </Link>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDistanceToNow(new Date(order.createdAt), { addSuffix: true })}
                </TableCell>
                <TableCell>
                  {order.customerName ? (
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{order.customerName}</span>
                      <span className="text-xs text-muted-foreground">{order.customerPhone}</span>
                    </div>
                  ) : (
                    <span className="text-sm text-muted-foreground">No customer</span>
                  )}
                </TableCell>
                <TableCell>
                  {getChannelBadge(order.orderSource)}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {order.currency} {formatCurrency(order.totalAmount)}
                </TableCell>
                <TableCell>
                  <OrderStatusBadge status={order.paymentStatus} type="payment" />
                </TableCell>
                <TableCell>
                  <OrderStatusBadge status={order.status} type="fulfillment" />
                </TableCell>
                <TableCell className="text-right text-sm">
                  {order.itemCount} {order.itemCount === 1 ? 'item' : 'items'}
                </TableCell>
                <TableCell className="text-sm">
                  {order.isCashOnDelivery ? (
                    <span className="text-xs">Cash on Delivery</span>
                  ) : (
                    <span className="text-xs capitalize">{order.paymentMethod?.replace('_', ' ')}</span>
                  )}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreHorizontal className="h-4 w-4" />
                        <span className="sr-only">Open menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {order.canBeArchived && onArchiveOrder && (
                        <DropdownMenuItem onClick={() => onArchiveOrder(order.id)}>
                          <Archive className="mr-2 h-4 w-4" />
                          Archive
                        </DropdownMenuItem>
                      )}
                      {order.canBeUnarchived && onUnarchiveOrder && (
                        <DropdownMenuItem onClick={() => onUnarchiveOrder(order.id)}>
                          <ArchiveRestore className="mr-2 h-4 w-4" />
                          Unarchive
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
