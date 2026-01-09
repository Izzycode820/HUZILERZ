'use client';

import * as React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from './Button';

interface AccordionItemProps {
    title: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
    className?: string;
}

export function AccordionItem({ title, children, defaultOpen = false, className }: AccordionItemProps) {
    const [isOpen, setIsOpen] = React.useState(defaultOpen);

    return (
        <div className={cn("border-b border-border py-4", className)}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className="flex w-full items-center justify-between py-1 text-sm font-medium hover:underline"
            >
                {title}
                <ChevronDown
                    className={cn("h-4 w-4 transition-transform duration-200", isOpen ? "rotate-180" : "")}
                />
            </button>
            {isOpen && (
                <div className="pt-4 animate-in slide-in-from-top-2 fade-in duration-200">
                    {children}
                </div>
            )}
        </div>
    );
}
