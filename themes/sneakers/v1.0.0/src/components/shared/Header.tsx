'use client';

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, ShoppingBag, User, X } from 'lucide-react';
import { Button } from '../shadcn-ui/button';
import { useSession } from '@/lib/session/SessionProvider';
import { useQuery } from '@apollo/client/react';
import { GetCartDocument } from '@/services/cart/__generated__/get-cart.generated';
import { cn } from '@/lib/utils';
import { SearchInput } from '../search/SearchInput';

export function Header() {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const { pathname } = useLocation();
    const { guestSessionId } = useSession();

    // Get cart data from cache only - no network requests to prevent re-renders
    const { data: cartData } = useQuery(GetCartDocument, {
        variables: { sessionId: guestSessionId || '' },
        skip: !guestSessionId,
        fetchPolicy: 'cache-only', // Only read from cache, don't trigger network requests
    });

    const cartItemCount = cartData?.cart?.itemCount || 0;

    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

    const navLinks = [
        { label: 'Home', href: '/' },
        { label: 'Products', href: '/products' },
        { label: 'About', href: '/about' },
        { label: 'Track Order', href: '/track-order' },
    ];

    return (
        <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto flex h-20 items-center justify-between px-4">
                {/* Mobile Menu Trigger */}
                <div className="flex items-center md:hidden">
                    <Button variant="ghost" size="icon" onClick={toggleMobileMenu} aria-label="Open menu" className="h-11 w-11">
                        {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                    </Button>
                </div>

                {/* Logo */}
                <div className="flex items-center gap-2">
                    <Link to="/" className="text-2xl font-bold tracking-tighter sm:text-3xl uppercase">
                        SNEAKERS
                    </Link>
                </div>

                {/* Desktop Navigation & Search */}
                <div className="hidden md:flex md:flex-1 md:items-center md:gap-6 md:px-8">
                    <nav className="flex items-center gap-6">
                        {navLinks.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={cn(
                                    'text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide',
                                    pathname === link.href ? 'text-foreground font-bold' : 'text-muted-foreground'
                                )}
                            >
                                {link.label}
                            </Link>
                        ))}
                    </nav>

                    {/* Desktop Search */}
                    <SearchInput />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3">
                    <Link to="/login">
                        <Button variant="ghost" size="icon" aria-label="Account" className="h-11 w-11">
                            <User className="h-6 w-6" />
                        </Button>
                    </Link>

                    <Link to="/cart">
                        <Button variant="ghost" size="icon" className="relative group h-11 w-11" aria-label="Cart" id="cart-button">
                            <ShoppingBag className="h-6 w-6" />
                            {cartItemCount > 0 && (
                                <span className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[11px] text-primary-foreground font-bold">
                                    {cartItemCount}
                                </span>
                            )}
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Mobile Menu */}
            {isMobileMenuOpen && (
                <div className="absolute top-16 left-0 w-full bg-background border-b border-border shadow-2xl md:hidden z-50 animate-in slide-in-from-top-2 duration-200">
                    <div className="flex flex-col p-6 gap-4">
                        {/* Mobile Navigation */}
                        <nav className="flex flex-col gap-4">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    className="text-lg font-bold uppercase tracking-wide hover:text-muted-foreground transition-colors"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    {link.label}
                                </Link>
                            ))}
                        </nav>
                    </div>
                </div>
            )}
        </header>
    );
}
