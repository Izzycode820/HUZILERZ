import { ApolloClient, InMemoryCache, HttpLink, from } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'
import { onError } from '@apollo/client/link/error'

// Error handling middleware
const errorLink = onError(({ graphQLErrors, networkError }: any) => {
  if (graphQLErrors)
    graphQLErrors.forEach(({ message, locations, path }: any) =>
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

// Lazy client initialization - waits for window config
let clientInstance: ApolloClient | null = null

function createStorefrontClient(): ApolloClient {
  // Get GraphQL endpoint from window config (injected by backend)
  const graphqlEndpoint = typeof window !== 'undefined'
    ? (window as any).__HUZILERZ_STORE_CONFIG__?.graphqlEndpoint
    : null

  const uri = graphqlEndpoint || 'http://localhost:8000/api/graphql'

  console.log('[Apollo Client] Initializing with endpoint:', uri)

  const httpLink = new HttpLink({
    uri,
    credentials: 'include',
  })

  return new ApolloClient({
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
}

// Export getter that lazily creates client on first access
export const storefrontClient = new Proxy({} as ApolloClient, {
  get(target, prop) {
    if (!clientInstance) {
      clientInstance = createStorefrontClient()
    }
    return (clientInstance as any)[prop]
  }
})
