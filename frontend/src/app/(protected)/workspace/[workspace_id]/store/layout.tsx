"use client"

import { ThemeWrapper } from "@/components/workspace/store/config/theme-wrapper"
import { StoreLayoutClient } from "@/components/workspace/store/config/store-layout-client"
import { ApolloProvider } from "@apollo/client/react"
import { adminStoreClient } from "@/services/graphql/clients"

import "@/app/(protected)/workspace/[workspace_id]/store/theme.css"

/**
 * Store Workspace Layout
 *
 * Industry Standard Pattern:
 * - ApolloProvider for GraphQL context
 * - ThemeWrapper for workspace theming
 * - StoreLayoutClient for universal layout
 * - All data from Zustand stores (auth + workspace context)
 */

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ApolloProvider client={adminStoreClient}>
      <ThemeWrapper>
        <StoreLayoutClient>
          {children}
        </StoreLayoutClient>
      </ThemeWrapper>
    </ApolloProvider>
  )
}
