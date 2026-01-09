# Downgrade Compliance Reference

Quick reference for adding new gated features to the downgrade system.

## Feature Categories

| Category | Enforcement | Grace Period | Example |
|----------|------------|--------------|---------|
| Boolean | Immediate | No | `custom_domain`, `payment_processing` |
| Count | Auto-enforce | 7 days | `product_limit`, `staff_limit` |
| Level | Read-block | No | `analytics` (none/basic/pro/advanced) |

## Adding a New Gated Feature

### 1. Boolean Feature (has/doesn't have)
```python
# In ComplianceService._check_X_violation():
if old_allowed and not new_allowed:
    # Count current usage
    # Return ViolationRecord with requires_grace=False
```

### 2. Count Feature (numeric limit)
```python
# In ComplianceService._check_X_violation():
if new_limit > 0 and current_count > new_limit:
    # Return ViolationRecord with requires_grace=True
```

### 3. Level Feature (tiered access)
No enforcement needed - gate at read/write time via `check_X_capability()`.

## Checklist for New Features

- [ ] Add capability to `plans.yaml`
- [ ] Add violation check method to `ComplianceService`
- [ ] Add enforcement method if count-based
- [ ] Add gating function to `gating.py`
- [ ] Add `active_by_plan` field if data needs preservation

## Key Files

| File | Purpose |
|------|---------|
| `subscription/services/compliance_service.py` | Violation detection + enforcement |
| `subscription/services/gating.py` | Runtime feature gating |
| `subscription/tasks/compliance_tasks.py` | Async enforcement |
| `subscription/events.py` | Compliance signals |

## Configuration

```python
# settings.py
COMPLIANCE_GRACE_PERIOD_DAYS = 7  # Default: 7 days
```

## Convention: 0 = Unlimited
All numeric limits use `0` to mean unlimited. This is handled in all check methods.

---

## Future UI Implementation

### Minimal MVP (Sidebar Card)
Reuse existing "Free tier - Upgrade now" sidebar card to show:
- Countdown timer ("5 days to resolve")
- Warning icon + "Plan violation" text
- Link to compliance dashboard

### Compliance Dashboard (Post-MVP)
- List violations by type (products, staff, workspaces)
- Let user select which items to keep
- Real-time compliance status
- Call `resolve_violation()` when user deactivates excess items

