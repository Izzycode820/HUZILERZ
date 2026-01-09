# React Component Development Principles

## 🎯 Core Principles

### 1. **Security** 🔒
- **Client-Side Boundaries**: Use `"use client"` directive for client components only
- **Input Validation**: React Hook Form + Zod schemas for all form inputs
- **No Data Leaks**: Type-safe props with explicit interfaces
- **Authentication Gates**: Protected routes and conditional rendering
- **Error Boundaries**: Graceful error handling without exposing sensitive info

### 2. **Performance** ⚡
- **Code Splitting**: Dynamic imports for heavy components
- **Memoization**: Use `React.memo`, `useMemo`, `useCallback` appropriately
- **Lazy Loading**: Component-level lazy loading for better initial load
- **Optimized Re-renders**: Minimize unnecessary re-renders with proper dependencies
- **Bundle Optimization**: Tree-shakable imports and selective component exports

### 3. **Scalability** 📈
- **Component Composition**: Build complex UIs from simple, reusable components
- **Props Interface Design**: Extensible props with optional parameters
- **Theme System**: Consistent design tokens and CSS variables
- **Layout Patterns**: Responsive design with mobile-first approach
- **State Management**: Proper separation of local vs global state

### 4. **Maintainability** 🛠️
- **Single Responsibility**: Each component has one clear purpose
- **Documentation**: JSDoc comments for complex components
- **Consistent Naming**: Follow established patterns across the codebase
- **Type Safety**: Full TypeScript coverage with strict mode
- **Error Handling**: Comprehensive error states and loading states

### 5. **Best Practices** ✅
- **Shadcn/UI Integration**: Use consistent design system components
- **React Hook Form**: Form management with Zod validation
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **Responsive Design**: Mobile-first approach with breakpoint utilities
- **Testing Ready**: Component structure optimized for unit testing

### 6. **Industry Standards** 🏢
- **Next.js Patterns**: Follow Next.js 14+ conventions and app router
- **React 18 Patterns**: Use concurrent features and modern hooks
- **Design System**: Consistent with shadcn/ui and Tailwind CSS
- **Performance Standards**: Core Web Vitals optimization
- **Security Standards**: OWASP principles for frontend security

---

## 📝 Implementation Rules

### **Component Structure Rules**
```typescript
// ✅ CORRECT: Proper component structure with TypeScript
"use client"

import React from 'react'
import { Button } from '@/components/shadcn-ui/button'
import { cn } from '@/lib/utils'

interface ComponentProps {
  readonly title: string
  readonly description?: string
  readonly className?: string
  readonly onAction?: () => void
}

/**
 * Component description with JSDoc
 * @param props - Component props interface
 */
export function ComponentName({
  title,
  description,
  className,
  onAction
}: ComponentProps) {
  // State and hooks
  const [isLoading, setIsLoading] = React.useState(false)

  // Event handlers
  const handleClick = async () => {
    setIsLoading(true)
    try {
      await onAction?.()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={cn('space-y-4', className)}>
      <h2 className="text-2xl font-bold">{title}</h2>
      {description && (
        <p className="text-muted-foreground">{description}</p>
      )}
      <Button
        onClick={handleClick}
        disabled={isLoading}
        className="w-full"
      >
        {isLoading ? 'Loading...' : 'Action'}
      </Button>
    </div>
  )
}
```

### **Form Component Rules**
```typescript
// ✅ CORRECT: React Hook Form + Zod validation
"use client"

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const formSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password too short')
})

type FormValues = z.infer<typeof formSchema>

export function LoginForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      password: ''
    },
    mode: 'onBlur'
  })

  const onSubmit = (data: FormValues) => {
    // Handle form submission
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        {/* Form fields */}
      </form>
    </Form>
  )
}
```

### **State Management Rules**
```typescript
// ✅ CORRECT: Proper state management patterns
interface ComponentState {
  readonly data: DataType | null
  readonly isLoading: boolean
  readonly error: string | null
}

// Use discriminated unions for complex state
interface LoadingState {
  readonly status: 'loading'
}

interface SuccessState {
  readonly status: 'success'
  readonly data: DataType
}

interface ErrorState {
  readonly status: 'error'
  readonly error: string
}

type ComponentState = LoadingState | SuccessState | ErrorState
```

### **File Organization Rules**
- **One component per file** (except for compound components)
- **Index files** for clean exports and tree shaking
- **Domain-based folders** (auth, workspace, subscription)
- **UI components** in `shadcn-ui` folder
- **No circular dependencies** between component modules

### **Performance Rules**
- **Use `React.memo`** for expensive components
- **Optimize dependencies** in `useEffect` and `useCallback`
- **Lazy load** heavy components with `React.lazy`
- **Avoid inline objects/functions** in render
- **Use `useTransition`** for non-urgent updates

### **⚠️ CRITICAL Performance Rule - Infinite Loop Prevention**
**NEVER use transformed/computed arrays or objects directly in useEffect dependencies!**

