'use client';

import { useQuery, useMutation } from '@apollo/client/react';
import { useRouter, useParams } from 'next/navigation';
import { Card } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Switch } from '@/components/shadcn-ui/switch';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { toast } from 'sonner';
import { useState } from 'react';
import { GetPaymentMethodsDocument } from '@/services/graphql/admin-store/queries/payments/__generated__/GetPaymentMethods.generated';
import { TogglePaymentMethodDocument } from '@/services/graphql/admin-store/mutations/payments/__generated__/TogglePaymentMethod.generated';
import { RemovePaymentMethodDocument } from '@/services/graphql/admin-store/mutations/payments/__generated__/RemovePaymentMethod.generated';
import {
    IconCreditCard,
    IconPlus,
    IconTrash,
    IconExternalLink,
    IconLoader2,
    IconInfoCircle,
    IconArrowLeft,
} from '@tabler/icons-react';

/**
 * Payment Methods Listing Page
 * 
 * Shows configured payment methods with toggle and remove actions.
 * "Add payment provider" button navigates to add-payment-methods page.
 */
export function PaymentMethodsListPage() {
    const router = useRouter();
    const params = useParams();
    const workspaceId = params.workspace_id as string;

    // Delete modal state
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [selectedMethod, setSelectedMethod] = useState<{
        id: string;
        providerName: string;
    } | null>(null);

    // Query
    const { data, loading, error, refetch } = useQuery(GetPaymentMethodsDocument);

    // Mutations
    const [toggleMethod, { loading: toggling }] = useMutation(TogglePaymentMethodDocument);
    const [removeMethod, { loading: removing }] = useMutation(RemovePaymentMethodDocument);

    // Handle toggle
    const handleToggle = async (methodId: string, enabled: boolean) => {
        try {
            const result = await toggleMethod({
                variables: {
                    methodId,
                    enabled,
                },
            });

            if (result.data?.togglePaymentMethod?.success) {
                toast.success(enabled ? 'Payment method enabled' : 'Payment method disabled');
                refetch();
            } else {
                toast.error('Error', {
                    description: result.data?.togglePaymentMethod?.error || 'Failed to update',
                });
            }
        } catch (err) {
            console.error('Toggle failed:', err);
            toast.error('Error', { description: 'Failed to update payment method' });
        }
    };

    // Handle delete
    const handleDelete = async () => {
        if (!selectedMethod) return;

        try {
            const result = await removeMethod({
                variables: {
                    methodId: selectedMethod.id,
                },
            });

            if (result.data?.removePaymentMethod?.success) {
                toast.success('Payment method removed');
                setShowDeleteModal(false);
                setSelectedMethod(null);
                refetch();
            } else {
                toast.error('Error', {
                    description: result.data?.removePaymentMethod?.error || 'Failed to remove',
                });
            }
        } catch (err) {
            console.error('Delete failed:', err);
            toast.error('Error', { description: 'Failed to remove payment method' });
        }
    };

    // Navigate to add page
    const goToAddPage = () => {
        router.push(`/workspace/${workspaceId}/store/settings/payments/add-payment-methods`);
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-24 w-full max-w-[1000px] mx-auto" />
                <Skeleton className="h-32 w-full max-w-[1000px] mx-auto" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full max-w-[1000px] mx-auto px-6">
                <Alert variant="destructive">
                    <div className="font-semibold">Error loading payment methods</div>
                    <div className="text-sm">{error.message}</div>
                </Alert>
            </div>
        );
    }

    const methods = data?.paymentMethods?.filter(Boolean) || [];

    return (
        <div className="space-y-6">
            {/* Header Card */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                <Card className="p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => router.push(`/workspace/${workspaceId}/store/settings`)}
                                className="md:hidden p-2 -ml-2 rounded-lg hover:bg-muted"
                            >
                                <IconArrowLeft className="w-5 h-5" />
                            </button>
                            <IconCreditCard className="w-6 h-6 text-muted-foreground flex-shrink-0" />
                            <div>
                                <h2 className="text-base font-semibold">Payment providers</h2>
                                <p className="text-sm text-muted-foreground">
                                    Manage how customers pay on your store
                                </p>
                            </div>
                        </div>
                        <Button onClick={goToAddPage} className="gap-2 w-full sm:w-auto">
                            <IconPlus className="w-4 h-4" />
                            Add payment provider
                        </Button>
                    </div>
                </Card>
            </div>

            {/* Payment Methods List */}
            {methods.length === 0 ? (
                <div className="w-full max-w-[1000px] mx-auto px-6">
                    <Card className="p-8">
                        <div className="text-center">
                            <IconCreditCard className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
                            <h3 className="text-lg font-medium mb-2">No payment methods configured</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Add a payment provider to accept payments on your store.
                            </p>
                            <Button onClick={goToAddPage} className="gap-2">
                                <IconPlus className="w-4 h-4" />
                                Add payment provider
                            </Button>
                        </div>
                    </Card>
                </div>
            ) : (
                methods.map((method) => {
                    if (!method) return null;
                    return (
                        <div key={method.id} className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                            <Card className="p-4 sm:p-6">
                                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                                    <div className="flex items-start gap-3 sm:gap-4">
                                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                                            <IconCreditCard className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <h3 className="font-semibold">{method.displayName || method.providerName}</h3>
                                                {method.verified && (
                                                    <span className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded">
                                                        Verified
                                                    </span>
                                                )}
                                                {!method.enabled && (
                                                    <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
                                                        Disabled
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                MTN MoMo and Orange Money via hosted checkout
                                            </p>
                                            {method.checkoutUrl && (
                                                <div className="flex items-center gap-2 mt-2">
                                                    <code className="text-xs bg-muted px-2 py-1 rounded max-w-[200px] sm:max-w-[350px] truncate block">
                                                        {method.checkoutUrl}
                                                    </code>
                                                    <a
                                                        href={method.checkoutUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-muted-foreground hover:text-foreground flex-shrink-0"
                                                    >
                                                        <IconExternalLink className="w-4 h-4" />
                                                    </a>
                                                </div>
                                            )}
                                            {method.totalTransactions > 0 && (
                                                <p className="text-xs text-muted-foreground mt-2">
                                                    {method.totalTransactions} transactions ({method.successRate?.toFixed(1)}% success)
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4 self-end sm:self-auto">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm text-muted-foreground hidden sm:inline">
                                                {method.enabled ? 'Enabled' : 'Disabled'}
                                            </span>
                                            <Switch
                                                checked={method.enabled}
                                                onCheckedChange={(checked) => handleToggle(method.id, checked)}
                                                disabled={toggling}
                                            />
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => {
                                                setSelectedMethod(method);
                                                setShowDeleteModal(true);
                                            }}
                                            className="text-destructive hover:text-destructive"
                                        >
                                            <IconTrash className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        </div>
                    );
                })
            )}

            {/* Info Card */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                <Alert className="bg-blue-500/10 border-blue-500/20">
                    <IconInfoCircle className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="ml-2 text-sm text-blue-900 dark:text-blue-300">
                        Customers will be redirected to your payment provider's checkout page to complete payments.
                    </AlertDescription>
                </Alert>
            </div>

            {/* Delete Confirmation Modal */}
            <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Remove Payment Provider</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to remove {selectedMethod?.providerName}?
                            Customers will no longer be able to pay using this method.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={handleDelete} disabled={removing}>
                            {removing ? (
                                <>
                                    <IconLoader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Removing...
                                </>
                            ) : (
                                'Remove'
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
