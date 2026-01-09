# Hosting Module Capability Refactoring Guide

**Target AI**: This guide is for an AI assistant with unlimited token context that can read full files and perform heavy refactoring.

---

## 🎯 Context: Event-Driven Capability Provisioning Architecture

### The Big Picture

We've migrated from a **hardcoded subscription plan model** to an **event-driven YAML-based capability system**:

- **Single Source of Truth**: `subscription/services/plans.yaml` defines ALL plan features
- **Event-Driven**: Subscription changes emit events → Receivers listen → Tasks provision capabilities
- **Module-Scoped Entitlements**: Each module (workspace, hosting, theme, store) maintains its own capability records **in the database**
- **No More Direct Plan Access**: Services no longer call `subscription.plan.sites_limit` or read from hardcoded dicts

### The Core Principle

**ALL inline validation MUST read from the database `capabilities` record. NEVER from:**
- ❌ Hardcoded `SUBSCRIPTION_HOSTING_TIERS` dicts
- ❌ Direct plan field access (`subscription.plan.sites_limit`)
- ❌ Manual tier checks in service logic

**ALWAYS from:**
- ✅ `hosting_env.capabilities['deployment_allowed']`
- ✅ `hosting_env.capabilities['storage_gb']`
- ✅ `hosting_env.capabilities['custom_domain']`

### The Flow

```
Subscription Change (upgrade/downgrade/activation)
    ↓
Subscription Module emits event (subscription_upgraded, etc.)
    ↓
Hosting Receivers (workspace/hosting/receivers.py) listen
    ↓
Queue Task: update_hosting_capabilities.delay()
    ↓
Task extracts hosting-specific capabilities from YAML via CapabilityEngine
    ↓
Saves to HostingEnvironment.capabilities JSON field in DB
    ↓
Services perform inline gating by reading from DB:
    if not hosting_env.capabilities['deployment_allowed']
```

---

## ✅ What Has Been Completed (Tasks 1-4)

### 1. **Task Registration**
- ✅ Added `provision_new_workspace` to `workspace/core/tasks/__init__.py`
- ✅ Added `update_hosting_capabilities`, `provision_new_hosting_capabilities` to `workspace/hosting/tasks/__init__.py`

### 2. **Event Listeners**
- ✅ Created `workspace/hosting/receivers.py`
  - Listens to: `subscription_activated`, `subscription_upgraded`, `subscription_downgraded`, `subscription_expired`, `subscription_cancelled`, `trial_converted`
  - Queues: `update_hosting_capabilities.delay()`

### 3. **Capability Provisioning Task**
- ✅ Created `workspace/hosting/tasks/hosting_capabilities.py`
  - `update_hosting_capabilities()` - Updates hosting entitlements on subscription changes
  - `provision_new_hosting_capabilities()` - Provisions hosting for new environments
  - Extracts only hosting-relevant keys from YAML: `storage_gb`, `custom_domain`, `deployment_allowed`

### 4. **Database Schema**
- ✅ Added `capabilities` JSONField to `HostingEnvironment` model
- ✅ Updated model properties to use capabilities:
  - `is_deployment_allowed` → reads `capabilities['deployment_allowed']`
  - `storage_usage_percentage` → reads `capabilities['storage_gb']`
- ✅ Marked legacy fields as DEPRECATED with comments

---

## 🚧 What Needs To Be Done (Tasks 5-8)

### Current Hosting Capabilities (From YAML)

The hosting module tracks **3 capabilities**:

```python
HOSTING_CAPABILITY_KEYS = [
    'storage_gb',          # Storage limit in GB
    'custom_domain',       # Boolean: can use custom domains
    'deployment_allowed',  # Boolean: can deploy sites (free tier = preview only)
]
```

**Important Notes**:
- `bandwidth_gb` was REMOVED from YAML (no longer tracked)
- `sites_limit` / `theme_library_limit` moved to **theme module** (not hosting concern)
- DB constraints enforce "one active site per workspace" (no manual count checks needed)

---

## 📋 Refactoring Tasks

### **Task 5: Delete Legacy Subscription Integration Service**

**Objective**: Remove the outdated subscription integration service that predates the event-driven architecture.

#### **5.1 Why Delete This File?**

**File**: `workspace/hosting/services/subscription_integration_service.py`

