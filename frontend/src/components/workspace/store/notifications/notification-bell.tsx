'use client';

/**
 * Notification Bell Component
 *
 * Sidebar button with bell icon and unread count badge.
 * Opens the NotificationPanel slide-over on click.
 */

import { useState } from 'react';
import { IconBell } from '@tabler/icons-react';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/shadcn-ui/sheet"
import { cn } from '@/lib/utils';
import { useNotificationSocket } from './use-notification-socket';
import { NotificationPanel } from './notification-panel';
import { ApolloProvider } from "@apollo/client/react"
import { notificationClient } from "@/services/graphql/clients"

interface NotificationBellProps {
  workspaceId: string;
  className?: string;
  collapsed?: boolean;
}

function NotificationBellInner({
  workspaceId,
  className,
  collapsed = false,
}: NotificationBellProps) {
  const [panelOpen, setPanelOpen] = useState(false);
  const { unreadCount } = useNotificationSocket();

  return (
    <>
      <Button
        variant="ghost"
        className={cn(
          'w-full justify-start gap-2 relative',
          collapsed && 'justify-center px-2',
          className
        )}
        onClick={() => setPanelOpen(true)}
      >
        <div className="relative">
          <IconBell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className={cn(
                'absolute -top-2 -right-2 h-4 min-w-4 px-1 text-[10px] flex items-center justify-center',
                'rounded-full'
              )}
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </div>

        {!collapsed && (
          <>
            <span className="flex-1 text-left">Notifications</span>
            {unreadCount > 0 && (
              <Badge
                variant="secondary"
                className="ml-auto rounded-full px-2 text-xs"
              >
                {unreadCount}
              </Badge>
            )}
          </>
        )}
      </Button>

      <NotificationPanel
        open={panelOpen}
        onOpenChange={setPanelOpen}
        workspaceId={workspaceId}
      />
    </>
  );
}

export function NotificationBell(props: NotificationBellProps) {
  return (
    <ApolloProvider client={notificationClient}>
      <NotificationBellInner {...props} />
    </ApolloProvider>
  )
}
