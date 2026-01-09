'use client';

/**
 * Authentication Mutex for handling race conditions during token refresh
 * Prevents multiple token refresh operations from running simultaneously
 */
class AuthMutex {
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;
  private subscribers: Array<(token: string | null) => void> = [];

  /**
   * Add a subscriber to be notified when refresh completes
   */
  addSubscriber(callback: (token: string | null) => void): void {
    this.subscribers.push(callback);
  }

  /**
   * Remove a subscriber
   */
  removeSubscriber(callback: (token: string | null) => void): void {
    this.subscribers = this.subscribers.filter(sub => sub !== callback);
  }

  /**
   * Notify all subscribers when refresh completes
   */
  private notifySubscribers(token: string | null): void {
    this.subscribers.forEach(callback => callback(token));
    this.subscribers = [];
  }

  /**
   * Execute token refresh with mutex protection
   * @param refreshFunction - Function that performs the actual token refresh
   * @returns Promise that resolves to the new token or null if refresh failed
   */
  async executeRefresh(
    refreshFunction: () => Promise<string | null>
  ): Promise<string | null> {
    // If already refreshing, wait for the existing refresh to complete
    if (this.isRefreshing && this.refreshPromise) {
      return await this.refreshPromise;
    }

    // Start the refresh process
    this.isRefreshing = true;

    this.refreshPromise = this.performRefresh(refreshFunction);

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * Perform the actual refresh with error handling
   */
  private async performRefresh(
    refreshFunction: () => Promise<string | null>
  ): Promise<string | null> {
    try {
      const newToken = await refreshFunction();

      if (newToken) {
        this.notifySubscribers(newToken);
        return newToken;
      } else {
        this.notifySubscribers(null);
        return null;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      this.notifySubscribers(null);
      return null;
    }
  }

  /**
   * Check if a refresh is currently in progress
   */
  isRefreshInProgress(): boolean {
    return this.isRefreshing;
  }

  /**
   * Reset the mutex (use carefully, mainly for testing)
   */
  reset(): void {
    this.isRefreshing = false;
    this.refreshPromise = null;
    this.subscribers = [];
  }
}

// Export a singleton instance
export const authMutex = new AuthMutex();