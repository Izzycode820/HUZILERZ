'use client'

import { ThemeProvider } from '@/utils/ThemeContext';
import { AuthInitializer } from '@/components/authentication/shared/AuthInitializer';
import { TokenManager } from '@/components/authentication/shared/TokenManager';

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ThemeProvider>
            <AuthInitializer>
                <TokenManager>
                    {children}
                </TokenManager>
            </AuthInitializer>
        </ThemeProvider>
    );
}
