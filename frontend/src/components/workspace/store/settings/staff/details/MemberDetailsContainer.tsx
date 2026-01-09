'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client/react';
import { GetWorkspaceMemberDocument } from '@/services/graphql/admin-store/queries/staffs/__generated__/GetWorkspaceMember.generated';
import { GetWorkspaceRolesDocument } from '@/services/graphql/admin-store/queries/staffs/__generated__/GetWorkspaceRoles.generated';
import { ChangeStaffRoleDocument } from '@/services/graphql/admin-store/mutations/staffs/__generated__/ChangeStaffRole.generated';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Badge } from '@/components/shadcn-ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/shadcn-ui/popover';
import { Avatar, AvatarFallback } from '@/components/shadcn-ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import { toast } from 'sonner';
import { ArrowLeft, Plus, Search, MoreVertical, Check, User, ChevronDown } from 'lucide-react';

interface MemberDetailsContainerProps {
  memberId: string;
}

export default function MemberDetailsContainer({ memberId }: MemberDetailsContainerProps) {
  const router = useRouter();
  const [roleSearchQuery, setRoleSearchQuery] = useState('');
  const [isRolePopoverOpen, setIsRolePopoverOpen] = useState(false);

  // Fetch member details
  const { data: memberData, loading: memberLoading, error: memberError, refetch } = useQuery(
    GetWorkspaceMemberDocument,
    {
      variables: { id: memberId },
      skip: !memberId,
    }
  );

  // Fetch all workspace roles
  const { data: rolesData, loading: rolesLoading } = useQuery(GetWorkspaceRolesDocument, {
    variables: {
      first: 50,
      isSystem: false,
    },
  });

  const [changeRole, { loading: changingRole }] = useMutation(ChangeStaffRoleDocument);

  const member = memberData?.workspaceMember;
  const allRoles = rolesData?.workspaceRoles?.edges?.map(edge => edge?.node).filter(Boolean) || [];
  const currentRoleId = member?.role?.id;

  const filteredRoles = allRoles.filter(role =>
    role?.name.toLowerCase().includes(roleSearchQuery.toLowerCase()) ||
    role?.description.toLowerCase().includes(roleSearchQuery.toLowerCase())
  );

  const handleBack = () => {
    router.back();
  };

  const handleAssignRole = async (roleId: string) => {
    if (!member) return;

    try {
      const { data } = await changeRole({
        variables: {
          input: {
            memberId: member.id,
            newRoleId: roleId,
          },
        },
      });

      if (data?.changeStaffRole?.success) {
        toast.success(data.changeStaffRole.message || 'Role updated successfully');
        refetch();
        setIsRolePopoverOpen(false);
        setRoleSearchQuery('');
      } else {
        toast.error(data?.changeStaffRole?.error || 'Failed to update role');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to update role');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
            Active
          </Badge>
        );
      case 'pending':
        return (
          <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
            Pending
          </Badge>
        );
      case 'suspended':
        return (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-100">
            Suspended
          </Badge>
        );
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (memberLoading) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading member details...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (memberError || !member) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive py-12">
              <p>Failed to load member details</p>
              <p className="text-sm text-muted-foreground">
                {memberError?.message || 'Member not found'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <User className="h-5 w-5" />
          <h1 className="text-2xl font-bold">{member.user.email}</h1>
          {getStatusBadge(member.status)}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Actions
              <ChevronDown className="h-4 w-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Suspend</DropdownMenuItem>
            <DropdownMenuItem>Reactivate</DropdownMenuItem>
            <DropdownMenuItem className="text-destructive">Remove</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* User Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12 bg-green-500">
              <AvatarFallback className="bg-green-500 text-white">
                <User className="h-6 w-6" />
              </AvatarFallback>
            </Avatar>
            <p className="font-medium">{member.user.email}</p>
          </div>
        </CardContent>
      </Card>

      {/* Roles Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Roles</CardTitle>
          <CardDescription>Assign roles to grant permissions.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Current Role */}
          {member.role && (
            <div className="flex items-center justify-between py-3 border-b">
              <div>
                <p className="font-medium">{member.role.name}</p>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem disabled>Remove role</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

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
                      const isCurrentRole = role?.id === currentRoleId;
                      return (
                        <button
                          key={role?.id}
                          type="button"
                          onClick={() => !isCurrentRole && handleAssignRole(role?.id || '')}
                          disabled={changingRole}
                          className="w-full px-4 py-3 text-left hover:bg-muted transition-colors flex items-start gap-3"
                        >
                          <div className="w-5 flex-shrink-0 pt-0.5">
                            {isCurrentRole && <Check className="h-4 w-4 text-primary" />}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium">{role?.name}</p>
                            <p className="text-sm text-muted-foreground">{role?.description}</p>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </PopoverContent>
          </Popover>
        </CardContent>
      </Card>
    </div>
  );
}
