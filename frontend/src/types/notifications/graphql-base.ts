export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export interface Scalars {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  DateTime: { input: string; output: string; }
  JSONString: { input: any; output: any; }
}

/**
 * Mark all notifications as read.
 *
 * Modes:
 * - No workspace_id: Mark only user-level notifications (workspace IS NULL)
 * - With workspace_id: Mark user-level + specific workspace notifications
 *
 * Performance: Single bulk UPDATE query.
 * Access: User-level (no workspace required)
 */
export interface MarkAllNotificationsAsRead {
  __typename?: 'MarkAllNotificationsAsRead';
  /** Number of notifications marked as read */
  count?: Maybe<Scalars['Int']['output']>;
  /** Whether operation succeeded */
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Mark a single notification as read.
 *
 * Security: Only the recipient can mark their notification as read.
 * Reliability: Uses select_for_update to prevent race conditions.
 *
 * Access: User-level (no workspace required)
 */
export interface MarkNotificationAsRead {
  __typename?: 'MarkNotificationAsRead';
  /** Updated notification */
  notification?: Maybe<NotificationType>;
  /** Whether operation succeeded */
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Notification mutations
 *
 * User-level mutations (auth required):
 * - markNotificationAsRead: Mark single notification as read
 * - markAllNotificationsAsRead: Bulk mark as read
 */
export interface Mutation {
  __typename?: 'Mutation';
  /**
   * Mark all notifications as read.
   *
   * Modes:
   * - No workspace_id: Mark only user-level notifications (workspace IS NULL)
   * - With workspace_id: Mark user-level + specific workspace notifications
   *
   * Performance: Single bulk UPDATE query.
   * Access: User-level (no workspace required)
   */
  markAllNotificationsAsRead?: Maybe<MarkAllNotificationsAsRead>;
  /**
   * Mark a single notification as read.
   *
   * Security: Only the recipient can mark their notification as read.
   * Reliability: Uses select_for_update to prevent race conditions.
   *
   * Access: User-level (no workspace required)
   */
  markNotificationAsRead?: Maybe<MarkNotificationAsRead>;
}


/**
 * Notification mutations
 *
 * User-level mutations (auth required):
 * - markNotificationAsRead: Mark single notification as read
 * - markAllNotificationsAsRead: Bulk mark as read
 */
export interface MutationMarkAllNotificationsAsReadArgs {
  workspaceId?: InputMaybe<Scalars['ID']['input']>;
  workspaceOnly?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Notification mutations
 *
 * User-level mutations (auth required):
 * - markNotificationAsRead: Mark single notification as read
 * - markAllNotificationsAsRead: Bulk mark as read
 */
export interface MutationMarkNotificationAsReadArgs {
  notificationId: Scalars['ID']['input'];
}

/** An object with an ID */
export interface Node {
  /** The ID of the object */
  id: Scalars['ID']['output'];
}

/**
 * GraphQL type for Notification model
 *
 * Features:
 * - All notification fields with proper typing
 * - Workspace relationship for store-level notifications
 * - Read status tracking
 *
 * Security: Only exposed to authenticated recipient
 */
export interface NotificationType extends Node {
  __typename?: 'NotificationType';
  /** Notification body text */
  body: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Event payload (order_id, subscription_id, etc.) */
  data: Scalars['JSONString']['output'];
  id: Scalars['ID']['output'];
  /** Whether notification has been read */
  isRead?: Maybe<Scalars['Boolean']['output']>;
  /** Notification category for filtering */
  notificationType: NotificationsNotificationNotificationTypeChoices;
  /** Human-readable notification type */
  notificationTypeDisplay?: Maybe<Scalars['String']['output']>;
  /** When notification was read, null if unread */
  readAt?: Maybe<Scalars['DateTime']['output']>;
  /** Short notification title */
  title: Scalars['String']['output'];
  /** Workspace name for store-level notifications */
  workspaceName?: Maybe<Scalars['String']['output']>;
}

/**
 * GraphQL enum for notification types.
 * Mirrors NotificationType model choices.
 */
export enum NotificationTypeEnum {
  OrderCancelled = 'ORDER_CANCELLED',
  OrderCreated = 'ORDER_CREATED',
  OrderPaid = 'ORDER_PAID',
  OrderStatusChanged = 'ORDER_STATUS_CHANGED',
  PaymentFailed = 'PAYMENT_FAILED',
  StockLow = 'STOCK_LOW',
  StockOut = 'STOCK_OUT',
  SubscriptionActivated = 'SUBSCRIPTION_ACTIVATED',
  SubscriptionExpired = 'SUBSCRIPTION_EXPIRED'
}

/** An enumeration. */
export enum NotificationsNotificationNotificationTypeChoices {
  /** Order Cancelled */
  OrderCancelled = 'ORDER_CANCELLED',
  /** New Order */
  OrderCreated = 'ORDER_CREATED',
  /** Order Paid */
  OrderPaid = 'ORDER_PAID',
  /** Order Status Changed */
  OrderStatusChanged = 'ORDER_STATUS_CHANGED',
  /** Payment Failed */
  PaymentFailed = 'PAYMENT_FAILED',
  /** Low Stock */
  StockLow = 'STOCK_LOW',
  /** Out of Stock */
  StockOut = 'STOCK_OUT',
  /** Subscription Activated */
  SubscriptionActivated = 'SUBSCRIPTION_ACTIVATED',
  /** Subscription Expired */
  SubscriptionExpired = 'SUBSCRIPTION_EXPIRED'
}

/**
 * Combined notification queries
 *
 * User-level queries (auth only, no workspace):
 * - myNotifications: All user's notifications
 * - unreadNotificationCount: Total unread count
 * - notification: Single notification by ID
 *
 * Workspace-scoped queries (auth + workspace header):
 * - workspaceNotifications: Current workspace + user-level notifications
 * - workspaceUnreadCount: Unread count for current workspace
 */
export interface Query {
  __typename?: 'Query';
  /** Get all notifications for authenticated user (user-level + all workspaces) */
  myNotifications?: Maybe<Array<Maybe<NotificationType>>>;
  /** Get single notification by ID */
  notification?: Maybe<NotificationType>;
  /** Get total unread notification count for user */
  unreadNotificationCount?: Maybe<Scalars['Int']['output']>;
  /** Get notifications for current workspace + user-level notifications */
  workspaceNotifications?: Maybe<Array<Maybe<NotificationType>>>;
  /** Get unread count for current workspace + user-level */
  workspaceUnreadCount?: Maybe<Scalars['Int']['output']>;
}


/**
 * Combined notification queries
 *
 * User-level queries (auth only, no workspace):
 * - myNotifications: All user's notifications
 * - unreadNotificationCount: Total unread count
 * - notification: Single notification by ID
 *
 * Workspace-scoped queries (auth + workspace header):
 * - workspaceNotifications: Current workspace + user-level notifications
 * - workspaceUnreadCount: Unread count for current workspace
 */
export interface QueryMyNotificationsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
  notificationType?: InputMaybe<NotificationTypeEnum>;
  unreadOnly?: InputMaybe<Scalars['Boolean']['input']>;
}


/**
 * Combined notification queries
 *
 * User-level queries (auth only, no workspace):
 * - myNotifications: All user's notifications
 * - unreadNotificationCount: Total unread count
 * - notification: Single notification by ID
 *
 * Workspace-scoped queries (auth + workspace header):
 * - workspaceNotifications: Current workspace + user-level notifications
 * - workspaceUnreadCount: Unread count for current workspace
 */
export interface QueryNotificationArgs {
  id: Scalars['ID']['input'];
}


/**
 * Combined notification queries
 *
 * User-level queries (auth only, no workspace):
 * - myNotifications: All user's notifications
 * - unreadNotificationCount: Total unread count
 * - notification: Single notification by ID
 *
 * Workspace-scoped queries (auth + workspace header):
 * - workspaceNotifications: Current workspace + user-level notifications
 * - workspaceUnreadCount: Unread count for current workspace
 */
export interface QueryWorkspaceNotificationsArgs {
  limit?: InputMaybe<Scalars['Int']['input']>;
  notificationType?: InputMaybe<NotificationTypeEnum>;
  unreadOnly?: InputMaybe<Scalars['Boolean']['input']>;
}
