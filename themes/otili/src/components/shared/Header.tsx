'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, Search, ShoppingBag, User, X } from 'lucide-react';
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
        <header className="sticky top-0 z-40 w-full border-b border-border bg-background">
            <div className="container mx-auto flex h-16 items-center justify-between px-4">
                {/* Mobile Menu Trigger */}
                <div className="flex items-center md:hidden">
                    <Button variant="ghost" size="icon" onClick={toggleMobileMenu} aria-label="Open menu">
                        {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                    </Button>
                </div>

                {/* Logo */}
                <div className="flex items-center gap-2">
                    <Link href="/" className="text-xl font-bold tracking-tighter sm:text-2xl uppercase">
                        Merchflow
                    </Link>
                </div>

                {/* Desktop Navigation */}
                <nav className="hidden items-center gap-6 md:flex">
                    <Link
                        href="/"
                        className={cn(
                            "text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide",
                            pathname === "/" ? "text-foreground font-bold" : "text-muted-foreground"
                        )}
                    >
                        Home
                    </Link>
                    {categories.map((category) => (
                        <Link
                            key={category.id}
                            href={`/shop/${category.slug}`}
                            className={cn(
                                "text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide",
                                pathname === `/shop/${category.slug}` ? "text-foreground font-bold" : "text-muted-foreground"
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
                            <div className="absolute right-0 top-1/2 flex w-64 -translate-y-1/2 items-center gap-2 animate-in fade-in slide-in-from-right-4">
                                <Input
                                    autoFocus
                                    placeholder="Search products..."
                                    className="h-9 rounded-none border-gray-300 focus-visible:ring-black"
                                    onBlur={() => setIsSearchOpen(false)}
                                />
                            </div>
                        ) : (
                            <Button variant="ghost" size="icon" onClick={() => setIsSearchOpen(true)} aria-label="Search">
                                <Search className="h-5 w-5" />
                            </Button>
                        )}
                    </div>

                    <Link href="/login">
                        <Button variant="ghost" size="icon" aria-label="Account">
                            <User className="h-5 w-5 hover:fill-black transition-colors" />
                        </Button>
                    </Link>

                    <Link href="/cart">
                        <Button variant="ghost" size="icon" className="relative group" aria-label="Cart">
                            <ShoppingBag className="h-5 w-5 group-hover:fill-black transition-colors" />
                            <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-black text-[10px] text-white">
                                0
                            </span>
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Mobile Menu - Standard Absolute Positioning (No Portal) */}
            {isMobileMenuOpen && (
                <div className="absolute top-16 left-0 w-full bg-background border-b border-border shadow-2xl md:hidden z-50 animate-in slide-in-from-top-2 duration-200">
                    <div className="flex flex-col p-6 gap-4">
                        <form className="relative" onSubmit={(e) => e.preventDefault()}>
                            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search products..."
                                className="h-10 pl-9 rounded-none border-gray-300 focus-visible:ring-black"
                            />
                        </form>
                        <nav className="flex flex-col space-y-4">
                            {categories.map((category) => (
                                <Link
                                    key={category.id}
                                    href={`/shop/${category.slug}`}
                                    className="text-lg font-bold uppercase tracking-wide hover:text-gray-600 transition-colors"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    {category.name}
                                </Link>
                            ))}
                            <hr className="border-gray-200" />
                            <Link
                                href="/account"
                                className="text-lg font-medium text-gray-500 hover:text-black transition-colors"
                                onClick={() => setIsMobileMenuOpen(false)}
                            >
                                Account
                            </Link>
                        </nav>
                    </div>
                </div>
            )}
        </header>
    );
}
