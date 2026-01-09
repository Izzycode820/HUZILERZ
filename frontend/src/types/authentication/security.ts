/**
 * User Security Types for Authentication Context
 * Complete alignment with backend SecurityEvent, SecurityAlert, ThreatIntelligence models
 */

// ============================================================================
// Personal Security Event Types
// ============================================================================

// Aligned with backend SecurityEvent model
export interface UserSecurityEvent {
  id: string;
  event_type: string; // Backend has many more types than just these 5
  description: string;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
  location_info?: {
    country?: string;
    city?: string;
    region?: string;
    timezone?: string;
  };
  device_info?: {
    device_name: string;
    browser: string;
    os: string;
    device_type: 'mobile' | 'tablet' | 'desktop';
  }; // From backend _extract_device_info
  risk_level: number; // 0-4 numeric levels matching backend
  metadata?: Record<string, unknown>; // Backend stores additional context
  is_processed: boolean; // Backend SecurityEvent.is_processed
  session_id?: string;
}

export interface UserSecurityEventsResponse {
  success: boolean;
  events?: UserSecurityEvent[];
  error?: string;
}

// ============================================================================
// Personal Security Alert Types
// ============================================================================

// Aligned with backend SecurityAlert model
export interface UserSecurityAlert {
  id: string;
  alert_type: string; // Backend uses alert_type field name
  title: string;
  description: string; // Backend uses description, not message
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'; // Backend uses uppercase
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED'; // Backend SecurityAlert.status
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  alert_data?: Record<string, unknown>; // Backend stores structured data
  related_events?: string[]; // IDs of related security events
}

export interface UserSecurityAlertsResponse {
  success: boolean;
  alerts?: UserSecurityAlert[];
  error?: string;
}

// ============================================================================
// Account Security Info Types
// ============================================================================

export interface AccountSecurityInfo {
  password_last_changed: string;
  login_attempts_count: number;
  last_failed_login?: string;
  security_score: number;
  active_sessions_count: number;
  mfa_enabled: boolean;
  backup_codes_remaining: number;
  recent_security_events: UserSecurityEvent[];
}

export interface AccountSecurityResponse {
  success: boolean;
  security_info?: AccountSecurityInfo;
  error?: string;
}

// ============================================================================
// Security Recommendations Types
// ============================================================================

export interface SecurityRecommendation {
  type: 'password_strength' | 'enable_mfa' | 'backup_codes' | 'password_age' | 'suspicious_activity';
  message: string;
  priority: 'low' | 'medium' | 'high';
  action: string;
  action_url?: string;
}

export interface SecurityRecommendationsResponse {
  success: boolean;
  recommendations?: SecurityRecommendation[];
  error?: string;
}

// ============================================================================
// Hook Return Types for User Security
// ============================================================================

export interface UseUserSecurityReturn {
  securityInfo: AccountSecurityInfo | null;
  securityEvents: UserSecurityEvent[];
  securityAlerts: UserSecurityAlert[];
  recommendations: SecurityRecommendation[];
  isLoading: boolean;
  error: string | null;
  refreshSecurity: () => Promise<void>;
  markEventRead: (eventId: string) => Promise<void>;
  markAlertRead: (alertId: string) => Promise<void>;
  dismissAlert: (alertId: string) => Promise<void>;
  clearError: () => void;
}

// ============================================================================
// Threat Intelligence Types (from Backend)
// ============================================================================

// Aligned with backend ThreatIntelligence model
export interface ThreatIntelligence {
  id: string;
  ioc_type: 'IP' | 'DOMAIN' | 'HASH' | 'URL';
  ioc_value: string;
  threat_type: string;
  confidence: number; // 0-100
  source: string;
  description: string;
  first_seen: string;
  last_seen: string;
  is_active: boolean;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Security Metrics Types (from Backend)
// ============================================================================

// Aligned with backend SecurityMetrics model
export interface SecurityMetrics {
  id: string;
  metric_type: string;
  aggregation_period: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  period_start: string;
  period_end: string;
  count: number;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Session Info Types (from Backend)
// ============================================================================

// Aligned with backend SessionInfo model
export interface SessionInfo {
  id: string;
  session_id: string;
  user_id: number;
  ip_address: string;
  user_agent: string;
  device_info?: {
    device_name: string;
    browser: string;
    os: string;
    device_type: 'mobile' | 'tablet' | 'desktop';
  };
  location_info?: {
    country?: string;
    city?: string;
    region?: string;
  };
  is_active: boolean;
  created_at: string;
  last_activity: string;
  expires_at: string;
}

// ============================================================================
// Constants for User Security
// ============================================================================

export const USER_SECURITY_EVENT_TYPES = {
  LOGIN_SUCCESS: 'login_success',
  LOGIN_FAILED: 'login_failed',
  MFA_VERIFICATION: 'mfa_verification',
  PASSWORD_CHANGE: 'password_change',
  SUSPICIOUS_LOGIN: 'suspicious_login',
} as const;

export const USER_SECURITY_ALERT_TYPES = {
  SUSPICIOUS_LOGIN: 'suspicious_login',
  NEW_DEVICE: 'new_device',
  PASSWORD_WEAK: 'password_weak',
  MFA_DISABLED: 'mfa_disabled',
  SECURITY_RECOMMENDATION: 'security_recommendation',
} as const;

// Aligned with backend SecurityMonitoringService.RISK_LEVELS
export const SECURITY_RISK_LEVELS = {
  NONE: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4,
} as const;

export const SECURITY_RECOMMENDATION_TYPES = {
  PASSWORD_STRENGTH: 'password_strength',
  ENABLE_MFA: 'enable_mfa',
  BACKUP_CODES: 'backup_codes',
  PASSWORD_AGE: 'password_age',
  SUSPICIOUS_ACTIVITY: 'suspicious_activity',
} as const;

export type UserSecurityEventType = typeof USER_SECURITY_EVENT_TYPES[keyof typeof USER_SECURITY_EVENT_TYPES];
export type UserSecurityAlertType = typeof USER_SECURITY_ALERT_TYPES[keyof typeof USER_SECURITY_ALERT_TYPES];
export type SecurityRiskLevel = typeof SECURITY_RISK_LEVELS[keyof typeof SECURITY_RISK_LEVELS];
export type SecurityRecommendationType = typeof SECURITY_RECOMMENDATION_TYPES[keyof typeof SECURITY_RECOMMENDATION_TYPES];