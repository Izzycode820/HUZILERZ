import { z } from 'zod';

/**
 * Invoice System Types
 * Comprehensive invoicing with Cameroon tax compliance following 4 principles
 */

// Core invoice structure
export interface Invoice {
  readonly id: string;
  readonly invoice_number: string;
  readonly user_id: string;
  readonly subscription_id: string;
  readonly billing_period_start: string;
  readonly billing_period_end: string;
  readonly issue_date: string;
  readonly due_date: string;
  readonly payment_date?: string;
  readonly status: InvoiceStatusType;
  readonly currency: 'FCFA' | 'USD';
  readonly subtotal: number;
  readonly tax_amount: number;
  readonly tax_rate: number; // Maintainability: configurable tax rates
  readonly total_amount: number;
  readonly amount_paid: number;
  readonly amount_due: number;
  readonly line_items: InvoiceLineItem[];
  readonly payment_terms: string;
  readonly notes?: string;
  readonly billing_address: BillingAddress;
  readonly tax_details: CameroonTaxDetails;
  readonly pdf_url?: string;
  readonly created_at: string;
  readonly updated_at: string;
}

// Invoice status management
export const InvoiceStatus = {
  DRAFT: 'draft',
  PENDING: 'pending',
  SENT: 'sent',
  PAID: 'paid',
  OVERDUE: 'overdue',
  CANCELLED: 'cancelled',
  REFUNDED: 'refunded',
} as const;

export type InvoiceStatusType = typeof InvoiceStatus[keyof typeof InvoiceStatus];

// Invoice line items for detailed billing
export interface InvoiceLineItem {
  readonly id: string;
  readonly description: string;
  readonly item_type: 'subscription' | 'overage' | 'addon' | 'discount' | 'tax';
  readonly quantity: number;
  readonly unit_price: number;
  readonly line_total: number;
  readonly tax_rate: number;
  readonly tax_amount: number;
  readonly period_start?: string;
  readonly period_end?: string;
  readonly metadata: Record<string, unknown>;
}

// Cameroon-specific tax compliance
export interface CameroonTaxDetails {
  readonly tax_id?: string; // Business tax ID
  readonly vat_rate: number; // 19.25% standard rate
  readonly vat_amount: number;
  readonly tax_exempt: boolean;
  readonly exemption_reason?: string;
  readonly municipality: string;
  readonly region: string;
  readonly tax_period: string; // YYYY-MM format
  readonly compliance_status: 'compliant' | 'pending' | 'non_compliant';
}

// Billing address with Cameroon specifics
export interface BillingAddress {
  readonly company_name?: string;
  readonly contact_name: string;
  readonly email: string;
  readonly phone: string;
  readonly address_line_1: string;
  readonly address_line_2?: string;
  readonly city: string;
  readonly region: CameroonRegionType;
  readonly postal_code?: string;
  readonly country: 'CM'; // Security: enforce Cameroon
}

// Cameroon regions for tax compliance
export const CameroonRegion = {
  CENTRE: 'centre',
  LITTORAL: 'littoral',
  OUEST: 'ouest',
  NORD_OUEST: 'nord_ouest',
  SUD_OUEST: 'sud_ouest',
  ADAMAWA: 'adamawa',
  EST: 'est',
  EXTREME_NORD: 'extreme_nord',
  NORD: 'nord',
  SUD: 'sud',
} as const;

export type CameroonRegionType = typeof CameroonRegion[keyof typeof CameroonRegion];

// Payment allocation tracking
export interface PaymentAllocation {
  readonly id: string;
  readonly invoice_id: string;
  readonly payment_id: string;
  readonly amount_allocated: number;
  readonly allocation_date: string;
  readonly allocation_type: 'full' | 'partial' | 'overpayment';
  readonly notes?: string;
}

// Invoice generation request
export const InvoiceGenerationSchema = z.object({
  subscription_id: z.string().uuid(),
  billing_period_start: z.string().datetime(),
  billing_period_end: z.string().datetime(),
  include_usage_charges: z.boolean().default(true),
  include_overages: z.boolean().default(true),
  custom_line_items: z.array(z.object({
    description: z.string(),
    quantity: z.number().positive(),
    unit_price: z.number(),
    tax_rate: z.number().min(0).max(1),
  })).optional(),
});

export interface InvoiceGenerationRequest {
  readonly subscription_id: string;
  readonly billing_period_start: string;
  readonly billing_period_end: string;
  readonly include_usage_charges?: boolean;
  readonly include_overages?: boolean;
  readonly custom_line_items?: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    tax_rate: number;
  }>;
}

