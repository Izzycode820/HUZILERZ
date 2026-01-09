'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, Search, ShoppingBag, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { categories } from '@/lib/mock-data/categories';
import { cn } from '../ui/Button';

export function Header() {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const pathname = usePathname();

    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

    return (
        <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-md">
            <div className="container mx-auto flex h-16 items-center justify-between px-4">
                {/* Mobile Menu Trigger */}
                <div className="flex items-center md:hidden">
                    <Button variant="ghost" size="icon" onClick={toggleMobileMenu} aria-label="Open menu">
                        <Menu className="h-5 w-5" />
                    </Button>
                </div>

                {/* Logo */}
                <div className="flex items-center gap-2">
                    <Link href="/" className="text-xl font-bold tracking-tighter sm:text-2xl">
                        MERCHFLOW
                    </Link>
                </div>

                {/* Desktop Navigation */}
                <nav className="hidden items-center gap-6 md:flex">
                    {categories.map((category) => (
                        <Link
                            key={category.id}
                            href={`/shop/${category.slug}`}
                            className={cn(
                                "text-sm font-medium transition-colors hover:text-primary",
                                pathname === `/shop/${category.slug}` ? "text-primary" : "text-muted-foreground"
                            )}
                        >
                            {category.name}
                        </Link>
                    ))}
                </nav>

                {/* Actions */}
                <div className="flex items-center gap-2">
                    <div className="relative hidden sm:block">
                        {isSearchOpen ? (
                            <div className="absolute right-0 top-1/2 flex w-64 -translate-y-1/2 items-center gap-2">
                                <Input
                                    autoFocus
                                    placeholder="Search products..."
                                    className="h-9"
                                    onBlur={() => setIsSearchOpen(false)}
                                />
                            </div>
                        ) : (
                            <Button variant="ghost" size="icon" onClick={() => setIsSearchOpen(true)} aria-label="Search">
                                <Search className="h-5 w-5" />
                            </Button>
                        )}
                    </div>

                    <Link href="/cart">
                        <Button variant="ghost" size="icon" className="relative" aria-label="Cart">
                            <ShoppingBag className="h-5 w-5" />
                            <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] text-primary-foreground">
                                0
                            </span>
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Mobile Menu Overlay */}
            {isMobileMenuOpen && (
                <div className="fixed inset-0 z-50 bg-background md:hidden">
                    <div className="flex h-16 items-center justify-between border-b px-4">
                        <span className="text-lg font-bold">Menu</span>
                        <Button variant="ghost" size="icon" onClick={toggleMobileMenu}>
                            <X className="h-5 w-5" />
                        </Button>
                    </div>
                    <div className="flex flex-col p-4">
                        <form className="mb-6 relative" onSubmit={(e) => e.preventDefault()}>
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input placeholder="Search..." className="pl-9" />
                        </form>
                        <nav className="flex flex-col space-y-4">
                            {categories.map((category) => (
                                <Link
                                    key={category.id}
                                    href={`/shop/${category.slug}`}
                                    className="text-lg font-medium"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    {category.name}
                                </Link>
                            ))}
                            <hr className="my-2 border-border" />
                            <Link href="/account" className="text-lg font-medium" onClick={() => setIsMobileMenuOpen(false)}>
                                Account
                            </Link>
                        </nav>
                    </div>
                </div>
            )}
        </header>
    );
}
