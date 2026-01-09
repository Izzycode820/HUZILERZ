# Capabilities-Driven Subscription System

**Single Source of Truth: `plans.yaml` → CapabilityEngine → workspace.capabilities → Runtime Enforcement**

## Architecture Overview

This system follows the **Shopify/Stripe pattern** for subscription-based feature gating:
- Subscription module owns **WHAT users can do** (limits/capabilities)
- Domain modules own **VALIDATION** and **COUNTING** at creation time
- No centralized usage tracking tables

---

## Core Components

### 1. Plans Definition (`subscription/plans.yaml`)
Single source of truth for all tier capabilities.

```yaml
tiers:
  free:
    product_limit: 20
    workspace_limit: 1
    storage_gb: 0.5
    custom_domain: false
    # ... all capabilities defined here
```

### 2. CapabilityEngine (`subscription/services/capability_engine.py`)
Converts YAML definitions into runtime capability maps.

**Key Methods:**
- `get_plan_capabilities(tier)` - Returns capability dict for tier (cached)
- `generate_workspace_capabilities(user)` - Generates merged capabilities with trial overrides
- `validate_plans_yaml()` - Validates YAML structure

**Caching:** 1 hour cache for performance (microsecond lookups)

### 3. Workspace Capabilities Field (`workspace.capabilities`)
Each workspace stores its current capabilities as JSONField:

```python
class Workspace(models.Model):
    capabilities = models.JSONField(default=dict)
    # Contains: {'product_limit': 50, 'storage_gb': 2, ...}
```

---

## The Complete Flow

### Flow A: Subscription Change → Update Existing Workspaces

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SUBSCRIPTION EVENT                                        │
│    User upgrades: beginner → pro                            │
│    Subscription.tier changes                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SIGNAL EMITTED                                           │
│    subscription/signals.py                                  │
│    post_save.connect(subscription_changed_handler)          │
│                                                             │
│    Emits: subscription_upgraded signal                      │
│    Payload: {user_id, old_tier, new_tier, metadata}        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. RECEIVER CATCHES EVENT                                   │
│    workspace/core/receivers.py                              │
│    @receiver(subscription_upgraded)                         │
│    def handle_subscription_upgraded(sender, **kwargs):      │
│        user_id = kwargs['user_id']                          │
│        new_tier = kwargs['new_tier']                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PROVISIONING TASK FIRED (Async)                         │
│    workspace/core/tasks/workspace_capabilities_             │
│    provisioning.py                                          │
│                                                             │
│    update_user_workspace_capabilities.delay(                │
│        user_id=user_id,                                     │
│        new_tier=new_tier,                                   │
│        event_type='subscription_upgraded'                   │
│    )                                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. CAPABILITY ENGINE CONSULTED                              │
│    Inside provisioning task:                                │
│                                                             │
│    new_capabilities = CapabilityEngine.get_plan_            │
│                      capabilities(new_tier)                 │
│                                                             │
│    Returns: {                                               │
│      'product_limit': 300,                                  │
│      'workspace_limit': 3,                                  │
│      'storage_gb': 10,                                      │
│      'custom_domain': True,                                 │
│      ...                                                    │
│    }                                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. WORKSPACE RECORDS UPDATED                                │
│    workspaces = Workspace.objects.filter(                   │
│        owner=user, status='active'                          │
│    )                                                        │
│                                                             │
│    for workspace in workspaces:                             │
│        workspace.capabilities = new_capabilities            │
│        workspace.save()                                     │
│                                                             │
│    Result: All user workspaces now have pro capabilities    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. EVENT LOGGED                                             │
│    SubscriptionEventLog.objects.create(                     │
│        event_type='provisioning_success',                   │
│        description='Provisioned 2 workspace(s)',            │
│        metadata={'tier': 'pro', 'workspaces_updated': 2}    │
│    )                                                        │
└─────────────────────────────────────────────────────────────┘
```

### Flow B: New Workspace Creation

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER CREATES WORKSPACE                                   │
│    WorkspaceService.create_workspace(user, name)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PRE-CREATION VALIDATION (Service Layer)                  │
│    workspace/core/services/workspace_service.py             │
│                                                             │
│    # Get user's current tier                                │
│    tier = user.subscription.plan.tier  # or 'free'          │
│                                                             │
│    # Get limits from CapabilityEngine                       │
│    capabilities = CapabilityEngine.get_plan_                │
│                  capabilities(tier)                         │
│    workspace_limit = capabilities['workspace_limit']        │
│                                                             │
│    # Count existing workspaces                              │
│    current_count = Workspace.objects.filter(                │
│        owner=user                                           │
│    ).count()                                                │
│                                                             │
│    # Validate limit                                         │
│    if workspace_limit != 0 and                              │
│       current_count >= workspace_limit:                     │
│        raise WorkspaceLimitExceeded(                        │
│            f"Limit: {workspace_limit}, Current: {current}"  │
│        )                                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. WORKSPACE CREATED                                        │
│    workspace = Workspace.objects.create(                    │
│        owner=user,                                          │
│        name=name,                                           │
│        capabilities={}  # Empty initially                   │
│    )                                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PROVISIONING TASK FIRED (Async)                         │
│    provision_new_workspace.delay(workspace.id)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. CAPABILITY ENGINE CONSULTED                              │
│    Inside provisioning task:                                │
│                                                             │
│    tier = workspace.owner.subscription.plan.tier            │
│    capabilities = CapabilityEngine.get_plan_                │
│                  capabilities(tier)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. WORKSPACE CAPABILITIES SET                               │
│    workspace.capabilities = capabilities                    │
│    workspace.save()                                         │
│                                                             │
│    Result: New workspace has correct tier capabilities      │
└─────────────────────────────────────────────────────────────┘
```

