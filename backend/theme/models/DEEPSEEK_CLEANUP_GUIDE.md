# DeepSeek AI - Model Cleanup Guide

**Task:** Remove bloat and deprecated logic from theme models to align with new GraphQL-based architecture.

**Context:** We're migrating from entry-file based theme loading to manifest + registry pattern. We're also simplifying from complex version/role/status tracking to Shopify's simple library model.

---

## Files to Clean

### 1. Template Model (`template.py`)

**REMOVE these fields and methods:**

1. **Entry URL (DEPRECATED - lines 224-228)**
   ```python
   entry_url = models.URLField(...)  # DELETE THIS ENTIRE FIELD
   ```

2. **get_entry_url method (lines 316-318)**
   ```python
   def get_entry_url(self):  # DELETE THIS ENTIRE METHOD
       """Get entry URL for dynamic import - use database field directly"""
       return self.entry_url or ''
   ```

3. **Rating fields (OUT OF SCOPE - lines 193-204)**
   ```python
   rating = models.DecimalField(...)  # DELETE
   rating_count = models.PositiveIntegerField(...)  # DELETE
   ```

4. **add_rating method (lines 340-364)**
   ```python
   def add_rating(self, user, rating_value):  # DELETE THIS ENTIRE METHOD
       ...
   ```

5. **Properties related to ratings**
   - No rating properties exist, so nothing to remove here

**KEEP but don't worry about:**
- `manifest_url` and `get_manifest_url()` - We use this
- GitHub fields - Future use, keep for now
- Usage metrics (view_count, download_count) - Useful for analytics

**ADD this field:**
```python
screenshots = models.JSONField(
    default=list,
    blank=True,
    verbose_name="Screenshots",
    help_text="Array of screenshot URLs for theme details page"
)
```
Insert after `preview_image` field (around line 174)

---

### 2. TemplateCustomization Model (`template_customization.py`)

**REMOVE these fields:**

1. **template_version FK (lines 61-67)**
   ```python
   template_version = models.ForeignKey(...)  # DELETE ENTIRE FIELD
   ```
   We're not using TemplateVersion table yet.

2. **custom_css and custom_js (lines 80-89)**
   ```python
   custom_css = models.TextField(...)  # DELETE
   custom_js = models.TextField(...)  # DELETE
   ```
   Users only customize via Puck, not raw code.

3. **status field (lines 92-99)**
   ```python
   status = models.CharField(...)  # DELETE
   ```
   We'll use only `is_active` boolean (Shopify model).

4. **role field (lines 100-107)**
   ```python
   role = models.CharField(...)  # DELETE
   ```
   Overcomplicated. Just use `is_active`.

5. **deployed_at (lines 124-128)**
   ```python
   deployed_at = models.DateTimeField(...)  # DELETE
   ```
   Legacy field, we only need `published_at`.

6. **cache_key (lines 131-137)**
   ```python
   cache_key = models.CharField(...)  # DELETE
   ```
   Premature optimization, CDN caching is future.

7. **Version tracking fields (lines 140-160)**
   ```python
   version = models.PositiveIntegerField(...)  # DELETE
   last_published_version = models.PositiveIntegerField(...)  # DELETE
   parent_customization = models.ForeignKey('self', ...)  # DELETE
   ```
   We're leaving CustomizationHistory for later. Keep it simple.

8. **customization_size (lines 163-167)**
   ```python
   customization_size = models.PositiveIntegerField(...)  # DELETE
   ```
   Not needed for MVP.

**REMOVE these methods:**

1. **clean() method validation for template_version (lines 227-231)**
   Remove the template_version validation block only.

2. **clean() method CSS/JS validation (lines 249-261)**
   Remove entire CSS/JS validation block.

3. **save() version auto-increment logic (lines 268-280)**
   Remove the version increment logic.

4. **save() cache key generation (lines 282-284)**
   Remove cache key logic.

5. **save() role-based active logic (lines 286-293)**
   Simplify to just ensure one active per workspace (no role checking).

6. **_calculate_customization_size (lines 296-316)**
   ```python
   def _calculate_customization_size(self):  # DELETE ENTIRE METHOD
       ...
   ```

