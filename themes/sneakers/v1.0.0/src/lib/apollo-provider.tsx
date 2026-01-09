'use client'

import { ApolloProvider } from '@apollo/client/react'
import { storefrontClient } from './apollo-client'
import { ReactNode } from 'react'

interface ApolloProviderWrapperProps {
  children: ReactNode
}

export function ApolloProviderWrapper({ children }: ApolloProviderWrapperProps) {
  return (
    <ApolloProvider client={storefrontClient}>
      {children}
    </ApolloProvider>
  )
}
