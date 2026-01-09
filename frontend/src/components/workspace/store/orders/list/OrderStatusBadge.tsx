import { Badge } from '@/components/shadcn-ui/badge';

interface OrderStatusBadgeProps {
  status: string;
  type: 'payment' | 'fulfillment' | 'order';
}

export function OrderStatusBadge({ status, type }: OrderStatusBadgeProps) {
  const getStatusConfig = () => {
    if (type === 'payment') {
      switch (status?.toLowerCase()) {
        case 'paid':
          return { label: 'Paid', variant: 'default' as const, className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900/30' };
        case 'pending':
          return { label: 'Pending', variant: 'secondary' as const, className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300 hover:bg-yellow-100 dark:hover:bg-yellow-900/30' };
        case 'unpaid':
          return { label: 'Unpaid', variant: 'secondary' as const, className: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800' };
        case 'refunded':
          return { label: 'Refunded', variant: 'outline' as const, className: 'text-gray-600 dark:text-gray-400' };
        default:
          return { label: status || 'Unknown', variant: 'outline' as const, className: '' };
      }
    }

    if (type === 'fulfillment') {
      switch (status?.toLowerCase()) {
        case 'unfulfilled':
          return { label: 'Unfulfilled', variant: 'secondary' as const, className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300 hover:bg-yellow-100 dark:hover:bg-yellow-900/30' };
        case 'fulfilled':
          return { label: 'Fulfilled', variant: 'default' as const, className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900/30' };
        case 'partially_fulfilled':
          return { label: 'Partially fulfilled', variant: 'secondary' as const, className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30' };
        case 'cancelled':
          return { label: 'Cancelled', variant: 'destructive' as const, className: '' };
        default:
          return { label: status || 'Unknown', variant: 'outline' as const, className: '' };
      }
    }

    // Order status
    switch (status?.toLowerCase()) {
      case 'open':
        return { label: 'Open', variant: 'default' as const, className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30' };
      case 'archived':
        return { label: 'Archived', variant: 'secondary' as const, className: '' };
      case 'cancelled':
        return { label: 'Cancelled', variant: 'destructive' as const, className: '' };
      default:
        return { label: status || 'Unknown', variant: 'outline' as const, className: '' };
    }
  };

  const config = getStatusConfig();

  return (
    <Badge variant={config.variant} className={config.className}>
      {config.label}
    </Badge>
  );
}
