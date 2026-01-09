import { ApolloClient, InMemoryCache, HttpLink, from } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'
import { onError } from '@apollo/client/link/error'

// Error handling middleware
const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors)
    graphQLErrors.forEach(({ message, locations, path }) =>
      console.log(
        `[GraphQL error]: Message: ${message}, Location: ${locations}, Path: ${path}`
      )
    )
  if (networkError) console.log(`[Network error]: ${networkError}`)
})

// Store identification middleware - sends hostname for backend tenant resolution
const storeIdentificationLink = setContext((_, { headers }) => {
  if (typeof window === 'undefined') {
    return { headers }
  }

  const hostname = window.location.hostname
  let storeHostname = hostname

  // DEV: localhost uses ?store= param, send as fake subdomain for middleware
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const params = new URLSearchParams(window.location.search)
    const storeSlug = params.get('store') || 'demo-store'
    storeHostname = `${storeSlug}.huzilerz.com`
  }

  console.log('[Apollo Store ID] Sending hostname:', {
    actual: hostname,
    sent: storeHostname,
    timestamp: new Date().toISOString()
  })

  return {
    headers: {
      ...headers,
      'X-Store-Hostname': storeHostname,
    }
  }
})

// Domain-based GraphQL endpoint (workspace identified by hostname)
const httpLink = new HttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URI || 'http://localhost:8000/api/graphql',
  credentials: 'include',
})

// Sneakers Theme Storefront Client
export const storefrontClient = new ApolloClient({
  link: from([
    errorLink,
    storeIdentificationLink.concat(httpLink),
  ]),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          products: {
            merge(existing, incoming) {
              return incoming
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
  },
})
