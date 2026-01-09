# Customer Section - Build Guide

## Objective
Build customer selection section with dropdown search and inline customer creation modal.

---

## File Structure
```
orders/form/customer/
├── CustomerSection.tsx          # Main component
├── CustomerSearchDropdown.tsx   # Searchable dropdown
├── CreateCustomerModal.tsx      # Add customer modal
├── types.ts                     # Type definitions
└── index.ts                     # Clean exports
```

---

## 1. types.ts

```typescript
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
  city?: string;
  region?: string;         // Cameroon region
  default_address?: {
    street: string;
    city: string;
    region: string;
    postal_code?: string;
  };
}

export interface CustomerSectionProps {
  customerId: string;
  onCustomerIdChange: (customerId: string) => void;
}
```

---

## 2. CustomerSearchDropdown.tsx

**UI Pattern:** Same as ProductOrganizationSection (Command + Popover)

**shadcn components:**
- Popover
- Command (search with keyboard nav)
- CommandInput (search field)
- CommandItem (customer list)
- Button

**GraphQL:**
- Use `useGetCustomersForOrderQuery` from codegen
- Query all customers (no pagination for MVP)

**Display format:**
```
John Doe
+237 670 123 456
```

**Behaviors:**
- Search filters by name OR phone
- Show "Add customer" button at top of list
- On select → call `onCustomerIdChange(customer.id)`
- Selected customer shows as badge with X to clear

---

## 3. CreateCustomerModal.tsx

**Form fields (Cameroon context):**

```
┌─ Modal ────────────────────────┐
│ Add customer              [X]   │
├─────────────────────────────────┤
│ Phone number *                  │
│ [+237 _________]                │
│                                 │
│ Full name *                     │
│ [____________]                  │
│                                 │
│ Email (optional)                │
│ [____________]                  │
│                                 │
│ City                            │
│ [____________]                  │
│                                 │
│ Region                          │
│ [Dropdown: Centre, Littoral...] │
│                                 │
│           [Cancel]  [Add]       │
└─────────────────────────────────┘
```

**Cameroon regions (match backend):**
```typescript
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
] as const;
```

**Validation:**
- Phone: Required, must start with +237, length 13 chars
- Name: Required, min 2 chars
- Email: Optional, valid email format

**shadcn components:**
- Dialog (modal)
- Form (react-hook-form)
- Input
- Select (region dropdown)
- Button

**GraphQL:**
- Use `useCreateCustomerMutation` from codegen
- On success → call `onCustomerCreated(newCustomer.id)`, close modal
- On error → show toast/error message

---

## 4. CustomerSection.tsx

**Layout:**
```
┌─ Card ─────────────────────────┐
│ Customer                        │
├─────────────────────────────────┤
│ [Search or create customer ▼]  │
│                                 │
│ Empty state: "No customer sel" │
│ OR                              │
│ Selected: Badge with name+phone │
└─────────────────────────────────┘
```

**Props:**
```typescript
interface Props {
  customerId: string;
  onCustomerIdChange: (customerId: string) => void;
}
```

**Behavior:**
- Renders CustomerSearchDropdown
- On "Add customer" click → opens CreateCustomerModal
- After customer created → auto-selects new customer
- Displays selected customer info below dropdown

---

## 5. GraphQL Files

### Query: `GetCustomersForOrder.graphql`

```graphql
query GetCustomersForOrder($first: Int, $search: String) {
  customers(first: $first, name_Icontains: $search) {
    edges {
      node {
        id
        name
        phone
        email
        city
        region
      }
    }
  }
}
```

### Mutation: `CreateCustomer.graphql`

```graphql
mutation CreateCustomer($customerData: CustomerCreateInput!) {
  createCustomer(customerData: $customerData) {
    success
    customer {
      id
      name
      phone
      email
      city
      region
    }
    message
    error
  }
}
```

**After creating:** Run `npm run codegen`

---

## 6. Phone Input Validation

**Pattern:**
```typescript
const CAMEROON_PHONE_REGEX = /^\+237[0-9]{9}$/;

function validateCameroonPhone(phone: string): boolean {
  return CAMEROON_PHONE_REGEX.test(phone);
}

// Error message: "Phone must be in format +237XXXXXXXXX"
```

**Auto-formatting (optional):**
- On input, add +237 prefix if user types digits only
- Format: +237 670 123 456 (with spaces for readability)

---

## Integration with Parent Form

```typescript
const [customerId, setCustomerId] = useState('');

<CustomerSection
  customerId={customerId}
  onCustomerIdChange={setCustomerId}
/>

// On form submit
const orderPayload = {
  customer_id: customerId, // Required
  items: items.map(...),
  payment_method: paymentMethod,
  shipping_address: {
    street: '...',
    city: '...',
    region: '...',
    country: 'Cameroon',
  },
};
```

---

## Backend Input Type

**From backend:** `CustomerCreateInput`
```python
phone: String (required)
name: String (required)
email: String (optional)
customer_type: String (default: 'individual')
city: String
region: String
default_address: CustomerAddressInput
addresses: [CustomerAddressInput]
tags: [String]
sms_notifications: Boolean (default: true)
email_notifications: Boolean (default: false)
whatsapp_notifications: Boolean (default: true)
```

**MVP fields to use:**
- phone (required)
- name (required)
- email (optional)
- city (optional)
- region (optional)

---

## Key Points

1. **Phone-first** - Phone is primary identifier, required field
2. **Cameroon context** - +237 prefix, 10 regions dropdown
3. **Auto-select after create** - New customer auto-populates in form
4. **Search both name and phone** - Filter customers by either
5. **Form validation** - Use react-hook-form with zod schema

---

## Testing Checklist

- [ ] Dropdown opens and shows customers
- [ ] Search filters by name
- [ ] Search filters by phone
- [ ] "Add customer" button opens modal
- [ ] Phone validation works (+237 format)
- [ ] Required field validation works
- [ ] Customer created successfully
- [ ] New customer auto-selected after creation
- [ ] Selected customer displays correctly
- [ ] Clear selection works
