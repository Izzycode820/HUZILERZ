'use client';

import React from 'react';
import { Button } from '@/components/shadcn-ui/button';
import { Card } from '@/components/shadcn-ui/card';
import { Ban, RotateCcw, Trash2 } from 'lucide-react';

interface StaffToolbarProps {
  selectedCount: number;
  onSuspend: () => void;
  onReactivate: () => void;
  onRemove: () => void;
}

export function StaffToolbar({
  selectedCount,
  onSuspend,
  onReactivate,
  onRemove,
}: StaffToolbarProps) {
  if (selectedCount === 0) return null;

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium">
          {selectedCount} {selectedCount === 1 ? 'staff member' : 'staff members'} selected
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onSuspend}
          >
            <Ban className="h-4 w-4 mr-2" />
            Suspend
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onReactivate}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reactivate
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={onRemove}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Remove
          </Button>
        </div>
      </div>
    </Card>
  );
}
