'use client';

/**
 * Staff List Container (Smart Component)
 * Container handles data fetching, presentational components handle UI
 */

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client/react';
import { GetWorkspaceMembersDocument } from '@/services/graphql/admin-store/queries/staffs/__generated__/GetWorkspaceMembers.generated';
import { GetPendingInvitesDocument } from '@/services/graphql/admin-store/queries/staffs/__generated__/GetPendingInvites.generated';
import { RemoveStaffDocument } from '@/services/graphql/admin-store/mutations/staffs/__generated__/RemoveStaff.generated';
import { SuspendStaffDocument } from '@/services/graphql/admin-store/mutations/staffs/__generated__/SuspendStaff.generated';
import { ReactivateStaffDocument } from '@/services/graphql/admin-store/mutations/staffs/__generated__/ReactivateStaff.generated';
import { ResendInviteDocument } from '@/services/graphql/admin-store/mutations/staffs/__generated__/ResendInvite.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { StaffTable } from './StaffTable';
import { PendingInvitesTable } from './PendingInvitesTable';
import { StaffToolbar } from './StaffToolbar';
import { Button } from '@/components/shadcn-ui/button';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { toast } from 'sonner';
import { Users, ArrowLeft } from 'lucide-react';

export default function StaffListContainer() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const [selectedStaff, setSelectedStaff] = useState<string[]>([]);

  // Fetch workspace members
  const { data, loading, error, refetch } = useQuery(GetWorkspaceMembersDocument, {
    variables: {
      first: 50,
    },
    skip: !currentWorkspace,
  });

  // Fetch pending invites
  const { data: pendingData, loading: pendingLoading, refetch: refetchPending } = useQuery(
    GetPendingInvitesDocument,
    {
      skip: !currentWorkspace,
    }
  );

  // Mutations
  const [removeStaff] = useMutation(RemoveStaffDocument);
  const [suspendStaff] = useMutation(SuspendStaffDocument);
  const [reactivateStaff] = useMutation(ReactivateStaffDocument);
  const [resendInvite] = useMutation(ResendInviteDocument);

  // Transform data
  const members = (data?.workspaceMembers?.edges
    ?.map(edge => {
      const node = edge?.node;
      if (!node) return null;

      return {
        id: node.id,
        email: node.user.email,
        firstName: node.user.firstName,
        lastName: node.user.lastName,
        status: node.status,
        role: node.role?.name || 'Unknown',
        roles: node.role ? [node.role.name] : [],
        joinedAt: node.joinedAt,
      };
    })
    .filter((member): member is NonNullable<typeof member> => member !== null) || []);

  // Transform pending invites data
  const pendingInvites = (pendingData?.pendingInvites
    ?.map(invite => {
      if (!invite) return null;
      return {
        id: invite.id,
        email: invite.email,
        role: invite.role?.name || 'Unknown',
        invitedBy: invite.invitedBy?.email || 'Unknown',
        createdAt: invite.createdAt,
        expiresAt: invite.expiresAt,
      };
    })
    .filter((invite): invite is NonNullable<typeof invite> => invite !== null) || []);

  // Handlers
  const handleAddStaff = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/settings/staff/new`);
  };

  const handleViewMember = (memberId: string) => {
    router.push(`/workspace/${currentWorkspace?.id}/store/settings/staff/${memberId}`);
  };

  const handleExport = () => {
    toast.info('Export functionality coming soon!');
  };

  const handleBulkSuspend = async () => {
    if (selectedStaff.length === 0) return;

    try {
      let successCount = 0;
      let errorCount = 0;

      for (const memberId of selectedStaff) {
        const { data: suspendData } = await suspendStaff({
          variables: {
            input: {
              memberId,
              reason: 'Suspended by administrator',
            },
          },
        });

        if (suspendData?.suspendStaff?.success) {
          successCount++;
        } else {
          errorCount++;
        }
      }

      if (successCount > 0) {
        toast.success(`Suspended ${successCount} staff member${successCount > 1 ? 's' : ''}`);
        refetch();
        setSelectedStaff([]);
      }
      if (errorCount > 0) {
        toast.error(`Failed to suspend ${errorCount} staff member${errorCount > 1 ? 's' : ''}`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to suspend staff members');
    }
  };

  const handleBulkReactivate = async () => {
    if (selectedStaff.length === 0) return;

    try {
      let successCount = 0;
      let errorCount = 0;

      for (const memberId of selectedStaff) {
        const { data: reactivateData } = await reactivateStaff({
          variables: { memberId },
        });

        if (reactivateData?.reactivateStaff?.success) {
          successCount++;
        } else {
          errorCount++;
        }
      }

      if (successCount > 0) {
        toast.success(`Reactivated ${successCount} staff member${successCount > 1 ? 's' : ''}`);
        refetch();
        setSelectedStaff([]);
      }
      if (errorCount > 0) {
        toast.error(`Failed to reactivate ${errorCount} staff member${errorCount > 1 ? 's' : ''}`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to reactivate staff members');
    }
  };

  const handleBulkRemove = async () => {
    if (selectedStaff.length === 0) return;

    if (!confirm(`Are you sure you want to remove ${selectedStaff.length} staff member${selectedStaff.length > 1 ? 's' : ''}?`)) {
      return;
    }

    try {
      let successCount = 0;
      let errorCount = 0;

      for (const memberId of selectedStaff) {
        const { data: removeData } = await removeStaff({
          variables: { memberId },
        });

        if (removeData?.removeStaff?.success) {
          successCount++;
        } else {
          errorCount++;
        }
      }

      if (successCount > 0) {
        toast.success(`Removed ${successCount} staff member${successCount > 1 ? 's' : ''}`);
        refetch();
        setSelectedStaff([]);
      }
      if (errorCount > 0) {
        toast.error(`Failed to remove ${errorCount} staff member${errorCount > 1 ? 's' : ''}`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove staff members');
    }
  };

  // Resend invite handler
  const handleResendInvite = async (inviteId: string) => {
    try {
      const { data: resendData } = await resendInvite({
        variables: { inviteId },
      });

      if (resendData?.resendInvite?.success) {
        toast.success('Invitation resent');
        refetchPending();
      } else {
        toast.error(resendData?.resendInvite?.error || 'Failed to resend invitation');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to resend invitation');
    }
  };

  // Loading state
  if (loading && members.length === 0) {
    return (
      <div className="max-w-5xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading staff members...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-5xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive py-12">
              <p>Failed to load staff members</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Empty state
  if (!loading && members.length === 0) {
    return (
      <div className="max-w-5xl mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No staff members yet</p>
            <p className="text-sm text-muted-foreground mb-4">
              Start by inviting team members to your workspace
            </p>
            <Button onClick={handleAddStaff}>Add users</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      {/* Header with actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/workspace/${currentWorkspace?.id}/store/settings`)}
            className="md:hidden"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <Users className="h-5 w-5" />
          <h1 className="text-2xl font-bold">Users</h1>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Button variant="outline" onClick={handleExport} className="flex-1 sm:flex-none">
            Export
          </Button>
          <Button onClick={handleAddStaff} className="flex-1 sm:flex-none">
            Add users
          </Button>
        </div>
      </div>

      {/* Bulk Actions Toolbar */}
      <StaffToolbar
        selectedCount={selectedStaff.length}
        onSuspend={handleBulkSuspend}
        onReactivate={handleBulkReactivate}
        onRemove={handleBulkRemove}
      />

      {/* Staff Table */}
      <StaffTable
        members={members}
        selectedStaff={selectedStaff}
        onSelectStaff={setSelectedStaff}
        onViewMember={handleViewMember}
      />

      {/* Pending Invites Table */}
      <PendingInvitesTable
        invites={pendingInvites}
        onResendInvite={handleResendInvite}
      />
    </div>
  );
}
