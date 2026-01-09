'use client';

import React from 'react';
import { useTheme } from '@/utils/ThemeContext';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger
} from '@/components/shadcn-ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/shadcn-ui/avatar';
import { Button } from '@/components/shadcn-ui/button';
import { IconSettings, IconSun, IconMoon } from '@tabler/icons-react';
import type { UserConfig } from '@/types/workspace/dashboard-ui/workspace';

interface MobileHeaderProps {
    user: UserConfig;
}

export function MobileHeader({ user }: MobileHeaderProps) {
    const { setTheme } = useTheme();

    return (
        <header className="sticky top-0 z-40 w-full border-b bg-background/80 backdrop-blur-md md:hidden">
            <div className="flex h-14 items-center justify-between px-4">
                {/* Left: User Avatar */}
                <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8 transition-transform active:scale-95">
                        <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                            {user.name.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                    <span className="font-semibold text-sm">My Store</span>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-1">
                    {/* Theme Dropdown (Compact) */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                                <IconSun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                                <IconMoon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                                <span className="sr-only">Toggle theme</span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-[120px] min-w-0">
                            <DropdownMenuItem onClick={() => setTheme('light')} className="gap-2 text-xs">
                                <IconSun className="h-3.5 w-3.5" /> Light
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => setTheme('dark')} className="gap-2 text-xs">
                                <IconMoon className="h-3.5 w-3.5" /> Dark
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Settings Button */}
                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                        <IconSettings className="h-5 w-5 opacity-70" />
                        <span className="sr-only">Settings</span>
                    </Button>
                </div>
            </div>
        </header>
    );
}
