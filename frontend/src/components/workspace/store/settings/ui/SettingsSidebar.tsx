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
  Crown
} from 'lucide-react';

const settingsNavItems = [
  {
    label: 'General',
    href: '/general',
    icon: Settings,
  },
  {
    label: 'Plan',
    href: '/plan',
    icon: Crown,
  },
  {
    label: 'Billing',
    href: '/billing',
    icon: Receipt,
  },
  {
    label: 'Domains',
    href: '/domains',
    icon: Globe,
  },
  {
    label: 'Shipping',
    href: '/shipping',
    icon: Truck,
  },
  {
    label: 'Payments',
    href: '/payments',
    icon: CreditCard,
  },
  {
    label: 'Notifications',
    href: '/notifications',
    icon: Bell,
  },
  {
    label: 'Team',
    href: '/staff',
    icon: Users,
  },
  
];

export function SettingsSidebar() {
  const params = useParams();
  const pathname = usePathname();
  const workspaceId = params.workspace_id as string;
  const baseUrl = `/workspace/${workspaceId}/store/settings`;

  return (
    <aside className="w-48 flex-shrink-0">
      <nav className="space-y-1">
        {settingsNavItems.map((item) => {
          const href = `${baseUrl}${item.href}`;
          const isActive = pathname.startsWith(href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors',
                'hover:bg-muted',
                isActive
                  ? 'bg-muted text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