This file contains **manual event handlers** that were used BEFORE the event-driven architecture:
- `on_subscription_activated()` (line 47) - manually creates HostingEnvironment
- `on_payment_failed()` (line 146) - manually suspends hosting
- `on_subscription_expired()` (line 111) - manually handles expiration
- `_create_hosting_environment()` (line 242) - uses hardcoded `SUBSCRIPTION_HOSTING_TIERS`
- `_configure_limits()` (line 323) - manually sets `sites_limit`, `storage_limit_gb` from dict

**These are OBSOLETE** because:
- ✅ We now have `workspace/hosting/receivers.py` listening to subscription events
- ✅ Receivers queue `update_hosting_capabilities` task automatically
- ✅ Tasks write to `HostingEnvironment.capabilities` DB field
- ✅ Services read from DB record (single source of truth)

**The old flow (manual)**:
```
Subscription change → Manually call on_subscription_activated()
  → Read SUBSCRIPTION_HOSTING_TIERS dict
  → Set hosting_env.sites_limit, storage_limit_gb fields
```

**The new flow (event-driven)**:
```
Subscription change → Emit event → Receiver captures → Queue task
  → Task reads YAML via CapabilityEngine
  → Writes to hosting_env.capabilities JSON field
```

#### **5.2 Delete the File**

Run this command:
```bash
rm "c:\S.T.E.V.E\V2\HUZILERZ\backend\workspace\hosting\services\subscription_integration_service.py"
```

#### **5.3 Find and Remove Imports**

Search for any imports of this service:
```bash
grep -r "subscription_integration_service" "c:\S.T.E.V.E\V2\HUZILERZ\backend"
```

Remove all imports like:
```python
from workspace.hosting.services.subscription_integration_service import HostingSubscriptionIntegration
```

**Note**: If you find manual calls to `HostingSubscriptionIntegration().on_subscription_*()`, delete them. The receivers handle everything now.

---

### **Task 6: Update Service Files - Replace Legacy Logic with DB Capability Record**

**Objective**: Remove ALL hardcoded `SUBSCRIPTION_HOSTING_TIERS` lookups and replace with `hosting_env.capabilities` DB reads.

**Core Principle**: Services should NEVER check tiers or read from dicts. They should ONLY read from the `capabilities` record in the database.

---

#### **6.1 Update `deployment_service.py`**

**File**: `workspace/hosting/services/deployment_service.py`

**Search for and REMOVE**:
- `hosting_env.can_deploy_new_site` calls → Replace with `hosting_env.is_deployment_allowed`
- `hosting_env.sites_limit` references → Remove entirely (theme module handles this)
- Any hardcoded tier checks

**Example Refactor** (around line 61):

**BEFORE (LEGACY)**:
```python
# Check site limits
if not hosting_env.can_deploy_new_site:
    return {
        'allowed': False,
        'reason': 'sites_limit_exceeded',
        'message': f'You have reached your {hosting_env.sites_limit} site limit',
        'current_sites': hosting_env.active_sites_count,
        'limit': hosting_env.sites_limit,
        'upgrade_required': True
    }
```

**AFTER (NEW - DB CAPABILITY RECORD)**:
```python
# Check deployment capability from DB record
if not hosting_env.is_deployment_allowed:
    return {
        'allowed': False,
        'reason': 'deployment_not_allowed',
        'message': 'Deployment requires a paid subscription (Beginner tier or higher)',
        'upgrade_required': True
    }
# Note: One-site-per-workspace enforced by DB constraint, no manual check needed
```

**Storage checks** (if any):
```python
# BEFORE (LEGACY):
storage_limit = hosting_env.storage_limit_gb

# AFTER (NEW - DB CAPABILITY RECORD):
storage_limit = hosting_env.capabilities.get('storage_gb', 0)
```

---

#### **6.2 Update `resource_usage_service.py`**

**File**: `workspace/hosting/services/resource_usage_service.py`

**CRITICAL**: This file has a hardcoded `SUBSCRIPTION_HOSTING_TIERS` dict (lines 27-48). **DO NOT delete it yet** - we'll phase it out gradually.

**Phase 1 Changes**:

