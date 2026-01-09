'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useOAuth2 } from '@/hooks/authentication/useOAuth2';
import { Loader2 } from 'lucide-react';

export default function OAuth2CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleCallback } = useOAuth2();

  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [error, setError] = useState('');

  useEffect(() => {
    const processCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const provider = searchParams.get('provider') || 'google';

        if (!code) {
          throw new Error('No authorization code received');
        }

        await handleCallback({
          provider,
          code,
          state: state || ''
        });

        setStatus('success');

        // Redirect to workspace after successful auth
        setTimeout(() => {
          router.replace('/workspace');
        }, 2000);

      } catch (err: any) {
        console.error('OAuth2 callback error:', err);
        setError(err.message || 'Authentication failed');
        setStatus('error');

        // Redirect to login page after error
        setTimeout(() => {
          router.replace('/auth/login?error=oauth_failed');
        }, 3000);
      }
    };

    processCallback();
  }, [searchParams, handleCallback, router]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-stone-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md text-center">
        {status === 'processing' && (
          <div className="space-y-4">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Completing sign in...
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Please wait while we finish setting up your account.
              </p>
            </div>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Sign in successful!
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Redirecting to your workspace...
              </p>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Sign in failed
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {error || 'Something went wrong during authentication.'}
              </p>
              <button
                onClick={() => router.replace('/auth/login')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}