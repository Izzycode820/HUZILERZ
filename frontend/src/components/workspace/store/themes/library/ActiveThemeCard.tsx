'use client';

import React from 'react';
import Image from 'next/image';
import { useParams } from 'next/navigation';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Button } from '@/components/shadcn-ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import { MoreHorizontal, Package, Edit2, Copy } from 'lucide-react';
import { toast } from 'sonner';

interface ActiveThemeCardProps {
  id: string;
  themeName: string;
  previewImage: string;
  version: string;
  createdAt: string;
  isPasswordProtected?: boolean | null;
  storefrontPassword?: string | null;
  onEditTheme: () => void;
  onDuplicate?: () => void;
  onRename?: () => void;
}

export function ActiveThemeCard({
  id,
  themeName,
  previewImage,
  version,
  createdAt,
  isPasswordProtected,
  storefrontPassword,
  onEditTheme,
  onDuplicate,
  onRename,
}: ActiveThemeCardProps) {
  const params = useParams();
  const workspaceId = params?.workspace_id as string;

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
    <Card>
      <CardContent className="p-4 sm:p-6">
        {/* Preview Image */}
        <div className="mb-4 sm:mb-6">
          <div className="relative w-full aspect-[16/9] rounded-lg overflow-hidden border border-border bg-muted/30">
            {previewImage ? (
              <Image
                src={previewImage}
                alt={themeName}
                fill
                className="object-cover"
              />
            ) : (
              <div className="w-full h-full bg-muted/30 flex items-center justify-center">
                <Package className="w-12 sm:w-16 h-12 sm:h-16 text-muted-foreground/30" />
              </div>
            )}

            {/* Password Protection Overlay/Badge */}
            {isPasswordProtected && (
              <div className="absolute top-2 sm:top-3 right-2 sm:right-3">
                <Badge variant="secondary" className="bg-black/70 text-white backdrop-blur-sm border-0 font-medium hover:bg-black/80 text-xs sm:text-sm">
                  <span className="mr-1 sm:mr-1.5">🔒</span> Protected
                </Badge>
              </div>
            )}
          </div>
        </div>

        {/* Theme Info - stack on mobile */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Title and Badge - stack on mobile */}
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h3 className="text-base font-semibold truncate">{themeName}</h3>
              <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 text-xs">
                Current theme
              </Badge>
            </div>

            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Added: {formatDate(createdAt)}
              </p>
              <p className="text-sm text-muted-foreground">
                Version {version}
              </p>

              {/* Password Protection Warning Banner */}
              {isPasswordProtected && (
                <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 rounded-md flex flex-col sm:flex-row sm:items-center gap-2 text-sm">
                  <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200">
                    <span className="text-xs">🔒</span>
                    <span>Your store is password protected.</span>
                  </div>
                  <a
                    href={`/workspace/${workspaceId}/store/themes/preferences`}
                    className="text-amber-700 dark:text-amber-300 font-medium underline hover:text-amber-800 dark:hover:text-amber-100 whitespace-nowrap"
                  >
                    Unlock it
                  </a>
                </div>
              )}

              {/* Show password if protected (secondary info) */}
              {isPasswordProtected && storefrontPassword && (
                <div className="flex flex-wrap items-center gap-2 mt-2 p-2 bg-muted/50 rounded-md w-fit max-w-full">
                  <span className="text-xs font-medium text-muted-foreground">Password:</span>
                  <code className="text-xs bg-background px-1.5 py-0.5 rounded border truncate max-w-[150px] sm:max-w-none">{storefrontPassword}</code>
                </div>
              )}
            </div>
          </div>

          {/* Actions - full width on mobile */}
          <div className="flex items-center gap-2 w-full sm:w-auto sm:ml-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="flex-shrink-0">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => toast.info('Customize coming soon')}>
                  Customize
                </DropdownMenuItem>
                {onDuplicate && (
                  <DropdownMenuItem onClick={onDuplicate}>
                    <Copy className="mr-2 h-4 w-4" />
                    Duplicate
                  </DropdownMenuItem>
                )}
                {onRename && (
                  <DropdownMenuItem onClick={onRename}>
                    <Edit2 className="mr-2 h-4 w-4" />
                    Rename
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            <Button onClick={onEditTheme} variant="default" className="flex-1 sm:flex-none">
              Edit theme
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
