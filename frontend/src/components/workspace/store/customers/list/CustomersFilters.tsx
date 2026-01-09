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
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';

interface CustomersFiltersProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  customerType: string | null;
  onCustomerTypeChange: (value: string | null) => void;
  region: string | null;
  onRegionChange: (value: string | null) => void;
}

const CUSTOMER_TYPES = [
  { value: 'individual', label: 'Individual' },
  { value: 'business', label: 'Business' },
];

const CAMEROON_REGIONS = [
  { value: 'centre', label: 'Centre' },
  { value: 'littoral', label: 'Littoral' },
  { value: 'west', label: 'West' },
  { value: 'northwest', label: 'Northwest' },
  { value: 'southwest', label: 'Southwest' },
  { value: 'adamawa', label: 'Adamawa' },
  { value: 'east', label: 'East' },
  { value: 'far_north', label: 'Far North' },
  { value: 'north', label: 'North' },
  { value: 'south', label: 'South' },
];

export function CustomersFilters({
  searchTerm,
  onSearchChange,
  customerType,
  onCustomerTypeChange,
  region,
  onRegionChange,
}: CustomersFiltersProps) {
  const hasActiveFilters = customerType || region;

  const clearFilters = () => {
    onCustomerTypeChange(null);
    onRegionChange(null);
  };

  return (
    <div className="flex items-center gap-2">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search customers by name or phone..."
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
                {[customerType, region].filter(Boolean).length}
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

          {/* Customer Type Filter */}
          <div className="p-2">
            <label className="text-sm font-medium mb-2 block">Customer Type</label>
            <Select
              value={customerType || 'all'}
              onValueChange={(value) => onCustomerTypeChange(value === 'all' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                {CUSTOMER_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Region Filter */}
          <div className="p-2">
            <label className="text-sm font-medium mb-2 block">Region</label>
            <Select
              value={region || 'all'}
              onValueChange={(value) => onRegionChange(value === 'all' ? null : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All regions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All regions</SelectItem>
                {CAMEROON_REGIONS.map((reg) => (
                  <SelectItem key={reg.value} value={reg.value}>
                    {reg.label}
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
