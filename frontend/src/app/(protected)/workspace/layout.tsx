import { ThemeWrapper } from "@/components/workspace/store/config/theme-wrapper"

/**
 * Workspace Management Layout (Server Component)
 * For the workspace home/listing page
 */

export default async function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ThemeWrapper>
      {children}
    </ThemeWrapper>
  )
}
