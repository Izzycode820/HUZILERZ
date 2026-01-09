import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { CustomerSearchDropdown } from './CustomerSearchDropdown';
import { CreateCustomerModal } from './CreateCustomerModal';
import type { CustomerSectionProps } from './types';

export function CustomerSection({
  customerId,
  onCustomerIdChange,
}: CustomerSectionProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCustomerCreated = (newCustomerId: string) => {
    onCustomerIdChange(newCustomerId);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Customer</CardTitle>
        </CardHeader>
        <CardContent>
          <CustomerSearchDropdown
            customerId={customerId}
            onCustomerIdChange={onCustomerIdChange}
            onCreateCustomerClick={() => setIsModalOpen(true)}
          />
        </CardContent>
      </Card>

      {/* Create Customer Modal */}
      <CreateCustomerModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        onCustomerCreated={handleCustomerCreated}
      />
    </>
  );
}
