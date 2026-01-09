# React Hook Implementation Rules & Guidelines

## Core Principles

### 1. **Performance-First Design**
- Use selective store subscriptions to prevent unnecessary re-renders
- Implement stable action references with `useCallback`
- Use granular hooks for specific use cases
- Optimize dependency arrays for minimal re-renders

### 2. **Clean Interface Contracts**
- Define explicit return interfaces for all hooks
- Provide consistent naming patterns across hooks
- Export granular hooks for performance optimization
- Maintain separation between state and actions

### 3. **Type Safety & Maintenance**
- Use TypeScript for all hook definitions
- Import types from centralized type definitions
- Define complete return interfaces
- Use proper generic typing for selectors

### 4. **Store Integration Patterns**
- Use store selectors for optimized state access
- Implement action wrappers with proper error handling
- Follow consistent store-to-hook mapping patterns
- Maintain proper store action chaining

## Implementation Rules

### File Organization
```
hooks/
├── authentication/
│   ├── useAuth.ts              # Main auth hook
│   └── index.ts                # Auth hook exports
├── subscription/
│   ├── useSubscription.ts      # Main subscription hook
│   └── index.ts                # Subscription hook exports
└── workspace/
    ├── core/
    │   ├── useWorkspace.ts     # Core workspace hook
    │   ├── useMembers.ts       # Member management hook
    │   └── index.ts            # Core hook exports
    └── index.ts                # Main hook exports
```

### Hook Structure Template
```typescript
/**
 * Hook Name - Hook description
 * 2024 Best Practices with Zustand
 * Custom hook layer for store - provides clean interface and performance
 * Following patterns: single responsibility, selective subscriptions, error boundaries
 */

import { useCallback } from 'react'
import { useStoreName, storeNameSelectors } from '../../stores/store/domain'
import type {
  RequestType,
  ResponseType
} from '../../types/domain'

// ============================================================================
// Hook Return Interface - Clean Contract
// ============================================================================

export interface UseHookNameReturn {
  // State selectors (performance optimized)
  data: ReturnType<typeof storeNameSelectors.data>
  isLoading: boolean
  error: string | null

  // Computed state
  hasData: boolean
  dataCount: number

  // Actions (stable references)
  fetchData: () => Promise<void>
  createData: (request: RequestType) => Promise<ResponseType>
  clearError: () => void

  // Helper methods
  isValid: () => boolean
  canPerformAction: () => boolean
}

// ============================================================================
// Main Hook Implementation
// ============================================================================

export function useHookName(): UseHookNameReturn {
  // Selective store subscriptions (performance optimized)
  const data = useStoreName(storeNameSelectors.data)
  const isLoading = useStoreName(storeNameSelectors.isLoading)
  const error = useStoreName(storeNameSelectors.error)
  const hasData = useStoreName(storeNameSelectors.hasData)
  const dataCount = useStoreName(storeNameSelectors.dataCount)

  // Store actions (use stable selectors for performance)
  const fetchDataAction = useStoreName(storeNameSelectors.fetchData)
  const createDataAction = useStoreName(storeNameSelectors.createData)
  const clearError = useStoreName(storeNameSelectors.clearError)
  const isValid = useStoreName(storeNameSelectors.isValid)
  const canPerformAction = useStoreName(storeNameSelectors.canPerformAction)

  // ============================================================================
  // Stable Action Implementations
  // ============================================================================

  const fetchData = useCallback(async (): Promise<void> => {
    return fetchDataAction()
  }, [fetchDataAction])

  const createData = useCallback(async (request: RequestType): Promise<ResponseType> => {
    return createDataAction(request)
  }, [createDataAction])

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State (reactive)
    data,
    isLoading,
    error,

    // Computed state
    hasData,
    dataCount,

    // Actions (stable)
    fetchData,
    createData,
    clearError,

    // Helper methods
    isValid,
    canPerformAction,
  }
}

// ============================================================================
// Granular Hooks (Performance Optimization)
// ============================================================================

/**
 * Hook for data status only - minimal re-renders
 */
export function useHookNameStatus() {
  return {
    hasData: useStoreName(storeNameSelectors.hasData),
    isLoading: useStoreName(storeNameSelectors.isLoading),
    error: useStoreName(storeNameSelectors.error)
  }
}

/**
 * Hook for data only - minimal re-renders
 */
export function useHookNameData() {
  return {
    data: useStoreName(storeNameSelectors.data),
    dataCount: useStoreName(storeNameSelectors.dataCount)
  }
}

/**
 * Hook for actions only - no reactive state
 */
export function useHookNameActions() {
  const clearError = useStoreName(storeNameSelectors.clearError)

  return { clearError }
}

// ============================================================================
// Default Export
// ============================================================================

export default useHookName
```

