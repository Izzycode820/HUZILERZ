/**
 * Notification Sound Module
 * 
 * Plays notification sounds when new notifications arrive.
 * Uses the browser Notification API for system sounds, with
 * audio fallback for browsers that don't support it.
 */

// Throttle state (module-level to persist across calls)
let isPlaying = false;
let throttleTimeout: NodeJS.Timeout | null = null;
const THROTTLE_MS = 1000;

interface NotificationData {
    id: string;
    title: string;
    body: string;
}

/**
 * Check if browser notification permission is granted
 */
export function isNotificationPermissionGranted(): boolean {
    if (typeof window === 'undefined' || !('Notification' in window)) {
        return false;
    }
    return Notification.permission === 'granted';
}

/**
 * Request notification permission from the user
 */
export async function requestNotificationPermission(): Promise<NotificationPermission | 'unsupported'> {
    if (typeof window === 'undefined' || !('Notification' in window)) {
        return 'unsupported';
    }

    if (Notification.permission !== 'default') {
        return Notification.permission;
    }

    try {
        return await Notification.requestPermission();
    } catch (error) {
        console.error('[NotificationSound] Permission request failed:', error);
        return 'denied';
    }
}

/**
 * Play notification sound for an incoming notification
 * 
 * Uses browser's Notification API with `silent: false` to trigger
 * the system default notification sound. Falls back to Audio API
 * if Notification isn't available or permitted.
 * 
 * @param notification - The notification data
 * @param options - Optional configuration
 */
export function playNotificationSound(
    notification: NotificationData,
    options: { showBrowserNotification?: boolean } = {}
): void {
    const { showBrowserNotification = true } = options;

    // Throttle to prevent sound spam
    if (isPlaying) return;

    isPlaying = true;

    // Clear throttle after delay
    if (throttleTimeout) {
        clearTimeout(throttleTimeout);
    }
    throttleTimeout = setTimeout(() => {
        isPlaying = false;
    }, THROTTLE_MS);

    // Method 1: Use browser Notification API (plays system sound)
    if (isNotificationPermissionGranted() && showBrowserNotification) {
        try {
            const browserNotification = new Notification(notification.title, {
                body: notification.body,
                icon: '/icons/icon-192x192.png',
                tag: notification.id, // Prevents duplicate notifications
                silent: false, // This triggers the system sound!
                requireInteraction: false,
            });

            // Auto-close after 5 seconds
            setTimeout(() => {
                browserNotification.close();
            }, 5000);

            // Handle click - focus the window
            browserNotification.onclick = () => {
                window.focus();
                browserNotification.close();
            };

            return;
        } catch (error) {
            console.warn('[NotificationSound] Browser notification failed:', error);
            // Fall through to audio fallback
        }
    }

    // Method 2: Fallback - play audio file directly
    try {
        const audio = new Audio('/sounds/notification.mp3');
        audio.volume = 0.5;
        audio.play().catch((err) => {
            // Audio play was blocked (user hasn't interacted with page yet)
            console.debug('[NotificationSound] Audio playback blocked:', err.message);
        });
    } catch (error) {
        console.debug('[NotificationSound] Audio fallback failed:', error);
    }
}

