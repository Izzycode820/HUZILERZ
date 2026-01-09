'use client';

import { Tabs, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';
import { Input } from '@/components/shadcn-ui/input';
import { Search } from 'lucide-react';

interface DiscountsFiltersProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  statusFilter: string | undefined;
  onStatusFilterChange: (status: string | undefined) => void;
}

export function DiscountsFilters({
  searchValue,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
}: DiscountsFiltersProps) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      {/* Tabs for status filtering */}
      <Tabs
        value={statusFilter || 'all'}
        onValueChange={(value) => onStatusFilterChange(value === 'all' ? undefined : value)}
      >
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
          <TabsTrigger value="expired">Expired</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Search */}
      <div className="relative w-full md:w-auto md:min-w-[300px]">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search discounts..."
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>
    </div>
  );
}
