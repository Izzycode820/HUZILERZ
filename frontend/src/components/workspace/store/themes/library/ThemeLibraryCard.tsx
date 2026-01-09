'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import { MoreHorizontal, Package, Edit2, Eye, Copy, Trash2, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';

interface ThemeLibraryCardProps {
  id: string;
  themeName: string;
  previewImage: string;
  version: string;
  createdAt: string;
  isPublished: boolean | null;
  canDelete: boolean | null;
  isPublishing?: boolean;
  isDuplicating?: boolean;
  onEditTheme: () => void;
  onPublish?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onRename?: () => void;
}

export function ThemeLibraryCard({
  id,
  themeName,
  previewImage,
  version,
  createdAt,
  isPublished,
  canDelete,
  isPublishing = false,
  isDuplicating = false,
  onEditTheme,
  onPublish,
  onDelete,
  onDuplicate,
  onRename,
}: ThemeLibraryCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4 sm:p-5">
        {/* Main container - stack on mobile, row on desktop */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 sm:items-start">
          {/* Preview Image */}
          <div className="flex-shrink-0">
            <div className="relative w-full sm:w-28 h-32 sm:h-20 rounded-md overflow-hidden border border-border bg-muted/30">
              {previewImage ? (
                <Image
                  src={previewImage}
                  alt={themeName}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="w-full h-full bg-muted/30 flex items-center justify-center">
                  <Package className="w-8 h-8 text-muted-foreground/30" />
                </div>
              )}
            </div>
          </div>

          {/* Theme Info */}
          <div className="flex-1 min-w-0">
            <h4 className="text-base font-semibold mb-1.5 truncate">
              {themeName}
            </h4>
            <div className="space-y-0.5">
              <p className="text-sm text-muted-foreground">
                Added: {formatDate(createdAt)}
              </p>
              <div className="flex items-center gap-1">
                <p className="text-sm text-muted-foreground">
                  Version {version}
                </p>
                <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
              </div>
            </div>
          </div>

          {/* Actions - full width on mobile, auto on desktop */}
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end sm:justify-start flex-wrap sm:flex-nowrap">
            {!isPublished && onPublish && (
              <Button
                variant="outline"
                size="sm"
                onClick={onPublish}
                disabled={isPublishing}
                className="flex-1 sm:flex-none"
              >
                {isPublishing ? 'Publishing...' : 'Publish'}
              </Button>
            )}
            <Button
              variant="default"
              size="sm"
              onClick={onEditTheme}
              disabled={isPublishing}
              className="flex-1 sm:flex-none"
            >
              Edit theme
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-9 w-9 flex-shrink-0">
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {onRename && (
                  <DropdownMenuItem onClick={onRename}>
                    <Edit2 className="mr-2 h-4 w-4" />
                    Rename
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={() => toast.info('Preview coming soon')}>
                  <Eye className="mr-2 h-4 w-4" />
                  Preview
                </DropdownMenuItem>
                {onDuplicate && (
                  <DropdownMenuItem onClick={onDuplicate} disabled={isDuplicating}>
                    <Copy className="mr-2 h-4 w-4" />
                    {isDuplicating ? 'Duplicating...' : 'Duplicate'}
                  </DropdownMenuItem>
                )}
                {canDelete && onDelete && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={onDelete} className="text-destructive">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
