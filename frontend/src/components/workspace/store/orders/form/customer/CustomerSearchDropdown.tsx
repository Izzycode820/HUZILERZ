import { useState, useMemo } from 'react';
import { Check, ChevronsUpDown, Plus, X } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from '@/components/shadcn-ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/shadcn-ui/popover';
import { Badge } from '@/components/shadcn-ui/badge';
import { useQuery } from '@apollo/client/react';
import { GetCustomersForOrderDocument } from '@/services/graphql/admin-store/queries/customers/__generated__/GetCustomersForOrder.generated';
import { cn } from '@/lib/utils';
import type { CustomerSearchDropdownProps, CustomerOption } from './types';

export function CustomerSearchDropdown({
  customerId,
  onCustomerIdChange,
  onCreateCustomerClick,
}: CustomerSearchDropdownProps) {
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Query customers - show 6 initially, search for more
  const { data, loading } = useQuery(GetCustomersForOrderDocument, {
    variables: {
      search: searchTerm, // Empty string on mount loads first 6 customers
      first: 6,
    },
  });

  const customers = useMemo(() => {
    return (
      data?.customers?.edges
        ?.map(edge => edge?.node)
        .filter((node): node is NonNullable<typeof node> => node != null) || []
    );
  }, [data]);

  const selectedCustomer = customers.find(c => c?.id === customerId);

  const handleSelect = (customer: CustomerOption) => {
    onCustomerIdChange(customer.id);
    setOpen(false);
  };

  const handleClear = () => {
    onCustomerIdChange('');
  };

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between text-left font-normal"
          >
            <span className="truncate">
              {selectedCustomer ? selectedCustomer.name : 'Search or create a customer'}
            </span>
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0" align="start">
          <Command>
            <CommandInput
              placeholder="Search customers..."
              value={searchTerm}
              onValueChange={setSearchTerm}
            />
            <CommandEmpty>
              <div className="p-4 text-center">
                <p className="text-sm text-muted-foreground mb-2">No customer found</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setOpen(false);
                    onCreateCustomerClick();
                  }}
                  className="w-full"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create a new customer
                </Button>
              </div>
            </CommandEmpty>
            <CommandGroup>
              {/* Create new customer button at top */}
              <CommandItem
                onSelect={() => {
                  setOpen(false);
                  onCreateCustomerClick();
                }}
                className="border-b"
              >
                <Plus className="mr-2 h-4 w-4" />
                Create a new customer
              </CommandItem>

              {/* Customer list */}
              {loading ? (
                <CommandItem disabled>Loading customers...</CommandItem>
              ) : (
                customers.map((customer) => (
                  <CommandItem
                    key={customer.id}
                    onSelect={() => handleSelect(customer)}
                    className="cursor-pointer"
                  >
                    <Check
                      className={cn(
                        'mr-2 h-4 w-4',
                        customerId === customer.id ? 'opacity-100' : 'opacity-0'
                      )}
                    />
                    <div className="flex flex-col">
                      <span className="font-medium">{customer.name}</span>
                      <span className="text-sm text-muted-foreground">
                        {customer.phone}
                      </span>
                    </div>
                  </CommandItem>
                ))
              )}
            </CommandGroup>
          </Command>
        </PopoverContent>
      </Popover>

      {/* Selected customer badge */}
      {selectedCustomer && (
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="gap-1">
            <span>{selectedCustomer.name}</span>
            <span className="text-muted-foreground">•</span>
            <span>{selectedCustomer.phone}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
              onClick={handleClear}
            >
              <X className="h-3 w-3" />
            </Button>
          </Badge>
        </div>
      )}
    </div>
  );
}
