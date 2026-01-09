"use client"

/**
 * Universal Workspace Layout
 * Simple shadcn design - no complex peer selectors
 * Same beautiful UI, cleaner code
 */

import { ReactNode } from "react"

interface WorkspaceLayoutProps {
  sidebar: ReactNode
  header: ReactNode
  children: ReactNode
  mobileHeader?: ReactNode
  mobileNav?: ReactNode
}

export function WorkspaceLayout({ sidebar, header, children, mobileHeader, mobileNav }: WorkspaceLayoutProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Sidebar - Fixed 288px (18rem) width like shadcn, scrollable. HIDDEN on mobile. */}
      <aside className="hidden md:block w-72 flex-shrink-0 overflow-y-auto border-r bg-sidebar text-sidebar-foreground">
        {sidebar}
      </aside>

      {/* Main Content Area */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile Header - Rendered explicitly on mobile */}
        <div className="md:hidden">
          {mobileHeader}
        </div>

        {/* Desktop Header - HIDDEN on mobile */}
        <header className="hidden md:flex h-14 shrink-0 items-center gap-2 border-b px-4 transition-colors lg:px-6">
          {header}
        </header>

        {/* Page Content - Scrollable. Added pb-24 for mobile bottom nav clearance. */}
        <div className="flex-1 overflow-y-auto bg-background p-4 md:p-6 pb-24 md:pb-6">
          {children}
        </div>

        {/* Mobile Nav Injection point (if not fixed in component itself, but helpful for structure) */}
        <div className="md:hidden">
          {mobileNav}
        </div>
      </main>
    </div>
  )
}
