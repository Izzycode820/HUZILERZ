/**
 * Auth Routes Layout - Clean Implementation
 * Removed AuthProvider to use Zustand directly
 * Modern authentication layout with proper styling
 */

import { Metadata } from 'next'

export const metadata: Metadata = {
  title: {
    template: '%s | Auth | HUZILERZ',
    default: 'Authentication | HUZILERZ',
  },
  description: 'Secure authentication for HUZILERZ platform',
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {children}
    </div>
  )
}