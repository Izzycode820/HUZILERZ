'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import Link from 'next/link';
import { CustomerForm, type CustomerFormData } from '@/components/workspace/store/customers/form/CustomerForm';
import { useMutation } from '@apollo/client/react';
import { CreateCustomerDocument } from '@/services/graphql/admin-store/mutations/customers/__generated__/CreateCustomer.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';

export default function AddCustomerPage() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const [createCustomer, { loading }] = useMutation(CreateCustomerDocument, {
    onCompleted: (data) => {
      if (data.createCustomer?.success && data.createCustomer?.customer) {
        toast.success(`Customer ${data.createCustomer.customer.name} created successfully`);
        router.push(`/workspace/${currentWorkspace?.id}/store/customers`);
      } else {
        toast.error(data.createCustomer?.error || 'Failed to create customer');
      }
    },
    onError: (error) => {
      toast.error(error.message || 'An unexpected error occurred');
    },
  });

  const handleSubmit = async (data: CustomerFormData) => {
    // Parse tags if provided
    const tagsArray = data.tags
      ? data.tags.split(',').map(tag => tag.trim()).filter(Boolean)
      : [];

    await createCustomer({
      variables: {
        customerData: {
          phone: data.phone,
          name: data.name,
          email: data.email || undefined,
          customerType: data.customerType || 'individual',
          city: data.city || undefined,
          region: data.region || undefined,
          address: data.address || undefined,
          tags: tagsArray.length > 0 ? JSON.stringify(tagsArray) : undefined,
          smsNotifications: data.smsNotifications ?? true,
          whatsappNotifications: data.whatsappNotifications ?? true,
        },
      },
    });
  };

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <div className="px-4 lg:px-6">
          <div className="flex items-center gap-4 mb-4">
            <Link href={`/workspace/${currentWorkspace.id}/store/customers`}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <h1 className="text-2xl font-bold">Add Customer</h1>
          </div>
          <p className="text-muted-foreground">
            Create a new customer for your store
          </p>
        </div>

        {/* Main Form */}
        <div className="px-4 lg:px-6">
          <CustomerForm onSubmit={handleSubmit} isLoading={loading} />
        </div>
      </div>
    </div>
  );
}
