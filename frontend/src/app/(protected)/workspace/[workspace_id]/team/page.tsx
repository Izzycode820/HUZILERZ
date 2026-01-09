/**
 * Workspace Team Page - Clean Implementation
 * Uses proper useMembers hook and workspace management hooks
 * Follows centralized workspace management pattern
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import {
  ArrowLeft,
  Users,
  Plus,
  Mail,
  UserX,
  Shield,
  Loader2,
  AlertCircle
} from 'lucide-react';

// Hooks
import { useMembers } from '@/hooks/workspace/core/useMembers';
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement';
import { useAuth } from '@/hooks/authentication/useAuth';

// Types
import type { MemberInviteRequest } from '@/types/workspace/core';

export default function WorkspaceTeamPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.workspace_id as string;

  const { user } = useAuth();
  const { workspaces, isWorkspaceOwner } = useWorkspaceManagement();
  const {
    members,
    pendingInvites,
    isLoading,
    isInviting,
    isRemoving,
    error,
    listMembers,
    inviteMember,
    removeMember,
    clearError,
    canManageMembers
  } = useMembers();

  const workspace = workspaces?.find(w => w.id === workspaceId);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');

  // Load members when component mounts
  useEffect(() => {
    if (workspaceId) {
      listMembers(workspaceId);
    }
  }, [workspaceId, listMembers]);

  const handleBack = () => {
    router.push(`/workspace/${workspaceId}/dashboard`);
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;

    clearError();
    try {
      const inviteRequest: MemberInviteRequest = {
        email: inviteEmail.trim(),
        role: 'editor' // Default role
      };

      await inviteMember(workspaceId, inviteRequest);
      setInviteEmail('');
      setShowInviteForm(false);
      // Success handled by hook - members list will be updated
    } catch (err) {
      // Error handled by hook
      console.error('Failed to invite member:', err);
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!confirm('Are you sure you want to remove this member?')) {
      return;
    }

    clearError();
    try {
      await removeMember(workspaceId, userId);
      // Success handled by hook - members list will be updated
    } catch (err) {
      console.error('Failed to remove member:', err);
    }
  };

  const workspaceMembers = members[workspaceId] || [];
  const workspacePendingInvites = pendingInvites[workspaceId] || [];
  const canManage = canManageMembers(workspaceId);

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
          <div className="flex items-center justify-between">
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
                <h1 className="text-2xl font-bold">Team Members</h1>
                <p className="text-muted-foreground">
                  Manage workspace members and permissions
                </p>
              </div>
            </div>
            {canManage && (
              <Button
                onClick={() => setShowInviteForm(true)}
                className="flex items-center gap-2"
                disabled={isInviting}
              >
                <Plus className="w-4 h-4" />
                Invite Member
              </Button>
            )}
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

            {/* Invite Form */}
            {showInviteForm && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="w-5 h-5" />
                    Invite Team Member
                  </CardTitle>
                  <CardDescription>
                    Send an invitation to collaborate on this workspace
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-4">
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="Enter email address"
                      className="flex-1 px-3 py-2 border rounded-md"
                    />
                    <Button
                      onClick={handleInvite}
                      disabled={!inviteEmail.trim() || isInviting}
                      className="flex items-center gap-2"
                    >
                      {isInviting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Mail className="w-4 h-4" />
                      )}
                      Send Invite
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setShowInviteForm(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Members List */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Team Members ({workspaceMembers.length})
                </CardTitle>
                <CardDescription>
                  People who have access to this workspace
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse flex items-center gap-4">
                        <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                          <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : workspaceMembers.length > 0 ? (
                  <div className="space-y-4">
                    {workspaceMembers.map(member => (
                      <div key={member.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <Users className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <h3 className="font-medium">
                              {member.user_name || member.user_email}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                              {member.user_email}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge variant="outline">
                            {member.role_name}
                          </Badge>
                          {canManage && member.user_id !== user?.id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveMember(member.user_id)}
                              disabled={isRemoving}
                              className="flex items-center gap-2 text-destructive"
                            >
                              {isRemoving ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <UserX className="w-4 h-4" />
                              )}
                              Remove
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Team Members</h3>
                    <p className="text-muted-foreground mb-4">
                      Invite team members to collaborate on this workspace
                    </p>
                    {canManage && (
                      <Button onClick={() => setShowInviteForm(true)}>
                        Invite Your First Member
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Pending Invites */}
            {workspacePendingInvites.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="w-5 h-5" />
                    Pending Invites ({workspacePendingInvites.length})
                  </CardTitle>
                  <CardDescription>
                    Invitations that have not been accepted yet
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {workspacePendingInvites.map(invite => (
                      <div key={invite.id} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <p className="font-medium">{invite.user_email}</p>
                          <p className="text-sm text-muted-foreground">
                            Invited {new Date(invite.joined_at).toLocaleDateString()}
                          </p>
                        </div>
                        <Badge variant="secondary">Pending</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Permission Info */}
            {!canManage && (
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  You do not have permission to manage team members in this workspace.
                  Contact the workspace owner for access.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}