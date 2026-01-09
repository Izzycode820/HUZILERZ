'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
    IconArchive,
    IconX,
    IconCheck,
    IconDotsVertical,
} from '@tabler/icons-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';

interface MobileOrdersActionBarProps {
    selectedCount: number;
    onCancel: () => void;
    onArchive: () => void;
    onMarkAsPaid: () => void;
    onBulkCancel: () => void;
    // Additional actions in overflow menu
    onMarkAsShipped?: () => void;
    onMarkAsDelivered?: () => void;
}

export function MobileOrdersActionBar({
    selectedCount,
    onCancel,
    onArchive,
    onMarkAsPaid,
    onBulkCancel,
    onMarkAsShipped,
    onMarkAsDelivered,
}: MobileOrdersActionBarProps) {
    if (selectedCount === 0) return null;

    return (
        <div className="fixed bottom-20 left-0 right-0 z-40 flex justify-center px-4 md:hidden pointer-events-none">
            <div className="flex items-center gap-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-full px-4 py-3 shadow-2xl pointer-events-auto">
                {/* Close / Cancel Selection */}
                <button
                    onClick={onCancel}
                    className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                    aria-label="Cancel selection"
                >
                    <IconX className="w-5 h-5" />
                </button>

                {/* Selected Count */}
                <span className="text-sm font-medium px-2 min-w-[60px] text-center">
                    {selectedCount} selected
                </span>

                {/* Divider */}
                <div className="h-6 w-px bg-white/20 dark:bg-zinc-900/20" />

                {/* Primary Actions (max 3) */}
                <button
                    onClick={onArchive}
                    className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                    aria-label="Archive"
                    title="Archive"
                >
                    <IconArchive className="w-5 h-5" />
                </button>

                <button
                    onClick={onMarkAsPaid}
                    className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                    aria-label="Mark as paid"
                    title="Mark as Paid"
                >
                    <IconCheck className="w-5 h-5" />
                </button>

                {/* Overflow Menu */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button
                            className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                            aria-label="More actions"
                        >
                            <IconDotsVertical className="w-5 h-5" />
                        </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        align="end"
                        side="top"
                        className="w-48 mb-2"
                    >
                        <DropdownMenuItem onClick={onBulkCancel}>
                            Cancel Orders
                        </DropdownMenuItem>
                        {onMarkAsShipped && (
                            <DropdownMenuItem onClick={onMarkAsShipped}>
                                Mark as Shipped
                            </DropdownMenuItem>
                        )}
                        {onMarkAsDelivered && (
                            <DropdownMenuItem onClick={onMarkAsDelivered}>
                                Mark as Delivered
                            </DropdownMenuItem>
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </div>
    );
}
