'use client';

/**
 * Pending Invites Table
 * Displays pending staff invitations with status and actions
 */

import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/shadcn-ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Button } from '@/components/shadcn-ui/button';
import { Clock, Mail, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface PendingInvite {
    id: string;
    email: string;
    role: string;
    invitedBy: string;
    createdAt: string;
    expiresAt: string;
}

interface PendingInvitesTableProps {
    invites: PendingInvite[];
    onCancelInvite?: (inviteId: string) => void;
    onResendInvite?: (inviteId: string) => void;
}

export function PendingInvitesTable({
    invites,
    onCancelInvite,
    onResendInvite,
}: PendingInvitesTableProps) {
    if (invites.length === 0) {
        return null; // Don't show anything if no pending invites
    }

    const isExpired = (expiresAt: string) => {
        return new Date(expiresAt) < new Date();
    };

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-medium flex items-center gap-2">
                        <Clock className="h-4 w-4 text-yellow-600" />
                        Pending Invitations
                        <Badge variant="secondary" className="ml-2">{invites.length}</Badge>
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="p-0 overflow-hidden">
                <div className="overflow-x-auto">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="whitespace-nowrap">Email</TableHead>
                                <TableHead className="whitespace-nowrap">Role</TableHead>
                                <TableHead className="whitespace-nowrap">Invited By</TableHead>
                                <TableHead className="whitespace-nowrap">Sent</TableHead>
                                <TableHead className="whitespace-nowrap">Status</TableHead>
                                <TableHead className="text-right whitespace-nowrap">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {invites.map((invite) => (
                                <TableRow key={invite.id}>
                                    <TableCell className="font-medium whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <Mail className="h-4 w-4 text-muted-foreground" />
                                            {invite.email}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-muted-foreground whitespace-nowrap">
                                        {invite.role}
                                    </TableCell>
                                    <TableCell className="text-muted-foreground whitespace-nowrap">
                                        {invite.invitedBy}
                                    </TableCell>
                                    <TableCell className="text-muted-foreground whitespace-nowrap">
                                        {formatDistanceToNow(new Date(invite.createdAt), { addSuffix: true })}
                                    </TableCell>
                                    <TableCell className="whitespace-nowrap">
                                        {isExpired(invite.expiresAt) ? (
                                            <Badge className="bg-red-100 text-red-800 hover:bg-red-100">
                                                Expired
                                            </Badge>
                                        ) : (
                                            <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
                                                Pending
                                            </Badge>
                                        )}
                                    </TableCell>
                                    <TableCell className="text-right whitespace-nowrap">
                                        <div className="flex items-center justify-end gap-2">
                                            {onResendInvite && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => onResendInvite(invite.id)}
                                                    disabled={!isExpired(invite.expiresAt)}
                                                >
                                                    Resend
                                                </Button>
                                            )}
                                            {onCancelInvite && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="text-destructive hover:text-destructive"
                                                    onClick={() => onCancelInvite(invite.id)}
                                                >
                                                    <X className="h-4 w-4" />
                                                </Button>
                                            )}
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
}