This is the #1 cause of infinite loops ("Maximum update depth exceeded"):

```typescript
// ❌ WRONG - Causes infinite loop if hook returns computed data
const { filteredData, sortedItems } = useCustomHook()
useEffect(() => {
  // If filteredData/sortedItems are computed (using .filter, .map, .sort)
  // this will cause infinite loop!
}, [filteredData, sortedItems])

// ✅ CORRECT - Get raw data, compute with useMemo in component
const { data, items } = useCustomHook()
const filteredData = useMemo(() => data.filter(d => d.active), [data])
const sortedItems = useMemo(() => [...items].sort((a, b) => a.id - b.id), [items])
useEffect(() => {
  // Safe - only runs when data/items actually change
}, [filteredData, sortedItems])
```

**Rule applies to ANY data transformation:**
- Array methods: `.filter()`, `.map()`, `.sort()`, `.reduce()`, `.slice()`
- Object spread: `{...obj}` or array spread: `[...arr]`
- Any computed values that create new references

**Always transform data in components using `useMemo()`, never rely on hooks to provide pre-transformed data!**

### **⚠️ CRITICAL SSR/Hydration Safety Rule - Next.js**
**Always add defensive checks when using Zustand store data in components!**

During SSR, Zustand store might not be hydrated yet, causing `undefined` errors:

```typescript
// ❌ WRONG - Will crash if store not hydrated
const { items } = useStore()
const filteredItems = useMemo(() => items.filter(i => i.active), [items])
// Error: Cannot read properties of undefined (reading 'filter')

// ✅ CORRECT - SSR-safe with optional chaining
const { items } = useStore()
const filteredItems = useMemo(() => items?.filter(i => i.active) ?? [], [items])

// ✅ CORRECT - Also safe for mapping
{items?.map(item => <Card key={item.id} {...item} />)}

// ✅ CORRECT - Safe for any array operation
const sortedItems = useMemo(() =>
  items ? [...items].sort((a, b) => a.name.localeCompare(b.name)) : [],
  [items]
)
```

**Universal pattern for all store arrays:**
- Use `array?.method() ?? []` for operations
- Use `array ?? []` when passing to components
- Use `array?.length ?? 0` for counts

### **Security Rules**
- **Validate all inputs** with Zod schemas
- **Sanitize user content** before rendering
- **Use CSRF protection** for forms
- **Implement proper CORS** for API calls
- **No sensitive data** in client-side code

---

## 🚀 Quick Start Checklist

### For New Components:
1. [ ] Define `readonly` props interface
2. [ ] Add `"use client"` directive for client components
3. [ ] Use proper TypeScript types and interfaces
4. [ ] Implement loading and error states
5. [ ] Add accessibility attributes
6. [ ] Write JSDoc documentation
7. [ ] Test responsive behavior
8. [ ] Export via index file

### For Form Components:
1. [ ] Use React Hook Form + Zod
2. [ ] Implement proper validation
3. [ ] Add loading states for submissions
4. [ ] Handle form errors gracefully
5. [ ] Include accessibility labels
6. [ ] Test form submission flow

### For Data-Fetching Components:
1. [ ] Implement loading skeleton
2. [ ] Handle error states
3. [ ] Add retry mechanisms
4. [ ] Use proper caching strategies
5. [ ] Implement optimistic updates
6. [ ] Test offline scenarios

### For UI Components:
1. [ ] Use shadcn/ui components
2. [ ] Follow design system tokens
3. [ ] Implement responsive design
4. [ ] Add proper focus states
5. [ ] Test keyboard navigation
6. [ ] Ensure color contrast compliance

---

## 📚 Reference Examples

See existing patterns in:
- `components/subscription/pricing/PricingTable.tsx` - Complex data display with state management
- `components/subscription/pricing/PricingCard.tsx` - Reusable UI component with props
- `components/shadcn-ui/checkbox.tsx` - Base UI component with Radix integration
- `components/authentication/forms/LoginForm.tsx` - Form component with validation

### Key Patterns Observed:

1. **Props Interface Design**
```typescript
interface ComponentProps {
  readonly prop1: string
  readonly prop2?: number
  readonly onAction?: () => void
  readonly className?: string
}
```

2. **State Management**
```typescript
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState<string | null>(null)
```

3. **Event Handling**
```typescript
const handleAction = async () => {
  setIsLoading(true)
  try {
    await onAction?.()
  } catch (err) {
    setError(err.message)
  } finally {
    setIsLoading(false)
  }
}
```

4. **Conditional Rendering**
```typescript
{isLoading ? (
  <Skeleton className="h-8 w-full" />
) : error ? (
  <Alert variant="destructive">{error}</Alert>
) : (
  <div>Content</div>
)}
```

5. **Styling with Tailwind**
```typescript
<div className={cn(
  'space-y-4 p-6 border rounded-lg',
  isActive && 'border-primary',
  className
)}>
  {/* Content */}
</div>
```

**Last Updated**: 2025-10-08
**Maintained By**: Development Team