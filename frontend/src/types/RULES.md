# TypeScript Development Principles

## 🎯 Core Principles

### 1. **Security** 🔒
- **Immutable Data**: Use `readonly` interfaces for all API responses
- **Type Safety**: Discriminated unions prevent invalid state transitions
- **Input Validation**: Zod schemas for runtime validation
- **No Data Leaks**: Explicit type guards for sensitive operations
- **Audit Trail**: Comprehensive error tracking and logging

### 2. **Performance** ⚡
- **Const Assertions**: Use `as const` for literal types and constants
- **Tree Shaking**: Optimized exports with selective re-exports
- **Feature Bitmaps**: O(1) feature checking vs array searches
- **Lazy Loading**: Import types only when needed
- **Memory Efficiency**: Avoid unnecessary type duplication

### 3. **Scalability** 📈
- **Modular Architecture**: Separate concerns with clear boundaries
- **Extensible Types**: Use union types for future expansion
- **Backward Compatibility**: Never break existing type contracts
- **API Alignment**: Types must match backend response structures exactly
- **Namespace Organization**: Logical folder structure for large codebases

### 4. **Maintainability** 🛠️
- **Single Responsibility**: Each type file has one clear purpose
- **Documentation**: JSDoc comments for complex types
- **Consistent Naming**: Follow established patterns across the codebase
- **Type Guards**: Runtime validation for discriminated unions
- **Error Handling**: Comprehensive error types with clear discrimination

### 5. **Best Practices** ✅
- **Discriminated Unions**: Use `status` field for type-safe state management
- **Zod Integration**: Runtime validation alongside compile-time types
- **Readonly Interfaces**: Prevent accidental mutations
- **Type Guards**: Runtime type checking for discriminated unions
- **Const Enums**: Use objects with `as const` for better performance

### 6. **Industry Standards** 🏢
- **Stripe/Chargebee Patterns**: Follow payment platform conventions
- **REST API Standards**: Align with OpenAPI specifications
- **TypeScript Handbook**: Follow official TypeScript guidelines
- **React Patterns**: Compatible with React state management
- **Security Standards**: OWASP principles for API design

---

## 📝 Implementation Rules

### **Type Definition Rules**
```typescript
// ✅ CORRECT: Readonly interfaces with discriminated unions
interface SuccessResponse {
  readonly success: true;
  readonly data: SomeData;
}

interface ErrorResponse {
  readonly success: false;
  readonly error: string;
}

type ApiResponse = SuccessResponse | ErrorResponse;

// ✅ CORRECT: Const assertions for performance
const STATUS = {
  ACTIVE: 'active',
  PENDING: 'pending',
  ERROR: 'error',
} as const;

type StatusType = typeof STATUS[keyof typeof STATUS];
```

### **File Organization Rules**
- **One domain per folder** (auth, workspace, subscription)
- **Core types in root**, specialized types in subfolders
- **Index files** for clean exports and tree shaking
- **No circular dependencies** between type modules

### **Error Handling Rules**
- **Discriminated error unions** with `error_code` field
- **Type guards** for runtime error discrimination
- **Comprehensive error metadata** for debugging
- **User-friendly error messages** with technical details

### **Performance Rules**
- **Use `readonly`** for all interface properties
- **Const assertions** for literal types
- **Feature bitmaps** over array searches
- **Selective imports** to avoid bundle bloat

### **Security Rules**
- **No `any` types** - use `unknown` with type guards
- **Input validation** with Zod schemas
- **Immutable data** structures
- **Type-safe state transitions** with discriminated unions

---

## 🚀 Quick Start Checklist

### For New Type Files:
1. [ ] Define `readonly` interfaces
2. [ ] Create discriminated unions with `status` field
3. [ ] Add Zod schemas for runtime validation
4. [ ] Write type guards for discriminated unions
5. [ ] Export selectively via index files
6. [ ] Add comprehensive JSDoc documentation
7. [ ] Test with real backend responses

### For API Integration:
1. [ ] Match backend response structure exactly
2. [ ] Use discriminated unions for error handling
3. [ ] Implement feature bitmap system
4. [ ] Add type guards for runtime validation
5. [ ] Follow Stripe/Chargebee patterns for payments

### For State Management:
1. [ ] Use discriminated unions for state
2. [ ] Implement type-safe transitions
3. [ ] Add loading/error/success states
4. [ ] Use const assertions for performance
5. [ ] Follow React patterns for hooks

---

## 📚 Reference Examples

See existing patterns in:
- `authentication/auth.ts` - Discriminated unions for auth state
- `subscription/subscription.ts` - Zod schemas and error unions
- `authentication/index.ts` - Optimized exports and type guards

**Last Updated**: 2025-10-07
**Maintained By**: Development Team