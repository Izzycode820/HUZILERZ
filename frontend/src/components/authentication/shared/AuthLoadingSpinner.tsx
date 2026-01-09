/**
 * Authentication Loading Spinner - Branded v2.0
 * Premium loading states with HUZILERZ CAMP branding
 */

'use client'

import React from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AuthLoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  className?: string
}

export function AuthLoadingSpinner({
  size = 'md',
  text = 'Loading...',
  className
}: AuthLoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  }

  return (
    <div className={cn(
      'flex items-center justify-center space-x-2',
      className
    )}>
      <Loader2 className={cn(
        'animate-spin text-muted-foreground',
        sizeClasses[size]
      )} />
      {text && (
        <span className="text-sm text-muted-foreground">
          {text}
        </span>
      )}
    </div>
  )
}

/**
 * HUZILERZ CAMP branded SVG logo
 * Features a tent icon with brand text
 */
function HuzilerzLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 60"
      className={cn('w-48 h-14', className)}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Tent icon */}
      <g className="fill-current">
        <path
          d="M25 45L12 45L18.5 20L25 8L31.5 20L38 45L25 45Z"
          className="fill-primary"
        />
        <path
          d="M25 45L18 45L25 25L32 45L25 45Z"
          className="fill-primary/70"
        />
        {/* Tent door */}
        <path
          d="M22 45L25 32L28 45L22 45Z"
          className="fill-background"
        />
      </g>

      {/* HUZILERZ text */}
      <text
        x="48"
        y="28"
        className="fill-foreground"
        style={{
          fontFamily: 'system-ui, -apple-system, sans-serif',
          fontSize: '18px',
          fontWeight: 700,
          letterSpacing: '0.05em'
        }}
      >
        HUZILERZ
      </text>

      {/* CAMP text */}
      <text
        x="48"
        y="48"
        className="fill-primary"
        style={{
          fontFamily: 'system-ui, -apple-system, sans-serif',
          fontSize: '14px',
          fontWeight: 600,
          letterSpacing: '0.2em'
        }}
      >
        CAMP
      </text>
    </svg>
  )
}

/**
 * Full page branded auth loading spinner
 * Premium UX with logo animation
 */
export function AuthPageSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center space-y-6">
        {/* Animated logo */}
        <div className="animate-pulse">
          <HuzilerzLogo />
        </div>

        {/* Loading indicator */}
        <div className="flex items-center justify-center space-x-2">
          <div className="flex space-x-1">
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce" />
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Compact branded spinner for inline use
 */
export function AuthBrandedSpinner({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center space-y-4 p-8">
      <div className="animate-pulse">
        <HuzilerzLogo className="w-32 h-10" />
      </div>
      <div className="flex items-center space-x-2">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">{text}</span>
      </div>
    </div>
  )
}

export { HuzilerzLogo }