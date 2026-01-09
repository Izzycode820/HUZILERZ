'use client';

import { useForm } from 'react-hook-form';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
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
import { Save } from 'lucide-react';

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

export interface CustomerFormData {
  phone: string;
  name: string;
  email?: string;
  customerType?: string;
  city?: string;
  region?: string;
  address?: string;
  tags?: string;
  smsNotifications?: boolean;
  whatsappNotifications?: boolean;
}

export interface CustomerFormProps {
  initialData?: Partial<CustomerFormData>;
  onSubmit?: (data: CustomerFormData) => void;
  isLoading?: boolean;
}

export function CustomerForm({
  initialData,
  onSubmit,
  isLoading = false,
}: CustomerFormProps) {
  const {
    register,
    handleSubmit,
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
      ...initialData,
    },
  });

  const region = watch('region');
  const customerType = watch('customerType');
  const smsNotifications = watch('smsNotifications');
  const whatsappNotifications = watch('whatsappNotifications');

  const saveHandler = handleSubmit((data) => onSubmit?.(data));

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main Column */}
        <div className="flex-1 max-w-3xl space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
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
                        CAMEROON_PHONE_REGEX.test(value) ||
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
            </CardContent>
          </Card>

          {/* Location Information */}
          <Card>
            <CardHeader>
              <CardTitle>Location</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* City */}
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input id="city" {...register('city')} placeholder="Douala" />
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
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Additional Information */}
          <Card>
            <CardHeader>
              <CardTitle>Additional Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
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
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Column */}
        <div className="w-full lg:w-96 lg:flex-shrink-0 space-y-6">
          {/* Action Buttons (Sticky) */}
          <Card className="p-4 space-y-3 sticky top-6 z-10">
            <Button
              onClick={saveHandler}
              className="w-full"
              disabled={isLoading}
            >
              <Save className="mr-2 h-4 w-4" />
              {isLoading ? 'Saving...' : 'Save customer'}
            </Button>
          </Card>

          {/* Notification Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
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
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
