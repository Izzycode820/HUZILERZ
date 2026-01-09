/**
 * Signup Page - Clean Implementation
 * Uses new SignupForm component with proper Shadcn/UI integration
 * Modern registration UX with proper error handling
 */

'use client'

import React from 'react'
import Link from 'next/link'
import { SignupForm } from '@/components/authentication/forms/SignupForm'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Separator } from '@/components/shadcn-ui/separator'

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="border-0 shadow-lg">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl font-semibold">
              Create account
            </CardTitle>
            <CardDescription>
              Join HUZILERZ and start building your workspace
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-6">
            <SignupForm
              onSuccess={() => {
                // Navigation handled by SignupForm internally
              }}
              onError={(error) => {
                console.error('Registration error:', error)
              }}
            />

            <Separator className="my-6" />

            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-4">
                By creating an account, you agree to our{' '}
                <Link href="/terms" className="text-primary hover:underline">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link href="/privacy" className="text-primary hover:underline">
                  Privacy Policy
                </Link>
              </p>

              <p className="text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link
                  href="/auth/login"
                  className="font-medium text-primary hover:underline"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}