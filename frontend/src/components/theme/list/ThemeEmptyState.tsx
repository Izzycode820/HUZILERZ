'use client';

import React from 'react';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Search } from 'lucide-react';

interface ThemeEmptyStateProps {
  hasFilters: boolean;
  onClearFilters?: () => void;
}

export function ThemeEmptyState({ hasFilters, onClearFilters }: ThemeEmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16 px-4">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>

        <h3 className="text-lg font-semibold mb-2">No themes found</h3>

        <p className="text-muted-foreground text-center mb-6 max-w-md">
          {hasFilters
            ? 'No themes match your current filters. Try adjusting your search criteria.'
            : 'No themes are currently available. Check back soon!'}
        </p>

        {hasFilters && onClearFilters && (
          <Button onClick={onClearFilters} variant="outline">
            Clear all filters
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
