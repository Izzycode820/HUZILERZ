/**
 * Billing Domain Routes
 * All billing and subscription-related routes
 */

// Billing routes
export const BILLING_ROUTES = {
  ROOT: '/billing',
  SUBSCRIPTION: '/billing/subscription',
  INVOICES: '/billing/invoices',
  PAYMENT_METHODS: '/billing/payment-methods',
} as const