"use client"

import React from 'react';
import {
  IconBuildingStore,
  IconFileText,
  IconBriefcase,
  IconLayout,
  IconUsers,
  IconTrendingUp,
  IconDots,
  IconRefresh,
  IconClock,
  IconTrash,
  IconLock,
  IconUserCheck
} from '@tabler/icons-react';

// Shadcn/UI Components
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Button } from '@/components/shadcn-ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';

// Hooks
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement';

// Types
import type { WorkspaceListItem } from '@/types/workspace/core';

interface WorkspaceCardProps {
  workspace: WorkspaceListItem;
  onClick: () => void;
  className?: string;
}

// Workspace type configurations
const workspaceTypeConfig = {
  store: {
    icon: IconBuildingStore,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950',
    label: 'Store',
  },
  blog: {
    icon: IconFileText,
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950',
    label: 'Blog',
  },
  services: {
    icon: IconBriefcase,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-950',
    label: 'Services',
  },
  portfolio: {
    icon: IconLayout,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50 dark:bg-orange-950',
    label: 'Portfolio',
  },
} as const;

// Status configurations - aligned with backend WorkspaceStatus
const statusConfig = {
  active: {
    variant: 'default' as const,
    label: 'Active',
  },
  inactive: {
    variant: 'secondary' as const,
    label: 'Inactive',
  },
  suspended: {
    variant: 'destructive' as const,
    label: 'Suspended',
  },
  suspended_by_plan: {
    variant: 'outline' as const,
    label: 'Plan Limit Exceeded',
    className: 'border-amber-500 text-amber-600 bg-amber-50 dark:bg-amber-950',
  },
  deleted: {
    variant: 'destructive' as const,
    label: 'Deleted',
  },
} as const;

