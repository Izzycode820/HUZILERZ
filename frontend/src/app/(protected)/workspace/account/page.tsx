/**
 * Account Settings Page - Simple Beta Version
 * Just a verify button that leads back to verification page
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { ArrowLeft, Shield, CheckCircle } from 'lucide-react';
import { useAuth } from '@/hooks/authentication/useAuth';

export default function AccountSettingsPage() {
    const router = useRouter();
    const { user } = useAuth();

    const phoneVerified = user?.phone_verified || false;
    const emailVerified = user?.email_verified || false;

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="border-b">
                <div className="container mx-auto px-6 py-4">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => router.back()}
                            className="flex items-center gap-2"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            Back
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold">Account Settings</h1>
                            <p className="text-muted-foreground">
                                Manage your account security
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="container mx-auto px-6 py-8">
                <div className="max-w-md mx-auto">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Shield className="w-5 h-5" />
                                Verification Status
                            </CardTitle>
                            <CardDescription>
                                Verify your phone and email for account security
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* Status badges */}
                            <div className="flex items-center gap-3">
                                <span className="text-sm">Email:</span>
                                {emailVerified ? (
                                    <span className="flex items-center gap-1 text-green-600 text-sm">
                                        <CheckCircle className="w-4 h-4" />
                                        Verified
                                    </span>
                                ) : (
                                    <span className="text-sm text-muted-foreground">Not verified</span>
                                )}
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-sm">Phone:</span>
                                {phoneVerified ? (
                                    <span className="flex items-center gap-1 text-green-600 text-sm">
                                        <CheckCircle className="w-4 h-4" />
                                        Verified
                                    </span>
                                ) : (
                                    <span className="text-sm text-muted-foreground">Not verified</span>
                                )}
                            </div>

                            {/* Verify Button */}
                            {(!phoneVerified || !emailVerified) && (
                                <Button
                                    onClick={() => router.push('/auth/verify')}
                                    className="w-full mt-4"
                                >
                                    Verify Now
                                </Button>
                            )}

                            {phoneVerified && emailVerified && (
                                <p className="text-center text-sm text-green-600 mt-4">
                                    Your account is fully verified
                                </p>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
