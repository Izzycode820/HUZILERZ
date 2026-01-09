'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import { MobileSettingsList } from '@/components/workspace/store/settings/ui/MobileSettingsList';

export default function SettingsPage() {
    const router = useRouter();
    const params = useParams();
    const workspaceId = params.workspace_id as string;
    const isMobile = useIsMobile();
    const [hasCheckedDevice, setHasCheckedDevice] = useState(false);

    useEffect(() => {
        // Wait until we've definitively determined if we're on mobile or desktop
        // isMobile is undefined during SSR/initial load
        if (isMobile !== undefined && !hasCheckedDevice) {
            setHasCheckedDevice(true);

            // Desktop ONLY: redirect to general settings
            if (!isMobile) {
                router.replace(`/workspace/${workspaceId}/store/settings/general`);
            }
            // Mobile: do nothing, stay on this page
        }
    }, [isMobile, hasCheckedDevice, workspaceId, router]);

    // Still loading / detecting device
    if (isMobile === undefined) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
            </div>
        );
    }

    // Mobile: show the settings list permanently
    if (isMobile) {
        return (
            <div className="flex flex-col gap-4">
                <h1 className="text-2xl font-bold">Settings</h1>
                <MobileSettingsList />
            </div>
        );
    }

    // Desktop: show loading while redirecting to general
    return (
        <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-white" />
        </div>
    );
}
