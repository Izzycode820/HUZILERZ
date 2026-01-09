'use client';

import { useState } from 'react';
import { Button } from '../../shadcn-ui/button';
import { Menu, ShoppingBag, Search, X, User } from 'lucide-react';

interface NavLink {
  label: string;
  href: string;
}

interface Category {
  id: string;
  name: string;
  slug: string;
}

interface NavBarProps {
  storeName: string;
  logoUrl?: string;
  links: NavLink[];
  alignment?: 'left' | 'center' | 'right';
  showSearch?: boolean;
  showCart?: boolean;
  categories?: Category[];
}

export default function NavBar({
  storeName,
  logoUrl,
  links = [],
  alignment = 'left',
  showSearch = true,
  showCart = true,
  categories = [],
}: NavBarProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const alignmentClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  };

  const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Mobile Menu Trigger */}
          <div className="flex items-center md:hidden">
            <Button variant="ghost" size="icon" onClick={toggleMobileMenu} aria-label="Open menu">
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>

          {/* Logo */}
          <div className="flex items-center gap-2">
            <a href="/" className="flex items-center gap-2">
              {logoUrl ? (
                <img src={logoUrl} alt={storeName} className="h-8 w-auto" />
              ) : (
                <span className="text-xl font-bold tracking-tighter uppercase">{storeName}</span>
              )}
            </a>
          </div>

          {/* Desktop Navigation */}
          <div className={`hidden md:flex flex-1 mx-8 ${alignmentClasses[alignment]}`}>
            <div className="flex items-center gap-8">
              <a
                href="/"
                className="text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide"
              >
                Home
              </a>

              {/* Dynamic Shop Dropdown or Menu */}
              {categories.length > 0 ? (
                <div className="relative group">
                  <button className="text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide flex items-center gap-1">
                    Shop
                  </button>
                  <div className="absolute top-full left-0 mt-2 w-48 bg-white border border-gray-200 shadow-lg rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    <div className="py-2">
                      <a
                        href="/products"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-black uppercase tracking-wide"
                      >
                        All Products
                      </a>
                      {categories.map((cat) => (
                        <a
                          key={cat.id}
                          href={`/products?collection=${cat.slug}`}
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-black uppercase tracking-wide"
                        >
                          {cat.name}
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <a
                  href="/products"
                  className="text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide"
                >
                  Shop
                </a>
              )}

              {/* Other Static Links */}
              {links.filter(l => l.label !== 'Shop' && l.label !== 'Home').map((link, index) => (
                <a
                  key={index}
                  href={link.href}
                  className="text-sm font-medium transition-colors hover:text-primary uppercase tracking-wide"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {showSearch && (
              <Button variant="ghost" size="icon" aria-label="Search">
                <Search className="h-5 w-5" />
              </Button>
            )}

            <a href="/login" className="hidden sm:inline-flex">
              <Button variant="ghost" size="icon" aria-label="Account">
                <User className="h-5 w-5 hover:fill-black transition-colors" />
              </Button>
            </a>

            {showCart && (
              <a href="/cart">
                <Button variant="ghost" size="icon" className="relative group" aria-label="Cart">
                  <ShoppingBag className="h-5 w-5 group-hover:fill-black transition-colors" />
                  <span className="absolute right-0 top-0 flex h-4 w-4 items-center justify-center rounded-full bg-black text-[10px] text-white">
                    0
                  </span>
                </Button>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Menu - Absolute Overlay */}
      {isMobileMenuOpen && (
        <div className="absolute top-16 left-0 w-full bg-background border-b border-border shadow-2xl md:hidden z-50 animate-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col p-6 gap-6">
            <nav className="flex flex-col space-y-4">
              <a
                href="/"
                className="text-lg font-bold uppercase tracking-wide hover:text-gray-600 transition-colors"
              >
                Home
              </a>

              {categories.length > 0 && (
                <div className="space-y-3 pl-2 border-l-2 border-gray-100">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Collections</p>
                  {categories.map((cat) => (
                    <a
                      key={cat.id}
                      href={`/products?collection=${cat.slug}`}
                      className="block text-md font-medium text-gray-800 hover:text-black uppercase tracking-wide"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      {cat.name}
                    </a>
                  ))}
                </div>
              )}

              {links.filter(l => l.label !== 'Shop' && l.label !== 'Home').map((link, index) => (
                <a
                  key={index}
                  href={link.href}
                  className="text-lg font-bold uppercase tracking-wide hover:text-gray-600 transition-colors"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.label}
                </a>
              ))}
            </nav>
            <hr className="border-gray-200" />
            <div className="flex flex-col gap-4">
              <a href="/account" className="flex items-center gap-2 text-lg font-medium text-gray-500 hover:text-black">
                <User className="h-5 w-5" /> Account
              </a>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