export interface InvoiceGenerationResponse {
  readonly invoice_id: string;
  readonly invoice_number: string;
  readonly total_amount: number;
  readonly due_date: string;
  readonly pdf_url?: string;
  readonly payment_instructions: PaymentInstructions;
}

// Payment instructions for Cameroon market
export interface PaymentInstructions {
  readonly payment_methods: Array<{
    method: 'mtn_momo' | 'orange_money' | 'fapshi' | 'bank_transfer';
    instructions: string;
    reference: string;
  }>;
  readonly payment_deadline: string;
  readonly late_fee_policy: string;
  readonly grace_period_days: number;
}

// Bulk invoice operations for scalability
export interface BulkInvoiceOperationRequest {
  readonly operation: 'generate' | 'send' | 'mark_paid' | 'cancel';
  readonly filters: InvoiceFilterCriteria;
  readonly parameters?: Record<string, unknown>;
}

export interface InvoiceFilterCriteria {
  readonly subscription_ids?: string[];
  readonly status?: InvoiceStatusType[];
  readonly date_range?: {
    start: string;
    end: string;
  };
  readonly amount_range?: {
    min: number;
    max: number;
  };
  readonly region?: CameroonRegionType;
}

export interface BulkInvoiceOperationResponse {
  readonly operation: string;
  readonly successful: string[];
  readonly failed: Array<{
    invoice_id: string;
    error: string;
    error_code: string;
  }>;
  readonly total_processed: number;
  readonly total_amount?: number;
}

// Invoice analytics and reporting
export interface InvoiceAnalytics {
  readonly period_start: string;
  readonly period_end: string;
  readonly total_invoices: number;
  readonly total_revenue: number;
  readonly average_invoice_value: number;
  readonly collection_rate: number;
  readonly overdue_rate: number;
  readonly regional_breakdown: Record<CameroonRegionType, {
    count: number;
    revenue: number;
  }>;
  readonly payment_method_breakdown: Record<string, {
    count: number;
    revenue: number;
    average_days_to_pay: number;
  }>;
  readonly tax_summary: {
    total_vat_collected: number;
    tax_exempt_amount: number;
    compliance_rate: number;
  };
}

// Automated invoice scheduling
export interface InvoiceSchedule {
  readonly id: string;
  readonly subscription_id: string;
  readonly frequency: 'monthly' | 'quarterly' | 'annually';
  readonly start_date: string;
  readonly end_date?: string;
  readonly next_invoice_date: string;
  readonly auto_send: boolean;
  readonly payment_terms_days: number;
  readonly include_usage: boolean;
  readonly template_id?: string;
  readonly is_active: boolean;
  readonly created_at: string;
}

// Invoice templates for consistency
export interface InvoiceTemplate {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly template_type: 'standard' | 'premium' | 'enterprise';
  readonly layout_config: InvoiceLayoutConfig;
  readonly default_payment_terms: string;
  readonly default_notes: string;
  readonly branding: InvoiceBranding;
  readonly is_default: boolean;
  readonly created_at: string;
}

export interface InvoiceLayoutConfig {
  readonly header_style: string;
  readonly color_scheme: string;
  readonly logo_position: 'left' | 'center' | 'right';
  readonly show_payment_qr: boolean;
  readonly language: 'en' | 'fr'; // Maintainability: multilingual support
  readonly currency_display: 'symbol' | 'code' | 'both';
}

export interface InvoiceBranding {
  readonly company_logo_url?: string;
  readonly company_name: string;
  readonly company_address: BillingAddress;
  readonly contact_info: string;
  readonly website_url?: string;
  readonly tax_registration_number?: string;
}

// Credit notes and refunds
export interface CreditNote {
  readonly id: string;
  readonly credit_note_number: string;
  readonly original_invoice_id: string;
  readonly user_id: string;
  readonly reason: 'refund' | 'correction' | 'discount' | 'goodwill';
  readonly amount: number;
  readonly issue_date: string;
  readonly status: 'draft' | 'issued' | 'applied';
  readonly line_items: InvoiceLineItem[];
  readonly notes?: string;
  readonly created_at: string;
}

// Real-time invoice events
export interface InvoiceEventMessage {
  readonly type: 'invoice_generated' | 'invoice_paid' | 'invoice_overdue' | 'credit_note_issued';
  readonly invoice_id: string;
  readonly user_id: string;
  readonly amount?: number;
  readonly data: Record<string, unknown>;
  readonly timestamp: string;
}

// Security: Invoice access control
export interface InvoiceAccessLog {
  readonly id: string;
  readonly invoice_id: string;
  readonly accessed_by: string;
  readonly access_type: 'view' | 'download' | 'share' | 'modify';
  readonly ip_address: string;
  readonly user_agent: string;
  readonly accessed_at: string;
}