import { Search, SlidersHorizontal } from 'lucide-react';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';

interface OrdersFiltersProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  paymentStatus: string | null;
  onPaymentStatusChange: (value: string | null) => void;
  paymentMethod: string | null;
  onPaymentMethodChange: (value: string | null) => void;
  orderSource: string | null;
  onOrderSourceChange: (value: string | null) => void;
  shippingRegion: string | null;
  onShippingRegionChange: (value: string | null) => void;
}

const PAYMENT_STATUSES = [
  { value: 'PAID', label: 'Paid' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'REFUNDED', label: 'Refunded' },
];

const PAYMENT_METHODS = [
  { value: 'cash_on_delivery', label: 'Cash on Delivery' },
  { value: 'mobile_money', label: 'Mobile Money' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Credit/Debit Card' },
];

const ORDER_SOURCES = [
  { value: 'WHATSAPP', label: 'WhatsApp' },
  { value: 'ADMIN', label: 'Admin' },
  { value: 'WEB', label: 'Online Store' },
];

const CAMEROON_REGIONS = [
  { value: 'CENTRE', label: 'Centre' },
  { value: 'LITTORAL', label: 'Littoral' },
  { value: 'WEST', label: 'West' },
  { value: 'NORTHWEST', label: 'Northwest' },
  { value: 'SOUTHWEST', label: 'Southwest' },
  { value: 'ADAMAWA', label: 'Adamawa' },
  { value: 'EAST', label: 'East' },
  { value: 'FAR_NORTH', label: 'Far North' },
  { value: 'NORTH', label: 'North' },
  { value: 'SOUTH', label: 'South' },
];

export function OrdersFilters({
  searchTerm,
  onSearchChange,
  paymentStatus,
  onPaymentStatusChange,
  paymentMethod,
  onPaymentMethodChange,
  orderSource,
  onOrderSourceChange,
  shippingRegion,
  onShippingRegionChange,
}: OrdersFiltersProps) {
  const hasActiveFilters = paymentStatus || paymentMethod || orderSource || shippingRegion;

  const clearFilters = () => {
    onPaymentStatusChange(null);
    onPaymentMethodChange(null);
    onOrderSourceChange(null);
    onShippingRegionChange(null);
  };

  return (
    <div className="flex items-center gap-2">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search orders..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Filters Dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="gap-2">
            <SlidersHorizontal className="h-4 w-4" />
            Filters
            {hasActiveFilters && (
              <span className="ml-1 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                {[paymentStatus, paymentMethod, orderSource, shippingRegion].filter(Boolean).length}
              </span>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>Filters</span>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="h-auto p-1 text-xs"
              >
                Clear all
              </Button>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {/* Payment Status Filter */}
          <div className="p-2">
            <label className="text-sm font-medium mb-2 block">Payment Status</label>
            <Select
              value={paymentStatus || 'all'}
              onValueChange={(value) => onPaymentStatusChange(value === 'all' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {PAYMENT_STATUSES.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Payment Method Filter */}
          <div className="p-2">
            <label className="text-sm font-medium mb-2 block">Payment Method</label>
            <Select
              value={paymentMethod || 'all'}
              onValueChange={(value) => onPaymentMethodChange(value === 'all' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All methods" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All methods</SelectItem>
                {PAYMENT_METHODS.map((method) => (
                  <SelectItem key={method.value} value={method.value}>
                    {method.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Order Source Filter */}
          <div className="p-2">
            <label className="text-sm font-medium mb-2 block">Order Source</label>
            <Select
              value={orderSource || 'all'}
              onValueChange={(value) => onOrderSourceChange(value === 'all' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All sources" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All sources</SelectItem>
                {ORDER_SOURCES.map((source) => (
                  <SelectItem key={source.value} value={source.value}>
                    {source.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Shipping Region Filter */}
          <div className="p-2">
            <label className="text-sm font-medium mb-2 block">Shipping Region</label>
            <Select
              value={shippingRegion || 'all'}
              onValueChange={(value) => onShippingRegionChange(value === 'all' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All regions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All regions</SelectItem>
                {CAMEROON_REGIONS.map((region) => (
                  <SelectItem key={region.value} value={region.value}>
                    {region.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
