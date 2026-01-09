/**
 * Protected Routes Layout
 * 
 * ARCHITECTURE NOTE:
 * Auth is handled EXCLUSIVELY by middleware.ts (Shopify pattern)
 * - Middleware has access to request.nextUrl (full path)
 * - Server layouts cannot reliably get URL from headers
 * - This layout only provides wrapper + metadata
 */

import { Metadata } from 'next'

export const metadata: Metadata = {
  title: {
    template: '%s | HUZILERZ',
    default: 'HUZILERZ',
  },
  description: 'Manage your workspaces, subscriptions, and AI-powered tools',
}

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Auth check removed - middleware handles this with proper URL capture
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {children}
    </div>
  )
}