1. **Remove `sites_limit` from the dict** (lines 27-48):
   ```python
   SUBSCRIPTION_HOSTING_TIERS = {
       'free': {
           'storage_gb': 0.5,
           'custom_domains': 0,
           # 'sites_limit': 3,  ← DELETE THIS LINE
       },
       'beginner': {
           'storage_gb': 2,
           'custom_domains': 0,
           # 'sites_limit': 3,  ← DELETE THIS LINE
       },
       'pro': {
           'storage_gb': 10,
           'custom_domains': 5,
           # 'sites_limit': 15,  ← DELETE THIS LINE
       },
       'enterprise': {
           'storage_gb': 50,
           'custom_domains': 999999,
           # 'sites_limit': 999999,  ← DELETE THIS LINE
       }
   }
   ```

2. **Find all references to `tier_limits['sites_limit']`** and DELETE those code blocks:
   - Line 151-157: Site limit validation → DELETE ENTIRE BLOCK
   - Line 177: Remaining sites calculation → DELETE
   - Line 462-463: Downgrade site validation → DELETE

3. **Replace tier dict lookups with DB reads** for storage:
   ```python
   # BEFORE (LEGACY):
   tier_limits = SUBSCRIPTION_HOSTING_TIERS.get(subscription.plan.tier, {})
   storage_limit = tier_limits['storage_gb']

   # AFTER (NEW - DB CAPABILITY RECORD):
   storage_limit = hosting_env.capabilities.get('storage_gb', 0)
   ```

**Phase 2 (Future)**: Eventually delete `SUBSCRIPTION_HOSTING_TIERS` dict entirely and use only `hosting_env.capabilities`.

---

#### **6.3 Update `infrastructure_service.py`**

**File**: `workspace/hosting/services/infrastructure_service.py`

**Search for**:
```bash
grep -n "sites_limit\|plan\.tier\|SUBSCRIPTION_HOSTING_TIERS" workspace/hosting/services/infrastructure_service.py
```

**Replace**:
- Any `sites_limit` references → Remove or replace with `capabilities['deployment_allowed']`
- Any `subscription.plan.tier` checks → Replace with `capabilities` check
- Any dict lookups → Replace with DB `capabilities` read

---

### **Task 7: Remove `can_deploy_new_site()` Method and References**

**Objective**: Remove the deprecated `can_deploy_new_site()` method that checks the removed `sites_limit` field.

#### **7.1 Find All References**

Run:
```bash
grep -rn "can_deploy_new_site" workspace/hosting/
```

**Expected locations**:
- `workspace/hosting/models.py:105` - Method definition
- `workspace/hosting/models.py:163` - Used in validation method
- `workspace/hosting/models.py:1148` - Used in DeployedSite validation
- `workspace/hosting/services/deployment_service.py:61` - Used in deployment check
- `workspace/hosting/graphql/types/usage_types.py` - GraphQL field

#### **7.2 Update Each Reference**

**In `models.py` (HostingEnvironment)**:

1. **DELETE the `can_deploy_new_site()` property** (lines ~104-109):
   ```python
   # DELETE THIS ENTIRE BLOCK:
   @property
   def can_deploy_new_site(self):
       """Check if user can deploy a new site based on capabilities"""
       return self.is_deployment_allowed
   ```

2. **Find any calls to `self.can_deploy_new_site`** and replace with `self.is_deployment_allowed`

**In `models.py` (DeployedSite)**:

Around line 1148:
```python
# BEFORE (LEGACY):
if not self.hosting_environment.can_deploy_new_site:
    return {
        'allowed': False,
        'reason': 'site_limit_exceeded',
        'message': f'Site limit reached: {self.hosting_environment.sites_limit} sites maximum',
        'upgrade_required': True
    }

# AFTER (NEW - DB CAPABILITY RECORD):
if not self.hosting_environment.is_deployment_allowed:
    return {
        'allowed': False,
        'reason': 'deployment_not_allowed',
        'message': 'Deployment requires a paid subscription',
        'upgrade_required': True
    }
# Note: One-site-per-workspace enforced by DB constraint (line 807-811)
```

**In GraphQL** (`usage_types.py`):

**Option A (Recommended)**: Deprecate and alias to `is_deployment_allowed`:
```python
can_deploy_new_site = graphene.Boolean(
    deprecation_reason="Use is_deployment_allowed instead"
)

def resolve_can_deploy_new_site(self, info):
    # Deprecated: Alias to is_deployment_allowed
    return self.is_deployment_allowed
```

**Option B**: Remove field entirely (breaking change for API clients)

---

### **Task 8: Database Migration - Remove Deprecated Fields**

**Objective**: Create and apply migrations to drop legacy fields from `HostingEnvironment` model.

