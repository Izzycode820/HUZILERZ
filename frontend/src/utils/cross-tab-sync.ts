/**
 * Cross-tab authentication synchronization service
 * Secure approach that syncs auth events without exposing tokens
 */

interface AuthSyncMessage {
  type: 'LOGIN' | 'LOGOUT' | 'TOKEN_REFRESHED' | 'SESSION_EXPIRED';
  timestamp: number;
  userId?: number; // Aligned with backend user ID type
}

class CrossTabAuthSync {
  private channel: BroadcastChannel | null = null;
  private listeners: Set<(message: AuthSyncMessage) => void> = new Set();

  constructor() {
    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      this.setupBroadcastChannel();
    }
  }

  private setupBroadcastChannel(): void {
    try {
      this.channel = new BroadcastChannel('auth-sync');

      this.channel.onmessage = (event) => {
        const message = event.data as AuthSyncMessage;

        // Basic validation
        if (!message.type || !message.timestamp) {
          console.warn('Cross-tab sync: Invalid message format');
          return;
        }

        // Ignore old messages (older than 5 seconds)
        if (Date.now() - message.timestamp > 5000) {
          return;
        }

        // Notify all listeners
        this.listeners.forEach(listener => {
          try {
            listener(message);
          } catch (error) {
            console.error('Cross-tab sync: Listener error', error);
          }
        });
      };

      this.channel.addEventListener('messageerror', (event) => {
        console.error('Cross-tab sync: Message deserialization error', event);
      });

    } catch (error) {
      console.warn('Cross-tab sync: Failed to setup BroadcastChannel', error);
    }
  }

  /**
   * Add listener for auth events
   */
  addListener(listener: (message: AuthSyncMessage) => void): void {
    this.listeners.add(listener);
  }

  /**
   * Remove listener
   */
  removeListener(listener: (message: AuthSyncMessage) => void): void {
    this.listeners.delete(listener);
  }

  /**
   * Broadcast authentication event to other tabs
   */
  broadcastAuthEvent(type: AuthSyncMessage['type'], userId?: number): void {
    if (!this.channel) return;

    const message: AuthSyncMessage = {
      type,
      timestamp: Date.now(),
      userId
    };

    try {
      this.channel.postMessage(message);
    } catch (error) {
      console.error('Cross-tab sync: Failed to broadcast', error);
    }
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.listeners.clear();

    if (this.channel) {
      this.channel.close();
      this.channel = null;
    }
  }
}

// Singleton instance
export const crossTabAuthSync = new CrossTabAuthSync();