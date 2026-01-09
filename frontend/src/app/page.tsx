'use client';

// Root page - Redirects to /camp
// This ensures users land on the new landing page

import { redirect } from 'next/navigation';
import { PUBLIC_ROUTES } from '@/routes';

export default function RootPage() {
  redirect(PUBLIC_ROUTES.CAMP);
}