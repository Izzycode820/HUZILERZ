'use client';

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table';
import { Card } from '@/components/shadcn-ui/card';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import { Badge } from '@/components/shadcn-ui/badge';
import { RefreshCcw, Ban } from 'lucide-react';

interface StaffMember {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  status: string;
  roles: string[];
}

interface StaffTableProps {
  members: StaffMember[];
  selectedStaff: string[];
  onSelectStaff: (ids: string[]) => void;
  onViewMember: (id: string) => void;
}

export function StaffTable({
  members,
  selectedStaff,
  onSelectStaff,
  onViewMember,
}: StaffTableProps) {
  const isAllSelected = members.length > 0 && selectedStaff.length === members.length;

  const handleSelectAll = () => {
    if (isAllSelected) {
      onSelectStaff([]);
    } else {
      onSelectStaff(members.map(m => m.id));
    }
  };

  const handleSelectMember = (id: string) => {
    if (selectedStaff.includes(id)) {
      onSelectStaff(selectedStaff.filter(staffId => staffId !== id));
    } else {
      onSelectStaff([...selectedStaff, id]);
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

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return <RefreshCcw className="h-4 w-4 text-muted-foreground" />;
      case 'suspended':
        return <Ban className="h-4 w-4 text-destructive" />;
      default:
        return null;
    }
  };

  const getUserDisplay = (member: StaffMember) => {
    if (member.firstName && member.lastName) {
      return `${member.firstName} ${member.lastName}`;
    }
    return member.email;
  };

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">
                <Checkbox
                  checked={isAllSelected}
                  onCheckedChange={handleSelectAll}
                  aria-label="Select all"
                />
              </TableHead>
              <TableHead className="whitespace-nowrap">User</TableHead>
              <TableHead className="whitespace-nowrap">Status</TableHead>
              <TableHead className="whitespace-nowrap">Role</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {members.map((member) => (
              <TableRow
                key={member.id}
                className="cursor-pointer"
                onClick={() => onViewMember(member.id)}
              >
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selectedStaff.includes(member.id)}
                    onCheckedChange={() => handleSelectMember(member.id)}
                    aria-label={`Select ${getUserDisplay(member)}`}
                  />
                </TableCell>
                <TableCell className="font-medium whitespace-nowrap">
                  {getUserDisplay(member)}
                </TableCell>
                <TableCell className="whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(member.status)}
                    {getStatusIcon(member.status)}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground whitespace-nowrap">
                  {member.roles.join(', ')}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
