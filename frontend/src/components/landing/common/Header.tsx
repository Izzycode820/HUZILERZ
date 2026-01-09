/**
 * Landing Page Header - Modern SaaS Design
 * Bigger, bolder, with auth-aware navigation
 * Features: h-20 height, text-base nav, rounded-full buttons, user avatar
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Menu, ChevronDown, LogOut, Settings, User } from 'lucide-react';
import { Button } from '@/components/shadcn-ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/shadcn-ui/sheet';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { HEADER_NAVIGATION, AUTH_ROUTES } from '@/routes';
import { useAuth } from '@/hooks/authentication/useAuth';

interface HeaderProps {
  className?: string;
}

export default function Header({ className }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated, user, logout, isLoading } = useAuth();

  // Generate user initials for avatar
  const userInitials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
    : '';

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className={cn(
      "absolute top-0 left-0 right-0 z-50",
      className
    )}>
      {/* Header content container */}
      <div className="h-20 flex items-center justify-between px-6 md:px-12 lg:px-16">
        {/* 1. Logo - Bigger */}
        <Link href="/" className="flex items-center space-x-2 group">
          <div className="font-display text-2xl font-bold tracking-tighter text-white transition-colors group-hover:text-huzilerz-lime">
            HUZILERZ CAMP
          </div>
        </Link>

        {/* 2. Center Links (Desktop) - Bigger text with underline hover */}
        <nav className="hidden md:flex items-center gap-10 text-lg font-medium text-gray-300">
          {HEADER_NAVIGATION.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="relative py-2 transition-colors hover:text-white group"
            >
              {item.label}
              {/* Underline effect */}
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-white transition-all duration-300 group-hover:w-full" />
            </Link>
          ))}
        </nav>

        {/* 3. Right Actions (Desktop) - Auth aware */}
        <div className="hidden md:flex items-center gap-4">
          {isLoading ? (
            // Loading skeleton
            <div className="w-24 h-10 bg-white/10 rounded-full animate-pulse" />
          ) : isAuthenticated && user ? (
            // Authenticated: Show user avatar dropdown
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 text-white hover:bg-white/10 rounded-full px-3 py-2 h-12 border border-white/30 hover:border-white/50"
                >
                  {/* Avatar circle */}
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-huzilerz-lime to-huzilerz-lime/60 flex items-center justify-center text-black font-semibold text-sm ring-2 ring-white/40">
                    {userInitials || <User className="w-4 h-4" />}
                  </div>
                  <span className="text-sm font-medium hidden lg:block">
                    {user.first_name}
                  </span>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-huzilerz-black border-gray-800">
                <div className="px-3 py-2 border-b border-gray-800">
                  <p className="text-sm font-medium text-white">
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {user.email}
                  </p>
                </div>
                <DropdownMenuItem asChild className="cursor-pointer text-gray-300 hover:text-white hover:bg-white/10">
                  <Link href="/workspace" className="flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Dashboard
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild className="cursor-pointer text-gray-300 hover:text-white hover:bg-white/10">
                  <Link href="/workspace/settings" className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-gray-800" />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="cursor-pointer text-red-400 hover:text-red-300 hover:bg-red-500/10"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            // Not authenticated: Show Sign In / Get Started
            <>
              <Button
                variant="ghost"
                asChild
                className="text-white hover:bg-white/10 rounded-full px-6 h-11 border border-white/20 hover:border-white/40 transition-all"
              >
                <Link href={AUTH_ROUTES.LOGIN}>Sign In</Link>
              </Button>
              <Button
                asChild
                className="rounded-full bg-white text-black hover:bg-huzilerz-lime px-6 h-11 font-semibold transition-all hover:scale-105"
              >
                <Link href={AUTH_ROUTES.SIGNUP}>Get Started</Link>
              </Button>
            </>
          )}
        </div>

        {/* Mobile Menu */}
        <div className="ml-auto md:hidden">
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-white hover:bg-white/10 w-11 h-11">
                <Menu className="h-6 w-6" />
                <span className="sr-only">Open menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="bg-huzilerz-black text-white border-l-gray-800 w-80">
              <div className="flex flex-col space-y-6 mt-8">
                {/* Mobile User Info (if authenticated) */}
                {isAuthenticated && user && (
                  <div className="flex items-center gap-3 pb-4 border-b border-gray-800">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-huzilerz-lime to-huzilerz-lime/60 flex items-center justify-center text-black font-semibold">
                      {userInitials || <User className="w-5 h-5" />}
                    </div>
                    <div>
                      <p className="font-medium text-white">
                        {user.first_name} {user.last_name}
                      </p>
                      <p className="text-sm text-gray-400 truncate">
                        {user.email}
                      </p>
                    </div>
                  </div>
                )}

                {/* Mobile Navigation */}
                <nav className="space-y-1">
                  {HEADER_NAVIGATION.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="block text-lg font-medium text-gray-300 transition-colors hover:text-white py-3 px-2 rounded-lg hover:bg-white/5"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      {item.label}
                    </Link>
                  ))}
                </nav>

                {/* Mobile Auth Actions */}
                <div className="pt-4 space-y-3 border-t border-gray-800">
                  {isAuthenticated && user ? (
                    <>
                      <Button
                        variant="outline"
                        className="w-full border-gray-700 hover:bg-gray-800 rounded-full h-12"
                        asChild
                      >
                        <Link href="/workspace" onClick={() => setMobileMenuOpen(false)}>
                          Go to Dashboard
                        </Link>
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => {
                          handleLogout();
                          setMobileMenuOpen(false);
                        }}
                        className="w-full text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-full h-12"
                      >
                        <LogOut className="w-4 h-4 mr-2" />
                        Sign Out
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        variant="outline"
                        className="w-full border-white/20 hover:bg-white/10 rounded-full h-12"
                        asChild
                      >
                        <Link href={AUTH_ROUTES.LOGIN} onClick={() => setMobileMenuOpen(false)}>
                          Sign In
                        </Link>
                      </Button>
                      <Button
                        className="w-full bg-white text-black hover:bg-huzilerz-lime rounded-full h-12 font-semibold"
                        asChild
                      >
                        <Link href={AUTH_ROUTES.SIGNUP} onClick={() => setMobileMenuOpen(false)}>
                          Get Started
                        </Link>
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      {/* Decorative partial bottom border - spans from logo center to auth area center */}
      <div className="hidden md:block absolute bottom-0 left-1/2 -translate-x-1/2 w-[70%] h-0.5 bg-gradient-to-r from-transparent via-white/40 to-transparent" />
    </header>
  );
}