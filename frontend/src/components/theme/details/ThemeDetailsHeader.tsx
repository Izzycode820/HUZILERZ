'use client';

import React from 'react';
import Link from 'next/link';

interface ThemeDetailsHeaderProps {
  themeName: string;
  demoUrl?: string | null;
  onUseTheme: () => void;
}

export function ThemeDetailsHeader({ themeName, demoUrl, onUseTheme }: ThemeDetailsHeaderProps) {
  const tabs = [
    { id: 'overview', label: 'Overview', href: '#overview' },
    { id: 'features', label: 'Features', href: '#features' },
    { id: 'reviews', label: 'Reviews', href: '#reviews' },
    { id: 'support', label: 'Support', href: '#support' },
  ];

  return (
    <header className="sticky top-0 z-50 border-b bg-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-4">
          {/* Theme Name */}
          <h1 className="text-xl font-semibold">{themeName}</h1>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-8">
            {tabs.map((tab) => (
              <a
                key={tab.id}
                href={tab.href}
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                {tab.label}
              </a>
            ))}
          </nav>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {demoUrl && (
              <button
                onClick={() => window.open(demoUrl, '_blank')}
                className="text-sm font-medium px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                View demo
              </button>
            )}
            <button
              onClick={onUseTheme}
              className="text-sm font-medium px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
            >
              Use theme
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