### Import Path Conventions
- **Stores**: `../../stores/store/domain` (from hook folder)
- **Types**: `../../types/domain` (from hook folder)
- **Selectors**: Import from store selector exports

### State Access Rules

#### 1. **Selective Store Subscriptions**
```typescript
// ✅ Correct - Selective subscriptions
const data = useStoreName(storeNameSelectors.data)
const isLoading = useStoreName(storeNameSelectors.isLoading)

// ❌ Incorrect - Full store subscription
const store = useStoreName()
const data = store.data
const isLoading = store.isLoading
```

#### 2. **Action References**
```typescript
// ✅ Correct - Stable action references
const fetchDataAction = useStoreName(storeNameSelectors.fetchData)

// ❌ Incorrect - Direct action access
const fetchData = useStoreName(state => state.fetchData)
```

#### 3. **CRITICAL: Never Subscribe to Transformed/Computed Array/Object Selectors** ⚠️
**This causes infinite loops when used in useEffect dependencies!**

```typescript
// ❌ WRONG - Subscribing to transformed data causes infinite loops
const filteredItems = useStore(selectors.filteredItems)      // New array every call
const sortedData = useStore(selectors.sortedData)            // New array every call
const computedObj = useStore(selectors.computedObject)       // New object every call

useEffect(() => {
  console.log('Data changed:', filteredItems)
  fetchRelatedData()
}, [filteredItems])  // ← New reference every render = INFINITE LOOP

// Why it loops:
// 1. Component renders → filteredItems is [1,2,3] (reference A)
// 2. useEffect runs → calls fetchRelatedData()
// 3. Store updates (or any re-render happens)
// 4. filteredItems is now [1,2,3] (reference B - different from A!)
// 5. React sees change → useEffect runs again
// 6. Loop continues... "Maximum update depth exceeded"

// ✅ CORRECT - Subscribe to stable state, compute in component
const items = useStore(selectors.items)  // Direct state - stable reference
const filteredItems = useMemo(
  () => items.filter(item => item.active),
  [items]  // Only changes when actual data changes
)

useEffect(() => {
  console.log('Data changed:', filteredItems)
  fetchRelatedData()
}, [filteredItems])  // ← Now stable, only runs when items actually change
```

**Why hooks should NEVER expose transformed data:**

**The Problem Chain:**
1. Hook exposes computed selector → `const data = useHook()` where hook does `useStore(state => state.items.filter(...))`
2. Every hook call returns new reference → Even if data identical, reference different
3. Component uses in useEffect → `useEffect(() => {...}, [data])`
4. Any re-render → Hook returns new reference
5. useEffect detects "change" → Runs callback
6. Callback updates something → Causes re-render
7. Back to step 4 → **INFINITE LOOP**

**Result: "Maximum update depth exceeded" or "getSnapshot should be cached"**

**Universal Safe Patterns (for ANY feature):**

✅ **Safe to subscribe to:**
- Direct state properties: `state.users`, `state.products`, `state.orders`
- Primitives: `state.count`, `state.total`, `state.id`
- Booleans: `state.isLoading`, `state.hasData`, `state.isActive`
- Strings: `state.status`, `state.message`, `state.name`
- Numbers: `state.items.length`, `state.price`, `state.quantity`
- Null checks: `state.data === null`, `state.user !== undefined`

❌ **NEVER subscribe to:**
- Filtered arrays: `state.items.filter(...)`
- Mapped arrays: `state.data.map(...)`
- Sorted arrays: `state.list.sort(...)`
- Sliced arrays: `state.array.slice(...)`
- Spread arrays: `[...state.items]`
- Spread objects: `{...state.config}`
- Computed objects: `{ total: state.count, active: state.isActive }`
- Any transformation that creates new reference

✅ **DO in components (ALWAYS):**
```typescript
// Get raw data from hook
const { items, users, products } = useHook()

// Transform with useMemo
const activeItems = useMemo(() => items.filter(item => item.active), [items])
const sortedUsers = useMemo(() => [...users].sort((a, b) => a.name.localeCompare(b.name)), [users])
const total = useMemo(() => products.reduce((sum, p) => sum + p.price, 0), [products])

// Now safe to use in useEffect
useEffect(() => {
  // Only runs when items actually change
}, [activeItems])
```

**This applies to EVERY hook in the codebase - not just one feature!**

### Action Implementation Rules

#### 1. **Action Wrapper Pattern**
```typescript
const actionName = useCallback(async (request: RequestType): Promise<ResponseType> => {
  return actionNameAction(request)
}, [actionNameAction])
```

