import { useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/shadcn-ui/dialog';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select';
import { Separator } from '@/components/shadcn-ui/separator';
import { useMutation } from '@apollo/client/react';
import { CreateCustomerDocument } from '@/services/graphql/admin-store/mutations/customers/__generated__/CreateCustomer.generated';
import { toast } from 'sonner';
import type { CreateCustomerModalProps, CustomerFormData } from './types';

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

const CUSTOMER_TYPES = [
  { value: 'individual', label: 'Individual' },
  { value: 'business', label: 'Business' },
] as const;

const CAMEROON_PHONE_REGEX = /^\+237[0-9]{9}$/;

function validateCameroonPhone(phone: string): boolean {
  return CAMEROON_PHONE_REGEX.test(phone);
}

export function CreateCustomerModal({
  open,
  onOpenChange,
  onCustomerCreated,
}: CreateCustomerModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
    setValue,
    watch,
  } = useForm<CustomerFormData>({
    defaultValues: {
      phone: '+237',
      name: '',
      email: '',
      customerType: 'individual',
      city: '',
      region: '',
      address: '',
      tags: '',
      smsNotifications: true,
      whatsappNotifications: true,
    },
  });

  const region = watch('region');
  const customerType = watch('customerType');
  const smsNotifications = watch('smsNotifications');
  const whatsappNotifications = watch('whatsappNotifications');

  const [createCustomer, { loading }] = useMutation(CreateCustomerDocument, {
    onCompleted: (data) => {
      if (data.createCustomer?.success && data.createCustomer?.customer) {
        toast.success(`Customer ${data.createCustomer.customer.name} created successfully`);
        onCustomerCreated(data.createCustomer.customer.id);
        onOpenChange(false);
        reset();
      } else {
        toast.error(data.createCustomer?.error || 'Failed to create customer');
      }
    },
    onError: (error) => {
      toast.error(error.message || 'An unexpected error occurred');
    },
  });

  const onSubmit = async (data: CustomerFormData) => {
    // Validate phone
    if (!validateCameroonPhone(data.phone)) {
      toast.error('Phone must be in format +237XXXXXXXXX');
      return;
    }

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

  const handleCancel = () => {
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create a new customer</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Basic Information</h3>

            <div className="grid grid-cols-2 gap-4">
              {/* Phone Number */}
              <div className="space-y-2">
                <Label htmlFor="phone">
                  Phone number <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="phone"
                  {...register('phone', {
                    required: 'Phone number is required',
                    validate: (value) =>
                      validateCameroonPhone(value) ||
                      'Phone must be in format +237XXXXXXXXX',
                  })}
                  placeholder="+237 670 123 456"
                  className={errors.phone ? 'border-red-500' : ''}
                />
                {errors.phone && (
                  <p className="text-sm text-red-500">{errors.phone.message}</p>
                )}
              </div>

              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="name">
                  Full name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="name"
                  {...register('name', {
                    required: 'Name is required',
                    minLength: {
                      value: 2,
                      message: 'Name must be at least 2 characters',
                    },
                  })}
                  placeholder="John Doe"
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  {...register('email', {
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: 'Invalid email format',
                    },
                  })}
                  placeholder="john.doe@example.com"
                  className={errors.email ? 'border-red-500' : ''}
                />
                {errors.email && (
                  <p className="text-sm text-red-500">{errors.email.message}</p>
                )}
              </div>

              {/* Customer Type */}
              <div className="space-y-2">
                <Label htmlFor="customerType">Customer type</Label>
                <Select
                  value={customerType || 'individual'}
                  onValueChange={(value) => setValue('customerType', value)}
                >
                  <SelectTrigger id="customerType">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {CUSTOMER_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          {/* Location Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Location</h3>

            <div className="grid grid-cols-2 gap-4">
              {/* City */}
              <div className="space-y-2">
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  {...register('city')}
                  placeholder="Douala"
                />
              </div>

              {/* Region */}
              <div className="space-y-2">
                <Label htmlFor="region">Region</Label>
                <Select
                  value={region || ''}
                  onValueChange={(value) => setValue('region', value)}
                >
                  <SelectTrigger id="region">
                    <SelectValue placeholder="Select region" />
                  </SelectTrigger>
                  <SelectContent>
                    {CAMEROON_REGIONS.map((reg) => (
                      <SelectItem key={reg.value} value={reg.value}>
                        {reg.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Address */}
            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Textarea
                id="address"
                {...register('address')}
                placeholder="Enter full address"
                rows={2}
              />
            </div>
          </div>

          <Separator />

          {/* Additional Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Additional Information</h3>

            {/* Tags */}
            <div className="space-y-2">
              <Label htmlFor="tags">Tags</Label>
              <Input
                id="tags"
                {...register('tags')}
                placeholder="VIP, Wholesale, Returning (comma-separated)"
              />
              <p className="text-xs text-muted-foreground">
                Separate multiple tags with commas
              </p>
            </div>
          </div>

          <Separator />

          {/* Notification Preferences */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Notification Preferences</h3>

            <div className="space-y-3">
              {/* SMS Notifications */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="smsNotifications"
                  checked={smsNotifications}
                  onCheckedChange={(checked) =>
                    setValue('smsNotifications', checked as boolean)
                  }
                />
                <Label
                  htmlFor="smsNotifications"
                  className="text-sm font-normal cursor-pointer"
                >
                  SMS notifications
                </Label>
              </div>

              {/* WhatsApp Notifications */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="whatsappNotifications"
                  checked={whatsappNotifications}
                  onCheckedChange={(checked) =>
                    setValue('whatsappNotifications', checked as boolean)
                  }
                />
                <Label
                  htmlFor="whatsappNotifications"
                  className="text-sm font-normal cursor-pointer"
                >
                  WhatsApp notifications
                </Label>
              </div>
            </div>
          </div>

          {/* Footer */}
          <DialogFooter className="sticky bottom-0 bg-background pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Add customer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
