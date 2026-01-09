"use client"

import React, { useState } from 'react';
import { IconPlus } from '@tabler/icons-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/authentication/useAuth';
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement';

// Shadcn/UI Components
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';

export function CreateWorkspaceCard() {
  const router = useRouter();
  const { isAuthenticated, maxWorkspaces } = useAuth();
  const { workspaceCount } = useWorkspaceManagement();


  // Check if user hit workspace limit (soft gate check)
  const isAtLimit = isAuthenticated && workspaceCount >= maxWorkspaces;


  const handleCreateWorkspace = () => {
    // Auth gate - redirect unauthenticated users to signup (industry standard)
    if (!isAuthenticated) {
      const redirectUrl = '/workspace/create';
      router.push(`/auth/signup?redirect=${encodeURIComponent(redirectUrl)}`);
      return;
    }


    // User can create workspace - proceed to form
    router.push('/workspace/create');
  };

  return (
    <>
      <Card
        className={`
          @container/card
          group cursor-pointer
          bg-gradient-to-t from-primary/5 to-card
          shadow-xs
          transition-all duration-200
          hover:from-primary/10 hover:to-card
          hover:shadow-md
          relative
          ${isAtLimit ? 'opacity-60 blur-[0.5px] pointer-events-auto' : ''}
        `}
        onClick={handleCreateWorkspace}
      >
        {/* Limit Reached Badge */}
        {isAtLimit && (
          <div className="absolute -top-2 -right-2 z-10">
            <Badge variant="secondary" className="bg-muted text-muted-foreground text-xs">
              {workspaceCount}/{maxWorkspaces}
            </Badge>
          </div>
        )}

        <CardContent className="flex flex-col items-center justify-center p-8 h-full min-h-[200px]">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center group-hover:bg-primary/30 transition-colors">
              <IconPlus className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-1">Create Workspace</h3>
              <p className="text-sm text-muted-foreground">
                Start a new store, blog, services, or portfolio
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

    </>
  );
}

export default CreateWorkspaceCard;