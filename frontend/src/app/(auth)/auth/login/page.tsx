/**
 * Login Page - Clean Implementation
 * Uses new LoginForm component with proper Shadcn/UI integration
 * Modern authentication UX with proper error handling
 */

'use client'

import React from 'react'
import Link from 'next/link'
import { LoginForm } from '@/components/authentication/forms/LoginForm'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Separator } from '@/components/shadcn-ui/separator'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="border-0 shadow-lg">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl font-semibold">
              Welcome back
            </CardTitle>
            <CardDescription>
              Sign in to your HUZILERZ account
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-6">
            <LoginForm
              onSuccess={() => {
                // Navigation handled by LoginForm internally
              }}
              onError={(error) => {
                console.error('Login error:', error)
              }}
            />

            <Separator className="my-6" />

            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                Don't have an account?{' '}
                <Link
                  href="/auth/signup"
                  className="font-medium text-primary hover:underline"
                >
                  Create account
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}