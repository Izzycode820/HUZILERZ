/**
 * Capabilities Manager - Industry Standard Pattern (Stripe/GitHub/Vercel)
 *
 * JWT contains: tier + capabilities_version hash
 * Full capabilities fetched separately via API
 * Version mismatch triggers refetch
 *
 * Flow:
 * 1. Login/Refresh → JWT has capabilities_version
 * 2. Check if cached version matches JWT version
 * 3. Match → use cache, Mismatch → fetch fresh capabilities
 * 4. Cache capabilities in memory + localStorage
 */

import type { CapabilitiesResponse, SubscriptionData } from '../types/authentication/auth'
import subscriptionService from '../services/subscription/subscription'

// ============================================================================
// Types
// ============================================================================

interface CachedCapabilities {
  version: string
  capabilities: Record<string, any>
  tier: string
  fetchedAt: number
}

// ============================================================================
// Capabilities Manager
// ============================================================================

class CapabilitiesManagerClass {
  private memoryCache: CachedCapabilities | null = null
  private isFetching: boolean = false
  private fetchPromise: Promise<CapabilitiesResponse> | null = null

  /**
   * Get storage key scoped by user (workspace-level scoping optional)
   */
  private getStorageKey(userId: number): string {
    return `capabilities:${userId}`
  }

  /**
   * Get capabilities with automatic version checking
   *
   * @param subscription - Subscription data from JWT
   * @param userId - User ID for cache scoping
   * @returns Full capabilities from API or cache
   */
  async getCapabilities(
    subscription: SubscriptionData | null,
    userId: number
  ): Promise<Record<string, any> | null> {
    if (!subscription) return null

    const jwtVersion = subscription.capabilities_version
    const key = this.getStorageKey(userId)

    // 1. Memory cache check (fastest)
    if (this.memoryCache && this.memoryCache.version === jwtVersion) {
      return this.memoryCache.capabilities
    }

    // 2. localStorage cache check
    const cached = this.getCached(key)
    if (cached && cached.version === jwtVersion) {
      // Restore memory cache
      this.memoryCache = cached
      return cached.capabilities
    }

    // 3. Version mismatch or no cache - fetch fresh
    // Prevent duplicate fetches (race condition protection)
    if (this.isFetching && this.fetchPromise) {
      const response = await this.fetchPromise
      return response.capabilities
    }

    try {
      this.isFetching = true
      this.fetchPromise = subscriptionService.getCapabilities()
      const response = await this.fetchPromise

      // Create snapshot
      const snapshot: CachedCapabilities = {
        version: response.version,
        capabilities: response.capabilities,
        tier: response.tier,
        fetchedAt: Date.now(),
      }

      // Cache in memory and localStorage
      this.memoryCache = snapshot
      this.saveToCache(key, snapshot)

      return snapshot.capabilities
    } catch (error) {
      console.error('Failed to fetch capabilities:', error)
      // Return cached capabilities if available (graceful degradation)
      return cached?.capabilities || null
    } finally {
      this.isFetching = false
      this.fetchPromise = null
    }
  }

  /**
   * Check if capabilities need refresh
   * Returns true if cached version doesn't match JWT version
   */
  needsRefresh(subscription: SubscriptionData | null, userId: number): boolean {
    if (!subscription) return false

    const jwtVersion = subscription.capabilities_version

    // Check memory cache
    if (this.memoryCache) {
      return this.memoryCache.version !== jwtVersion
    }

    // Check localStorage cache
    const cached = this.getCached(this.getStorageKey(userId))
    return !cached || cached.version !== jwtVersion
  }

  /**
   * Check if user can access a specific capability
   */
  can(feature: string): boolean {
    return !!this.memoryCache?.capabilities?.[feature]
  }

  /**
   * Get specific capability value
   */
  get(feature: string): any {
    return this.memoryCache?.capabilities?.[feature]
  }