---

## Runtime Feature Gating (Per Module)

Each domain module validates against `workspace.capabilities` at **creation time**.

### Example 1: Product Creation

```python
# workspace/store/services/product_service.py

def create_product(workspace, product_data):
    # Get limit from workspace capabilities
    product_limit = workspace.capabilities.get('product_limit', 0)

    # Count existing products
    current_count = Product.objects.filter(
        workspace=workspace
    ).count()

    # Validate
    if product_limit != 0 and current_count >= product_limit:
        raise ProductLimitExceeded(
            f"Your {workspace.owner.subscription.plan.name} plan "
            f"allows {product_limit} products. "
            f"Upgrade to create more."
        )

    # Create product
    return Product.objects.create(workspace=workspace, **product_data)
```

### Example 2: Storage Upload

```python
# medialib/services/storage_service.py

def upload_file(workspace, file):
    # Get storage limit from workspace capabilities
    storage_limit_gb = workspace.capabilities.get('storage_gb', 0)

    # Get current usage (actual calculation)
    current_usage_gb = calculate_workspace_storage(workspace)

    # Check if upload would exceed limit
    file_size_gb = file.size / (1024 ** 3)
    new_total = current_usage_gb + file_size_gb

    if storage_limit_gb != 0 and new_total > storage_limit_gb:
        raise StorageLimitExceeded(
            f"Upload would exceed {storage_limit_gb}GB limit. "
            f"Current usage: {current_usage_gb:.2f}GB"
        )

    # Upload file
    return upload_to_storage(file)
```

### Example 3: Custom Domain (Boolean Feature)

```python
# workspace/hosting/services/domain_service.py

def add_custom_domain(workspace, domain):
    # Check if custom domains are allowed
    if not workspace.capabilities.get('custom_domain', False):
        raise FeatureNotAvailable(
            f"Custom domains require Pro or Enterprise plan. "
            f"Current plan: {workspace.owner.subscription.plan.name}"
        )

    # Add domain
    return CustomDomain.objects.create(
        workspace=workspace,
        domain=domain
    )
```

### Example 4: Staff Invitations

```python
# workspace/core/services/membership_service.py

def invite_staff(workspace, email):
    # Get staff limit
    staff_limit = workspace.capabilities.get('staff_limit', 1)

    # Count existing staff
    current_count = Membership.objects.filter(
        workspace=workspace
    ).count()

    # Validate
    if current_count >= staff_limit:
        raise StaffLimitExceeded(
            f"Your plan allows {staff_limit} staff members. "
            f"Upgrade to invite more."
        )

    # Send invitation
    return send_invitation(workspace, email)
```

---

## Resources That Need Tracking vs Simple Counting

### Simple Counting (No Usage Table Needed)
Just query the database at creation time:

```python
# Products
Product.objects.filter(workspace=workspace).count()

# Workspaces
Workspace.objects.filter(owner=user).count()

# Staff
Membership.objects.filter(workspace=workspace).count()

# Themes
Theme.objects.filter(user=user).count()
```

### Storage (Needs Dedicated Tracking)
Storage requires progressive tracking because:
- Cumulative across many files
- Needs historical data
- Needs progressive alerts (80%, 90%, 100%)
- Can't just "count" - need to sum sizes

**Location:** `workspace/hosting/services/storage_tracking_service.py`

