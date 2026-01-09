import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '../ui/Button';

interface BreadcrumbItem {
    label: string;
    href?: string;
}

interface BreadcrumbsProps {
    items: BreadcrumbItem[];
    className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
    return (
        <nav aria-label="Breadcrumb" className={cn("flex", className)}>
            <div className="flex items-center space-x-2">
                <Link
                    href="/"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                >
                    <Home className="h-4 w-4" />
                    <span className="sr-only">Home</span>
                </Link>

                {items.map((item, index) => (
                    <div key={index} className="flex items-center">
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        {item.href ? (
                            <Link
                                href={item.href}
                                className="ml-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                            >
                                {item.label}
                            </Link>
                        ) : (
                            <span className="ml-2 text-sm font-medium text-foreground">
                                {item.label}
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </nav>
    );
}
