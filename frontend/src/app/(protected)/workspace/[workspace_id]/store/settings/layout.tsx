'use client';

import { usePathname } from 'next/navigation';
import { SettingsSidebar } from '@/components/workspace/store/settings/ui/SettingsSidebar';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const isMobile = useIsMobile();
  const pathname = usePathname();

  // Check if we're on the main settings page (no specific section selected)
  const isMainSettingsPage = pathname.endsWith('/settings') || pathname.endsWith('/settings/');

  // Mobile layout (no sidebar)
  if (isMobile) {
    return (
      <div className="@container/main flex flex-1 flex-col">
        <div className="flex flex-col gap-4 py-4 px-4">
          {children}
        </div>
      </div>
    );
  }

  // Desktop layout with sidebar
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <div className="px-4 lg:px-6">
          <div className="flex gap-8">
            <SettingsSidebar />
            <div className="flex-1 min-w-0">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
