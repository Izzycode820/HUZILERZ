import type { GetCustomersForOrderQuery } from '@/services/graphql/admin-store/queries/customers/__generated__/GetCustomersForOrder.generated';
import type { CreateCustomerMutation } from '@/services/graphql/admin-store/mutations/customers/__generated__/CreateCustomer.generated';

// Extract customer from codegen query
export type CustomerOption = NonNullable<
  NonNullable<
    NonNullable<GetCustomersForOrderQuery['customers']>['edges'][number]
  >['node']
>;

// Customer form data for modal (Cameroon context)
export interface CustomerFormData {
  phone: string;           // Required: +237XXXXXXXXX
  name: string;            // Required
  email?: string;          // Optional
  customerType?: string;   // 'individual' or 'business'
  city?: string;
  region?: string;         // Cameroon region
  address?: string;        // Full address
  tags?: string;           // Comma-separated tags
  smsNotifications?: boolean;
  whatsappNotifications?: boolean;
}

export interface CustomerSectionProps {
  customerId: string;
  onCustomerIdChange: (customerId: string) => void;
}

export interface CreateCustomerModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCustomerCreated: (customerId: string) => void;
}

export interface CustomerSearchDropdownProps {
  customerId: string;
  onCustomerIdChange: (customerId: string) => void;
  onCreateCustomerClick: () => void;
}
