# Service Implementation Rules & Guidelines

## Core Principles

### 1. **Security-First Design**
- All services extend `BaseService` for consistent auth handling
- Default to `requireAuth: true` for all authenticated endpoints
- Use `getPublic()`/`postPublic()` only for public endpoints
- Validate all required fields before API calls
- Never expose sensitive data in service responses

### 2. **Performance Optimization**
- Use singleton service instances to avoid duplicate initialization
- Implement proper error boundaries and fallbacks
- Cache frequently accessed data appropriately
- Use pagination for large datasets
- Clean undefined values before sending requests

### 3. **Scalability Patterns**
- Follow consistent naming conventions across services
- Use proper folder structure with `core` subfolders
- Implement proper error handling and status codes
- Support pagination and filtering for list endpoints
- Use TypeScript generics for type-safe responses

### 4. **Maintainability Standards**
- Keep services focused on single responsibility
- Document backend endpoint alignment in JSDoc comments
- Use descriptive method names matching backend endpoints
- Implement consistent validation patterns
- Export singleton instances for easy consumption

### 5. **Best Practices**
- Always validate required fields before API calls
- Clean undefined values from request payloads
- Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Implement proper error handling with meaningful messages
- Follow RESTful endpoint naming conventions

### 6. **Industry Standards**
- Align with backend endpoint structures
- Use consistent response type patterns
- Implement proper token management
- Follow REST API conventions
- Use proper HTTP status code handling

## Implementation Rules

### File Organization
```
services/
├── base/
│   └── BaseService.ts          # Foundation service class
├── api/
│   ├── client.ts              # API client singleton
│   └── config.ts              # API configuration
├── workspace/
│   ├── core/
│   │   ├── workspace.ts       # Core workspace service
│   │   ├── members.ts         # Member management service
│   │   └── index.ts           # Core service exports
│   └── index.ts               # Main service exports
└── authentication/
    └── auth.ts                # Auth service
```

### Service Structure Template
```typescript
/**
 * Service Name - Service description
 * Aligned with backend endpoint_name.py endpoints
 */

import BaseService from '../base/BaseService'
import type {
  // Import all required types
  RequestType,
  ResponseType,
  ErrorType
} from '../../types/service/domain'

// ============================================================================
// Service Class
// ============================================================================

export class ServiceName extends BaseService {
  constructor() {
    super('endpoint_key') // Must match API_BASE key
  }

  /**
   * Method description
   * Backend: HTTP_METHOD /api/endpoint/path/
   */
  async methodName(request: RequestType): Promise<ResponseType> {
    // Validate required fields
    this.validateRequired(request as unknown as Record<string, unknown>, ['field1', 'field2'])

    // Clean undefined values
    const cleanedRequest = this.cleanData(request as unknown as Record<string, unknown>)

    return this.post<ResponseType>('/endpoint-path/', cleanedRequest)
  }

  /**
   * Get method example
   * Backend: GET /api/endpoint/path/
   */
  async getMethod(): Promise<ResponseType> {
    return this.get<ResponseType>('/endpoint-path/')
  }
}

// ============================================================================
// Export Service Instance
// ============================================================================

const serviceInstance = new ServiceName()
export default serviceInstance
```

### Import Path Conventions
- **BaseService**: `../base/BaseService` (from core folder)
- **Types**: `../../../types/service/domain` (from core folder)
- **API Client**: `../api/client` (from base folder)

### Method Implementation Rules

#### 1. **Constructor Rules**
- Always call `super('endpoint_key')` with correct API_BASE key
- Use lowercase, singular endpoint keys matching backend

#### 2. **Method Documentation**
- Include JSDoc with method description
- Specify backend endpoint path and HTTP method
- Document required parameters and validation

#### 3. **Validation Rules**
- Always validate required fields before API calls
- Use `this.validateRequired()` for field validation
- Throw meaningful error messages for missing fields

#### 4. **Data Cleaning**
- Use `this.cleanData()` to remove undefined values
- Only send defined fields in request payloads
- Avoid sending null or undefined to backend

#### 5. **HTTP Method Usage**
- **GET**: Retrieve data (no side effects)
- **POST**: Create new resources
- **PUT**: Replace entire resource
- **PATCH**: Update partial resource
- **DELETE**: Remove resources

### Error Handling Rules

#### 1. **Validation Errors**
```typescript
if (!requiredField) {
  throw new Error('Required field is missing')
}
```

#### 2. **API Errors**
- Let BaseService handle HTTP errors
- Implement specific error handling in consuming components
- Use proper error boundaries in React components

#### 3. **Network Errors**
- Handle connection failures gracefully
- Implement retry logic where appropriate
- Provide meaningful user feedback

### Type Safety Rules

#### 1. **Request Types**
- Use imported types from types folder
- Ensure type alignment with backend schemas
- Use proper TypeScript generics

#### 2. **Response Types**
- Always specify response type in method signature
- Use proper Promise typing
- Handle both success and error responses

#### 3. **Type Imports**
- Import types from centralized types folder
- Maintain type consistency across services
- Use proper relative import paths

### Core Subfolder Rules

#### 1. **Core Services**
- Place core business logic in `core/` subfolder
- Export core services from `core/index.ts`
- Use consistent naming patterns

#### 2. **Service Index Files**
- Export service instances and types
- Provide clean public API
- Hide implementation details

#### 3. **Main Index Files**
- Re-export from core folder
- Provide unified service access
- Maintain clean import paths

### Singleton Pattern Rules

#### 1. **Service Instances**
- Export singleton service instances
- Avoid creating multiple instances
- Use consistent naming: `serviceNameService`

#### 2. **Instance Export**
```typescript
const serviceNameService = new ServiceName()
export default serviceNameService
```

### Authentication Rules

#### 1. **Auth-Required Endpoints**
- Default to authenticated endpoints
- Use `requireAuth: true` (default in BaseService)
- Handle token refresh automatically

#### 2. **Public Endpoints**
- Use `getPublic()`/`postPublic()` for public endpoints
- Specify `skipAuth: true` for public calls
- Handle public endpoints appropriately

#### 3. **Token Management**
- Let BaseService handle token management
- Use apiClient for token operations
- Implement proper logout handling

### Testing & Quality Rules

#### 1. **Method Coverage**
- Test all public methods
- Mock API responses appropriately
- Test error scenarios

#### 2. **Validation Testing**
- Test required field validation
- Test data cleaning functionality
- Test error handling paths

#### 3. **Integration Testing**
- Test service integration with stores
- Test proper type handling
- Test error propagation

## Anti-Patterns to Avoid

### ❌ **Don't Mix Concerns**
- Don't put UI logic in services
- Don't handle component state in services
- Don't mix authentication with business logic

### ❌ **Don't Over-Engineer**
- Don't create unnecessary abstraction layers
- Don't implement complex caching without need
- Don't add features not required by current use cases

### ❌ **Don't Break Patterns**
- Don't use different import paths
- Don't skip validation steps
- Don't create multiple service instances

### ❌ **Don't Ignore Types**
- Don't use `any` types
- Don't skip type imports
- Don't ignore TypeScript errors

## Example Implementation

See existing services for reference:
- `services/authentication/auth.ts` - Auth service pattern
- `services/subscription/subscription.ts` - Subscription service pattern
- `services/workspace/core/workspace.ts` - Workspace service pattern
- `services/workspace/core/members.ts` - Member service pattern

Follow these rules consistently to maintain code quality and ensure service reliability across the application.