export function WorkspaceCard({ workspace, onClick, className }: WorkspaceCardProps) {
  const typeConfig = workspaceTypeConfig[workspace.type] || workspaceTypeConfig.store;
  const status = statusConfig[workspace.status] || statusConfig.active;
  const IconComponent = typeConfig.icon;

  const { deleteWorkspace, restoreWorkspace, isDeleting, isRestoring } = useWorkspaceManagement();
  const [isActionLoading, setIsActionLoading] = React.useState(false);

  // Staff-aware checks
  const isOwner = workspace.role === 'owner';
  const isStaff = workspace.role === 'staff';
  const isDeleted = workspace.status === 'suspended';
  const isSuspendedByPlan = workspace.status === 'suspended_by_plan';
  const isRestricted = workspace.restricted_mode;
  const canRestore = workspace.deletionInfo?.canRestore || false;
  const isClickable = !isDeleted && !isSuspendedByPlan;

  // Real-time countdown
  const [timeRemaining, setTimeRemaining] = React.useState<{ days: number, hours: number, minutes: number } | null>(null);

  React.useEffect(() => {
    if (!isDeleted || !workspace.deletionInfo?.scheduledFor) return;

    const calculateTimeRemaining = () => {
      const now = new Date();
      const scheduled = new Date(workspace.deletionInfo!.scheduledFor);
      const diffMs = scheduled.getTime() - now.getTime();

      if (diffMs <= 0) {
        setTimeRemaining({ days: 0, hours: 0, minutes: 0 });
        return;
      }

      const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      setTimeRemaining({ days, hours, minutes });
    };

    // Calculate immediately
    calculateTimeRemaining();

    // Update every minute
    const interval = setInterval(calculateTimeRemaining, 60000);

    return () => clearInterval(interval);
  }, [isDeleted, workspace.deletionInfo?.scheduledFor]);

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Handle delete workspace
  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isActionLoading) return;

    if (!confirm(`Are you sure you want to delete "${workspace.name}"? You'll have 5 days to restore it.`)) {
      return;
    }

    setIsActionLoading(true);
    try {
      await deleteWorkspace(workspace.id);
    } catch (error) {
      console.error('Failed to delete workspace:', error);
      alert('Failed to delete workspace. Please try again.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Handle restore workspace
  const handleRestore = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isActionLoading) return;

    setIsActionLoading(true);
    try {
      await restoreWorkspace(workspace.id);
    } catch (error) {
      console.error('Failed to restore workspace:', error);
      alert('Failed to restore workspace. Please try again.');
    } finally {
      setIsActionLoading(false);
    }
  };

  return (
    <Card
      className={`
        @container/card
        group
        bg-gradient-to-t from-primary/5 to-card
        shadow-xs
        transition-all duration-200
        hover:from-primary/10 hover:to-card
        hover:shadow-md
        ${isDeleted || isSuspendedByPlan ? 'opacity-60 bg-muted/50' : 'cursor-pointer'}
        ${isRestricted ? 'border-amber-500/40' : ''}
        ${className}
      `}
      onClick={isClickable ? onClick : undefined}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${typeConfig.bgColor}`}>
              <IconComponent className={`h-5 w-5 ${typeConfig.color}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg font-semibold truncate">
                  {workspace.name}
                </CardTitle>
                {/* Status Indicator Dot */}
                <div className={`h-2 w-2 rounded-full ${isDeleted ? 'bg-red-500' : 'bg-green-500'}`} />
              </div>
              <CardDescription className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs">
                  {typeConfig.label}
                </Badge>
                {/* Role badge - staff-aware */}
                <Badge
                  variant={isOwner ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {isOwner ? 'Owner' : 'Staff'}
                </Badge>
                {/* Status badge with custom class for suspended_by_plan */}
                <Badge
                  variant={status.variant}
                  className={`text-xs ${'className' in status ? status.className : ''}`}
                >
                  {status.label}
                </Badge>
              </CardDescription>
            </div>
          </div>

          {/* Three Dot Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
                disabled={isActionLoading}
                onClick={(e) => e.stopPropagation()}
              >
                <IconDots className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
              {isDeleted ? (
                canRestore && (
                  <DropdownMenuItem onClick={handleRestore} disabled={isActionLoading}>
                    <IconRefresh className="mr-2 h-4 w-4" />
                    <span>Restore</span>
                  </DropdownMenuItem>
                )
              ) : (
                /* SECURITY: Only owners can delete workspaces */
                isOwner && (
                  <DropdownMenuItem
                    onClick={handleDelete}
                    disabled={isActionLoading}
                    className="text-destructive focus:text-destructive"
                  >
                    <IconTrash className="mr-2 h-4 w-4" />
                    <span>Delete</span>
                  </DropdownMenuItem>
                )
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Restricted Mode Warning Banner */}
        {isRestricted && !isDeleted && !isSuspendedByPlan && (
          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <IconLock className="h-4 w-4" />
              <span className="font-medium">Write access restricted</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {isOwner
                ? 'Renew subscription to restore full access'
                : 'Contact workspace owner to resolve'}
            </p>
          </div>
        )}

        {/* Plan Limit Exceeded Warning Banner */}
        {isSuspendedByPlan && (
          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <IconLock className="h-4 w-4" />
              <span className="font-medium">Workspace inaccessible</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {isOwner
                ? 'Upgrade plan or delete excess workspaces to access'
                : 'Contact workspace owner for access'}
            </p>
          </div>
        )}

        {/* Deletion Warning Banner */}
        {isDeleted && workspace.deletionInfo && timeRemaining && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-destructive">
              <IconClock className="h-4 w-4" />
              <span className="font-medium">
                {timeRemaining.days}d {timeRemaining.hours}h {timeRemaining.minutes}m left to restore
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Permanently deletes on {formatDate(workspace.deletionInfo.scheduledFor)}
            </p>
          </div>
        )}

        {/* Workspace Stats */}
        {!isDeleted && !isSuspendedByPlan && (
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <IconUsers className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{workspace.member_count || 0}</span>
              <span className="text-muted-foreground">members</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <IconUserCheck className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium capitalize">{workspace.role}</span>
            </div>
          </div>
        )}

        {/* Description placeholder - WorkspaceListItem doesn't include description */}
        {!isDeleted && !isSuspendedByPlan && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {workspace.type.charAt(0).toUpperCase() + workspace.type.slice(1)} workspace
          </p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Created {formatDate(workspace.createdAt)}</span>
          {workspace.updatedAt !== workspace.createdAt && (
            <span>Updated {formatDate(workspace.updatedAt)}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default WorkspaceCard;