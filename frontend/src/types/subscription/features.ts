// Feature gating types matching Django backend

export const CORE_FEATURES = {
  // Deployment and hosting
  DEPLOYMENT: 'deployment',
  CUSTOM_DOMAIN: 'custom_domain',
  SSL_CERTIFICATES: 'ssl_certificates',

  // Analytics and insights
  ANALYTICS: 'analytics',
  ANALYTICS_BASIC: 'analytics_basic',
  ANALYTICS_ADVANCED: 'analytics_advanced',
  CONVERSION_TRACKING: 'conversion_tracking',

  // Branding and customization
  WHITE_LABEL: 'white_label',
  REMOVE_BRANDING: 'remove_branding',
  CUSTOM_FAVICON: 'custom_favicon',

  // Support and priority
  PRIORITY_SUPPORT: 'priority_support',
  DEDICATED_SUPPORT: 'dedicated_support',
  PHONE_SUPPORT: 'phone_support',

  // API and integrations
  API_ACCESS: 'api_access',
  WEBHOOK_INTEGRATION: 'webhook_integration',
  THIRD_PARTY_INTEGRATIONS: 'third_party_integrations',

  // SEO and marketing
  SEO_TOOLS: 'seo_tools',
  META_TAGS_CONTROL: 'meta_tags_control',
  SITEMAP_GENERATION: 'sitemap_generation',

  // Storage and bandwidth
  EXTENDED_STORAGE: 'extended_storage',
  UNLIMITED_BANDWIDTH: 'unlimited_bandwidth',
  CDN_ACCELERATION: 'cdn_acceleration',

  // Team and collaboration
  TEAM_COLLABORATION: 'team_collaboration',
  USER_ROLES_PERMISSIONS: 'user_roles_permissions',
  AUDIT_LOGS: 'audit_logs',

  // Advanced features
  A_B_TESTING: 'a_b_testing',
  CUSTOM_CODE_INJECTION: 'custom_code_injection',
  DATABASE_BACKUPS: 'database_backups',
} as const;

export type CoreFeatureType = typeof CORE_FEATURES[keyof typeof CORE_FEATURES];

// Feature limits by subscription tier
export const FEATURE_LIMITS = {
  free: {
    workspaces: 1,
    sites_per_workspace: 0, // Build only, no deployment
    storage_gb: 0.5,
    bandwidth_gb: 0,
    custom_domains: 0,
    team_members: 1,
    api_calls_per_month: 0,
  },
  beginning: {
    workspaces: 1,
    sites_per_workspace: 1,
    storage_gb: 10,
    bandwidth_gb: 100,
    custom_domains: 1,
    team_members: 2,
    api_calls_per_month: 1000,
  },
  pro: {
    workspaces: 3,
    sites_per_workspace: 5,
    storage_gb: 50,
    bandwidth_gb: 500,
    custom_domains: 10,
    team_members: 10,
    api_calls_per_month: 10000,
  },
  enterprise: {
    workspaces: -1, // Unlimited
    sites_per_workspace: -1, // Unlimited
    storage_gb: 500,
    bandwidth_gb: 2000,
    custom_domains: -1, // Unlimited
    team_members: -1, // Unlimited
    api_calls_per_month: 100000,
  },
} as const;

// Feature access result from backend
export interface FeatureAccessResult {
  readonly available: boolean;
  readonly current_tier: 'free' | 'beginning' | 'pro' | 'enterprise';
  readonly required_tier?: 'beginning' | 'pro' | 'enterprise';
  readonly upgrade_message?: string;
  readonly usage_info?: {
    readonly current_usage: number;
    readonly limit: number;
    readonly percentage_used: number;
  };
  readonly grace_period?: {
    readonly enabled: boolean;
    readonly expires_at?: string;
    readonly remaining_days?: number;
  };
}

// Feature gate configuration
export interface FeatureGateConfig {
  readonly feature: CoreFeatureType;
  readonly required_tier: 'beginning' | 'pro' | 'enterprise';
  readonly fallback_component?: React.ComponentType;
  readonly upgrade_prompt?: {
    readonly title: string;
    readonly description: string;
    readonly cta_text: string;
    readonly upgrade_url: string;
  };
  readonly usage_based?: boolean;
  readonly soft_limit?: boolean; // Allow usage with warning vs hard block
}

// Batch feature check request
export interface BatchFeatureCheckRequest {
  readonly features: readonly CoreFeatureType[];
  readonly include_usage_info?: boolean;
  readonly include_upgrade_suggestions?: boolean;
}

// Batch feature check response
export interface BatchFeatureCheckResponse {
  readonly feature_availability: Record<string, FeatureAccessResult>;
  readonly current_tier: string;
  readonly is_subscription_active: boolean;
  readonly upgrade_suggestions?: Array<{
    readonly feature: string;
    readonly required_tier: string;
    readonly message: string;
    readonly priority: 'low' | 'medium' | 'high';
  }>;
  readonly usage_warnings?: Array<{
    readonly resource: string;
    readonly current_usage: number;
    readonly limit: number;
    readonly warning_threshold: number;
    readonly days_until_limit?: number;
  }>;
}

// Feature usage tracking
export interface FeatureUsageEvent {
  readonly feature: CoreFeatureType;
  readonly user_id: number;
  readonly workspace_id?: string;
  readonly event_type: 'access_granted' | 'access_denied' | 'upgrade_prompt_shown' | 'upgrade_completed';
  readonly metadata?: Record<string, unknown>;
  readonly timestamp: string;
}

// Feature analytics for conversion optimization
export interface FeatureAnalytics {
  readonly feature: CoreFeatureType;
  readonly total_access_attempts: number;
  readonly successful_accesses: number;
  readonly blocked_attempts: number;
  readonly upgrade_prompt_shown: number;
  readonly upgrade_conversions: number;
  readonly conversion_rate: number;
  readonly average_time_to_upgrade: number; // in hours
  readonly top_converting_messages: Array<{
    readonly message: string;
    readonly conversion_rate: number;
    readonly impressions: number;
  }>;
}

// Conversion optimization messages
export interface ConversionMessage {
  readonly feature: CoreFeatureType;
  readonly tier_gap: 'free_to_beginning' | 'beginning_to_pro' | 'pro_to_enterprise';
  readonly message_type: 'soft_prompt' | 'hard_block' | 'usage_warning' | 'benefit_highlight';
  readonly title: string;
  readonly description: string;
  readonly cta_text: string;
  readonly psychological_triggers: ('scarcity' | 'social_proof' | 'authority' | 'reciprocity' | 'commitment')[];
  readonly urgency_level: 'none' | 'low' | 'medium' | 'high';
  readonly personalization_tags: string[];
}

// Feature rollout and A/B testing
export interface FeatureFlag {
  readonly feature: CoreFeatureType;
  readonly enabled: boolean;
  readonly rollout_percentage: number; // 0-100
  readonly target_tiers: ('free' | 'beginning' | 'pro' | 'enterprise')[];
  readonly target_user_segments: string[];
  readonly ab_test_variant?: 'control' | 'variant_a' | 'variant_b';
  readonly rollout_start_date: string;
  readonly rollout_end_date?: string;
}

// Feature gate component props
export interface FeatureGateProps {
  feature: CoreFeatureType;
  fallback?: React.ReactNode;
  children: React.ReactNode;
  showUpgradePrompt?: boolean;
  softLimit?: boolean;
  onAccessDenied?: (feature: CoreFeatureType, reason: string) => void;
  onUpgradePromptShown?: (feature: CoreFeatureType) => void;
}