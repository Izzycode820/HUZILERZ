# Restricted Mode & Gating System

> **TL;DR**: Gating blocks actions based on plan limits. Restricted Mode blocks ALL write actions due to payment issues. They work together to enforce subscription compliance.

---

## 1. Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER ACTION REQUEST                           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CHECK #1: RESTRICTED MODE                           │
│         "Is the workspace blocked due to payment issues?"            │
│                                                                       │
│   workspace.restricted_mode == True?                                 │
│   ├── YES → BLOCK ALL WRITES (return error)                         │
│   └── NO  → Continue to Gating                                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CHECK #2: PLAN GATING                               │
│         "Does the user's plan allow this action?"                    │
│                                                                       │
│   check_product_limit(), check_staff_limit(), etc.                   │
│   ├── LIMIT EXCEEDED → BLOCK (return error with upgrade prompt)     │
│   └── WITHIN LIMIT   → ALLOW ACTION                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Restricted Mode

### What It Is
A **payment enforcement** mechanism that blocks ALL write operations when a subscription has payment issues.

### When It's Set
```python
# Triggered by subscription_suspended signal
workspace.restricted_mode = True
workspace.restricted_at = timezone.now()
workspace.restricted_reason = 'grace_period_expired'  # or 'payment_failed', 'admin_action'
```

### What It Blocks (Write Operations)
| Action | Blocked? |
|--------|----------|
| Create product | ✅ Yes |
| Invite staff | ✅ Yes |
| Add domain | ✅ Yes |
| Deploy site | ✅ Yes |
| **Delete product** | ❌ No (helps compliance) |
| **Delete workspace** | ❌ No (helps compliance) |
| **View data** | ❌ No (read access) |
| **Switch to workspace** | ❌ No (read access) |

### Key Files
- `workspace.core.models.Workspace` - `restricted_mode`, `restricted_at`, `restricted_reason` fields
- `subscription.services.gating.check_restricted_mode()` - The check function
- `subscription.tasks.compliance_tasks.enforce_workspace_restriction()` - Sets restricted mode
- `subscription.tasks.compliance_tasks.clear_workspace_restriction()` - Clears restricted mode

---

## 3. Plan Gating

### What It Is
A **capability enforcement** mechanism that blocks actions when user exceeds their plan's limits.

### Based On
```python
workspace.capabilities = {
    'product_limit': 10,
    'staff_limit': 3,
    'workspace_limit': 2,
    'theme_library_limit': 5,
    'custom_domain': True,
    'payment_processing': True,
    # ...
}
```

### What It Checks
| Function | What It Gates |
|----------|---------------|
| `check_product_limit()` | Can create more products? |
| `check_staff_limit()` | Can invite more staff? |
| `check_workspace_limit()` | Can create more workspaces? |
| `check_theme_library_limit()` | Can add more themes? |
| `check_payment_processing()` | Can accept payments? |
| `check_capability()` | Generic boolean/count check |

### Key Files
- `subscription.services.gating.py` - All gating functions
- `subscription.services.capability_engine.py` - Loads capabilities from plan
- `workspace.core.tasks.workspace_capabilities_provisioning.py` - Updates capabilities on plan change

---

## 4. How They Work Together

### Order of Checks
```python
def create_product(request, workspace):
    # ALWAYS check restricted mode FIRST
    allowed, error = check_restricted_mode(workspace, request.user)
    if not allowed:
        return Response({'success': False, **error}, status=403)
    
    # THEN check plan gating
    allowed, error = check_product_limit(workspace)
    if not allowed:
        return Response({'success': False, 'error': error}, status=403)
    
    # Both passed → create the product
    product = Product.objects.create(...)
```

### Error Response Hierarchy
1. **Restricted Mode Error** → "Renew subscription to continue"
2. **Plan Gating Error** → "Upgrade plan to add more products"

### Subscription Lifecycle

```
Active Subscription
       │
       ▼ (payment fails)
Grace Period (7 days)
       │ capabilities intact
       │ warning notifications
       ▼ (grace expires)
Restricted Status ────────────────────┐
       │                               │
       │ restricted_mode = True        │
       │ ALL writes blocked            │
       ▼                               │
Smart Selection Applied                │
       │                               │
       │ Oldest N workspaces: active   │
       │ Excess workspaces: suspended  │
       │                               │
       ▼ (user pays)                   │
Subscription Reactivated ◄─────────────┘
       │
       │ restricted_mode = False
       │ suspended workspaces restored
       ▼
Back to Active
```

---

## 5. Workspace Access vs Write Access

### Different Checks for Different Purposes

| Check | Purpose | Used In |
|-------|---------|---------|
| `check_restricted_mode()` | Block writes | Product/Staff/Domain creation |
| `check_workspace_access()` | Block read access | Workspace switching |

### Why Separate?
- **Restricted Mode** → User can VIEW workspace to see "renew" message
- **Workspace Access** → Completely blocks access to suspended workspaces

### Access Matrix

| Workspace State | Can Switch? | Can View? | Can Create? |
|-----------------|-------------|-----------|-------------|
| Active | ✅ | ✅ | ✅ |
| Active + `restricted_mode` | ✅ | ✅ | ❌ |
| `suspended_by_plan` | ❌ | ❌ | ❌ |
| `suspended` (deleted) | ❌ | ❌ | ❌ |

---

## 6. Staff-Aware Messaging

Both systems provide context-aware error messages:

### Owner Sees
```json
{
    "error": "Your subscription payment is overdue. Please renew to continue.",
    "suggestion": "Go to Settings > Subscription to renew your plan.",
    "error_code": "WORKSPACE_RESTRICTED"
}
```

### Staff Sees
```json
{
    "error": "This workspace's subscription payment is overdue. Contact owner@email.com to resolve.",
    "suggestion": "Ask owner@email.com to renew the subscription.",
    "error_code": "WORKSPACE_RESTRICTED"
}
```

---

## 7. Quick Reference

### Gating Check Usage
```python
from subscription.services.gating import (
    check_restricted_mode,
    check_product_limit,
    check_staff_limit,
    check_workspace_access
)

# Always check restricted mode first
allowed, error = check_restricted_mode(workspace, user)
if not allowed:
    return {'success': False, **error}

# Then check specific limit
allowed, error = check_product_limit(workspace)
if not allowed:
    return {'success': False, 'error': error}
```

### Key Signals
- `subscription_suspended` → Triggers `enforce_workspace_restriction`
- `subscription_reactivated` → Triggers `clear_workspace_restriction`
- `subscription_downgraded` → Triggers `detect_and_handle_violations`

### Migration Required
```bash
python manage.py migrate workspace_core  # For restricted_mode fields
```
