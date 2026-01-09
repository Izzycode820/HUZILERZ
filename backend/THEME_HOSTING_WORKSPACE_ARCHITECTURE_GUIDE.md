# Theme ↔ Hosting ↔ Workspace Architecture Guide
**Session Continuation Guide - For Claude**

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Current Implementation Status](#current-implementation-status)
3. [Key Files and Their Operations](#key-files-and-their-operations)
4. [What Needs to be Fixed](#what-needs-to-be-fixed)
5. [Complete Flow Diagrams](#complete-flow-diagrams)
6. [Implementation Checklist](#implementation-checklist)

---

## Architecture Overview

### **The Core Principle:**
**Workspace creation = Infrastructure provisioning happens ONCE**
**Theme publish = Just boolean swap (is_active)**
**Tier changes = Infrastructure migration**

### **Module Responsibilities:**

#### **Workspace Module** (Core)
- Creates workspace with unique slug
- Triggers infrastructure setup based on user's tier
- Manages workspace lifecycle
- **DOES NOT** handle themes or hosting directly

#### **Hosting Module**
- Provisions infrastructure based on subscription tier
- Manages DNS, CloudFront, SSL, custom domains
- Handles tier upgrades/downgrades
- **DOES NOT** manage theme is_active state

#### **Theme Module**
- Manages theme library (cloning, customization)
- Handles is_active boolean swap (one active per workspace)
- Stores puck data/config
- **DOES NOT** call hosting module directly

### **The Separation:**
```
┌─────────────┐
│  Workspace  │ ──[creates]──> ┌──────────┐
│   Module    │                │ Hosting  │
└─────────────┘                │  Module  │
       │                       └──────────┘
       │                             │
       │                             │
       │                       [Provisions]
       │                             │
       ▼                             ▼
  Workspace                   Infrastructure
  (slug, name)                (DNS, CDN, tier)
       │
       │
       │
       ▼
  ┌──────────┐
  │  Theme   │
  │  Module  │
  └──────────┘
       │
       ▼
  Theme Library
  (is_active, puck_data)
```

**Communication:**
- Workspace → Hosting: **Signals/Events** (on creation, tier change)
- Theme → Hosting: **NONE** (completely separate)
- Hosting → Theme: **Read-only** (queries is_active for deployment logs)

---

## Current Implementation Status

### ✅ **What's Working:**

1. **Workspace slug uniqueness**
   - File: `backend/workspace/core/models/workspace_model.py`
   - DB constraint + app-level validation
   - Auto-generation with random suffix

2. **DeployedSite subdomain uniqueness**
   - File: `backend/workspace/hosting/models.py`
   - DB constraint on subdomain field
   - Signal creates DeployedSite on workspace creation

3. **Theme is_active boolean swap**
   - File: `backend/theme/models/template_customization.py`
   - DB constraint: Only one is_active per workspace
   - Auto-unpublishes other themes on save()

4. **Public puck data query**
   - File: `backend/theme/graphql/queries/public_puck_data_query.py`
   - Returns active theme's puck data
   - Uses X-Store-Hostname header (no JWT)

### 🚨 **What's Broken/Wrong:**

1. **Theme service incorrectly updates DeployedSite**
   - Currently: `publish_theme()` updates hosting module
   - Problem: Violates separation of concerns
   - Fix: Remove hosting calls from theme service

2. **Missing tier-based infrastructure setup**
   - Currently: Signal creates DeployedSite with status='inactive'
   - Problem: Doesn't provision infrastructure based on tier
   - Fix: Add tier-based provisioning logic

3. **Deployment service calls wrong method**
   - Currently: Calls `publish_customization()` (doesn't exist)
   - Problem: Will crash
   - Status: PARTIALLY FIXED (added `publish_for_deployment()`)
   - Remaining: Should deployment service even call theme?

4. **No tier upgrade/downgrade handling**
   - Currently: No signals for tier changes
   - Problem: Infrastructure doesn't migrate when user upgrades
   - Fix: Add subscription tier change signals

5. **Missing domain in workspace API**
   - Currently: WorkspaceSerializer doesn't return subdomain/domain
   - Problem: Frontend can't show user their URL
   - Fix: Add domain computed field

---

## Key Files and Their Operations

### **Workspace Module**

#### `backend/workspace/core/models/workspace_model.py`
**Lines:** 11-140
**Operations:**
- Defines Workspace model (id, name, slug, type, owner)
- `_generate_unique_slug()`: Creates unique slug with random suffix
- `clean()`: Validates slug uniqueness
- `save()`: Auto-generates slug if missing

**Current State:** ✅ Working correctly

---

#### `backend/workspace/core/signals.py`
**Lines:** 28-68
**Operations:**
- `setup_workspace_extensions()`: Creates workspace-specific extensions
- `assign_subdomain_to_workspace()`: Creates DeployedSite on workspace creation

**Current Implementation:**
```python
@receiver(post_save, sender='workspace_core.Workspace')
def assign_subdomain_to_workspace(sender, instance, created, **kwargs):
    if created:
        DeployedSite.objects.create(
            workspace=instance,
            subdomain=instance.slug,
            status='inactive',  # ❌ Always inactive, no tier logic
            template=None,
            customization=None,
        )
```

**Problem:** Doesn't provision infrastructure based on tier

**Fix Needed:**
```python
@receiver(post_save, sender='workspace_core.Workspace')
def provision_workspace_infrastructure(sender, instance, created, **kwargs):
    if created:
        from workspace.hosting.services.infrastructure_service import InfrastructureProvisioningService

        # Get user's tier
        user_tier = instance.owner.get_subscription_tier()

        # Provision infrastructure based on tier
        InfrastructureProvisioningService.provision_for_workspace(
            workspace=instance,
            tier=user_tier
        )
```

---

#### `backend/workspace/core/serializers/core_serializers.py`
**Lines:** 33-77
**Operations:**
- Serializes workspace for REST API
- Returns: id, name, type, status, member_count

**Current Implementation:**
```python
fields = [
    'id', 'name', 'type', 'status', 'permissions',
    'member_count', 'created_at', 'updated_at'
]
# ❌ Missing: slug, domain
```

**Fix Needed:**
```python
class WorkspaceSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(read_only=True)
    domain = serializers.SerializerMethodField()

    fields = [
        'id', 'name', 'slug', 'type', 'status',
        'domain', 'permissions', 'member_count',
        'created_at', 'updated_at'
    ]

    def get_domain(self, obj):
        """Return user's storefront domain"""
        deployed_site = obj.deployed_sites.first()
        if deployed_site:
            return f"{deployed_site.subdomain}.huzilerz.com"
        return None
```

---

### **Hosting Module**

#### `backend/workspace/hosting/models.py`
**Lines:** 330-621
**Operations:**
- Defines DeployedSite model
- Links workspace to infrastructure
- Stores subdomain, status, tier-specific config

**Key Fields:**
- `workspace`: FK to Workspace
- `subdomain`: Unique subdomain (johns-shop)
- `status`: 'inactive', 'active', 'suspended'
- `template`: FK to Template (set on clone)
- `customization`: FK to TemplateCustomization (set on publish)
- `hosting_environment`: FK to tier-based infrastructure

**Current State:** ✅ Model structure correct

---

#### `backend/workspace/hosting/services/deployment_service.py`
**Lines:** 1-500
**Operations:**
- Orchestrates deployment based on tier
- `can_user_deploy()`: Validates subscription limits
- `deploy_site()`: Sets up DNS/CDN routing
- `_setup_pool_routing()`: Basic tier (shared infrastructure)
- `_setup_bridge_routing()`: Pro tier (dedicated CloudFront)
- `_setup_silo_routing()`: Enterprise tier (isolated)

**Current Implementation (Line 140-147):**
```python
# Step 1: Publish customization (sets is_active=True, idempotent)
from theme.services.template_customization_service import TemplateCustomizationService
published_customization = TemplateCustomizationService.publish_for_deployment(
    workspace_id=workspace.id,
    user=user
)
```

**Problem:** Deployment service calls theme module - violates separation

**Questions to Resolve:**
1. Should `deploy_site()` even exist for basic tier?
2. Is this endpoint ONLY for custom domains/premium features?
3. Should basic tier users never call this?

**Likely Answer:**
- Basic tier (POOL): Infrastructure already set up on workspace creation → NO deployment needed
- Pro/Enterprise: This endpoint adds custom domain, premium CDN → Theme publish SEPARATE

---

#### `backend/workspace/hosting/views.py`
**Lines:** 453-690
**Operations:**
- REST API endpoint: `POST /api/hosting/deploy_site/`
- Validates subscription tier
- Calls DeploymentService.deploy_site()

**Current Implementation (Line 595-604):**
```python
if deployment_result['success']:
    try:
        TemplateCustomizationService.publish_for_deployment(
            workspace_id=workspace_id,
            user=request.user
        )
```

**Problem:** Same as above - deployment endpoint calls theme module

**Fix:** Remove theme service call (deployment != theme publish)

---

### **Theme Module**

#### `backend/theme/models/template_customization.py`
**Lines:** 1-272
**Operations:**
- Defines TemplateCustomization model
- `is_active`: Boolean (only one True per workspace)
- `publish()`: Sets is_active=True, auto-unpublishes others
- `unpublish()`: Sets is_active=False
- DB constraint: `UniqueConstraint(fields=['workspace'], condition=Q(is_active=True))`

**Current Implementation (Line 170-176):**
```python
def save(self, *args, **kwargs):
    if self.is_active:
        # Auto-unpublish all other themes in this workspace
        TemplateCustomization.objects.filter(
            workspace=self.workspace,
            is_active=True
        ).exclude(pk=self.pk).update(is_active=False)
    super().save(*args, **kwargs)
```

**Current State:** ✅ Correct - handles is_active swap automatically

---

#### `backend/theme/services/template_customization_service.py`
**Lines:** 1-279
**Operations:**
- `clone_template_to_workspace()`: Creates draft customization
- `save_customizations()`: Updates puck_data/config
- `publish_theme()`: Publishes theme (sets is_active=True)
- `publish_for_deployment()`: Idempotent publish for hosting module

**Current Implementation (Line 195-210):**
```python
def publish_theme(customization_id, user):
    customization.publish(user=user)

    # ❌ WRONG: Updates hosting module
    deployed_site = DeployedSite.objects.get(workspace=customization.workspace)
    deployed_site.customization = customization
    deployed_site.status = 'active'
    deployed_site.save()
```

**Problem:** Theme service modifying hosting module state

**Fix:**
```python
def publish_theme(customization_id, user):
    """Publish theme - ONLY sets is_active=True"""
    customization = TemplateCustomization.objects.get(id=customization_id)

    with transaction.atomic():
        customization.publish(user=user)  # Sets is_active=True

    return customization
    # ✅ DONE - No hosting module interaction
```

---

#### `backend/theme/services/template_customization_service.py` (Lines 221-275)
**`publish_for_deployment()` method**

**Current Implementation:**
- Created to fix deployment service calling wrong method
- Idempotent: Returns active theme if exists, publishes draft otherwise

**Question:** Should this method exist at all?

**Answer:**
- If deployment endpoint is ONLY for custom domains/premium → **YES, keep it**
- If basic tier never deploys → **MAYBE not needed**
- It's idempotent and safe → **KEEP for now**

---

#### `backend/theme/graphql/mutations/theme_management_mutations.py`
**Lines:** 138-191
**Operations:**
- GraphQL mutation: `publishTheme(id)`
- Validates ownership
- Calls TemplateCustomizationService.publish_theme()

**Current State:** ✅ Correct - just calls service

---

#### `backend/theme/graphql/queries/public_puck_data_query.py`
**Lines:** 1-110
**Operations:**
- Public GraphQL query (no JWT)
- Extracts subdomain from X-Store-Hostname header
- Looks up DeployedSite by subdomain
- Returns active theme's puck_data

**Current Implementation (Line 75-90):**
```python
deployed_site = DeployedSite.objects.get(subdomain=subdomain, status='active')

active_customization = TemplateCustomization.objects.filter(
    workspace=deployed_site.workspace,
    is_active=True
).first()

return PuckDataResponse(
    success=True,
    data=active_customization.puck_data
)
```

**Current State:** ✅ Correct - reads is_active, doesn't modify

---


---

#### 4. Add Tier Upgrade/Downgrade Handler

### **Priority 3: CLEANUP (Remove wrong connections)**

#### 5. Review Deployment Service Theme Calls
**File:** `backend/workspace/hosting/services/deployment_service.py`
**Lines:** 140-147

**Current:**
```python
# Step 1: Publish customization
TemplateCustomizationService.publish_for_deployment(workspace.id, user)
```

**Question:** Should this exist?

**Analysis:**
- `deploy_site()` is called from REST endpoint
- This endpoint is for custom domains/premium features
- User has already published theme via GraphQL mutation

**Decision Options:**

**Option A: Remove theme call entirely**
```python
# Deployment service should NOT publish themes
# User publishes via GraphQL mutation separately
# This endpoint only handles infrastructure
```

**Option B: Keep for backwards compatibility**
```python
# Keep publish_for_deployment() as idempotent safety
# If theme not published, auto-publish
# Allows one-click deployment flow
```

**Recommendation:** Option A (strict separation)

---

#### 6. Review Hosting Views Theme Calls
**File:** `backend/workspace/hosting/views.py`
**Lines:** 595-604

**Current:**
```python
if deployment_result['success']:
    TemplateCustomizationService.publish_for_deployment(workspace_id, request.user)
```

**Same question as above**

**Fix:** Remove this call (theme publish = separate operation)

---


**Key 
**Key Points:**
- Master theme serves ALL users
- Each user gets different puck_data
- is_active determines which theme's data to return
- Infrastructure routing set up on workspace creation
- Theme publish just swaps is_active boolean

---

## Implementation Checklist

### **Session 1: Fix Critical Bugs**

- [ ] **Remove hosting calls from theme service**
  - File: `backend/theme/services/template_customization_service.py`
  - Lines: 195-210
  - Remove: DeployedSite updates from `publish_theme()`

- [ ] **Add domain to WorkspaceSerializer**
  - File: `backend/workspace/core/serializers/core_serializers.py`
  - Add: `slug` and `domain` fields

- [ ] **Review deployment service theme calls**
  - File: `backend/workspace/hosting/services/deployment_service.py`
  - Lines: 140-147
  - Decision: Remove or keep `publish_for_deployment()`?

- [ ] **Review hosting views theme calls**
  - File: `backend/workspace/hosting/views.py`
  - Lines: 595-604
  - Decision: Remove theme service call?

### **Session 2: Infrastructure Provisioning**

- [ ] **Implement tier-based provisioning**
  - File: `backend/workspace/core/signals.py`
  - Replace: `assign_subdomain_to_workspace()`
  - With: `provision_workspace_infrastructure()`

- [ ] **Add tier migration signals**
  - File: `backend/subscription/signals.py` (NEW)
  - Create: `handle_tier_change()`

- [ ] **Create tier migration service**
  - File: `backend/workspace/hosting/services/tier_migration_service.py` (NEW)
  - Implement: Infrastructure migration logic

### **Session 3: Testing & Validation**

- [ ] **Test workspace creation**
  - Verify subdomain assigned
  - Verify infrastructure provisioned based on tier

- [ ] **Test theme publish**
  - Verify is_active swap works
  - Verify NO hosting module calls

- [ ] **Test tier upgrade**
  - Verify infrastructure migrates
  - Verify themes unaffected

- [ ] **Test end-to-end flow**
  - Create workspace → Clone theme → Publish → Customer visit
  - Verify puck data returned correctly

---

## Key Decisions Needed

### **Decision 1: Deployment Service Role**

**Question:** What is `DeploymentService.deploy_site()` for?

**Options:**
A. Custom domains only (Pro/Enterprise feature)
B. Initial infrastructure setup (called once per workspace)
C. Both theme publish + infrastructure (current - WRONG)

**Recommendation:** Option A
- Theme publish = GraphQL mutation (separate)
- deploy_site() = Custom domain setup only

---

### **Decision 2: publish_for_deployment() Method**

**Question:** Should this method exist?

**Current Use:** Called by deployment service
**Problem:** Violates separation of concerns

**Options:**
A. Remove entirely (strict separation)
B. Keep for idempotency (deployment service might need it)

**Recommendation:** Option A if Decision 1 = Option A

---

### **Decision 3: DeployedSite Status Field**

**Question:** What does `status` mean?

**Values:** 'inactive', 'active', 'suspended', 'provisioning'

**Current Usage:**
- 'inactive': Infrastructure not ready
- 'active': Infrastructure ready
- ??? Theme active (is_active in TemplateCustomization)

**Problem:** Confusion between infrastructure status and theme status

**Recommendation:**
- DeployedSite.status = Infrastructure status ONLY
- Theme active status = TemplateCustomization.is_active
- Separate concerns

---


## Next Session TODO

1. **Read this document first**
2. **Make Decision 1, 2, 3** (see Key Decisions section)
3. **Implement Priority 1 fixes** (remove hosting calls from theme)
4. **Implement Priority 2** (tier-based provisioning)
5. **Test complete flow**

---

## Important Notes

- **Theme module = is_active boolean ONLY**
- **Hosting module = Infrastructure provisioning/management**
- **Workspace creation = Infrastructure provisioning happens ONCE**
- **Theme publish = Boolean swap (no infrastructure changes)**
- **Tier changes = Infrastructure migration (no theme changes)**
- **Complete separation of concerns**

**END OF GUIDE**
