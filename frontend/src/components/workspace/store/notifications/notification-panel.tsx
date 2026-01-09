'use client';

/**
 * Notification Panel Component
 *
 * Slide-over panel from the right side showing all notifications.
 * Uses shadcn/ui Sheet component for the slide-over effect.
 */

import { useEffect } from 'react';
import { useQuery, useMutation, ApolloProvider } from '@apollo/client/react';
import { notificationClient } from '@/services/graphql/clients';
import { formatDistanceToNow } from 'date-fns';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from '@/components/shadcn-ui/sheet';
import { Button } from '@/components/shadcn-ui/button';
import { ScrollArea } from '@/components/shadcn-ui/scroll-area';
import { Badge } from '@/components/shadcn-ui/badge';
import { Separator } from '@/components/shadcn-ui/separator';
import {
    IconBell,
    IconChecks,
    IconPackage,
    IconCreditCard,
    IconAlertCircle,
    IconX,
    IconCheck,
} from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { useNotificationSocket } from './use-notification-socket';
import { GetWorkspaceNotificationsDocument } from '@/services/graphql/notifications/queries/__generated__/getWorkspaceNotifications.generated';
import { MarkNotificationAsReadDocument } from '@/services/graphql/notifications/mutations/__generated__/markAsRead.generated';
import { MarkAllNotificationsAsReadDocument } from '@/services/graphql/notifications/mutations/__generated__/markAllAsRead.generated';

interface NotificationPanelProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    workspaceId: string;
}

// Map notification types to icons
const notificationIcons: Record<string, React.ElementType> = {
    order_created: IconPackage,
    order_paid: IconCreditCard,
    order_cancelled: IconX,
    payment_failed: IconAlertCircle,
    subscription_activated: IconCheck,
    subscription_expired: IconAlertCircle,
    stock_low: IconAlertCircle,
    stock_out: IconAlertCircle,
};

function NotificationPanelInner({
    open,
    onOpenChange,
    workspaceId,
}: NotificationPanelProps) {
    const { unreadCount, notifications: wsNotifications, markAsRead, markAllAsRead } =
        useNotificationSocket();

    // Fetch notifications via GraphQL
    const { data, loading, refetch } = useQuery(GetWorkspaceNotificationsDocument, {
        variables: { limit: 50 },
        skip: !open,
    });

    const [markRead] = useMutation(MarkNotificationAsReadDocument);
    const [markAllRead] = useMutation(MarkAllNotificationsAsReadDocument);

    // Refetch when new WebSocket notification arrives
    useEffect(() => {
        if (wsNotifications.length > 0 && open) {
            refetch();
        }
    }, [wsNotifications, open, refetch]);

    const notifications = data?.workspaceNotifications || [];

    const handleMarkAsRead = async (notificationId: string) => {
        // Optimistic via WebSocket
        markAsRead(notificationId);
        // Also via GraphQL for persistence
        await markRead({ variables: { notificationId } });
    };

    const handleMarkAllAsRead = async () => {
        // Optimistic via WebSocket
        markAllAsRead(workspaceId);
        // Also via GraphQL for persistence
        await markAllRead({ variables: { workspaceId } });
        refetch();
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="w-full sm:max-w-md overflow-hidden flex flex-col">
                <SheetHeader className="flex-shrink-0">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <IconBell className="h-5 w-5" />
                            <SheetTitle>Notifications</SheetTitle>
                            {unreadCount > 0 && (
                                <Badge variant="destructive" className="rounded-full px-2">
                                    {unreadCount}
                                </Badge>
                            )}
                        </div>
                        {unreadCount > 0 && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleMarkAllAsRead}
                                className="text-xs"
                            >
                                <IconChecks className="h-4 w-4 mr-1" />
                                Mark all read
                            </Button>
                        )}
                    </div>
                    <SheetDescription>
                        Stay updated with your store activity
                    </SheetDescription>
                </SheetHeader>

                <Separator className="my-4" />

                <ScrollArea className="flex-1 -mx-6 px-6">
                    {loading ? (
                        <div className="space-y-4">
                            {[...Array(3)].map((_, i) => (
                                <div key={i} className="animate-pulse">
                                    <div className="h-4 bg-muted rounded w-3/4 mb-2" />
                                    <div className="h-3 bg-muted rounded w-full" />
                                </div>
                            ))}
                        </div>
                    ) : notifications.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <IconBell className="h-12 w-12 text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">No notifications yet</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                You'll see order updates and alerts here
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {notifications.map((notification) => {
                                if (!notification) return null;

                                const IconComponent =
                                    notificationIcons[notification.notificationType] || IconBell;
                                const isUnread = !notification.isRead;

                                return (
                                    <div
                                        key={notification.id}
                                        className={cn(
                                            'relative p-3 rounded-lg cursor-pointer transition-colors',
                                            isUnread
                                                ? 'bg-accent/50 hover:bg-accent'
                                                : 'hover:bg-muted/50'
                                        )}
                                        onClick={() => handleMarkAsRead(notification.id)}
                                    >
                                        <div className="flex gap-3">
                                            <div
                                                className={cn(
                                                    'flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center',
                                                    isUnread ? 'bg-primary/10' : 'bg-muted'
                                                )}
                                            >
                                                <IconComponent
                                                    className={cn(
                                                        'h-4 w-4',
                                                        isUnread ? 'text-primary' : 'text-muted-foreground'
                                                    )}
                                                />
                                            </div>

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-2">
                                                    <p
                                                        className={cn(
                                                            'text-sm font-medium truncate',
                                                            isUnread && 'text-foreground'
                                                        )}
                                                    >
                                                        {notification.title}
                                                    </p>
                                                    {isUnread && (
                                                        <span className="flex-shrink-0 h-2 w-2 rounded-full bg-primary" />
                                                    )}
                                                </div>

                                                <p className="text-sm text-muted-foreground line-clamp-2 mt-0.5">
                                                    {notification.body}
                                                </p>

                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-xs text-muted-foreground">
                                                        {formatDistanceToNow(new Date(notification.createdAt), {
                                                            addSuffix: true,
                                                        })}
                                                    </span>
                                                    {notification.workspaceName && (
                                                        <>
                                                            <span className="text-xs text-muted-foreground">
                                                                -
                                                            </span>
                                                            <span className="text-xs text-muted-foreground">
                                                                {notification.workspaceName}
                                                            </span>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}

export function NotificationPanel(props: NotificationPanelProps) {
    return (
        <ApolloProvider client={notificationClient}>
            <NotificationPanelInner {...props} />
        </ApolloProvider>
    )
}
