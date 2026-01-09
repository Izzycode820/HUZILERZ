/**
 * Public Routes Layout
 * Layout for unauthenticated routes (auth, marketing pages)
 */

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    template: '%s | HUZILERZ',
    default: 'HUZILERZ - AI-Powered E-commerce Platform',
  },
  description: 'Build and deploy your online store with AI-powered tools and analytics',
};

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {children}
    </div>
  );
}