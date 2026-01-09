// Usage analytics and resource monitoring types matching Django backend

export const RESOURCE_TYPES = {
  WORKSPACES: 'workspaces',
  SITES: 'sites',
  STORAGE: 'storage',
  BANDWIDTH: 'bandwidth',
  CUSTOM_DOMAINS: 'custom_domains',
  TEAM_MEMBERS: 'team_members',
  API_CALLS: 'api_calls',
  DEPLOYMENTS: 'deployments',
} as const;

export type ResourceTypeType = typeof RESOURCE_TYPES[keyof typeof RESOURCE_TYPES];

// Individual resource usage record
export interface UsageRecord {
  readonly resource_type: ResourceTypeType;
  readonly current_usage: number;
  readonly limit: number;
  readonly percentage_used: number;
  readonly period_start: string;
  readonly period_end: string;
  readonly unit: string; // 'count', 'GB', 'MB', 'requests', etc.
  readonly usage_trend: 'increasing' | 'decreasing' | 'stable';
  readonly projected_usage_end_of_period?: number;
  readonly days_until_limit?: number;
}

// Comprehensive usage analytics
export interface UsageAnalytics {
  readonly user_id: number;
  readonly subscription_tier: 'free' | 'beginning' | 'pro' | 'enterprise';
  readonly billing_period: 'monthly' | 'quarterly' | 'annually';
  readonly period_start: string;
  readonly period_end: string;
  readonly usage_records: Record<ResourceTypeType, UsageRecord>;
  readonly total_usage_score: number; // 0-100 representing overall usage intensity
  readonly efficiency_score: number; // How well user utilizes their limits
  readonly upgrade_recommendation?: {
    readonly recommended_tier: 'beginning' | 'pro' | 'enterprise';
    readonly reason: string;
    readonly potential_savings: number;
    readonly urgency: 'low' | 'medium' | 'high';
  };
}

// Usage limit configuration
export interface UsageLimit {
  readonly resource_type: ResourceTypeType;
  readonly tier: 'free' | 'beginning' | 'pro' | 'enterprise';
  readonly soft_limit: number;
  readonly hard_limit: number;
  readonly unit: string;
  readonly reset_period: 'daily' | 'weekly' | 'monthly' | 'never';
  readonly overage_allowed: boolean;
  readonly overage_price_per_unit?: number; // FCFA
  readonly grace_period_days?: number;
}

// Usage alert configuration
export interface UsageAlert {
  readonly id: string;
  readonly resource_type: ResourceTypeType;
  readonly alert_type: 'warning' | 'critical' | 'limit_reached' | 'overage';
  readonly threshold_percentage: number; // 75%, 90%, 100%, etc.
  readonly message: string;
  readonly action_required: boolean;
  readonly auto_upgrade_suggested: boolean;
  readonly created_at: string;
  readonly acknowledged: boolean;
  readonly acknowledged_at?: string;
}

// Historical usage data for trends
export interface UsageHistory {
  readonly resource_type: ResourceTypeType;
  readonly data_points: Array<{
    readonly date: string;
    readonly usage: number;
    readonly limit: number;
    readonly percentage_used: number;
  }>;
  readonly period_type: 'daily' | 'weekly' | 'monthly';
  readonly trend_analysis: {
    readonly direction: 'up' | 'down' | 'stable';
    readonly growth_rate: number; // percentage per period
    readonly seasonality_detected: boolean;
    readonly predicted_next_period: number;
  };
}

// Batch usage analytics request
export interface BatchUsageAnalyticsRequest {
  readonly resource_types?: ResourceTypeType[];
  readonly period_start?: string;
  readonly period_end?: string;
  readonly include_history?: boolean;
  readonly include_predictions?: boolean;
  readonly include_alerts?: boolean;
}

// Batch usage analytics response
export interface BatchUsageAnalyticsResponse {
  readonly usage_analytics: Record<string, UsageRecord>;
  readonly summary: {
    readonly total_storage_used: number;
    readonly total_bandwidth_used: number;
    readonly total_sites: number;
    readonly total_custom_domains: number;
    readonly period_start: string;
    readonly period_end: string;
    readonly overall_usage_health: 'excellent' | 'good' | 'warning' | 'critical';
  };
  readonly alerts?: Array<{
    readonly resource_type: string;
    readonly current_usage: number;
    readonly limit: number;
    readonly percentage_used: number;
    readonly alert_level: 'warning' | 'critical';
    readonly message: string;
    readonly days_until_limit?: number;
    readonly suggested_action: string;
  }>;
  readonly recommendations?: Array<{
    readonly type: 'upgrade' | 'optimize' | 'cleanup';
    readonly priority: 'low' | 'medium' | 'high';
    readonly resource_affected: ResourceTypeType;
    readonly description: string;
    readonly estimated_impact: string;
    readonly action_url?: string;
  }>;
}

