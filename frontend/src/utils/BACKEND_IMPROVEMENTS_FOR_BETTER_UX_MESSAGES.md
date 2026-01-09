# Backend API Improvements

This file tracks suggested improvements to backend API responses for better frontend UX.

---

## Subscription Error Responses

### 1. CannotCancelActiveSubscriptionError - Add Missing Fields

**Current Response:**
```json
{
  "error": "Cannot cancel active subscription",
  "error_code": "CANNOT_CANCEL_ACTIVE_SUBSCRIPTION",
  "current_status": "active"
}
```

**Suggested Improvement:**
```json
{
  "error": "Cannot cancel active subscription",
  "error_code": "CANNOT_CANCEL_ACTIVE_SUBSCRIPTION",
  "current_status": "active",
  "current_plan": "beginning",  // ADD: The user's current plan tier
  "expires_at": "2025-11-02T13:43:59.708624+00:00"  // ADD: When subscription expires
}
```

**Benefit:**
- Better UX: Show specific details in error message
- Current: "Your subscription is currently active. Contact support..."
- Improved: "Your Beginning subscription is active until Nov 2, 2025. Contact support..."

**Frontend Type Update Needed:**
```typescript
// File: src/lib/types/subscription/subscription.ts
export interface CannotCancelActiveSubscriptionError {
  readonly error: string;
  readonly error_code: 'CANNOT_CANCEL_ACTIVE_SUBSCRIPTION';
  readonly current_status: 'active';
  readonly current_plan: 'beginning' | 'pro' | 'enterprise'; // ADD
  readonly expires_at: string; // ADD
}
```

**Priority:** Low (nice-to-have for better UX)

---

## Notes

- All entries should include current response, suggested improvement, and benefit
- Mark as completed when backend implements the change
- Update frontend types after backend deployment
