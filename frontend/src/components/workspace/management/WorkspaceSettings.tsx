"use client"

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Settings,
  Users,
  Shield,
  Trash2,
  Save,
  AlertCircle,
  Loader2
} from 'lucide-react';

// Shadcn/UI Components
import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Badge } from '@/components/shadcn-ui/badge';
import { Separator } from '@/components/shadcn-ui/separator';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs';

// Hooks
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement';
import { useAuth } from '@/hooks/authentication/useAuth';

interface WorkspaceSettingsProps {
  workspaceId: string;
  className?: string;
}

export function WorkspaceSettings({ workspaceId, className }: WorkspaceSettingsProps) {
  const router = useRouter();
  const { user } = useAuth();
  const {
    workspaces,
    updateWorkspace,
    deleteWorkspace,
    isLoading,
    error
  } = useWorkspaceManagement();

  const workspace = workspaces?.find(w => w.id === workspaceId);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [formData, setFormData] = useState({
    name: workspace?.name || '',
    description: workspace?.description || '',
  });

  const handleSave = async () => {
    if (!workspace) return;

    setIsSaving(true);
    try {
      await updateWorkspace(workspaceId, formData);
      // Success handled by hook
    } catch (err) {
      console.error('Failed to update workspace:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!workspace) return;

    setIsDeleting(true);
    try {
      await deleteWorkspace(workspaceId);
      router.push('/workspace');
    } catch (err) {
      console.error('Failed to delete workspace:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const isOwner = workspace?.owner_id === user?.id;

  if (!workspace) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Workspace not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Workspace Settings</h1>
          <p className="text-muted-foreground">
            Manage your workspace settings and preferences
          </p>
        </div>

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
            <TabsTrigger value="danger" className="text-destructive">
              Danger Zone
            </TabsTrigger>
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
                  />
                </div>

                <div className="flex items-center gap-4">
                  <Badge variant="outline">
                    Type: {workspace.type}
                  </Badge>
                  <Badge variant="outline">
                    Status: {workspace.status}
                  </Badge>
                </div>

                <Button
                  onClick={handleSave}
                  disabled={isSaving || isLoading}
                  className="flex items-center gap-2"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Save Changes
                </Button>
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
                    disabled={!isOwner || isDeleting}
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

                {!isOwner && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Only workspace owners can delete this workspace
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}