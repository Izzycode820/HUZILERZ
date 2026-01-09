// WebSocket types for real-time subscription and payment updates

// WebSocket message base structure
export interface WebSocketMessage<T = unknown> {
  readonly type: string;
  readonly data: T;
  readonly timestamp: string;
  readonly message_id: string;
  readonly user_id?: number;
}

// Payment status WebSocket messages
export interface PaymentStatusMessage extends WebSocketMessage<{
  readonly payment_id: string;
  readonly status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  readonly amount: number;
  readonly currency: 'FCFA';
  readonly phone_number_masked: string;
  readonly method_type: 'mtn_momo' | 'orange_money';
  readonly failure_reason?: string;
  readonly retry_available?: boolean;
  readonly next_retry_at?: string;
}> {
  readonly type: 'payment_status_update';
}

// Subscription status WebSocket messages
export interface SubscriptionStatusMessage extends WebSocketMessage<{
  readonly subscription_id: string;
  readonly status: 'active' | 'expired' | 'grace_period' | 'suspended' | 'cancelled';
  readonly plan_tier: 'free' | 'beginning' | 'pro' | 'enterprise';
  readonly expires_at?: string;
  readonly is_active: boolean;
  readonly days_until_expiry?: number;
  readonly grace_period_ends_at?: string;
  readonly auto_renew: boolean;
}> {
  readonly type: 'subscription_status_update' | 'subscription_renewed' | 'subscription_expired' | 'subscription_cancelled' | 'subscription_upgraded';
}

// Usage alert WebSocket messages
export interface UsageAlertMessage extends WebSocketMessage<{
  readonly resource_type: 'storage' | 'bandwidth' | 'sites' | 'custom_domains';
  readonly current_usage: number;
  readonly limit: number;
  readonly percentage_used: number;
  readonly alert_level: 'warning' | 'critical';
  readonly message: string;
  readonly suggested_action: string;
  readonly days_until_limit?: number;
}> {
  readonly type: 'usage_alert';
}

// Feature access WebSocket messages
export interface FeatureAccessMessage extends WebSocketMessage<{
  readonly feature: string;
  readonly access_granted: boolean;
  readonly reason?: string;
  readonly upgrade_required?: {
    readonly from_tier: string;
    readonly to_tier: string;
    readonly upgrade_url: string;
  };
}> {
  readonly type: 'feature_access_check';
}

// Real-time billing updates
export interface BillingUpdateMessage extends WebSocketMessage<{
  readonly invoice_id?: string;
  readonly amount_due: number;
  readonly due_date: string;
  readonly status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  readonly payment_method_required?: boolean;
  readonly auto_charge_failed?: boolean;
}> {
  readonly type: 'billing_update' | 'invoice_generated' | 'payment_due' | 'payment_overdue';
}

// Discount and promotion notifications
export interface PromotionMessage extends WebSocketMessage<{
  readonly promotion_id: string;
  readonly discount_code?: string;
  readonly title: string;
  readonly description: string;
  readonly discount_percentage?: number;
  readonly discount_amount?: number;
  readonly valid_until: string;
  readonly auto_apply: boolean;
  readonly target_tiers: string[];
  readonly urgency_level: 'low' | 'medium' | 'high';
}> {
  readonly type: 'promotion_available' | 'discount_applied' | 'promotion_expiring';
}

// System maintenance and downtime notifications
export interface SystemNotificationMessage extends WebSocketMessage<{
  readonly notification_type: 'maintenance' | 'downtime' | 'feature_release' | 'security_alert';
  readonly title: string;
  readonly description: string;
  readonly severity: 'info' | 'warning' | 'critical';
  readonly starts_at?: string;
  readonly ends_at?: string;
  readonly affected_features?: string[];
  readonly action_required?: boolean;
  readonly action_url?: string;
}> {
  readonly type: 'system_notification';
}

// WebSocket connection states
export type WebSocketConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';

// WebSocket client configuration
export interface WebSocketClientConfig {
  readonly url: string;
  readonly protocols?: string[];
  readonly reconnectInterval?: number; // milliseconds
  readonly maxReconnectAttempts?: number;
  readonly heartbeatInterval?: number; // milliseconds
  readonly authentication?: {
    readonly token: string;
    readonly tokenType: 'Bearer' | 'JWT';
  };
  readonly debug?: boolean;
}

// WebSocket event handlers
export interface WebSocketEventHandlers {
  onPaymentStatus?: (message: PaymentStatusMessage) => void;
  onSubscriptionStatus?: (message: SubscriptionStatusMessage) => void;
  onUsageAlert?: (message: UsageAlertMessage) => void;
  onFeatureAccess?: (message: FeatureAccessMessage) => void;
  onBillingUpdate?: (message: BillingUpdateMessage) => void;
  onPromotion?: (message: PromotionMessage) => void;
  onSystemNotification?: (message: SystemNotificationMessage) => void;
  onConnectionStateChange?: (state: WebSocketConnectionState, error?: Error) => void;
  onError?: (error: Error) => void;
}

// WebSocket client interface
export interface WebSocketClient {
  readonly connectionState: WebSocketConnectionState;
  readonly url: string;
  readonly isConnected: boolean;

  connect(): Promise<void>;
  disconnect(): void;
  reconnect(): Promise<void>;
  subscribe(channel: string): void;
  unsubscribe(channel: string): void;
  send(message: unknown): void;
  on<K extends keyof WebSocketEventHandlers>(event: K, handler: WebSocketEventHandlers[K]): void;
  off<K extends keyof WebSocketEventHandlers>(event: K, handler: WebSocketEventHandlers[K]): void;
  destroy(): void;
}

// Heartbeat message for connection health
export interface HeartbeatMessage extends WebSocketMessage<{
  readonly server_time: string;
  readonly connection_id: string;
  readonly latency_ms?: number;
}> {
  readonly type: 'heartbeat' | 'heartbeat_response';
}

// WebSocket error types
export interface WebSocketError {
  readonly code: number;
  readonly message: string;
  readonly timestamp: string;
  readonly connection_id?: string;
  readonly retry_after?: number; // seconds
}

// Channel subscription management
export interface ChannelSubscription {
  readonly channel: string;
  readonly subscribed_at: string;
  readonly last_message_at?: string;
  readonly message_count: number;
  readonly is_active: boolean;
}

// WebSocket metrics for monitoring
export interface WebSocketMetrics {
  readonly connection_uptime: number; // milliseconds
  readonly messages_sent: number;
  readonly messages_received: number;
  readonly reconnect_count: number;
  readonly average_latency: number; // milliseconds
  readonly last_heartbeat: string;
  readonly subscriptions: ChannelSubscription[];
}