#### **8.1 Fields to Remove**

From `HostingEnvironment` model (in `models.py`):
```python
# DELETE THESE FIELDS:
storage_limit_gb = models.DecimalField(...)    # Line ~56
bandwidth_limit_gb = models.DecimalField(...)  # Line ~57
sites_limit = models.IntegerField(...)         # Line ~58
custom_domains_limit = models.IntegerField(...) # Line ~59
```

**KEEP** (these track USAGE, not limits):
- `capabilities` JSONField (new source of truth)
- `storage_used_gb` (current usage)
- `bandwidth_used_gb` (current usage)
- `active_sites_count` (current usage)

#### **8.2 Migration Strategy**

**Step 1**: Data migration to populate `capabilities` for existing records

```bash
python manage.py makemigrations workspace_hosting --empty -n populate_hosting_capabilities
```

Edit the migration file:
```python
from django.db import migrations

def populate_capabilities(apps, schema_editor):
    """Populate capabilities field from YAML for existing HostingEnvironment records"""
    HostingEnvironment = apps.get_model('workspace_hosting', 'HostingEnvironment')

    # Import at runtime to avoid migration dependencies
    from subscription.services.capability_engine import CapabilityEngine

    for hosting_env in HostingEnvironment.objects.select_related('subscription__plan').all():
        tier = hosting_env.subscription.plan.tier

        # Get full capabilities from YAML
        all_capabilities = CapabilityEngine.get_plan_capabilities(tier)

        # Extract only hosting capabilities
        hosting_env.capabilities = {
            'storage_gb': all_capabilities.get('storage_gb', 0),
            'custom_domain': all_capabilities.get('custom_domain', False),
            'deployment_allowed': all_capabilities.get('deployment_allowed', False),
        }
        hosting_env.save(update_fields=['capabilities'])

    print(f"✅ Populated capabilities for {HostingEnvironment.objects.count()} hosting environments")

def reverse_populate(apps, schema_editor):
    """Reverse migration - clear capabilities"""
    HostingEnvironment = apps.get_model('workspace_hosting', 'HostingEnvironment')
    HostingEnvironment.objects.update(capabilities={})

class Migration(migrations.Migration):
    dependencies = [
        ('workspace_hosting', '0001_initial'),  # Adjust to your latest migration
    ]

    operations = [
        migrations.RunPython(populate_capabilities, reverse_populate),
    ]
```

Run the migration:
```bash
python manage.py migrate workspace_hosting
```

**Step 2**: Remove the deprecated fields from the model

Edit `workspace/hosting/models.py` and DELETE these lines:
```python
# DELETE THESE 4 LINES:
storage_limit_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
bandwidth_limit_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0)
sites_limit = models.IntegerField(default=0)
custom_domains_limit = models.IntegerField(default=0)
```

**Step 3**: Create schema migration to drop database columns

```bash
python manage.py makemigrations workspace_hosting -n remove_legacy_limit_fields
```

This will auto-generate:
```python
operations = [
    migrations.RemoveField(model_name='hostingenvironment', name='storage_limit_gb'),
    migrations.RemoveField(model_name='hostingenvironment', name='bandwidth_limit_gb'),
    migrations.RemoveField(model_name='hostingenvironment', name='sites_limit'),
    migrations.RemoveField(model_name='hostingenvironment', name='custom_domains_limit'),
]
```

Run the migration:
```bash
python manage.py migrate workspace_hosting
```

**Step 4**: Remove deprecated model methods

From `HostingEnvironment` model, DELETE:
- `sync_limits_from_subscription()` method (if it exists) - no longer needed

---

## 🔍 Validation Checklist

After refactoring, verify:

### **Event-Driven Capability Provisioning**
- [ ] Subscription activated → `update_hosting_capabilities` task queued (check Celery logs)
- [ ] Subscription upgraded → `HostingEnvironment.capabilities` updated in DB
- [ ] New workspace created → Hosting capabilities provisioned via task

### **Database Capability Record Usage**
- [ ] ALL service validations read from `hosting_env.capabilities['key']`
- [ ] NO hardcoded `SUBSCRIPTION_HOSTING_TIERS` lookups for `sites_limit`
- [ ] NO direct `subscription.plan.field` access in hosting services
- [ ] `hosting_env.is_deployment_allowed` works (reads from `capabilities['deployment_allowed']`)
- [ ] Storage checks use `capabilities['storage_gb']` not `storage_limit_gb` field

