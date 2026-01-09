import { useState } from 'react';
import { Edit, Save, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Separator } from '@/components/shadcn-ui/separator';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { useMutation } from '@apollo/client/react';
import { UpdateOrderNotesDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/UpdateOrderNotes.generated';
import { toast } from 'sonner';

interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string | null;
  city?: string | null;
  region?: string | null;
  totalOrders: number;
  totalSpent: string;
}

interface OrderSidebarProps {
  orderId: string;
  notes?: string | null;
  customer?: Customer | null;
  customerName?: string;
  customerPhone?: string;
  customerEmail?: string | null;
  shippingAddress?: string | null;
  billingAddress?: string | null;
  shippingRegion?: string | null;
}

export function OrderSidebar({
  orderId,
  notes: initialNotes,
  customer,
  customerName,
  customerPhone,
  customerEmail,
  shippingAddress,
  billingAddress,
  shippingRegion,
}: OrderSidebarProps) {
  // Use live customer data if available, otherwise use snapshot
  const displayName = customer?.name || customerName;
  const displayPhone = customer?.phone || customerPhone;
  const displayEmail = customer?.email || customerEmail;

  // Notes state
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notes, setNotes] = useState(initialNotes || '');

  // Mutation
  const [updateNotes, { loading: updatingNotes }] = useMutation(UpdateOrderNotesDocument);

  const handleSaveNotes = async () => {
    try {
      const result = await updateNotes({ variables: { orderId, notes } });

      if (result.data?.updateOrderNotes?.success) {
        toast.success('Notes updated successfully');
        setIsEditingNotes(false);
      } else {
        toast.error(result.data?.updateOrderNotes?.error || 'Failed to update notes');
      }
    } catch (error) {
      toast.error('An error occurred while updating notes');
    }
  };

  const parseAddress = (addressString?: string | null) => {
    if (!addressString) return null;
    try {
      const parsed = JSON.parse(addressString);
      // Check if it looks like our address object
      if (typeof parsed === 'object' && parsed !== null) {
        return parsed;
      }
      return { address: addressString }; // Fallback for plain strings
    } catch (e) {
      return { address: addressString }; // Fallback for plain strings
    }
  };

  const shipping = parseAddress(shippingAddress);
  const billing = parseAddress(billingAddress);

  return (
    <div className="space-y-4">
      {/* Notes */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle className="text-base font-semibold">Notes</CardTitle>
          {isEditingNotes ? (
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-50"
                onClick={() => {
                  setNotes(initialNotes || '');
                  setIsEditingNotes(false);
                }}
                disabled={updatingNotes}
              >
                <X className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50"
                onClick={handleSaveNotes}
                disabled={updatingNotes}
              >
                <Save className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setIsEditingNotes(true)}
            >
              <Edit className="h-4 w-4" />
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isEditingNotes ? (
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this order..."
              className="min-h-[100px] resize-none"
            />
          ) : (
            notes ? (
              <p className="text-sm whitespace-pre-wrap">{notes}</p>
            ) : (
              <p className="text-sm text-muted-foreground">No notes from customer</p>
            )
          )}
        </CardContent>
      </Card>

      {/* Customer */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Customer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {displayName ? (
            <>
              <div>
                <p className="text-sm font-medium">{displayName}</p>
                {customer && (
                  <p className="text-xs text-muted-foreground">
                    {customer.totalOrders} order{customer.totalOrders !== 1 ? 's' : ''}
                  </p>
                )}
              </div>

              <Separator />

              {/* Contact Information */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium">Contact information</p>
                  <Button variant="ghost" size="icon" className="h-6 w-6">
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
                {displayEmail ? (
                  <p className="text-sm text-blue-600">{displayEmail}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">No email provided</p>
                )}
                {displayPhone ? (
                  <p className="text-sm">{displayPhone}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">No phone number</p>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">No customer information</p>
          )}
        </CardContent>
      </Card>

      {/* Shipping Address */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">Shipping address</CardTitle>
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <Edit className="h-3 w-3" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {shipping ? (
            <div className="text-sm space-y-1">
              {displayName && <p className="font-medium">{displayName}</p>}
              {shipping.address && <p>{shipping.address}</p>}
              {shipping.apartment && <p>{shipping.apartment}</p>}
              <p>
                {shipping.city && <span>{shipping.city}</span>}
                {shipping.postalCode && <span> {shipping.postalCode}</span>}
              </p>
              {(shipping.region || shippingRegion) && (
                <p className="capitalize">{(shipping.region || shippingRegion || '').replace('_', ' ')}</p>
              )}
              <p>{shipping.country || 'Cameroon'}</p>
              {shipping.phoneNumber && <p>{shipping.phoneNumber}</p>}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No shipping address provided</p>
          )}
        </CardContent>
      </Card>

      {/* Billing Address */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">Billing address</CardTitle>
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <Edit className="h-3 w-3" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {billing ? (
            <div className="text-sm space-y-1">
              {displayName && <p className="font-medium">{displayName}</p>}
              {billing.address && <p>{billing.address}</p>}
              {billing.apartment && <p>{billing.apartment}</p>}
              <p>
                {billing.city && <span>{billing.city}</span>}
                {billing.postalCode && <span> {billing.postalCode}</span>}
              </p>
              {billing.region && (
                <p className="capitalize">{billing.region.replace('_', ' ')}</p>
              )}
              <p>{billing.country || 'Cameroon'}</p>
              {billing.phoneNumber && <p>{billing.phoneNumber}</p>}

            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No billing address provided</p>
          )}
        </CardContent>
      </Card>

      {/* Conversion Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Conversion summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            There aren't any conversion details available for this order
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
