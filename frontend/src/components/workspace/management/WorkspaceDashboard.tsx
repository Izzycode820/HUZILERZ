"use client"

import React from 'react';
import { useRouter } from 'next/navigation';

// Shadcn/UI Components
import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent, CardHeader } from '@/components/shadcn-ui/card';
import { Skeleton } from '@/components/shadcn-ui/skeleton';

// Hooks
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement';
import { useWorkspace } from '@/hooks/authentication/useWorkspace';

// Components
import { WorkspaceCard } from './WorkspaceCard';
import { CreateWorkspaceCard } from './CreateWorkspaceCard';

// Routes
import { WORKSPACE_ROUTES, STORE_ROUTES, BLOG_ROUTES, SERVICES_ROUTES } from '@/routes/domains/workspace';

// Types
import type { WorkspaceListItem } from '@/types/workspace/core';

export function WorkspaceDashboard() {
  const router = useRouter();
  const {
    workspaces,
    isLoading,
    error,
    hasWorkspaces,
    listWorkspaces
  } = useWorkspaceManagement();

  const { switchWorkspace, isSwitching } = useWorkspace();

  // Load workspace data on mount (empty deps - run once only)
  // Store-level guard prevents infinite loops (see workspaceManagementStore.ts)
  React.useEffect(() => {
    listWorkspaces();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle workspace selection - stable reference with useCallback
  const handleWorkspaceSelect = React.useCallback(async (workspace: WorkspaceListItem) => {
    if (isSwitching) return; // Prevent double clicks during switching

    try {
      // Switch workspace context
      await switchWorkspace(workspace.id);

      // Navigate to the correct workspace dashboard based on type
      let workspaceRoute: string;
      switch (workspace.type) {
        case 'store':
          workspaceRoute = STORE_ROUTES.HOME(workspace.id);
          break;
        case 'blog':
          workspaceRoute = BLOG_ROUTES.HOME(workspace.id);
          break;
        case 'services':
          workspaceRoute = SERVICES_ROUTES.HOME(workspace.id);
          break;
        case 'portfolio':
          // Portfolio fallback (if/when implemented)
          workspaceRoute = WORKSPACE_ROUTES.DASHBOARD(workspace.id);
          break;
        default:
          // Fallback to workspace management page
          workspaceRoute = WORKSPACE_ROUTES.ROOT;
      }

      router.push(workspaceRoute);
    } catch (error) {
      console.error('Failed to Load Dashboard:', error);
    }
  }, [switchWorkspace, isSwitching, router]);

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 px-4 lg:px-6">
            {Array.from({ length: 4 }).map((_, index) => (
              <Card key={index} className="animate-pulse">
                <CardHeader>
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-6 w-3/4" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-2/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="px-4 lg:px-6">
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-destructive text-lg font-medium mb-2">
                    Failed to load workspaces
                  </div>
                  <p className="text-muted-foreground">{error}</p>
                  <Button
                    variant="outline"
                    onClick={() => listWorkspaces(true)}
                    className="mt-4"
                  >
                    Try Again
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Workspaces Grid - Always show (CreateWorkspaceCard + existing workspaces) */}
        {!isLoading && !error && (
          <div className="px-4 lg:px-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {/* Create Workspace Card (always visible) */}
              <CreateWorkspaceCard />

              {/* Workspace Cards */}
              {workspaces.map((workspace) => (
                <WorkspaceCard
                  key={workspace.id}
                  workspace={workspace}
                  onClick={() => handleWorkspaceSelect(workspace)}
                  className={isSwitching ? 'opacity-50 cursor-not-allowed' : ''}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkspaceDashboard;