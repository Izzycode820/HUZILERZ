'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

// TODO: [BLOAT-FLAG] MFASetup component needs to be created
// For now, this is a placeholder that redirects to workspace
export default function MFASetupPage() {
  const router = useRouter();

  React.useEffect(() => {
    // MFA setup not yet implemented - redirect to workspace
    router.push('/workspace');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-stone-900 flex items-center justify-center p-4">
      <div className="text-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
        <p className="text-gray-600 dark:text-gray-400">Redirecting...</p>
      </div>
    </div>
  );
}