  /**
   * Get all capabilities (from memory cache)
   */
  getAll(): Record<string, any> | null {
    return this.memoryCache?.capabilities || null
  }

  /**
   * Clear capabilities cache for user
   */
  clear(userId: number): void {
    this.memoryCache = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.getStorageKey(userId))
    }
  }

  /**
   * Clear all capabilities caches
   */
  clearAll(): void {
    this.memoryCache = null
    if (typeof window !== 'undefined') {
      // Clear all capabilities keys
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('capabilities:')) {
          localStorage.removeItem(key)
        }
      })
    }
  }

  // ============================================================================
  // Private Methods
  // ============================================================================

  private getCached(key: string): CachedCapabilities | null {
    if (typeof window === 'undefined') return null

    try {
      const raw = localStorage.getItem(key)
      return raw ? JSON.parse(raw) : null
    } catch (error) {
      console.error('Failed to read capabilities cache:', error)
      return null
    }
  }

  private saveToCache(key: string, snapshot: CachedCapabilities): void {
    if (typeof window === 'undefined') return

    try {
      localStorage.setItem(key, JSON.stringify(snapshot))
    } catch (error) {
      console.error('Failed to save capabilities cache:', error)
    }
  }
}

// ============================================================================
// Export Singleton
// ============================================================================

export const CapabilitiesManager = new CapabilitiesManagerClass()
export default CapabilitiesManager

// ============================================================================
// Usage Guide - UI Gating and Capability-Based Decisions
// ============================================================================

