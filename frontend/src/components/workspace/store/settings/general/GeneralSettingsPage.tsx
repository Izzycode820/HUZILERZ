'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@apollo/client/react';
import { Card } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Button } from '@/components/shadcn-ui/button';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { toast } from 'sonner';
import { GetStoreProfileDocument } from '@/services/graphql/admin-store/queries/settings/__generated__/GetStoreProfile.generated';
import { UpdateStoreProfileDocument } from '@/services/graphql/admin-store/mutations/settings/__generated__/UpdateStoreProfile.generated';
import {
    IconBuilding,
    IconMail,
    IconBrandWhatsapp,
    IconPhone,
    IconInfoCircle,
    IconDeviceFloppy,
    IconLoader2,
    IconArrowLeft,
} from '@tabler/icons-react';
import { useRouter, useParams } from 'next/navigation';

export function GeneralSettingsPage() {
    const router = useRouter();
    const params = useParams();

    // Form state
    const [storeName, setStoreName] = useState('');
    const [storeDescription, setStoreDescription] = useState('');
    const [storeEmail, setStoreEmail] = useState('');
    const [supportEmail, setSupportEmail] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [whatsappNumber, setWhatsappNumber] = useState('');
    const [isDirty, setIsDirty] = useState(false);

    // Query store profile
    const { data, loading, error } = useQuery(GetStoreProfileDocument);

    // Mutation
    const [updateProfile, { loading: saving }] = useMutation(UpdateStoreProfileDocument);

    // Populate form when data loads (strip +237 prefix for display)
    useEffect(() => {
        if (data?.storeProfile) {
            const profile = data.storeProfile;
            setStoreName(profile.storeName || '');
            setStoreDescription(profile.storeDescription || '');
            setStoreEmail(profile.storeEmail || '');
            setSupportEmail(profile.supportEmail || '');
            // Strip +237 prefix for display
            setPhoneNumber(profile.phoneNumber?.replace(/^\+237/, '') || '');
            setWhatsappNumber(profile.whatsappNumber?.replace(/^\+237/, '') || '');
        }
    }, [data]);

    // Track changes
    const handleChange = (setter: (value: string) => void) => (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
        setter(e.target.value);
        setIsDirty(true);
    };

    // Validate 9-digit Cameroon phone number (without prefix)
    const validateCameroonPhone = (phone: string): boolean => {
        if (!phone) return true; // Optional field
        return /^[0-9]{9}$/.test(phone);
    };

    // Format phone number with +237 prefix for API
    const formatPhoneForApi = (phone: string): string | null => {
        if (!phone) return null;
        return `+237${phone}`;
    };

    // Save handler
    const handleSave = async () => {
        // Validate phone numbers (9 digits without prefix)
        if (whatsappNumber && !validateCameroonPhone(whatsappNumber)) {
            toast.error('Invalid WhatsApp Number', {
                description: 'Please enter exactly 9 digits (e.g., 612345678)',
            });
            return;
        }

        if (phoneNumber && !validateCameroonPhone(phoneNumber)) {
            toast.error('Invalid Phone Number', {
                description: 'Please enter exactly 9 digits (e.g., 612345678)',
            });
            return;
        }

        try {
            const result = await updateProfile({
                variables: {
                    input: {
                        storeName: storeName || null,
                        storeDescription: storeDescription || null,
                        storeEmail: storeEmail || null,
                        supportEmail: supportEmail || null,
                        phoneNumber: formatPhoneForApi(phoneNumber),
                        whatsappNumber: formatPhoneForApi(whatsappNumber),
                    },
                },
            });

            if (result.data?.updateStoreProfile?.success) {
                toast.success('Settings saved', {
                    description: 'Your store settings have been updated successfully.',
                });
                setIsDirty(false);
            } else {
                toast.error('Error', {
                    description: result.data?.updateStoreProfile?.error || 'Failed to save settings',
                });
            }
        } catch (err) {
            console.error('Failed to save settings:', err);
            toast.error('Error', {
                description: 'Failed to save settings. Please try again.',
            });
        }
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-80 w-full max-w-[1000px] mx-auto" />
                <Skeleton className="h-64 w-full max-w-[1000px] mx-auto" />
                <Skeleton className="h-48 w-full max-w-[1000px] mx-auto" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full max-w-[1000px] mx-auto px-6">
                <Alert variant="destructive">
                    <div className="font-semibold">Error loading settings</div>
                    <div className="text-sm">{error.message}</div>
                </Alert>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Store Identity Card */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                <div className="flex items-center gap-2 mb-4 md:hidden">
                    <Button variant="ghost" size="icon" onClick={() => router.push(`/workspace/${params.workspace_id}/store/settings`)}>
                        <IconArrowLeft className="w-5 h-5" />
                    </Button>
                    <h1 className="text-xl font-bold">General Settings</h1>
                </div>

                <Card className="p-4 md:p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <IconBuilding className="w-5 h-5 text-muted-foreground" />
                        <h2 className="text-base font-semibold">Store identity</h2>
                    </div>

                    <div className="space-y-5">
                        {/* Store Name */}
                        <div className="space-y-2">
                            <Label htmlFor="storeName" className="text-sm font-medium">
                                Store name
                            </Label>
                            <Input
                                id="storeName"
                                type="text"
                                value={storeName}
                                onChange={handleChange(setStoreName)}
                                maxLength={255}
                                placeholder="Enter your store name"
                            />
                            <p className="text-xs text-muted-foreground">
                                {storeName.length} of 255 characters used
                            </p>
                        </div>

                        {/* Store Description */}
                        <div className="space-y-2">
                            <Label htmlFor="storeDescription" className="text-sm font-medium">
                                Store description
                            </Label>
                            <Textarea
                                id="storeDescription"
                                value={storeDescription}
                                onChange={handleChange(setStoreDescription)}
                                maxLength={500}
                                rows={4}
                                placeholder="Describe your store in a few sentences"
                                className="resize-none"
                            />
                            <p className="text-xs text-muted-foreground">
                                {storeDescription.length} of 500 characters used
                            </p>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Contact Information Card */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                <Card className="p-4 md:p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <IconMail className="w-5 h-5 text-muted-foreground" />
                        <h2 className="text-base font-semibold">Contact information</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {/* Store Email */}
                        <div className="space-y-2">
                            <Label htmlFor="storeEmail" className="text-sm font-medium">
                                Store email
                            </Label>
                            <Input
                                id="storeEmail"
                                type="email"
                                value={storeEmail}
                                onChange={handleChange(setStoreEmail)}
                                placeholder="store@example.com"
                            />
                            <p className="text-xs text-muted-foreground">
                                Primary contact email for your store
                            </p>
                        </div>

                        {/* Support Email */}
                        <div className="space-y-2">
                            <Label htmlFor="supportEmail" className="text-sm font-medium">
                                Support email
                            </Label>
                            <Input
                                id="supportEmail"
                                type="email"
                                value={supportEmail}
                                onChange={handleChange(setSupportEmail)}
                                placeholder="support@example.com"
                            />
                            <p className="text-xs text-muted-foreground">
                                Customer support email (optional)
                            </p>
                        </div>

                        {/* Phone Number */}
                        <div className="space-y-2">
                            <Label htmlFor="phoneNumber" className="text-sm font-medium">
                                Phone number
                            </Label>
                            <div className="flex">
                                <span className="inline-flex items-center px-3 text-sm text-muted-foreground bg-muted border border-r-0 border-input rounded-l-md">
                                    +237
                                </span>
                                <Input
                                    id="phoneNumber"
                                    type="tel"
                                    value={phoneNumber}
                                    onChange={handleChange(setPhoneNumber)}
                                    placeholder="612345678"
                                    maxLength={9}
                                    className="rounded-l-none"
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Enter 9 digits (e.g., 612345678)
                            </p>
                        </div>
                    </div>
                </Card>
            </div>

            {/* WhatsApp Settings Card */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6">
                <Card className="p-4 md:p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <IconBrandWhatsapp className="w-5 h-5 text-green-600" />
                        <h2 className="text-base font-semibold">WhatsApp checkout</h2>
                        <IconInfoCircle className="w-4 h-4 text-muted-foreground" />
                    </div>

                    <Alert className="bg-green-500/10 border-green-500/20 mb-5">
                        <IconBrandWhatsapp className="h-4 w-4 text-green-600" />
                        <AlertDescription className="ml-2 text-sm text-green-900 dark:text-green-300">
                            WhatsApp orders will be sent to this number. Customers can place orders directly via WhatsApp for a seamless checkout experience.
                        </AlertDescription>
                    </Alert>

                    <div className="space-y-2">
                        <Label htmlFor="whatsappNumber" className="text-sm font-medium">
                            WhatsApp number
                        </Label>
                        <div className="flex max-w-md">
                            <span className="inline-flex items-center px-3 text-sm text-muted-foreground bg-muted border border-r-0 border-input rounded-l-md">
                                +237
                            </span>
                            <Input
                                id="whatsappNumber"
                                type="tel"
                                value={whatsappNumber}
                                onChange={handleChange(setWhatsappNumber)}
                                placeholder="612345678"
                                maxLength={9}
                                className="rounded-l-none"
                            />
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Enter 9 digits (required for WhatsApp orders)
                        </p>
                    </div>
                </Card>
            </div>

            {/* Save Button */}
            <div className="w-full max-w-[1000px] mx-auto px-4 md:px-6 pb-6">
                <div className="flex justify-end">
                    <Button
                        onClick={handleSave}
                        disabled={saving || !isDirty}
                        className="gap-2"
                    >
                        {saving ? (
                            <>
                                <IconLoader2 className="w-4 h-4 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <IconDeviceFloppy className="w-4 h-4" />
                                Save changes
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}
