"use client";

import React, { useState } from 'react';
import { Download, Eye, Calendar, CreditCard, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Badge } from '@/components/shadcn-ui/badge';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/shadcn-ui/table';
import { cn } from '@/lib/utils';
import { useBilling } from '@/hooks/subscription';
import type { BillingHistoryEntry } from '@/types/subscription';

interface InvoiceListProps {
  onDownloadInvoice?: (invoiceId: string) => void;
  onViewInvoice?: (invoiceId: string) => void;
  className?: string;
  limit?: number;
}

/**
 * Invoice List Component
 * Displays user's billing history with download and view options
 */
export function InvoiceList({
  onDownloadInvoice,
  onViewInvoice,
  className,
  limit
}: InvoiceListProps) {
  const { billingHistory, loading, error, refreshBillingData } = useBilling();
  const [processingInvoice, setProcessingInvoice] = useState<string | null>(null);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('fr-CM', {
      style: 'currency',
      currency: 'XAF',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'paid':
        return 'default';
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'refunded':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const handleDownload = async (invoiceId: string) => {
    if (processingInvoice) return;
    
    try {
      setProcessingInvoice(invoiceId);
      await onDownloadInvoice?.(invoiceId);
    } finally {
      setProcessingInvoice(null);
    }
  };

  const handleView = (invoiceId: string) => {
    onViewInvoice?.(invoiceId);
  };

  const displayInvoices = limit ? billingHistory.slice(0, limit) : billingHistory;

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
          <Button variant="outline" onClick={refreshBillingData} className="mt-4">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="w-5 h-5" />
          Billing History
        </CardTitle>
        <CardDescription>
          View and download your invoices and payment history
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {displayInvoices.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-2">No invoices found</p>
            <p className="text-sm text-muted-foreground">
              Your billing history will appear here once you have active subscriptions
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Desktop table view */}
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayInvoices.map((invoice: BillingHistoryEntry) => (
                    <TableRow key={invoice.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">#{invoice.id}</div>
                          <div className="text-sm text-muted-foreground">
                            Subscription payment
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <div className="text-sm">
                          <div>{formatDate(invoice.created_at)}</div>
                          <div className="text-muted-foreground">
                            Created: {formatDate(invoice.created_at)}
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <div className="font-medium">
                          {formatCurrency(invoice.amount)}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(invoice.status)}>
                          {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                        </Badge>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleView(invoice.id)}
                            disabled={!!processingInvoice}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          
                          {invoice.status === 'completed' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDownload(invoice.id)}
                              disabled={processingInvoice === invoice.id}
                            >
                              {processingInvoice === invoice.id ? (
                                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                              ) : (
                                <Download className="w-4 h-4" />
                              )}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Mobile card view */}
            <div className="md:hidden space-y-4">
              {displayInvoices.map((invoice) => (
                <Card key={invoice.id} className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-medium">#{invoice.id}</div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(invoice.created_at)}
                      </div>
                    </div>
                    <Badge variant={getStatusBadgeVariant(invoice.status)}>
                      {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-muted-foreground">Amount:</span>
                    <span className="font-medium">{formatCurrency(invoice.amount)}</span>
                  </div>
                  
                  
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleView(invoice.id)}
                      className="flex-1"
                      disabled={!!processingInvoice}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View
                    </Button>
                    
                    {invoice.status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(invoice.id)}
                        disabled={processingInvoice === invoice.id}
                      >
                        {processingInvoice === invoice.id ? (
                          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>

            {/* Load more button */}
            {limit && billingHistory.length > limit && (
              <div className="text-center pt-4">
                <Button variant="outline" onClick={() => window.location.href = '/billing'}>
                  View All Invoices
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}