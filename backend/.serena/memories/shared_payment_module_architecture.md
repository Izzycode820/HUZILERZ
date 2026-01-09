# Shared Payment Module Architecture Design

## Core Principles (Following Shopify Pattern)
- **Shared Core Logic**: Payment processing, gateway integration, security, error handling
- **Specialized Flows**: Subscription-specific logic remains in subscription app
- **Universal Payment Model**: Supports multiple revenue streams (subscriptions, trials, templates, etc.)

## Architecture Components

### 1. Core Payment Models (`payment/models/`)
- `Payment` - Universal payment model with revenue stream types
- `PaymentMethod` - Payment method storage (MTN/Orange mobile money)
- `PaymentAttempt` - Retry tracking and session management
- `PaymentGateway` - Gateway configuration and settings

### 2. Shared Services (`payment/services/`)
- `PaymentService` - Main payment orchestrator
- `GatewayService` - Gateway selection and communication
- `SecurityService` - Signature verification, data masking
- `FraudProtectionService` - Risk assessment and fraud detection

### 3. Gateway Integrations (`payment/gateways/`)
- `FapshiGateway` - Cameroon mobile money integration
- `BaseGateway` - Abstract base class for future gateways
- `GatewayFactory` - Gateway selection based on payment type

### 4. Utilities (`payment/utils/`)
- `CircuitBreaker` - Resilience pattern for external services
- `PaymentValidator` - Payment data validation
- `WebhookProcessor` - Webhook handling utilities

### 5. Security Layer (`payment/security/`)
- `SignatureVerifier` - Payment signature validation
- `DataMasker` - Sensitive data protection
- `TokenManager` - Payment token management

## Subscription-Specific Logic (Remains in Subscription App)
- Subscription lifecycle management (renewals, trials, grace periods)
- Subscription plan tier logic (Free, Beginning, Pro, Enterprise)
- Manual renewal workflows
- Subscription-specific webhook handlers
- Usage tracking and limits

## Integration Pattern
- Subscription app imports shared payment services
- Payment app remains gateway-agnostic
- Clear separation of concerns between payment processing and subscription business logic