/**
 * HOW TO USE CAPABILITIES IN YOUR UI
 *
 * Capabilities are fetched automatically on:
 * - Login (when JWT is received)
 * - Token refresh (every 15 minutes)
 * - Workspace switch (if workspace context changes)
 * - App reload (session restoration)
 *
 * The system automatically compares JWT's capabilities_version hash with cached version.
 * If they differ → fresh capabilities are fetched from /api/subscriptions/me/capabilities/
 *
 * ============================================================================
 * EXAMPLE 1: Basic Feature Gating
 * ============================================================================
 *
 * import { useAuth } from '@/hooks/authentication/useAuth'
 *
 * function DeployButton() {
 *   const { can } = useAuth()
 *
 *   if (!can('deployment_allowed')) {
 *     return <UpgradeBanner feature="Deployment" />
 *   }
 *
 *   return <button onClick={handleDeploy}>Deploy Site</button>
 * }
 *
 * ============================================================================
 * EXAMPLE 2: Conditional UI Rendering
 * ============================================================================
 *
 * function SettingsPage() {
 *   const { can, capabilities } = useAuth()
 *
 *   return (
 *     <div>
 *       <ProfileSettings />
 *
 *       {can('custom_domains') && (
 *         <CustomDomainSettings limit={capabilities?.custom_domains ?? 0} />
 *       )}
 *
 *       {can('analytics') && (
 *         <AnalyticsSettings level={capabilities?.analytics_level} />
 *       )}
 *
 *       {can('white_label') && <WhiteLabelSettings />}
 *     </div>
 *   )
 * }
 *
 * ============================================================================
 * EXAMPLE 3: Multiple Capability Checks
 * ============================================================================
 *
 * function AdvancedFeatures() {
 *   const { can, capabilities, deploymentAllowed, maxWorkspaces } = useAuth()
 *
 *   const hasProFeatures =
 *     can('analytics') &&
 *     can('custom_domains') &&
 *     deploymentAllowed
 *
 *   if (!hasProFeatures) {
 *     return <ProPlanUpsell />
 *   }
 *
 *   return (
 *     <div>
 *       <WorkspaceList max={maxWorkspaces} />
 *       <AnalyticsDashboard />
 *       <DomainManager limit={capabilities?.custom_domains} />
 *     </div>
 *   )
 * }
 *
 * ============================================================================
 * EXAMPLE 4: Navigation Guards
 * ============================================================================
 *
 * function ProtectedRoute({ children, requiredCapability }) {
 *   const { can, isLoading } = useAuth()
 *
 *   if (isLoading) return <LoadingSpinner />
 *
 *   if (!can(requiredCapability)) {
 *     return <Navigate to="/upgrade" />
 *   }
 *
 *   return children
 * }
 *
 * // Usage:
 * <ProtectedRoute requiredCapability="deployment_allowed">
 *   <DeploymentPage />
 * </ProtectedRoute>
 *
 * ============================================================================
 * EXAMPLE 5: Form Validation Based on Limits
 * ============================================================================
 *
 * function CreateWorkspaceForm() {
 *   const { maxWorkspaces, capabilities } = useAuth()
 *   const currentWorkspaceCount = useWorkspaces().length
 *
 *   const canCreateMore = currentWorkspaceCount < maxWorkspaces
 *
 *   return (
 *     <form>
 *       {!canCreateMore && (
 *         <Alert>
 *           You've reached your limit of {maxWorkspaces} workspaces.
 *           Upgrade to create more.
 *         </Alert>
 *       )}
 *       <button disabled={!canCreateMore}>Create Workspace</button>
 *     </form>
 *   )
 * }
 *
 * ============================================================================
 * HOW VERSION VALIDATION WORKS (Behind the Scenes)
 * ============================================================================
 *
 * 1. User logs in → Backend returns JWT with:
 *    {
 *      subscription: {
 *        tier: "pro",
 *        capabilities_version: "v2_abc123de"  ← Hash from plans.yaml
 *      }
 *    }
 *
 * 2. Frontend extracts subscription from JWT → Triggers syncCapabilities()
 *
 * 3. CapabilitiesManager.getCapabilities() checks:
 *    - Memory cache: Does cached.version === jwt.capabilities_version?
 *      → YES: Return cached capabilities (no API call) ✅
 *      → NO: Continue to step 4
 *
 *    - localStorage cache: Does cached.version === jwt.capabilities_version?
 *      → YES: Restore to memory cache, return capabilities ✅
 *      → NO: Continue to step 5
 *
 * 4. Version mismatch detected → Fetch fresh capabilities:
 *    GET /api/subscriptions/me/capabilities/
 *    Response:
 *    {
 *      tier: "pro",
 *      capabilities: { deployment_allowed: true, custom_domains: 3, ... },
 *      version: "v2_abc123de"
 *    }
 *
 * 5. Cache the response:
 *    - Memory cache (fast in-session access)
 *    - localStorage (survives page refresh)
 *
 * 6. User can now access capabilities via useAuth():
 *    const { can, capabilities } = useAuth()
 *
 * ============================================================================
 * WHEN CAPABILITIES ARE REFRESHED
 * ============================================================================
 *
 * Automatic Triggers:
 * ✅ Login - JWT received → Version check → Fetch if needed
 * ✅ Token Refresh - JWT refreshed (every 15min) → Version check → Fetch if needed
 * ✅ App Reload - Session restored → JWT decoded → Version check → Fetch if needed
 * ✅ Workspace Switch - New workspace context → JWT refreshed → Version check
 *
 * Manual Trigger (if plans.yaml changes):
 * 1. Admin runs: python manage.py sync_plans
 * 2. Backend invalidates capabilities_version cache
 * 3. New JWTs get new hash: "v2_xyz789"
 * 4. User refreshes token → Frontend detects version mismatch → Fetches fresh capabilities
 * 5. UI updates automatically with new capabilities
 *
 * ============================================================================
 * SECURITY NOTE
 * ============================================================================
 *
 * Frontend capabilities are ADVISORY ONLY - for UX decisions (hiding buttons, etc.)
 * Backend MUST enforce capabilities on every API request:
 *
 * // Backend enforcement (example):
 * if (!workspace.capabilities.deployment_allowed) {
 *   raise PermissionDenied("Deployment not allowed on your plan")
 * }
 *
 * Never trust frontend checks alone - always enforce server-side!
 */
