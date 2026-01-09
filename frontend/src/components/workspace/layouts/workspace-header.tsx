"use client"

/**
 * Universal Workspace Header
 * shadcn design - clean and simple
 */

import { ThemeSelector } from "@/components/workspace/layouts/theme-selector"
import { ModeToggle } from "@/components/workspace/layouts/mode-toggle"

interface WorkspaceHeaderProps {
  title: string
  actions?: React.ReactNode
}

export function WorkspaceHeader({ title, actions }: WorkspaceHeaderProps) {
  return (
    <div className="flex w-full items-center justify-between">
      <h1 className="text-base font-medium">{title}</h1>

      <div className="flex items-center gap-2">
        {actions}
        <ThemeSelector />
        <ModeToggle />
      </div>
    </div>
  )
}
