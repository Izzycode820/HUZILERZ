/**
 * Notification WebSocket Hook
 *
 * Real-time notification updates via WebSocket connection.
 * Auto-connects when mounted, auto-reconnects on disconnect.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuthStore, authSelectors } from '@/stores/authentication/authStore';
import { playNotificationSound } from './useNotificationSound';

export interface WebSocketNotification {
    id: string;
    type: string;
    title: string;
    body: string;
    workspace_id: string | null;
    workspace_name: string | null;
    created_at: string;
    is_read: boolean;
    data: Record<string, any>;
}

export interface NotificationSocketState {
    isConnected: boolean;
    unreadCount: number;
    notifications: WebSocketNotification[];
    lastNotification: WebSocketNotification | null;
}

interface UseNotificationSocketOptions {
    onNewNotification?: (notification: WebSocketNotification) => void;
    onUnreadCountChange?: (count: number) => void;
}

export function useNotificationSocket(options?: UseNotificationSocketOptions) {
    const isAuthenticated = useAuthStore(authSelectors.isAuthenticated);
    const token = useAuthStore((state) => state.token);

    const [state, setState] = useState<NotificationSocketState>({
        isConnected: false,
        unreadCount: 0,
        notifications: [],
        lastNotification: null,
    });

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    const connect = useCallback(() => {
        if (!isAuthenticated || !token) {
            return;
        }

        // Don't connect if already connected
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = process.env.NEXT_PUBLIC_WS_HOST || 'localhost:8000';
        const wsUrl = `${wsProtocol}//${wsHost}/ws/notifications/?token=${token}`;

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('[NotificationSocket] Connected');
                setState((prev) => ({ ...prev, isConnected: true }));
                reconnectAttempts.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    switch (data.type) {
                        case 'connection_established':
                            setState((prev) => ({
                                ...prev,
                                unreadCount: data.unread_count || 0,
                            }));
                            break;

                        case 'new_notification':
                            const notification = data.notification as WebSocketNotification;
                            setState((prev) => ({
                                ...prev,
                                unreadCount: prev.unreadCount + 1,
                                notifications: [notification, ...prev.notifications],
                                lastNotification: notification,
                            }));
                            options?.onNewNotification?.(notification);

                            // Play system notification sound
                            playNotificationSound(notification);
                            break;

                        case 'unread_count_update':
                            setState((prev) => ({
                                ...prev,
                                unreadCount: data.unread_count || 0,
                            }));
                            options?.onUnreadCountChange?.(data.unread_count || 0);
                            break;

                        case 'notification_read':
                            if (data.success) {
                                setState((prev) => ({
                                    ...prev,
                                    unreadCount: Math.max(0, prev.unreadCount - 1),
                                    notifications: prev.notifications.map((n) =>
                                        n.id === data.notification_id ? { ...n, is_read: true } : n
                                    ),
                                }));
                            }
                            break;

                        case 'all_notifications_read':
                            setState((prev) => ({
                                ...prev,
                                unreadCount: 0,
                                notifications: prev.notifications.map((n) => ({
                                    ...n,
                                    is_read: true,
                                })),
                            }));
                            break;

                        case 'pong':
                            // Heartbeat response
                            break;

                        default:
                            console.log('[NotificationSocket] Unknown message type:', data.type);
                    }
                } catch (e) {
                    console.error('[NotificationSocket] Parse error:', e);
                }
            };

            ws.onclose = (event) => {
                console.log('[NotificationSocket] Disconnected:', event.code);
                setState((prev) => ({ ...prev, isConnected: false }));
                wsRef.current = null;

                // Auto-reconnect with exponential backoff
                if (
                    event.code !== 1000 &&
                    reconnectAttempts.current < maxReconnectAttempts
                ) {
                    const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
                    reconnectAttempts.current++;
                    console.log(
                        `[NotificationSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`
                    );
                    reconnectTimeoutRef.current = setTimeout(connect, delay);
                }
            };

            ws.onerror = (error) => {
                // Silently handle errors - onclose will handle reconnection
                // console.error('[NotificationSocket] Error:', error);
            };
        } catch (e) {
            console.error('[NotificationSocket] Connection failed:', e);
        }
    }, [isAuthenticated, token, options]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close(1000, 'User disconnect');
            wsRef.current = null;
        }
        setState((prev) => ({ ...prev, isConnected: false }));
    }, []);

    const markAsRead = useCallback((notificationId: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
                JSON.stringify({
                    action: 'mark_read',
                    notification_id: notificationId,
                })
            );
        }
    }, []);

    const markAllAsRead = useCallback((workspaceId?: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
                JSON.stringify({
                    action: 'mark_all_read',
                    workspace_id: workspaceId,
                })
            );
        }
    }, []);

    // Auto-connect on mount
    useEffect(() => {
        if (isAuthenticated && token) {
            connect();
        }

        return () => {
            disconnect();
        };
    }, [isAuthenticated, token, connect, disconnect]);

    // Heartbeat to keep connection alive
    useEffect(() => {
        if (!state.isConnected) return;

        const interval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ action: 'ping' }));
            }
        }, 30000);

        return () => clearInterval(interval);
    }, [state.isConnected]);

    return {
        ...state,
        connect,
        disconnect,
        markAsRead,
        markAllAsRead,
    };
}
