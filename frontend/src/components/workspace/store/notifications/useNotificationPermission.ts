/**
 * Notification Permission Hook
 * 
 * Manages browser notification permission state and provides
 * methods to request permission from the user.
 */

import { useCallback, useEffect, useState } from 'react';

export type NotificationPermissionState = 'granted' | 'denied' | 'default' | 'unsupported';

interface UseNotificationPermissionReturn {
    /** Current permission state */
    permission: NotificationPermissionState;
    /** Whether notifications are supported by the browser */
    isSupported: boolean;
    /** Whether permission has been granted */
    isGranted: boolean;
    /** Whether permission was denied */
    isDenied: boolean;
    /** Whether we should prompt the user for permission */
    shouldPrompt: boolean;
    /** Request notification permission from user */
    requestPermission: () => Promise<NotificationPermissionState>;
}

/**
 * Hook to manage browser notification permissions
 * 
 * @example
 * ```tsx
 * const { isGranted, shouldPrompt, requestPermission } = useNotificationPermission();
 * 
 * if (shouldPrompt) {
 *   return <Button onClick={requestPermission}>Enable Notifications</Button>;
 * }
 * ```
 */
export function useNotificationPermission(): UseNotificationPermissionReturn {
    const [permission, setPermission] = useState<NotificationPermissionState>('default');

    // Check if browser supports notifications
    const isSupported = typeof window !== 'undefined' && 'Notification' in window;

    // Sync permission state on mount and when it changes
    useEffect(() => {
        if (!isSupported) {
            setPermission('unsupported');
            return;
        }

        // Get initial permission state
        setPermission(Notification.permission as NotificationPermissionState);

        // Listen for permission changes (some browsers support this)
        const handlePermissionChange = () => {
            setPermission(Notification.permission as NotificationPermissionState);
        };

        // Some browsers expose permissionchange event
        if ('permissions' in navigator) {
            navigator.permissions
                .query({ name: 'notifications' as PermissionName })
                .then((status) => {
                    status.addEventListener('change', handlePermissionChange);
                })
                .catch(() => {
                    // Permission API not fully supported, that's okay
                });
        }

        return () => {
            // Cleanup if needed
        };
    }, [isSupported]);

    const requestPermission = useCallback(async (): Promise<NotificationPermissionState> => {
        if (!isSupported) {
            return 'unsupported';
        }

        // Already granted
        if (Notification.permission === 'granted') {
            return 'granted';
        }

        // Already denied - can't re-request
        if (Notification.permission === 'denied') {
            return 'denied';
        }

        try {
            const result = await Notification.requestPermission();
            setPermission(result as NotificationPermissionState);
            return result as NotificationPermissionState;
        } catch (error) {
            console.error('[NotificationPermission] Request failed:', error);
            return 'denied';
        }
    }, [isSupported]);

    return {
        permission,
        isSupported,
        isGranted: permission === 'granted',
        isDenied: permission === 'denied',
        shouldPrompt: permission === 'default' && isSupported,
        requestPermission,
    };
}
