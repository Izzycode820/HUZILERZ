"use client"

import { ThemeConfigProvider } from "@/components/workspace/layouts/active-theme"

export function ThemeWrapper({ children }: { children: React.ReactNode }) {
  return <ThemeConfigProvider>{children}</ThemeConfigProvider>
}
