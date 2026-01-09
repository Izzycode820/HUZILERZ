'use client';

import React, { useState } from 'react';
import { useMutation, useQuery } from '@apollo/client/react';
import { useRouter, useParams } from 'next/navigation';
import { PurchaseDomainDocument } from '@/services/graphql/domains/mutations/purchases/__generated__/purchaseDomain.generated';
import { PrepareDomainCheckoutDocument } from '@/services/graphql/domains/mutations/purchases/__generated__/prepareDomainCheckout.generated';
import { GetPurchaseStatusDocument } from '@/services/graphql/domains/queries/purchases/__generated__/getPurchaseStatus.generated';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Switch } from '@/components/shadcn-ui/switch';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select';
import { Globe, Info, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

interface PurchaseConfirmationProps {
  domain: string;
  priceUsd?: number;
}

export function PurchaseConfirmation({ domain }: PurchaseConfirmationProps) {
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspace_id as string;

  const [autoRenew, setAutoRenew] = useState(true);
  const [pollingId, setPollingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    storeName: '',
    phone: '',
    faxNumber: '',
    country: 'Cameroon',
    address: '',
    apartment: '',
    city: '',
    state: '',
    postalCode: '',
  });

  // Prepare checkout mutation (to get authoritative pricing)
  const [prepareCheckout, { data: prepareData, loading: prepareLoading, error: prepareError }] = useMutation(PrepareDomainCheckoutDocument);

  // Purchase domain mutation
  const [purchaseDomain, { loading: purchaseLoading }] = useMutation(PurchaseDomainDocument);

  // Poll purchase status
  const { data: statusData } = useQuery(GetPurchaseStatusDocument, {
    variables: { purchaseId: pollingId || '' },
    skip: !pollingId,
    pollInterval: pollingId ? 2000 : 0, // Poll every 2 seconds only when pollingId is set
  });

  // Fetch pricing on mount
  React.useEffect(() => {
    if (domain && workspaceId) {
      prepareCheckout({
        variables: {
          domain,
          workspaceId
        }
      });
    }
  }, [domain, workspaceId, prepareCheckout]);

  // Handle polling completion
  React.useEffect(() => {
    if (statusData?.purchaseStatus) {
      const status = statusData.purchaseStatus.paymentStatus;
      if (status === 'COMPLETED') {
        toast.success('Domain purchase successful!');
        router.push(`/workspace/${workspaceId}/store/settings/domains`);
        setPollingId(null);
      } else if (status === 'FAILED') {
        toast.error(statusData.purchaseStatus.errorMessage || 'Purchase failed');
        setPollingId(null);
      }
    }
  }, [statusData, router, workspaceId]);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prepareData?.prepareDomainCheckout?.success) {
      toast.error('Unable to verify domain pricing. Please try refreshing.');
      return;
    }

    // Validate required fields
    const requiredFields = ['firstName', 'lastName', 'email', 'phone', 'address', 'city', 'state', 'postalCode'];
    const missingFields = requiredFields.filter((field) => !formData[field as keyof typeof formData]);

    if (missingFields.length > 0) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      const { data } = await purchaseDomain({
        variables: {
          workspaceId,
          domain,
          registrationPeriodYears: 1,
          phone: formData.phone,
          address: `${formData.address}${formData.apartment ? ', ' + formData.apartment : ''}`,
          city: formData.city,
          state: formData.state,
          postalCode: formData.postalCode,
          country: formData.country,
        },
      });

      if (data?.purchaseDomain?.success && data.purchaseDomain.purchase?.id) {
        setPollingId(data.purchaseDomain.purchase.id);
        toast.message('Payment initiated', {
          description: 'Please check your phone to confirm the transaction.',
          duration: 10000,
        });
      } else {
        toast.error(data?.purchaseDomain?.error || 'Failed to initiate purchase');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to purchase domain');
      console.error('Purchase domain error:', err);
    }
  };

  const renewalDate = new Date();
  renewalDate.setFullYear(renewalDate.getFullYear() + 1);

  // Loading state
  if (prepareLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground animate-pulse">Loading domain pricing...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (prepareError || (prepareData?.prepareDomainCheckout && !prepareData.prepareDomainCheckout.success)) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Card className="w-full max-w-md border-red-200 bg-red-50">
          <CardContent className="pt-6 text-center">
            <h3 className="text-lg font-medium text-red-900">Unable to load purchase details</h3>
            <p className="mt-2 text-sm text-red-700">
              {prepareData?.prepareDomainCheckout?.error || prepareError?.message || 'Something went wrong.'}
            </p>
            <Button
              variant="outline"
              className="mt-4 border-red-200 bg-white text-red-900 hover:bg-red-50"
              onClick={() => window.location.reload()}
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const pricing = prepareData?.prepareDomainCheckout;
  const priceFcfa = pricing?.priceFcfa || 0;
  const priceUsd = pricing?.priceUsd || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/workspace/${workspaceId}/store/settings/domains/buy`)}
          className="md:hidden"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <Globe className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-xl sm:text-2xl font-bold">Buy new domain</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">{domain}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Auto-renew */}
              <div className="flex items-center justify-between">
                <Label htmlFor="auto-renew" className="text-sm font-normal">
                  Auto-renew every year
                </Label>
                <Switch
                  id="auto-renew"
                  checked={autoRenew}
                  onCheckedChange={setAutoRenew}
                />
              </div>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Contact information</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                This information will be submitted to Huzilerz's domain registration provider.
              </p>
            </CardHeader>
            <CardContent>
              <form id="purchase-form" onSubmit={handleSubmit} className="space-y-4">
                {/* Name Fields */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First name</Label>
                    <Input
                      id="firstName"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange('firstName', e.target.value)}
                      required
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last name</Label>
                    <Input
                      id="lastName"
                      value={formData.lastName}
                      onChange={(e) => handleInputChange('lastName', e.target.value)}
                      required
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                </div>

                {/* Email and Store Name */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      required
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="storeName">Store name</Label>
                    <Input
                      id="storeName"
                      value={formData.storeName}
                      onChange={(e) => handleInputChange('storeName', e.target.value)}
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                </div>

                {/* Phone and Fax */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone (Mobile Money)</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="e.g. 677123456"
                      required
                      disabled={purchaseLoading || !!pollingId}
                    />
                    <p className="text-[0.8rem] text-muted-foreground">
                      Enter your MTN or Orange Money number (9 digits)
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="faxNumber">Fax number (Optional)</Label>
                    <Input
                      id="faxNumber"
                      type="tel"
                      value={formData.faxNumber}
                      onChange={(e) => handleInputChange('faxNumber', e.target.value)}
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                </div>

                {/* Country */}
                <div className="space-y-2">
                  <Label htmlFor="country">Country/region</Label>
                  <Select
                    value={formData.country}
                    onValueChange={(value) => handleInputChange('country', value)}
                    disabled={purchaseLoading || !!pollingId}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Cameroon">Cameroon</SelectItem>
                      <SelectItem value="Nigeria">Nigeria</SelectItem>
                      <SelectItem value="Ghana">Ghana</SelectItem>
                      <SelectItem value="Kenya">Kenya</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Address */}
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    required
                    disabled={purchaseLoading || !!pollingId}
                  />
                </div>

                {/* Apartment */}
                <div className="space-y-2">
                  <Label htmlFor="apartment">Apartment, suite, etc</Label>
                  <Input
                    id="apartment"
                    value={formData.apartment}
                    onChange={(e) => handleInputChange('apartment', e.target.value)}
                    disabled={purchaseLoading || !!pollingId}
                  />
                </div>

                {/* City */}
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    required
                    disabled={purchaseLoading || !!pollingId}
                  />
                </div>

                {/* State and Postal Code (if needed, add grid) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="state">State/Province</Label>
                    <Input
                      id="state"
                      value={formData.state}
                      onChange={(e) => handleInputChange('state', e.target.value)}
                      required
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="postalCode">Postal code</Label>
                    <Input
                      id="postalCode"
                      value={formData.postalCode}
                      onChange={(e) => handleInputChange('postalCode', e.target.value)}
                      required
                      disabled={purchaseLoading || !!pollingId}
                    />
                  </div>
                </div>

                {/* WHOIS Privacy */}
                <Alert className="bg-blue-50 border-blue-200">
                  <Info className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-900">
                    <strong>WHOIS privacy:</strong> This domain includes WHOIS Privacy. Your contact
                    information won't be displayed in public domain registration records.
                  </AlertDescription>
                </Alert>
              </form>
            </CardContent>
          </Card>

          {/* Payment Method */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Payment method</CardTitle>
            </CardHeader>
            <CardContent>
              <Alert>
                <AlertDescription>
                  Payment via Mobile Money (MTN/Orange). {priceFcfa.toLocaleString()} XAF will be requested from your phone.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>

        {/* Summary Sidebar */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="text-lg">Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Today */}
              <div className="flex justify-between text-sm">
                <div>
                  <p className="font-medium">Today</p>
                  <p className="text-muted-foreground">Domain purchase</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{priceFcfa.toLocaleString()} XAF</p>
                  <p className="text-xs text-muted-foreground">(${priceUsd.toFixed(2)} USD)</p>
                </div>
              </div>

              {/* Next Renewal */}
              <div className="flex justify-between text-sm pb-4 border-b">
                <div>
                  <p className="font-medium">
                    {renewalDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </p>
                  <p className="text-muted-foreground">Annual renewal</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{priceFcfa.toLocaleString()} XAF</p>
                  <p className="text-xs text-muted-foreground">Every year</p>
                </div>
              </div>

              {/* Amount Due */}
              <div className="flex justify-between">
                <div>
                  <p className="font-semibold">Amount due</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-lg">{priceFcfa.toLocaleString()} XAF</p>
                  <p className="text-xs text-muted-foreground">(${priceUsd.toFixed(2)} USD)</p>
                </div>
              </div>

              {/* Buy Button */}
              <Button
                type="submit"
                form="purchase-form"
                disabled={purchaseLoading || !!pollingId}
                className="w-full bg-black hover:bg-black/90 text-white relative"
              >
                {pollingId ? (
                  <>
                    <span className="animate-spin mr-2">⟳</span>
                    Confirming Payment...
                  </>
                ) : purchaseLoading ? (
                  'Processing...'
                ) : (
                  'Pay Now'
                )}
              </Button>

              {pollingId && (
                <div className="text-center text-xs text-muted-foreground animate-pulse">
                  Please check your phone to approve the transaction.
                </div>
              )}

              {/* Warning */}
              <Alert className="bg-blue-50 border-blue-200">
                <Info className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-xs text-blue-900">
                  This is a <strong>non-refundable purchase</strong> and will be charged immediately.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
