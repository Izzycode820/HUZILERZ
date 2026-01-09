'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client/react';
import { GetWorkspaceRolesDocument } from '@/services/graphql/admin-store/queries/staffs/__generated__/GetWorkspaceRoles.generated';
import { InviteStaffDocument } from '@/services/graphql/admin-store/mutations/staffs/__generated__/InviteStaff.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/shadcn-ui/popover';
import { Badge } from '@/components/shadcn-ui/badge';
import { toast } from 'sonner';
import { ArrowLeft, Plus, Search, X, Check } from 'lucide-react';

export default function AddStaffForm() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const [email, setEmail] = useState('');
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [roleSearchQuery, setRoleSearchQuery] = useState('');
  const [isRolePopoverOpen, setIsRolePopoverOpen] = useState(false);

  // Fetch workspace roles
  const { data: rolesData, loading: rolesLoading } = useQuery(GetWorkspaceRolesDocument, {
    variables: {
      first: 50,
      isSystem: false,
    },
    skip: !currentWorkspace,
  });

  const [inviteStaff, { loading: inviting }] = useMutation(InviteStaffDocument);

  const roles = rolesData?.workspaceRoles?.edges?.map(edge => edge?.node).filter(Boolean) || [];
  const selectedRoles = roles.filter(role => selectedRoleIds.includes(role?.id || ''));

  const filteredRoles = roles.filter(role =>
    role?.name.toLowerCase().includes(roleSearchQuery.toLowerCase()) ||
    role?.description.toLowerCase().includes(roleSearchQuery.toLowerCase())
  );

  const handleBack = () => {
    router.back();
  };

  const handleCancel = () => {
    router.push(`/workspace/${currentWorkspace?.id}/store/settings/staff`);
  };

  const handleSelectRole = (roleId: string) => {
    if (!selectedRoleIds.includes(roleId)) {
      setSelectedRoleIds([...selectedRoleIds, roleId]);
    }
    setRoleSearchQuery('');
  };

  const handleRemoveRole = (roleId: string) => {
    setSelectedRoleIds(selectedRoleIds.filter(id => id !== roleId));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast.error('Please enter an email address');
      return;
    }

    if (selectedRoleIds.length === 0) {
      toast.error('Please select at least one role');
      return;
    }

    try {
      const { data } = await inviteStaff({
        variables: {
          input: {
            email,
            roleIds: selectedRoleIds,
          },
        },
      });

      if (data?.inviteStaff?.success) {
        toast.success(data.inviteStaff.message || 'Staff invitation sent successfully');
        router.push(`/workspace/${currentWorkspace?.id}/store/settings/staff`);
      } else {
        toast.error(data?.inviteStaff?.error || 'Failed to send invitation');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to send invitation');
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header with back button */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={handleBack}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold">Add users</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Emails Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Emails</CardTitle>
          </CardHeader>
          <CardContent>
            <Input
              type="email"
              placeholder="Enter email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full"
            />
          </CardContent>
        </Card>

        {/* Roles Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Roles</CardTitle>
            <CardDescription>Assign roles to grant user actions.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Selected Roles (supports multiple like Shopify) */}
            {selectedRoles.map((role) => (
              <div key={role?.id} className="flex items-center justify-between p-3 border rounded-md">
                <div>
                  <p className="font-medium">{role?.name}</p>
                  <p className="text-sm text-muted-foreground">{role?.description}</p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRemoveRole(role?.id || '')}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}

            {/* Assign Button with Popover */}
            <Popover open={isRolePopoverOpen} onOpenChange={setIsRolePopoverOpen}>
              <PopoverTrigger asChild>
                <Button type="button" variant="outline" className="w-full justify-start">
                  <Plus className="h-4 w-4 mr-2" />
                  Assign
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0" align="start">
                <div className="p-3 border-b">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search"
                      value={roleSearchQuery}
                      onChange={(e) => setRoleSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="max-h-80 overflow-y-auto">
                  {rolesLoading ? (
                    <div className="p-8 text-center text-sm text-muted-foreground">
                      Loading roles...
                    </div>
                  ) : filteredRoles.length === 0 ? (
                    <div className="p-8 text-center text-sm text-muted-foreground">
                      No roles found
                    </div>
                  ) : (
                    <div className="py-2">
                      {filteredRoles.map((role) => {
                        const isSelected = selectedRoleIds.includes(role?.id || '');
                        return (
                          <button
                            key={role?.id}
                            type="button"
                            onClick={() => handleSelectRole(role?.id || '')}
                            className="w-full px-4 py-3 text-left hover:bg-muted transition-colors flex items-start gap-3"
                          >
                            <div className="flex-1">
                              <p className="font-medium">{role?.name}</p>
                              <p className="text-sm text-muted-foreground">{role?.description}</p>
                            </div>
                            {isSelected && (
                              <Check className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                            )}
                          </button>
                        );
                      })}

                      {/* Create new role button (disabled for now) */}
                      <button
                        type="button"
                        disabled
                        className="w-full px-4 py-3 text-left flex items-center gap-2 text-muted-foreground opacity-50 cursor-not-allowed"
                      >
                        <Plus className="h-4 w-4" />
                        Create new role
                      </button>
                    </div>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <Button type="button" variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={inviting}>
            {inviting ? 'Sending...' : 'Send invite'}
          </Button>
        </div>
      </form>
    </div>
  );
}
