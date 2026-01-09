'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client/react';
import { useRouter, useParams } from 'next/navigation';
import { Card } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Button } from '@/components/shadcn-ui/button';
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
import { GetPaymentMethodsDocument } from '@/services/graphql/admin-store/queries/payments/__generated__/GetPaymentMethods.generated';
import { AddPaymentMethodDocument } from '@/services/graphql/admin-store/mutations/payments/__generated__/AddPaymentMethod.generated';
import {
    IconCreditCard,
    IconArrowLeft,
    IconPlus,
    IconLoader2,
    IconCheck,
} from '@tabler/icons-react';

/**
 * Add Payment Methods Page
 * 
 * Shows grid of available payment providers.
 * Clicking "Add" on Fapshi opens modal for URL input.
 * On success, redirects back to listing page.
 */
export function AddPaymentMethodsPage() {
    const router = useRouter();
    const params = useParams();
    const workspaceId = params.workspace_id as string;

    // Modal state
    const [showUrlModal, setShowUrlModal] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
    const [checkoutUrl, setCheckoutUrl] = useState('');

    // Query for available providers
    const { data, loading } = useQuery(GetPaymentMethodsDocument);

    // Mutation
    const [addMethod, { loading: adding }] = useMutation(AddPaymentMethodDocument);

    // Validate Fapshi URL
    const validateFapshiUrl = (url: string): boolean => {
        if (!url) return false;
        try {
            const parsed = new URL(url);
            return parsed.protocol === 'https:' && url.toLowerCase().includes('fapshi.com');
        } catch {
            return false;
        }
    };

    // Handle add click - open modal for URL input
    const handleAddClick = (provider: string) => {
        setSelectedProvider(provider);
        setCheckoutUrl('');
        setShowUrlModal(true);
    };

    // Handle confirm add
    const handleConfirmAdd = async () => {
        if (!selectedProvider) return;

        if (selectedProvider === 'fapshi' && !validateFapshiUrl(checkoutUrl)) {
            toast.error('Invalid URL', {
                description: 'Please enter a valid Fapshi checkout URL (https://...fapshi.com/...)',
            });
            return;
        }

        try {
            const result = await addMethod({
                variables: {
                    input: {
                        providerName: selectedProvider,
                        checkoutUrl: checkoutUrl,
                    },
                },
            });

            if (result.data?.addPaymentMethod?.success) {
                toast.success('Payment provider added', {
                    description: `${selectedProvider} has been configured successfully.`,
                });
                setShowUrlModal(false);
                // Navigate back to listing page
                router.push(`/workspace/${workspaceId}/store/settings/payments`);
            } else {
                toast.error('Error', {
                    description: result.data?.addPaymentMethod?.error || 'Failed to add payment provider',
                });
            }
        } catch (err) {
            console.error('Add payment method failed:', err);
            toast.error('Error', {
                description: 'Failed to add payment provider. Please try again.',
            });
        }
    };

    // Navigate back to listing
    const goBack = () => {
        router.push(`/workspace/${workspaceId}/store/settings/payments`);
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-16 w-full max-w-[1000px] mx-auto" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-[1000px] mx-auto px-6">
                    <Skeleton className="h-40" />
                    <Skeleton className="h-40" />
                </div>
            </div>
        );
    }

    const availableProviders = data?.availableProviders?.filter(Boolean) || [];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                <div className="flex items-center gap-4 mb-2">
                    <Button variant="ghost" size="icon" onClick={goBack}>
                        <IconArrowLeft className="w-5 h-5" />
                    </Button>
                    <div>
                        <h1 className="text-xl font-semibold">Add payment provider</h1>
                        <p className="text-sm text-muted-foreground">
                            Choose a payment provider for your store
                        </p>
                    </div>
                </div>
            </div>

            {/* Providers Grid */}
            <div className="w-full max-w-[1000px] mx-auto px-6">
                <div className="grid grid-cols-1 gap-4">
                    {availableProviders.map((provider) => {
                        if (!provider) return null;
                        const isAlreadyAdded = provider.alreadyAdded;

                        return (
                            <Card
                                key={provider.provider}
                                className={`p-4 sm:p-6 ${isAlreadyAdded ? 'bg-muted/30' : ''}`}
                            >
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <div className="flex items-center gap-3 sm:gap-4">
                                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                                            <IconCreditCard className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">{provider.displayName}</h3>
                                            <p className="text-sm text-muted-foreground">
                                                {provider.description}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex-shrink-0">
                                        {isAlreadyAdded ? (
                                            <div className="flex items-center gap-2 text-green-600">
                                                <IconCheck className="w-5 h-5" />
                                                <span className="text-sm font-medium">Activated</span>
                                            </div>
                                        ) : (
                                            <Button
                                                onClick={() => handleAddClick(provider.provider)}
                                                className="bg-green-600 hover:bg-green-700 w-full sm:w-auto"
                                            >
                                                Activate
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
                </div>
            </div>

            {/* Empty state if no providers */}
            {availableProviders.length === 0 && (
                <div className="w-full max-w-[1000px] mx-auto px-6">
                    <Card className="p-8 text-center">
                        <IconCreditCard className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No providers available</h3>
                        <p className="text-sm text-muted-foreground">
                            All available payment providers have been configured.
                        </p>
                        <Button onClick={goBack} className="mt-4">
                            Back to payment settings
                        </Button>
                    </Card>
                </div>
            )}

            {/* URL Input Modal (for Fapshi) */}
            <Dialog open={showUrlModal} onOpenChange={setShowUrlModal}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Add Fapshi Payment</DialogTitle>
                        <DialogDescription>
                            Enter your Fapshi checkout URL to accept mobile money payments.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="checkoutUrl">Fapshi Checkout URL</Label>
                            <Input
                                id="checkoutUrl"
                                value={checkoutUrl}
                                onChange={(e) => setCheckoutUrl(e.target.value)}
                                placeholder="https://checkout.fapshi.com/pay/..."
                            />
                            <p className="text-xs text-muted-foreground">
                                Get this URL from your{' '}
                                <a
                                    href="https://dashboard.fapshi.com"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="underline"
                                >
                                    Fapshi dashboard
                                </a>{' '}
                                under Payment Links
                            </p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowUrlModal(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleConfirmAdd} disabled={adding || !checkoutUrl}>
                            {adding ? (
                                <>
                                    <IconLoader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Adding...
                                </>
                            ) : (
                                'Add Fapshi'
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