#### 2. **No Additional Logic in Wrappers**
```typescript
// ✅ Correct - Direct action forwarding
const createData = useCallback(async (request: RequestType): Promise<ResponseType> => {
  return createDataAction(request)
}, [createDataAction])

// ❌ Incorrect - Avoid adding logic in wrappers
const createData = useCallback(async (request: RequestType): Promise<ResponseType> => {
  // Don't add validation or transformation here
  if (!request.valid) throw new Error('Invalid')
  return createDataAction(request)
}, [createDataAction])
```

### Return Interface Rules

#### 1. **Complete Return Interface**
```typescript
export interface UseHookNameReturn {
  // State selectors
  data: ReturnType<typeof storeNameSelectors.data>
  isLoading: boolean
  error: string | null

  // Computed state
  hasData: boolean

  // Actions
  fetchData: () => Promise<void>
  clearError: () => void

  // Helper methods
  isValid: () => boolean
}
```

#### 2. **Consistent Grouping**
```typescript
return {
  // State (reactive)
  data,
  isLoading,
  error,

  // Computed state
  hasData,

  // Actions (stable)
  fetchData,
  clearError,

  // Helper methods
  isValid,
}
```

### Granular Hook Rules

#### 1. **Status-Only Hook**
```typescript
export function useHookNameStatus() {
  return {
    hasData: useStoreName(storeNameSelectors.hasData),
    isLoading: useStoreName(storeNameSelectors.isLoading),
    error: useStoreName(storeNameSelectors.error)
  }
}
```

#### 2. **Data-Only Hook**
```typescript
export function useHookNameData() {
  return {
    data: useStoreName(storeNameSelectors.data),
    dataCount: useStoreName(storeNameSelectors.dataCount)
  }
}
```

#### 3. **Actions-Only Hook**
```typescript
export function useHookNameActions() {
  const clearError = useStoreName(storeNameSelectors.clearError)
  return { clearError }
}
```

### Performance Optimization Rules

#### 1. **Minimal Dependency Arrays**
```typescript
// ✅ Correct - Minimal dependencies
const action = useCallback(async () => {
  return actionAction()
}, [actionAction])

// ❌ Incorrect - Unnecessary dependencies
const action = useCallback(async () => {
  return actionAction()
}, [actionAction, data, isLoading]) // data and isLoading not used
```

#### 2. **Stable Action References**
```typescript
// ✅ Correct - Stable selector references
const actionAction = useStoreName(storeNameSelectors.action)

// ❌ Incorrect - Unstable references
const action = useStoreName(state => state.action)
```

### Type Safety Rules

#### 1. **ReturnType Pattern**
```typescript
// ✅ Correct - Type-safe selector references
data: ReturnType<typeof storeNameSelectors.data>

// ❌ Incorrect - Manual typing
data: DataType | null
```

#### 2. **Complete Type Imports**
```typescript
import type {
  RequestType,
  ResponseType,
  DataType
} from '../../types/domain'
```

### Error Handling Rules

#### 1. **Error State Access**
```typescript
const error = useStoreName(storeNameSelectors.error)
const clearError = useStoreName(storeNameSelectors.clearError)
```

#### 2. **No Error Handling in Wrappers**
```typescript
// ✅ Correct - Let store handle errors
const action = useCallback(async (request: RequestType): Promise<ResponseType> => {
  return actionAction(request)
}, [actionAction])

// ❌ Incorrect - Don't handle errors in wrappers
const action = useCallback(async (request: RequestType): Promise<ResponseType> => {
  try {
    return await actionAction(request)
  } catch (error) {
    // Error handling should be in store
    console.error(error)
    throw error
  }
}, [actionAction])
```

### Naming Conventions

#### 1. **Hook Names**
- Main hook: `useHookName`
- Status hook: `useHookNameStatus`
- Data hook: `useHookNameData`
- Actions hook: `useHookNameActions`

#### 2. **Action Names**
- Match store action names exactly
- Use consistent verb patterns
- Follow RESTful naming conventions

### Anti-Patterns to Avoid

#### ❌ **Don't Mix Concerns**
- Don't add business logic in hook wrappers
- Don't handle component-specific state in hooks
- Don't mix multiple store subscriptions in one hook

#### ❌ **Don't Break Performance**
- Don't use full store subscriptions
- Don't create unstable action references
- Don't include unnecessary dependencies

#### ❌ **Don't Ignore Type Safety**
- Don't use `any` types
- Don't skip return interface definitions
- Don't mix manual typing with selector typing

#### ❌ **Don't Over-Engineer**
- Don't create hooks for trivial state
- Don't add unnecessary abstraction layers
- Don't implement features not required by current use cases

## Example Implementation

See existing hooks for reference:
- `hooks/authentication/useAuth.ts` - Auth hook pattern
- `hooks/subscription/useSubscription.ts` - Subscription hook pattern

Follow these rules consistently to maintain code quality and ensure hook reliability across the application.