```python
class StorageTrackingService:
    @staticmethod
    def get_workspace_storage_usage(workspace):
        """Calculate total storage used by workspace"""
        total_bytes = MediaUpload.objects.filter(
            workspace=workspace
        ).aggregate(
            total=Sum('file_size')
        )['total'] or 0

        return total_bytes / (1024 ** 3)  # Convert to GB

    @staticmethod
    def check_storage_threshold(workspace):
        """Check if approaching storage limit"""
        usage_gb = get_workspace_storage_usage(workspace)
        limit_gb = workspace.capabilities.get('storage_gb', 0)

        if limit_gb == 0:  # Unlimited
            return {'status': 'ok'}

        percentage = (usage_gb / limit_gb) * 100

        if percentage >= 100:
            return {'status': 'exceeded', 'percentage': percentage}
        elif percentage >= 90:
            return {'status': 'critical', 'percentage': percentage}
        elif percentage >= 80:
            return {'status': 'warning', 'percentage': percentage}
        else:
            return {'status': 'ok', 'percentage': percentage}
```

---

## Subscription Events Reference

Events emitted by `subscription` module:

| Event | When | Payload |
|-------|------|---------|
| `subscription_created` | New subscription created | `{user_id, tier, plan_id}` |
| `subscription_activated` | Subscription activated | `{user_id, tier}` |
| `subscription_upgraded` | Tier upgraded | `{user_id, old_tier, new_tier}` |
| `subscription_downgraded` | Tier downgraded | `{user_id, old_tier, new_tier}` |
| `subscription_renewed` | Subscription renewed | `{user_id, tier}` |
| `subscription_cancelled` | Subscription cancelled | `{user_id, tier}` |
| `subscription_expired` | Subscription expired | `{user_id, tier}` |

---

## Key Principles

### 1. Separation of Concerns
- **Subscription module:** Capabilities/limits definition
- **Domain modules:** Validation and enforcement
- **CapabilityEngine:** Translation layer between YAML and runtime

### 2. Performance
- CapabilityEngine caches capabilities (1 hour)
- Validation happens at **creation time only** (infrequent operation)
- No overhead on reads/queries
- Database queries for counts are cheap with proper indexes

### 3. Consistency
- `workspace.capabilities` is updated **asynchronously** via Celery
- Pre-creation validation uses **CapabilityEngine directly** (always fresh)
- This handles race conditions where capabilities not yet updated

### 4. Extensibility
- Add new capability to `plans.yaml` → automatically available everywhere
- No code changes needed for new limits
- Just implement validation in relevant service

### 5. Industry Standard
This pattern follows:
- **Shopify:** Plans → capabilities → runtime enforcement
- **Stripe:** Subscription features → usage validation
- **AWS:** Service quotas → API throttling
- **Domain-Driven Design:** Each bounded context owns its validation

---

## Future: Fine-Grained Inline Validation

When implementing inline validation (e.g., "Can I create one more product?"):

```python
# GraphQL mutation example
def resolve_create_product(root, info, input):
    workspace = info.context.workspace

    # Inline validation
    validator = CapabilityValidator(workspace)
    validator.check_or_raise('product_limit')  # Raises if exceeded

    # Create product
    return ProductService.create_product(workspace, input)
```

**Validator service:**
```python
class CapabilityValidator:
    def __init__(self, workspace):
        self.workspace = workspace
        self.capabilities = workspace.capabilities

    def check_or_raise(self, capability_key):
        """Check capability and raise detailed error if exceeded"""
        limit = self.capabilities.get(capability_key, 0)

        # Map capability to resource
        resource_map = {
            'product_limit': ('Product', Product),
            'workspace_limit': ('Workspace', Workspace),
            'staff_limit': ('Staff', Membership),
        }

        name, model = resource_map[capability_key]
        current = model.objects.filter(workspace=self.workspace).count()

        if limit != 0 and current >= limit:
            raise CapabilityExceeded(
                capability=capability_key,
                limit=limit,
                current=current,
                upgrade_required=True
            )
```

---

## Troubleshooting

### Issue: Workspace capabilities not updated after subscription change
- Check: Signal emitted? (`SubscriptionEventLog`)
- Check: Receiver connected? (`workspace/core/receivers.py`)
- Check: Celery task executed? (Celery logs)
- Check: Task succeeded? (`SubscriptionEventLog` provisioning events)

### Issue: Validation using stale limits
- Pre-creation validation uses `CapabilityEngine` directly (always fresh)
- Runtime enforcement uses `workspace.capabilities` (may be seconds behind)
- This is acceptable: worst case = user creates one extra resource during provisioning

### Issue: Different workspaces showing different capabilities
- This is expected during provisioning (async update)
- All workspaces converge within seconds
- Consider: UI loading state while provisioning in progress

---

## Summary

```
plans.yaml (SSOT)
    ↓
CapabilityEngine (cached lookups)
    ↓
workspace.capabilities (denormalized for performance)
    ↓
Service layer validation (at creation time)
    ↓
User feedback (upgrade prompts)
```

**Zero usage tracking tables. Domain-driven. Scales infinitely.**