// Resource optimization suggestions
export interface OptimizationSuggestion {
  readonly resource_type: ResourceTypeType;
  readonly current_usage: number;
  readonly optimization_type: 'compression' | 'cleanup' | 'archival' | 'upgrade' | 'downgrade';
  readonly potential_savings: {
    readonly amount: number;
    readonly unit: string;
    readonly cost_impact?: number; // FCFA
  };
  readonly effort_required: 'low' | 'medium' | 'high';
  readonly implementation_steps: string[];
  readonly estimated_time_to_complete: number; // minutes
}

// Usage-based billing calculation
export interface UsageBasedBilling {
  readonly base_subscription_cost: number;
  readonly overage_charges: Array<{
    readonly resource_type: ResourceTypeType;
    readonly units_over_limit: number;
    readonly price_per_unit: number;
    readonly total_charge: number;
  }>;
  readonly total_overage_cost: number;
  readonly total_bill_amount: number;
  readonly billing_period: string;
  readonly next_billing_date: string;
}

// Real-time usage monitoring
export interface RealTimeUsage {
  readonly resource_type: ResourceTypeType;
  readonly current_usage: number;
  readonly rate_per_hour: number;
  readonly projected_end_of_day: number;
  readonly projected_end_of_period: number;
  readonly last_updated: string;
  readonly status: 'normal' | 'approaching_limit' | 'over_limit';
}

// Usage analytics export
export interface UsageExport {
  readonly export_id: string;
  readonly user_id: number;
  readonly export_type: 'csv' | 'json' | 'pdf_report';
  readonly period_start: string;
  readonly period_end: string;
  readonly resource_types: ResourceTypeType[];
  readonly status: 'pending' | 'processing' | 'completed' | 'failed';
  readonly download_url?: string;
  readonly expires_at?: string;
  readonly created_at: string;
}

// Enhanced alert system matching backend AlertService
export interface UsageAlertConfig {
  readonly id: string;
  readonly user_id: string;
  readonly resource_type: ResourceTypeType;
  readonly alert_level: UsageAlertLevelType;
  readonly threshold_type: 'percentage' | 'absolute';
  readonly threshold_value: number;
  readonly notification_channels: AlertNotificationChannelType[];
  readonly is_active: boolean;
  readonly created_at: string;
  readonly last_triggered_at?: string;
}

export const UsageAlertLevel = {
  WARNING: 'warning',
  CRITICAL: 'critical',
  EMERGENCY: 'emergency',
} as const;

export type UsageAlertLevelType = typeof UsageAlertLevel[keyof typeof UsageAlertLevel];

export const AlertNotificationChannel = {
  EMAIL: 'email',
  SMS: 'sms',
  IN_APP: 'in_app',
  WEBHOOK: 'webhook',
} as const;

export type AlertNotificationChannelType = typeof AlertNotificationChannel[keyof typeof AlertNotificationChannel];

// Alert instance from backend
export interface UsageAlertInstance {
  readonly id: string;
  readonly alert_config_id: string;
  readonly user_id: string;
  readonly resource_type: ResourceTypeType;
  readonly alert_level: UsageAlertLevelType;
  readonly current_usage: number;
  readonly threshold_value: number;
  readonly threshold_type: 'percentage' | 'absolute';
  readonly message: string;
  readonly metadata: Record<string, unknown>;
  readonly status: 'active' | 'acknowledged' | 'resolved' | 'auto_resolved';
  readonly created_at: string;
  readonly acknowledged_at?: string;
  readonly resolved_at?: string;
  readonly auto_resolve_reason?: string;
}

// Real-time monitoring events matching backend
export interface UsageMonitoringEvent {
  readonly event_type: 'threshold_exceeded' | 'limit_reached' | 'usage_spike' | 'unusual_pattern';
  readonly resource_type: ResourceTypeType;
  readonly user_id: string;
  readonly current_usage: number;
  readonly previous_usage: number;
  readonly limit: number;
  readonly severity: 'info' | 'warning' | 'critical' | 'emergency';
  readonly context: Record<string, unknown>;
  readonly timestamp: string;
  readonly requires_action: boolean;
}

// System health monitoring matching backend MonitoringService
export interface UsageSystemHealth {
  readonly overall_status: 'healthy' | 'degraded' | 'critical';
  readonly resource_health: Record<ResourceTypeType, {
    status: 'healthy' | 'warning' | 'critical';
    active_alerts: number;
    average_usage_percentage: number;
    trend: 'stable' | 'increasing' | 'decreasing';
  }>;
  readonly alert_summary: {
    total_active: number;
    by_level: Record<UsageAlertLevelType, number>;
    escalated: number;
    auto_resolved: number;
  };
  readonly performance_metrics: {
    response_time_ms: number;
    throughput_per_second: number;
    error_rate: number;
    uptime_percentage: number;
  };
  readonly last_updated: string;
}