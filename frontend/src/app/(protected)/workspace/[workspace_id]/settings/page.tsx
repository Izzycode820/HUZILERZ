/**
 * Workspace Settings Page - Clean Implementation
 * Uses proper workspace management hooks and types
 * Follows centralized workspace management pattern
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Badge } from '@/components/shadcn-ui/badge';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';
import {
  ArrowLeft,
  Settings,
  Users,
  Shield,
  Trash2,
  Save,
  AlertCircle,
  Loader2
} from 'lucide-react';

// Hooks
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement';

// Types
import type { WorkspaceUpdateRequest } from '@/types/workspace/core';

export default function WorkspaceSettingsPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.workspace_id as string;

  const {
    workspaces,
    currentWorkspace,
    getWorkspace,
    updateWorkspace,
    deleteWorkspace,
    isLoading,
    isUpdating,
    isDeleting,
    error,
    clearError,
    isWorkspaceOwner
  } = useWorkspaceManagement();

  const workspace = workspaces?.find(w => w.id === workspaceId);
  const [formData, setFormData] = useState<WorkspaceUpdateRequest>({
    name: '',
    description: ''
  });

  // Initialize form data when workspace loads
  useEffect(() => {
    if (workspaceId) {
      // Fetch full workspace data with description
      getWorkspace(workspaceId);
    }
  }, [workspaceId, getWorkspace]);

  // Update form data when current workspace changes
  useEffect(() => {
    if (currentWorkspace && currentWorkspace.id === workspaceId) {
      setFormData({
        name: currentWorkspace.name || '',
        description: currentWorkspace.description || ''
      });
    }
  }, [currentWorkspace, workspaceId]);

  const handleSave = async () => {
    if (!workspace) return;

    clearError();
    try {
      await updateWorkspace(workspaceId, formData);
      // Success handled by hook - workspace will be updated in store
    } catch (err) {
      // Error handled by hook
      console.error('Failed to update workspace:', err);
    }
  };

  const handleDelete = async () => {
    if (!workspace) return;

    if (!confirm('Are you sure you want to delete this workspace? This action cannot be undone.')) {
      return;
    }

    clearError();
    try {
      await deleteWorkspace(workspaceId);
      // Navigate back to workspace dashboard after successful deletion
      router.push('/workspace');
    } catch (err) {
      console.error('Failed to delete workspace:', err);
    }
  };

  const handleBack = () => {
    router.push(`/workspace/${workspaceId}/dashboard`);
  };

  const canManageWorkspace = isWorkspaceOwner(workspaceId);

  if (isLoading && !workspace) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-xl font-semibold mb-2">Workspace Not Found</h2>
          <p className="text-muted-foreground mb-4">
            The workspace you are looking for does not exist or you do not have access.
          </p>
          <Button onClick={() => router.push('/workspace')}>
            Back to Workspaces
          </Button>
        </div>
      </div>
    );
  }

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
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-2xl font-bold">Workspace Settings</h1>
              <p className="text-muted-foreground">
                Manage your workspace configuration
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="space-y-6">
            {/* Error State */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Tabs defaultValue="general" className="space-y-6">
              <TabsList>
                <TabsTrigger value="general">General</TabsTrigger>
                <TabsTrigger value="members">Members</TabsTrigger>
                {canManageWorkspace && (
                  <TabsTrigger value="danger" className="text-destructive">
                    Danger Zone
                  </TabsTrigger>
                )}
              </TabsList>

              {/* General Settings */}
              <TabsContent value="general" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="w-5 h-5" />
                      General Information
                    </CardTitle>
                    <CardDescription>
                      Update your workspace name and description
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="name" className="text-sm font-medium">
                        Workspace Name
                      </label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Enter workspace name"
                        disabled={!canManageWorkspace}
                      />
                    </div>

                    <div className="space-y-2">
                      <label htmlFor="description" className="text-sm font-medium">
                        Description
                      </label>
                      <Textarea
                        id="description"
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Enter workspace description"
                        rows={3}
                        disabled={!canManageWorkspace}
                      />
                    </div>

                    <div className="flex items-center gap-4">
                      <Badge variant="outline">
                        Type: {workspace.type}
                      </Badge>
                      <Badge variant="outline">
                        Status: {workspace.status}
                      </Badge>
                      <Badge variant="outline">
                        ID: {workspace.id}
                      </Badge>
                    </div>

                    {canManageWorkspace && (
                      <Button
                        onClick={handleSave}
                        disabled={isUpdating}
                        className="flex items-center gap-2"
                      >
                        {isUpdating ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                        Save Changes
                      </Button>
                    )}

                    {!canManageWorkspace && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          Only workspace owners can modify workspace settings
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Members Settings */}
              <TabsContent value="members" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="w-5 h-5" />
                      Team Members
                    </CardTitle>
                    <CardDescription>
                      Manage workspace members and permissions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-8">
                      <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                      <h3 className="text-lg font-medium mb-2">Member Management</h3>
                      <p className="text-muted-foreground mb-4">
                        Invite team members and manage their permissions
                      </p>
                      <Button disabled>
                        Coming Soon
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Danger Zone */}
              {canManageWorkspace && (
                <TabsContent value="danger" className="space-y-6">
                  <Card className="border-destructive">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-destructive">
                        <Shield className="w-5 h-5" />
                        Danger Zone
                      </CardTitle>
                      <CardDescription>
                        Irreversible actions that affect your workspace
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between p-4 border border-destructive rounded-lg">
                        <div>
                          <h4 className="font-medium text-destructive">
                            Delete Workspace
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            Permanently delete this workspace and all its data
                          </p>
                        </div>
                        <Button
                          variant="destructive"
                          onClick={handleDelete}
                          disabled={isDeleting}
                          className="flex items-center gap-2"
                        >
                          {isDeleting ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                          Delete Workspace
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              )}
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}