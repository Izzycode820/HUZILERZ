# Next.js 14+ App Router Implementation Rules

## File Structure Rules

### Route Groups
- Use `(auth)` for authentication routes: `/app/(auth)/auth/*`
- Use `(protected)` for authenticated routes: `/app/(protected)/*`
- Use `(public)` for public routes: `/app/(public)/*`

### Layout Organization
```
/app/
├── (auth)/
│   ├── layout.tsx          # Auth-specific layout
│   └── auth/
│       ├── login/page.tsx
│       ├── signup/page.tsx
│       └── ...
├── (protected)/
│   ├── layout.tsx          # Protected layout with auth verification
│   ├── workspace/
│   │   ├── page.tsx        # Workspace dashboard
│   │   └── [workspace_id]/
│   │       ├── store/
│   │       │   ├── dashboard/page.tsx
│   │       │   └── ...
│   │       ├── blog/
│   │       └── services/
│   └── billing/
│       └── page.tsx
└── (public)/
    └── ...
```

## Data Fetching Patterns

### Server vs Client Components
- **Server Components**: Use for layouts, static pages, initial data fetching
- **Client Components**: Use for interactive features, forms, real-time updates

### Authentication Verification
```typescript
// In protected layout
async function verifyAuth() {
  const cookieStore = await cookies()
  const refreshToken = cookieStore.get('refresh_token')

  if (!refreshToken) {
    redirect('/auth/login')
  }

  return true
}
```

### Route Parameter Handling
```typescript
// Dynamic routes
'use client';
import { useParams } from 'next/navigation';

export default function StoreDashboard() {
  const params = useParams();
  const workspaceId = params.workspace_id as string;
  // ...
}
```

## Authentication Guards

### Route-Level Protection
- Use server-side auth verification in `(protected)/layout.tsx`
- Redirect unauthenticated users to `/auth/login`
- Use middleware for advanced route protection

### Client-Side Protection
```typescript
// Use Zustand hooks for client-side auth state
const { isAuthenticated, user } = useAuth();

if (!isAuthenticated) {
  router.push('/auth/login');
  return null;
}
```

## Error Handling

### Loading States
```typescript
// Loading skeleton pattern
if (isLoading) {
  return (
    <div className="animate-pulse">
      {/* Loading skeleton */}
    </div>
  );
}
```

### Error Boundaries
```typescript
// Error state pattern
if (error) {
  return (
    <div className="text-center">
      <h1>Error</h1>
      <p>{error}</p>
    </div>
  );
}
```

### Empty States
```typescript
// Empty state pattern
if (isEmpty) {
  return (
    <div className="text-center">
      <h3>No data available</h3>
      <p>Get started by creating your first item</p>
    </div>
  );
}
```

## Performance Optimization

### Route Groups
- Use route groups for code splitting
- Keep layouts minimal and focused

### Dynamic Imports
```typescript
// For large components
const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'), {
  loading: () => <div>Loading...</div>,
});
```

### Metadata Patterns
```typescript
// Page metadata
export const metadata: Metadata = {
  title: {
    template: '%s | HUZILERZ',
    default: 'HUZILERZ',
  },
  description: 'Manage your workspaces and AI-powered tools',
};
```

## Type Safety

### Route Parameters
```typescript
// Type-safe route parameters
interface PageParams {
  workspace_id: string;
  id?: string;
}
```

### Search Parameters
```typescript
// Type-safe search params
'use client';
import { useSearchParams } from 'next/navigation';

const searchParams = useSearchParams();
const tab = searchParams.get('tab') as 'settings' | 'billing' | null;
```

## Navigation Patterns

### Client Navigation
```typescript
import { useRouter } from 'next/navigation';

const router = useRouter();
router.push('/workspace/settings?tab=billing');
```

### Server Redirection
```typescript
import { redirect } from 'next/navigation';

redirect('/auth/login');
```

## Workspace Route Patterns

### Workspace Dashboard Routes
```
/workspace                          # Main workspace dashboard
/workspace/create                   # Workspace creation
/workspace/[workspace_id]/dashboard # Individual workspace dashboard
/workspace/[workspace_id]/settings  # Workspace settings
/workspace/[workspace_id]/team      # Member management
/workspace/[workspace_id]/analytics # Workspace analytics
```

### Workspace Type Routes
```
/workspace/[workspace_id]/store/*     # Store workspace routes
/workspace/[workspace_id]/blog/*      # Blog workspace routes
/workspace/[workspace_id]/services/*  # Services workspace routes
```

## Component Integration

### Hook Integration
```typescript
// Use custom hooks for data fetching
const {
  data,
  isLoading,
  error,
  refresh
} = useCustomHook();

// ⚠️ CRITICAL: Never use transformed data directly in useEffect!
// ❌ WRONG - Causes infinite loop if hook returns computed data
const { filteredData, sortedItems, computedList } = useCustomHook()
useEffect(() => {
  // If these values are computed (using .filter, .map, .sort, etc.)
  // This creates INFINITE LOOP!
  console.log('Data changed')
}, [filteredData, sortedItems, computedList])  // ← New references every render

// ✅ CORRECT - Get raw data from hook, compute in component
const { rawData, items, list } = useCustomHook()

// Transform with useMemo (creates stable references)
const filteredData = useMemo(
  () => rawData.filter(item => item.active),
  [rawData]
)
const sortedItems = useMemo(
  () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
  [items]
)

useEffect(() => {
  // Safe - only runs when rawData/items actually change
  console.log('Data changed')
}, [filteredData, sortedItems])  // ← Stable references, no infinite loop

// This pattern applies to ALL data: users, products, orders, settings, etc.
```

### Store Integration
```typescript
// Use Zustand stores for state management
const { workspaces, createWorkspace } = useWorkspace();
```

## Security Best Practices

### JWT Validation
- Validate JWT claims in middleware
- Check permissions for workspace access
- Implement proper error handling for auth failures

### Permission-Based Access
```typescript
// Check user permissions
const { user } = useAuth();
const canAccess = user?.permissions?.includes('workspace:read');

if (!canAccess) {
  return <div>Access denied</div>;
}
```

## SEO & Metadata

### Dynamic Metadata
```typescript
// Dynamic page titles
export const metadata: Metadata = {
  title: {
    template: '%s | Workspace | HUZILERZ',
    default: 'Workspace | HUZILERZ',
  },
};
```

### Structured Data
- Implement proper Open Graph tags
- Add structured data for better SEO
- Use semantic HTML for accessibility

## Testing & Maintenance

### Route Testing
- Test route protection
- Test dynamic route parameters
- Test error states and loading patterns

### Code Organization
- Keep route files focused and single-purpose
- Use consistent naming conventions
- Document complex route patterns

---

*Last Updated: 2025-10-08*
*Based on existing patterns in auth, billing, and workspace routes*