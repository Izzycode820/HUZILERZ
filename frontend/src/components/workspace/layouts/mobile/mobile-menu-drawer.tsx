'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { IconX, IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { Drawer, DrawerContent, DrawerClose } from '@/components/shadcn-ui/drawer';
import type { WorkspaceSidebarConfig } from "@/types/workspace/dashboard-ui/workspace";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/shadcn-ui/collapsible";
import { Button } from '@/components/shadcn-ui/button';

interface MobileMenuDrawerProps {
    config: WorkspaceSidebarConfig;
    isOpen: boolean;
    onClose: (open: boolean) => void;
}

export function MobileMenuDrawer({ config, isOpen, onClose }: MobileMenuDrawerProps) {
    const pathname = usePathname();
    const [openCollapsible, setOpenCollapsible] = React.useState<string | null>(null);

    // Filter main items - we might want to show ALL items here or just the ones not in bottom bar
    // Standard pattern: Show everything for completeness, or just the "More" items.
    // Let's show everything but styled like the "Dark List" screenshot.

    return (
        <Drawer open={isOpen} onOpenChange={onClose}>
            <DrawerContent className="bg-black text-white border-zinc-800 h-[85vh]">
                <div className="flex flex-col h-full overflow-y-auto px-4 py-6">

                    {/* Header with Close Button */}
                    <div className="flex justify-between items-center mb-6">
                        <span className="text-lg font-semibold">Menu</span>
                        <DrawerClose asChild>
                            <Button variant="ghost" size="icon" className="rounded-full hover:bg-zinc-800 text-white">
                                <IconX className="w-5 h-5" />
                            </Button>
                        </DrawerClose>
                    </div>

                    {/* Navigation List */}
                    <div className="flex flex-col gap-1">
                        {/* Main Nav */}
                        {config.navMain.map((item) => {
                            const Icon = item.icon;
                            // Check if item has children
                            const hasChildren = item.items && item.items.length > 0;
                            const isActive = pathname.startsWith(item.url);
                            const isOpen = openCollapsible === item.title;

                            if (hasChildren) {
                                return (
                                    <Collapsible
                                        key={item.title}
                                        open={isOpen}
                                        onOpenChange={(open) => setOpenCollapsible(open ? item.title : null)}
                                    >
                                        <div className="flex items-center justify-between py-3 px-2 rounded-lg active:bg-zinc-900">
                                            <Link
                                                href={item.url}
                                                onClick={() => onClose(false)}
                                                className="flex items-center gap-3 flex-1"
                                            >
                                                {Icon && <Icon className="w-5 h-5 text-zinc-400" />}
                                                <span className="text-base font-medium">{item.title}</span>
                                            </Link>
                                            <CollapsibleTrigger asChild>
                                                <button className="p-1">
                                                    <IconChevronDown className={cn("w-5 h-5 text-zinc-500 transition-transform", isOpen && "rotate-180")} />
                                                </button>
                                            </CollapsibleTrigger>
                                        </div>
                                        <CollapsibleContent className="pl-10 space-y-2 py-1">
                                            {item.items!.map(sub => (
                                                <Link
                                                    key={sub.title}
                                                    href={sub.url}
                                                    onClick={() => onClose(false)}
                                                    className="block py-2 text-sm text-zinc-400 hover:text-white"
                                                >
                                                    {sub.title}
                                                </Link>
                                            ))}
                                        </CollapsibleContent>
                                    </Collapsible>
                                );
                            }

                            return (
                                <Link
                                    key={item.title}
                                    href={item.url}
                                    onClick={() => onClose(false)}
                                    className={cn(
                                        "flex items-center gap-3 py-3 px-2 rounded-lg active:bg-zinc-900",
                                        isActive ? "text-white" : "text-zinc-300"
                                    )}
                                >
                                    {Icon && <Icon className={cn("w-5 h-5", isActive ? "text-white" : "text-zinc-400")} />}
                                    <span className="text-base font-medium">{item.title}</span>
                                </Link>
                            );
                        })}

                        {/* Sales Channels / Nav Sections */}
                        {config.navSections && config.navSections.length > 0 && (
                            <>
                                <div className="my-4 h-px bg-zinc-900" />
                                {config.navSections.map((section) => (
                                    <div key={section.label} className="mb-2">
                                        {/* Section Label */}
                                        <span className="block text-xs font-semibold text-zinc-500 uppercase tracking-wider px-2 mb-2">
                                            {section.label}
                                        </span>

                                        {/* Section Items */}
                                        {section.items.map((sectionItem) => {
                                            const SectionIcon = sectionItem.icon;
                                            const hasSubItems = sectionItem.items && sectionItem.items.length > 0;
                                            const isOpen = openCollapsible === sectionItem.name;

                                            if (hasSubItems) {
                                                return (
                                                    <Collapsible
                                                        key={sectionItem.name}
                                                        open={isOpen}
                                                        onOpenChange={(open) => setOpenCollapsible(open ? sectionItem.name : null)}
                                                    >
                                                        <div className="flex items-center justify-between py-3 px-2 rounded-lg active:bg-zinc-900">
                                                            <div className="flex items-center gap-3 flex-1">
                                                                {SectionIcon && <SectionIcon className="w-5 h-5 text-zinc-400" />}
                                                                <span className="text-base font-medium text-zinc-300">{sectionItem.name}</span>
                                                            </div>
                                                            <CollapsibleTrigger asChild>
                                                                <button className="p-1">
                                                                    <IconChevronDown className={cn("w-5 h-5 text-zinc-500 transition-transform", isOpen && "rotate-180")} />
                                                                </button>
                                                            </CollapsibleTrigger>
                                                        </div>
                                                        <CollapsibleContent className="pl-10 space-y-2 py-1">
                                                            {sectionItem.items!.map(sub => (
                                                                <Link
                                                                    key={sub.title}
                                                                    href={sub.url}
                                                                    onClick={() => onClose(false)}
                                                                    className="block py-2 text-sm text-zinc-400 hover:text-white"
                                                                >
                                                                    {sub.title}
                                                                </Link>
                                                            ))}
                                                        </CollapsibleContent>
                                                    </Collapsible>
                                                );
                                            }

                                            return (
                                                <Link
                                                    key={sectionItem.name}
                                                    href={sectionItem.url}
                                                    onClick={() => onClose(false)}
                                                    className="flex items-center gap-3 py-3 px-2 rounded-lg active:bg-zinc-900 text-zinc-300"
                                                >
                                                    {SectionIcon && <SectionIcon className="w-5 h-5 text-zinc-400" />}
                                                    <span className="text-base font-medium">{sectionItem.name}</span>
                                                </Link>
                                            );
                                        })}
                                    </div>
                                ))}
                            </>
                        )}

                        {/* Divider */}
                        <div className="my-4 h-px bg-zinc-900" />

                        {/* Secondary/Settings */}
                        {config.navSecondary.map((item) => {
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.title}
                                    href={item.url}
                                    onClick={() => onClose(false)}
                                    className="flex items-center gap-3 py-3 px-2 rounded-lg active:bg-zinc-900 text-zinc-300"
                                >
                                    {Icon && <Icon className="w-5 h-5 text-zinc-400" />}
                                    <span className="text-base font-medium">{item.title}</span>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </DrawerContent>
        </Drawer>
    );
}
