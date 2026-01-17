import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming utils exists, otherwise I'll stub it

interface BreadcrumbsProps {
    items: {
        label: string;
        href?: string;
    }[];
    className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
    return (
        <nav className={cn("flex items-center text-sm text-muted-foreground", className)}>
            {items.map((item, index) => {
                const isLast = index === items.length - 1;
                return (
                    <div key={index} className="flex items-center">
                        {index > 0 && <ChevronRight className="h-4 w-4 mx-2" />}
                        {item.href && !isLast ? (
                            <Link to={item.href} className="hover:text-foreground transition-colors">
                                {item.label}
                            </Link>
                        ) : (
                            <span className={cn("font-medium text-foreground", isLast && "truncate max-w-[200px] sm:max-w-none")}>
                                {item.label}
                            </span>
                        )}
                    </div>
                );
            })}
        </nav>
    );
}
