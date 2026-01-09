/**
 * Workspace Creation Page - Clean Implementation
 * Uses WorkspaceCreate component with proper route integration
 * Follows auth page pattern for simplicity
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { WorkspaceCreate } from '@/components/workspace/management/WorkspaceCreate';
import { Button } from '@/components/shadcn-ui/button';
import { ArrowLeft } from 'lucide-react';

export default function WorkspaceCreatePage() {
  const router = useRouter();

  const handleWorkspaceCreate = (workspace: { id: string } | unknown) => {
    // Navigate to the new workspace dashboard
    if (workspace && typeof workspace === 'object' && 'id' in workspace) {
      router.push(`/workspace/${workspace.id}/dashboard`);
    }
  };

  const handleBack = () => {
    router.push('/workspace');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Workspaces
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Create New Workspace</h1>
              <p className="text-muted-foreground">
                Set up a new workspace for your projects
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <WorkspaceCreate
            onWorkspaceCreate={handleWorkspaceCreate}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}