### **Deployment Flow**
- [ ] Free tier users blocked from deployment (only preview allowed)
- [ ] Paid tier users can deploy
- [ ] DB constraint enforces one active site per workspace
- [ ] NO more `can_deploy_new_site()` calls

### **GraphQL**
- [ ] `HostingEnvironmentType` exposes `capabilities` field
- [ ] `can_deploy_new_site` deprecated or aliased to `is_deployment_allowed`

### **Database**
- [ ] Migration populated `capabilities` for existing records
- [ ] Legacy `*_limit` fields removed from model and DB schema
- [ ] NO breaking changes to usage tracking fields (`storage_used_gb`, etc.)

---

## 🎯 Execution Order

**Follow this exact sequence**:

1. ✅ **Task 5**: Delete `subscription_integration_service.py` and remove imports
2. ✅ **Task 6.1**: Update `deployment_service.py` to use DB capabilities
3. ✅ **Task 6.2**: Update `resource_usage_service.py` to remove `sites_limit`
4. ✅ **Task 6.3**: Update `infrastructure_service.py` (if needed)
5. ✅ **Task 7**: Remove `can_deploy_new_site()` method and all references
6. ✅ **Task 8.1**: Run data migration to populate `capabilities`
7. ✅ **Task 8.2-8.4**: Remove legacy fields from model and run schema migration

**Test after each task** before proceeding to the next.

---

## 📁 Files to Modify (Summary)

### DELETE
- `workspace/hosting/services/subscription_integration_service.py` ← **DELETE ENTIRE FILE**

### Service Files - Refactor to Use DB Capabilities
- `workspace/hosting/services/deployment_service.py`
- `workspace/hosting/services/resource_usage_service.py`
- `workspace/hosting/services/infrastructure_service.py`

### Models - Remove Legacy Fields
- `workspace/hosting/models.py` (HostingEnvironment, DeployedSite)

### GraphQL - Deprecate Old Fields
- `workspace/hosting/graphql/types/usage_types.py`

### Migrations
- Create data migration to populate `capabilities`
- Create schema migration to remove deprecated `*_limit` fields

---

## 🚨 Common Pitfalls to Avoid

1. **Don't delete USAGE tracking fields**
   - ✅ KEEP: `storage_used_gb`, `bandwidth_used_gb`, `active_sites_count`
   - ❌ DELETE: `storage_limit_gb`, `bandwidth_limit_gb`, `sites_limit`, `custom_domains_limit`

2. **Don't check site counts in hosting module**
   - DB constraint `unique_active_site_per_workspace` handles this automatically
   - Theme module will handle theme library limits separately

3. **Don't read from hardcoded dicts or plan fields**
   - ❌ BAD: `SUBSCRIPTION_HOSTING_TIERS[tier]['sites_limit']`
   - ❌ BAD: `subscription.plan.sites_limit`
   - ✅ GOOD: `hosting_env.capabilities['deployment_allowed']`

4. **Don't forget to register hosting receivers**
   - Ensure `workspace/hosting/apps.py` imports receivers in `ready()` method

5. **Don't break the event flow**
   - Subscription events → Receivers → Tasks → Update DB
   - Services should NEVER manually set capabilities
   - Tasks are the ONLY place that writes to `capabilities` field

---

## 🔧 Debugging Tips

If capabilities aren't updating:
1. Check Celery is running: `celery -A backend worker -l info`
2. Verify receivers registered: Check `workspace/hosting/apps.py`
3. Check task logs: Look for `update_hosting_capabilities` in Celery output
4. Verify events emitted: Check subscription module signals
5. Test task manually:
   ```python
   from workspace.hosting.tasks import update_hosting_capabilities
   update_hosting_capabilities.delay(user_id='...', new_tier='pro', event_type='test')
   ```

---

## 📞 Questions?

If you encounter issues:
1. Check `subscription/services/plans.yaml` for current capability definitions
2. Verify receivers are registered in `workspace/hosting/apps.py`
3. Check Celery logs for task execution
4. Confirm DB constraints in `theme/models/template_customization.py` (one active theme)
5. Confirm DB constraints in `workspace/hosting/models.py` (one active site)

---

**Remember**: The goal is **ZERO hardcoded logic**. Everything reads from the database `capabilities` record. The event-driven system keeps it updated.

**Good luck! 🚀**
