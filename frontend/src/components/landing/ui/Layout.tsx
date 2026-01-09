/**
 * Landing Page Layout - Clean and Modern
 * Combines header with page content
 * Uses shadcn/ui components for consistent styling
 */

import React from 'react'
import Header from '../common/Header'
import { cn } from '@/lib/utils'

interface LayoutProps {
  children: React.ReactNode
  className?: string
}

export default function Layout({ children, className }: LayoutProps) {
  return (
    <div className={cn("min-h-screen bg-background", className)}>
      <Header />
      <main>
        {children}
      </main>
    </div>
  )
}