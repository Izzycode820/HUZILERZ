/**
 * Verify Page - Account Verification
 * Handles phone and email verification after signup
 * Clean component-based implementation
 */

'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Button } from '@/components/shadcn-ui/button'
import { PhoneVerificationCard, EmailVerificationCard } from '@/components/authentication/verification'
import { useAuth } from '@/hooks/authentication/useAuth'

export default function VerifyPage() {
    const router = useRouter()
    const { user, isAuthenticated, isLoading } = useAuth()

    const [phoneVerified, setPhoneVerified] = React.useState(false)
    const [emailVerified, setEmailVerified] = React.useState(false)

    // Check if user is authenticated
    React.useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace('/auth/login')
        }
    }, [isAuthenticated, isLoading, router])

    // Initialize verified states from user data
    React.useEffect(() => {
        if (user) {
            setPhoneVerified(user.phone_verified || false)
            setEmailVerified(user.email_verified || false)
        }
    }, [user])

    const bothVerified = phoneVerified && emailVerified

    const handleContinue = () => {
        router.push('/workspace')
    }

    // Loading state
    if (isLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-pulse text-muted-foreground">Loading...</div>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-md space-y-4">
                {/* Header Card */}
                <Card className="border-0 shadow-lg">
                    <CardHeader className="text-center pb-2">
                        <CardTitle className="text-2xl font-semibold">
                            Verify Your Account
                        </CardTitle>
                        <CardDescription>
                            Complete verification to secure your account
                        </CardDescription>
                    </CardHeader>
                </Card>

                {/* Phone Verification */}
                {user.phone_number && (
                    <PhoneVerificationCard
                        phoneNumber={user.phone_number}
                        onVerified={() => setPhoneVerified(true)}
                        className="shadow-lg"
                    />
                )}

                {/* Email Verification */}
                <EmailVerificationCard
                    email={user.email}
                    onVerified={() => setEmailVerified(true)}
                    className="shadow-lg"
                />

                {/* Continue Button - enabled when both verified */}
                <Button
                    onClick={handleContinue}
                    disabled={!bothVerified}
                    className="w-full h-12"
                    size="lg"
                >
                    Continue to Dashboard
                </Button>

                {/* Skip Button - Beta testing */}
                {!bothVerified && (
                    <Button
                        variant="ghost"
                        onClick={handleContinue}
                        className="w-full h-10 text-muted-foreground hover:text-foreground"
                    >
                        Skip for now (Beta)
                    </Button>
                )}

                <p className="text-center text-xs text-muted-foreground">
                    You can verify later in Settings
                </p>
            </div>
        </div>
    )
}