7. **create_new_version (lines 318-341)**
   ```python
   def create_new_version(self, user):  # DELETE ENTIRE METHOD
       ...
   ```

8. **publish method (lines 342-365)**
   Delete this complex version - we'll write a simpler one.

9. **archive (lines 367-377)**
   ```python
   def archive(self):  # DELETE ENTIRE METHOD
       ...
   ```

10. **set_as_preview (lines 379-388)**
    ```python
    def set_as_preview(self):  # DELETE ENTIRE METHOD
        ...
    ```

11. **revert_to_version (lines 390-412)**
    ```python
    def revert_to_version(self, target_version):  # DELETE ENTIRE METHOD
        ...
    ```

12. **get_customization_summary (lines 414-426)**
    ```python
    def get_customization_summary(self):  # DELETE ENTIRE METHOD
        ...
    ```

13. **All properties (lines 428-517)**
    Delete ALL properties:
    - `formatted_customization_size`
    - `is_publishable`
    - `has_unpublished_changes`
    - `preview_url`
    - `live_url`
    - `is_deployable`
    - `deployment_status`
    - `version_history`

**UPDATE these:**

1. **unique_together constraint (line 198)**
   Change from:
   ```python
   unique_together = ['workspace', 'template', 'version']
   ```
   To:
   ```python
   # Remove this line entirely - we'll handle uniqueness differently
   ```

2. **indexes (lines 199-207)**
   Remove version and cache_key indexes.

**ADD these fields:**

1. **theme_name field** (insert after template FK)
   ```python
   theme_name = models.CharField(
       max_length=255,
       verbose_name="Theme Name",
       help_text="User-friendly name for this theme (can be renamed)"
   )
   ```

2. **last_edited_at field** (replace updated_at usage)
   ```python
   last_edited_at = models.DateTimeField(
       auto_now=True,
       verbose_name="Last Edited At",
       help_text="When customization was last modified"
   )
   ```

**KEEP:**
- workspace FK ✅
- template FK ✅
- puck_config, puck_data ✅
- is_active ✅
- published_at ✅
- created_at, created_by ✅
- last_modified_by ✅

---

## Important Notes for DeepSeek

1. **Don't break migrations:** After removing fields, you'll need to create Django migrations.

2. **Check validation logic:** After removing fields from `clean()`, ensure the method still works.

3. **Update Meta class:** Remove references to deleted fields in indexes and unique_together.

4. **Model relationships:** Template FK should stay as is, but template_version FK must be removed.

5. **Status choices:** Delete STATUS_CHOICES and ROLE_CHOICES constants entirely.

6. **Imports:** Check if any removed fields used specific imports (e.g., timezone for cache_key generation).

---

## Verification Checklist

After cleanup, verify:
- [ ] No `entry_url` references exist
- [ ] No rating fields or methods exist
- [ ] No CSS/JS fields exist
- [ ] No version tracking fields exist
- [ ] No role/status complexity (just is_active boolean)
- [ ] No cache management code
- [ ] template_version FK removed
- [ ] All complex methods removed
- [ ] theme_name field added
- [ ] screenshots field added to Template
- [ ] Model still has clean() and save() methods (simplified)
- [ ] __str__ methods still work

---

## What Remains After Cleanup

**Template Model:**
- Core: id, name, slug, description
- Type: template_type, workspace_types
- Metadata: features, tags, compatibility, author, license
- Pricing: price_tier, price_amount
- Version: version string
- Status: status (draft/active/deprecated)
- Preview: demo_url, preview_image, screenshots
- Metrics: view_count, download_count, active_usage_count
- Puck: puck_config, puck_data (master copies)
- CDN: manifest_url, cdn_base_url, get_manifest_url()
- GitHub: repo fields (for future)
- Timestamps: created_at, updated_at, created_by

**TemplateCustomization Model:**
- Core: id, workspace, template, theme_name
- Puck: puck_config, puck_data (user's copies)
- Status: is_active (one true per workspace)
- Timestamps: created_at, last_edited_at, published_at
- Users: created_by, last_modified_by

---

**After you finish, save the cleaned files and report back what you removed.**
