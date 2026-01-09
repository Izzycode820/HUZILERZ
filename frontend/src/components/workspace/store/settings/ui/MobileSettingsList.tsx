'use client';

import { useParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
    Globe,
    Truck,
    CreditCard,
    Bell,
    Users,
    Settings,
    Receipt,
    Crown,
    ChevronRight
} from 'lucide-react';

// Setting navigation items grouped by section
const settingsSections = [
    {
        title: 'Store settings',
        items: [
            {
                label: 'Store details',
                description: 'Basic store information',
                href: '/general',
                icon: Settings,
            },
        ],
    },
    {
        title: 'Plan and Permissions',
        items: [
            {
                label: 'Plan',
                description: 'Manage your subscription',
                href: '/plan',
                icon: Crown,
            },
            {
                label: 'Billing',
                description: 'Payment and invoices',
                href: '/billing',
                icon: Receipt,
            },
            {
                label: 'Staff',
                description: 'Team members and permissions',
                href: '/staff',
                icon: Users,
            },
        ],
    },
    {
        title: 'Checkout',
        items: [
            {
                label: 'Payments',
                description: 'Accepted payment methods',
                href: '/payments',
                icon: CreditCard,
            },
            {
                label: 'Shipping and delivery',
                description: 'Shipping rates and zones',
                href: '/shipping',
                icon: Truck,
            },
        ],
    },
    {
        title: 'Store',
        items: [
            {
                label: 'Domains',
                description: 'Custom and Shopify domains',
                href: '/domains',
                icon: Globe,
            },
            {
                label: 'Notifications',
                description: 'Email and SMS notifications',
                href: '/notifications',
                icon: Bell,
            },
        ],
    },
];

export function MobileSettingsList() {
    const params = useParams();
    const pathname = usePathname();
    const workspaceId = params.workspace_id as string;
    const baseUrl = `/workspace/${workspaceId}/store/settings`;

    return (
        <div className="flex flex-col gap-6 pb-24">
            {settingsSections.map((section, sectionIndex) => (
                <div key={sectionIndex} className="flex flex-col">
                    {/* Section Title */}
                    <h2 className="text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider px-1 mb-2">
                        {section.title}
                    </h2>

                    {/* Settings Cards */}
                    <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
                        {section.items.map((item, itemIndex) => {
                            const href = `${baseUrl}${item.href}`;
                            const isActive = pathname.startsWith(href);
                            const Icon = item.icon;
                            const isLast = itemIndex === section.items.length - 1;

                            return (
                                <Link
                                    key={item.href}
                                    href={href}
                                    className={cn(
                                        'flex items-center gap-4 px-4 py-4 transition-colors active:bg-zinc-100 dark:active:bg-zinc-800',
                                        !isLast && 'border-b border-zinc-100 dark:border-zinc-800'
                                    )}
                                >
                                    {/* Icon */}
                                    <div className={cn(
                                        'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                                        isActive
                                            ? 'bg-primary/10 text-primary'
                                            : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                                    )}>
                                        <Icon className="h-5 w-5" />
                                    </div>

                                    {/* Text */}
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-sm text-zinc-900 dark:text-zinc-100">
                                            {item.label}
                                        </div>
                                        <div className="text-xs text-zinc-500 dark:text-zinc-400 truncate">
                                            {item.description}
                                        </div>
                                    </div>

                                    {/* Chevron */}
                                    <ChevronRight className="flex-shrink-0 h-5 w-5 text-zinc-400" />
                                </Link>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
}
