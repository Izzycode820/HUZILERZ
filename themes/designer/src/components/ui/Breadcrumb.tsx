"use client";

import Link from "next/link";
import { Home, ChevronRight } from "lucide-react";
import { usePathname } from "next/navigation";

interface BreadcrumbProps {
    title: string;
    links?: { label: string; href: string }[];
}

export default function Breadcrumb({ title, links = [] }: BreadcrumbProps) {
    return (
        <div className="py-8 bg-white">
            <div className="container mx-auto px-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between">
                    <div className="flex items-center text-sm text-gray-500 space-x-2">
                        <Link href="/" className="hover:text-primary flex items-center">
                            <Home size={14} className="mr-1" /> Home
                        </Link>
                        {links.map((link, index) => (
                            <div key={index} className="flex items-center">
                                <ChevronRight size={14} className="mx-1" />
                                <Link href={link.href} className="hover:text-primary">
                                    {link.label}
                                </Link>
                            </div>
                        ))}
                        <ChevronRight size={14} className="mx-1" />
                        <span className="text-secondary font-medium">{title}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
