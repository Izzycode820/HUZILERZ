/**
 * Coming Soon Section - Modern Minimal Design
 * Uses shadcn/ui components for consistent styling
 * Email capture with form validation
 */

'use client'

import React, { useState } from 'react'
import { Button } from '@/components/shadcn-ui/button'
import { Input } from '@/components/shadcn-ui/input'
import { Card, CardContent } from '@/components/shadcn-ui/card'
import { Badge } from '@/components/shadcn-ui/badge'
import { Progress } from '@/components/shadcn-ui/progress'
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert'
import { Mail, CheckCircle } from 'lucide-react'

export default function ComingSoon() {
  const [email, setEmail] = useState('')
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address')
      setIsLoading(false)
      return
    }

    try {
      // TODO: Implement email capture
      await new Promise(resolve => setTimeout(resolve, 1000))
      setIsSubmitted(true)
    } catch (err) {
      setError('Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  if (isSubmitted) {
    return (
      <section className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
        <div className="max-w-md mx-auto text-center">
          <div className="mx-auto h-16 w-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mb-6">
            <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-2xl font-semibold mb-2">You're on the list!</h2>
          <p className="text-muted-foreground">
            We'll notify you when HUZILERZ launches. Thank you for your interest!
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-2xl font-medium text-foreground">
          Huzilerz Camp, Coming Soon
        </h1>
      </div>
    </section>
  )
}