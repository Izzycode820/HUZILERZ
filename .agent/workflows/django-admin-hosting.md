---
description: Build Django admin panels for production monitoring (solo dev)
---

# Django Admin Panel Development Workflow

## Context
Building production-ready Django admin panels for a SaaS platform. Designed for solo developers who need to monitor their system in early stages with room for extension.

## Current Focus: Hosting Module Admin
The `workspace.hosting` module handles domain management, SSL certificates, CDN, bandwidth tracking, and site deployments.

---

## Critical Best Practices (Django 6.0+)

### 1. format_html vs mark_safe
```python
# ❌ WRONG - Django 6.0 requires at least one format argument
return format_html('<span style="color: red;">Error</span>')

# ✅ CORRECT - Use mark_safe for static HTML
from django.utils.html import format_html, mark_safe
return mark_safe('<span style="color: red;">Error</span>')

# ✅ CORRECT - Use format_html when you have variables
return format_html('<span>{}</span>', variable)
```

### 2. Number Formatting
```python
# ❌ WRONG - format_html doesn't support Python format specifiers
return format_html('<strong>{:,.0f} XAF</strong>', amount)

# ✅ CORRECT - Pre-format numbers, then pass to format_html
amount_formatted = f"{amount:,.0f}"
return format_html('<strong>{} XAF</strong>', amount_formatted)
```

### 3. Always Import Both
```python
from django.utils.html import format_html, mark_safe
```

---

## Admin Template Locations
For custom changelist templates, the path must be:
```
app_name/templates/admin/app_label/model_name/change_list.html
```
Example for Subscription model:
```
subscription/templates/admin/subscription/subscription/change_list.html
```

---

## Color Coding Standards (Consistent UX)

| Status | Color | Hex |
|--------|-------|-----|
| Active/Success | Green | #28a745 |
| Warning/Pending | Yellow | #ffc107 |
| Grace Period/Soon | Orange | #fd7e14 |
| Error/Expired | Red | #dc3545 |
| Neutral/Inactive | Gray | #6c757d |
| Info/Processing | Blue | #17a2b8 |
| Premium/Special | Purple | #6f42c1 |

---

## Standard Admin Features to Include

### List Display
- Color-coded status badges
- Linked related objects (clickable user, workspace, etc.)
- Date formatting with relative indicators
- Pre-formatted currency amounts

### Filters
- Status filters
- Date field filters using `admin.DateFieldListFilter`
- Related model filters

### Search
- Email, name, ID fields
- Transaction/reference IDs

### Actions
- Bulk status changes
- Export to CSV
- Manual intervention actions

### Inlines
- Related history/logs
- Payment records

### Detail View
- Health summary section
- Linked related objects
- Collapsible metadata sections

---

## Query Optimization
Always use `select_related` and `prefetch_related`:
```python
def get_queryset(self, request):
    return super().get_queryset(request).select_related(
        'user', 'workspace', 'related_model'
    )
```

---

## Dashboard Metrics Pattern
Override `changelist_view` to add dashboard metrics:
```python
def changelist_view(self, request, extra_context=None):
    extra_context = extra_context or {}
    extra_context['dashboard_metrics'] = {
        'total_active': Model.objects.filter(status='active').count(),
        # ... more metrics
    }
    return super().changelist_view(request, extra_context=extra_context)
```

---

## Hosting Module - Key Models to Admin

Based on typical hosting patterns, expect these models:
- **Domain** - Custom domain management
- **SSLCertificate** - Let's Encrypt certs
- **HostingEnvironment** - S3/CloudFront resources
- **BandwidthUsage** - Monthly tracking
- **Site/Deployment** - Published sites

### Critical Monitoring for Hosting
1. Domain verification status
2. SSL certificate expiry
3. Bandwidth usage vs limits
4. Failed deployments
5. DNS propagation status

---

// turbo-all
