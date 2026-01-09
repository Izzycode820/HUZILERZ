'use client';

import React, { useTransition } from 'react';
import { useRouter, usePathname, useParams } from 'next/navigation';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
    IconHome,
    IconShoppingCart,
    IconPackage,
    IconUsers,
    IconMenu2,
} from '@tabler/icons-react';

// Hard-coded nav items for consistent animation
// These are the 4 main shortcuts + menu button
const NAV_ITEMS = [
    { key: 'home', label: 'Home', icon: IconHome, pathSegment: 'store' },
    { key: 'orders', label: 'Orders', icon: IconShoppingCart, pathSegment: 'store/orders' },
    { key: 'products', label: 'Products', icon: IconPackage, pathSegment: 'store/products' },
    { key: 'customers', label: 'Customers', icon: IconUsers, pathSegment: 'store/customers' },
] as const;

interface MobileBottomNavProps {
    onMenuClick: () => void;
}

export function MobileBottomNav({ onMenuClick }: MobileBottomNavProps) {
    const router = useRouter();
    const pathname = usePathname();
    const params = useParams();
    const [isPending, startTransition] = useTransition();

    // Get workspace ID from params (or extract from pathname)
    const workspaceId = params?.workspace_id as string || '';

    // Build URLs from workspace ID
    const getUrl = (pathSegment: string) => `/workspace/${workspaceId}/${pathSegment}`;

    // Determine active index based on current pathname
    const getActiveIndex = (): number => {
        // Check each item - more specific paths first
        for (let i = NAV_ITEMS.length - 1; i >= 0; i--) {
            const item = NAV_ITEMS[i];
            const itemUrl = getUrl(item.pathSegment);

            // Exact match
            if (pathname === itemUrl) return i;

            // Child path match (e.g., /store/orders/123 matches /store/orders)
            // But NOT /store matching /store/orders (Home shouldn't match Orders)
            if (i !== 0 && pathname.startsWith(itemUrl + '/')) return i;
        }

        // Default to Home if we're in the store workspace
        if (pathname.includes('/store')) return 0;

        return -1;
    };

    const activeIndex = getActiveIndex();

    // Handle navigation with SPA-like transition
    const handleNavigation = (index: number, pathSegment: string) => {
        const url = getUrl(pathSegment);

        // Start transition for SPA-like feel
        startTransition(() => {
            router.push(url);
        });
    };

    return (
        <div className="fixed bottom-4 left-0 right-0 z-50 flex justify-center px-2 md:hidden pointer-events-none">
            <nav
                className="relative flex items-center justify-between w-full max-w-md rounded-[2rem] bg-white dark:bg-zinc-900 border border-black/5 dark:border-white/10 p-2 shadow-[0_8px_30px_rgb(0,0,0,0.12)] pointer-events-auto"
            >
                {/* Nav Items with shared layout animation */}
                {NAV_ITEMS.map((item, index) => {
                    const isActive = index === activeIndex;
                    const Icon = item.icon;

                    return (
                        <button
                            key={item.key}
                            onClick={() => handleNavigation(index, item.pathSegment)}
                            className={cn(
                                "relative z-10 flex items-center justify-center gap-2 rounded-full h-12 px-4 transition-colors duration-200 outline-none",
                                isActive
                                    ? "text-black dark:text-white"
                                    : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300",
                                isPending && "opacity-70"
                            )}
                        >
                            {/* Animated background capsule */}
                            {isActive && (
                                <motion.div
                                    layoutId="nav-capsule"
                                    className="absolute inset-0 bg-black/5 dark:bg-white/10 rounded-full"
                                    initial={false}
                                    transition={{
                                        type: "spring",
                                        stiffness: 500,
                                        damping: 35,
                                    }}
                                />
                            )}

                            <Icon
                                className={cn(
                                    "relative z-10 flex-shrink-0 transition-all duration-200",
                                    isActive ? "w-5 h-5 stroke-[2]" : "w-6 h-6 stroke-[1.5]"
                                )}
                            />

                            {/* Text - only show for active tab with animation */}
                            <AnimatePresence mode="wait">
                                {isActive && (
                                    <motion.span
                                        key={item.key}
                                        initial={{ width: 0, opacity: 0 }}
                                        animate={{ width: 'auto', opacity: 1 }}
                                        exit={{ width: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="relative z-10 text-sm font-semibold whitespace-nowrap overflow-hidden"
                                    >
                                        {item.label}
                                    </motion.span>
                                )}
                            </AnimatePresence>
                        </button>
                    );
                })}

                {/* Separator */}
                <div className="h-6 w-px bg-zinc-200 dark:bg-zinc-800 mx-1" />

                {/* Menu (Hamburger) */}
                <button
                    className="relative z-10 flex items-center justify-center rounded-full w-12 h-12 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 active:scale-95 outline-none transition-colors"
                    onClick={onMenuClick}
                >
                    <IconMenu2 className="w-6 h-6 stroke-[1.5]" />
                </button>
            </nav>
        </div>
    );
}
