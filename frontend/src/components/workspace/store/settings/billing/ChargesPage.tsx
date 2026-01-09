'use client';

import React, { useState } from 'react';
import { useQuery } from '@apollo/client/react';
import { useRouter } from 'next/navigation';
import { GetChargesDocument } from '@/services/graphql/subscription/queries/billing/__generated__/get-charges.generated';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table';
import { Skeleton } from '@/components/shadcn-ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import { ChevronLeft, ChevronRight, ChevronDown, ArrowLeft } from 'lucide-react';

export function ChargesPage() {
  const router = useRouter();
  const [currentPage, setCurrentPage] = useState(0);
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [chargeTypeFilter, setChargeTypeFilter] = useState<string>('all');
  const pageSize = 50;

  // Calculate date range based on filter
  const getDateRange = () => {
    if (dateFilter === 'all') return { dateFrom: undefined, dateTo: undefined };

    const now = new Date();
    const dateTo = now.toISOString();
    let dateFrom: string | undefined;

    switch (dateFilter) {
      case 'last_7_days':
        dateFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
        break;
      case 'last_30_days':
        dateFrom = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
        break;
      case 'last_90_days':
        dateFrom = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString();
        break;
      default:
        dateFrom = undefined;
    }

    return { dateFrom, dateTo };
  };

  const { dateFrom, dateTo } = getDateRange();

  // Query for charges
  const { data, loading } = useQuery(GetChargesDocument, {
    variables: {
      limit: pageSize,
      offset: currentPage * pageSize,
      chargeType: chargeTypeFilter === 'all' ? undefined : chargeTypeFilter,
      dateFrom,
      dateTo,
    },
  });

  const charges = data?.charges || [];

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatCurrency = (amount: string | number | null | undefined) => {
    if (amount === null || amount === undefined) return 'XAF 0.00';
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    return `XAF ${numAmount.toFixed(2)}`;
  };

  const getChargeTypeLabel = (chargeType: string) => {
    const chargeTypeMap: Record<string, string> = {
      SUBSCRIPTION: 'Subscription charges',
      SUBSCRIPTION_RENEWAL: 'Subscription renewal',
      SUBSCRIPTION_UPGRADE: 'Subscription upgrade',
      DOMAIN: 'Domain purchase',
      DOMAIN_RENEWAL: 'Domain renewal',
      THEME: 'Theme purchase',
      CHECKOUT: 'Checkout',
      ADDON: 'Add-on',
      OTHER: 'Other',
    };
    return chargeTypeMap[chargeType] || chargeType;
  };

  const dateFilterOptions = [
    { label: 'All time', value: 'all' },
    { label: 'Last 7 days', value: 'last_7_days' },
    { label: 'Last 30 days', value: 'last_30_days' },
    { label: 'Last 90 days', value: 'last_90_days' },
  ];

  const chargeTypeOptions = [
    { label: 'All types', value: 'all' },
    { label: 'Subscription charges', value: 'SUBSCRIPTION' },
    { label: 'Subscription renewal', value: 'SUBSCRIPTION_RENEWAL' },
    { label: 'Subscription upgrade', value: 'SUBSCRIPTION_UPGRADE' },
    { label: 'Domain purchase', value: 'DOMAIN' },
    { label: 'Domain renewal', value: 'DOMAIN_RENEWAL' },
    { label: 'Theme purchase', value: 'THEME' },
    { label: 'Checkout', value: 'CHECKOUT' },
    { label: 'Add-on', value: 'ADDON' },
    { label: 'Other', value: 'OTHER' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.back()}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl sm:text-3xl font-bold">Charges</h1>
        </div>
        <Button variant="default" className="bg-black hover:bg-black/90 text-white w-full sm:w-auto">
          Export
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-6 overflow-x-auto pb-2">
            {/* Date Filter */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2 whitespace-nowrap">
                  Date
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {dateFilterOptions.map((option) => (
                  <DropdownMenuItem
                    key={option.value}
                    onClick={() => {
                      setDateFilter(option.value);
                      setCurrentPage(0);
                    }}
                  >
                    {option.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Bill Number Filter - Placeholder for now */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2 whitespace-nowrap">
                  Bill number
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuItem>All bills</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Charge Type Filter */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2 whitespace-nowrap">
                  Charge type
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {chargeTypeOptions.map((option) => (
                  <DropdownMenuItem
                    key={option.value}
                    onClick={() => {
                      setChargeTypeFilter(option.value);
                      setCurrentPage(0);
                    }}
                  >
                    {option.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Table */}
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (
            <>
              <div className="overflow-x-auto -mx-4 sm:mx-0">
                <div className="min-w-[500px] px-4 sm:px-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="whitespace-nowrap">Bill number</TableHead>
                        <TableHead className="whitespace-nowrap">Date</TableHead>
                        <TableHead className="whitespace-nowrap">Charge type</TableHead>
                        <TableHead className="whitespace-nowrap">Source</TableHead>
                        <TableHead className="text-right whitespace-nowrap">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {charges.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                            No charges found
                          </TableCell>
                        </TableRow>
                      ) : (
                        charges.map((charge) => (
                          <TableRow key={charge?.reference}>
                            <TableCell className="font-medium whitespace-nowrap">#{charge?.reference}</TableCell>
                            <TableCell className="whitespace-nowrap">{charge?.createdAt ? formatDate(charge.createdAt) : '-'}</TableCell>
                            <TableCell className="whitespace-nowrap">{charge?.chargeType ? getChargeTypeLabel(charge.chargeType) : '-'}</TableCell>
                            <TableCell>-</TableCell>
                            <TableCell className="text-right whitespace-nowrap">
                              {formatCurrency(charge?.amount)}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Pagination */}
              {charges.length >= pageSize && (
                <div className="flex items-center justify-center gap-2 pt-4">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                    disabled={currentPage === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setCurrentPage((p) => p + 1)}
                    disabled={charges.length < pageSize}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
