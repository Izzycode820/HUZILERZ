/**
 * Email Verification Card Component
 * Clean inline verification flow with OTP input
 * Uses shadcn/ui + useEmail hook
 */

'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Loader2, Check } from 'lucide-react'

// Shadcn/UI Components
import { Button } from '@/components/shadcn-ui/button'
import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/shadcn-ui/card'

// Hooks
import { useEmail } from '@/hooks/authentication/useEmail'

// Utils - mask email for display
function maskEmail(email: string): string {
    const [local, domain] = email.split('@')
    if (!local || !domain) return email

    const visibleStart = local.slice(0, 2)
    const visibleEnd = local.length > 2 ? local.slice(-1) : ''

    return `${visibleStart}***${visibleEnd}@${domain}`
}

interface EmailVerificationCardProps {
    email: string
    onVerified?: () => void
    className?: string
}

type VerificationStep = 'initial' | 'code_sent' | 'verified'

export function EmailVerificationCard({
    email,
    onVerified,
    className = ''
}: EmailVerificationCardProps) {
    const [step, setStep] = useState<VerificationStep>('initial')
    const [otpValues, setOtpValues] = useState<string[]>(['', '', '', '', '', ''])
    const [countdown, setCountdown] = useState(0)
    const inputRefs = useRef<(HTMLInputElement | null)[]>([])

    const {
        requestVerificationCode,
        verifyCode,
        isLoading,
        error,
        clearError
    } = useEmail()

    // Countdown timer for resend
    useEffect(() => {
        if (countdown > 0) {
            const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
            return () => clearTimeout(timer)
        }
    }, [countdown])

    // Mask email for display
    const maskedEmail = maskEmail(email)

    // Handle request code
    const handleRequestCode = async () => {
        try {
            clearError()
            await requestVerificationCode({
                email: email,
                code_type: 'account_verification'
            })
            setStep('code_sent')
            setCountdown(60)
            // Focus first OTP input
            setTimeout(() => inputRefs.current[0]?.focus(), 100)
        } catch {
            // Error handled by hook
        }
    }

    // Handle OTP input change
    const handleOtpChange = (index: number, value: string) => {
        // Only allow digits
        const digit = value.replace(/\D/g, '').slice(-1)

        const newValues = [...otpValues]
        newValues[index] = digit
        setOtpValues(newValues)

        // Auto-focus next input
        if (digit && index < 5) {
            inputRefs.current[index + 1]?.focus()
        }

        // Clear error when user types
        if (error) clearError()
    }

    // Handle backspace
    const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
        if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
            inputRefs.current[index - 1]?.focus()
        }
    }

    // Handle paste
    const handlePaste = (e: React.ClipboardEvent) => {
        e.preventDefault()
        const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
        const newValues = [...otpValues]
        for (let i = 0; i < 6; i++) {
            newValues[i] = pasted[i] || ''
        }
        setOtpValues(newValues)

        // Focus last filled or first empty
        const lastIndex = Math.min(pasted.length, 5)
        inputRefs.current[lastIndex]?.focus()
    }

    // Handle verify code
    const handleVerify = async () => {
        const code = otpValues.join('')
        if (code.length !== 6) return

        try {
            clearError()
            await verifyCode({
                email: email,
                code_type: 'account_verification',
                code
            })
            setStep('verified')
            onVerified?.()
        } catch {
            // Error handled by hook
        }
    }

    // Handle resend
    const handleResend = () => {
        setOtpValues(['', '', '', '', '', ''])
        handleRequestCode()
    }

    const isCodeComplete = otpValues.every(v => v !== '')

    return (
        <Card className={className}>
            <CardHeader className="pb-4">
                <CardTitle className="text-lg">Email Verification</CardTitle>
                <CardDescription>
                    Verify your email address to secure your account
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Error Display */}
                {error && (
                    <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                    </div>
                )}

                {/* Verified State */}
                {step === 'verified' ? (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                        <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                        <span className="text-sm text-green-600 dark:text-green-400">
                            Email verified
                        </span>
                    </div>
                ) : (
                    <>
                        {/* Email Display + Request Button */}
                        <div className="flex items-center justify-between gap-4">
                            <div>
                                <Label className="text-sm text-muted-foreground">Email</Label>
                                <p className="font-medium">{maskedEmail}</p>
                            </div>

                            {step === 'initial' && (
                                <Button
                                    onClick={handleRequestCode}
                                    disabled={isLoading}
                                    variant="outline"
                                    size="sm"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Sending...
                                        </>
                                    ) : (
                                        'Request Code'
                                    )}
                                </Button>
                            )}
                        </div>

                        {/* OTP Input Section */}
                        {step === 'code_sent' && (
                            <div className="space-y-4 pt-2">
                                <div className="space-y-2">
                                    <Label className="text-sm">Enter verification code</Label>
                                    <div className="flex gap-2 justify-center">
                                        {otpValues.map((value, index) => (
                                            <Input
                                                key={index}
                                                ref={(el) => { inputRefs.current[index] = el }}
                                                type="text"
                                                inputMode="numeric"
                                                maxLength={1}
                                                value={value}
                                                onChange={(e) => handleOtpChange(index, e.target.value)}
                                                onKeyDown={(e) => handleKeyDown(index, e)}
                                                onPaste={handlePaste}
                                                disabled={isLoading}
                                                className="w-10 h-12 text-center text-lg font-semibold"
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* Verify Button */}
                                <Button
                                    onClick={handleVerify}
                                    disabled={!isCodeComplete || isLoading}
                                    className="w-full"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Verifying...
                                        </>
                                    ) : (
                                        'Verify'
                                    )}
                                </Button>

                                {/* Resend Link */}
                                <div className="text-center text-sm text-muted-foreground">
                                    {countdown > 0 ? (
                                        <span>Resend code in {countdown}s</span>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={handleResend}
                                            disabled={isLoading}
                                            className="text-primary hover:underline disabled:opacity-50"
                                        >
                                            Resend code
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    )
}

export default EmailVerificationCard
