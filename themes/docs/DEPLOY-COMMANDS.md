# Theme Deployment Commands

## Prerequisites (One-Time Setup)

### 1. Configure AWS Credentials
```powershell
# Option A: Set environment variables (session only)
$env:AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_ACCESS_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"

# Option B: Configure AWS CLI permanently
aws configure
# When prompted:
# AWS Access Key ID: YOUR_AWS_ACCESS_KEY_ID
# AWS Secret Access Key: YOUR_AWS_SECRET_ACCESS_KEY
# Default region: us-east-1
# Default output format: json
```

**Verify credentials work:**
```powershell
aws s3 ls
# Should list your buckets (including huzilerz-themes)
```

---

## Standard Deployment Workflow

### Step 1: Build Theme
```powershell
cd c:\S.T.E.V.E\V2\HUZILERZ\themes\sneakers\v1.0.0
npm run build:theme
```

**Expected output:**
```
✓ 2391 modules transformed.
dist/bundle.css       78.13 kB │ gzip:  13.49 kB
dist/bundle.iife.js  712.55 kB │ gzip: 217.17 kB
✓ built in 28.76s
```

**What it does:**
- Bundles all React components, Puck config, styles into single JS file
- Output: `dist/bundle.iife.js` (theme renderer for customers)
- Output: `dist/bundle.css` (Tailwind styles)

---

### Step 2: Deploy to S3 + CloudFront
```powershell
.\deploy-theme.ps1
```

**Expected output:**
```
Theme version: 1.0.0
Building theme...
✓ built in 28.76s
Build complete: dist/bundle.iife.js
Uploading to S3...
upload: dist\bundle.iife.js to s3://huzilerz-themes/themes/sneakers/1.0.0/bundle.js
Uploaded to: s3://huzilerz-themes/themes/sneakers/1.0.0/bundle.js
Uploading sourcemap...
upload: dist\bundle.iife.js.map to s3://huzilerz-themes/themes/sneakers/1.0.0/bundle.js.map
Sourcemap uploaded
Invalidating CloudFront cache...
CloudFront invalidation created: I3VJQH8EXAMPLE
================================
Deployment Complete!
================================
CDN URL: https://dnvvhsr5crm69.cloudfront.net/themes/sneakers/1.0.0/bundle.js
```

**What it does:**
1. Builds theme (runs `npm run build:theme`)
2. Uploads `bundle.iife.js` → S3 bucket `huzilerz-themes`
3. Uploads `bundle.iife.js.map` (sourcemap for debugging)
4. Invalidates CloudFront cache (forces CDN to fetch new version)

---

## Version Updates

### When to Bump Version:
- Bug fixes → Patch version (1.0.0 → 1.0.1)
- New features → Minor version (1.0.1 → 1.1.0)
- Breaking changes → Major version (1.1.0 → 2.0.0)

### How to Bump Version:
```powershell
# Edit package.json manually
# OR use npm version command:
npm version patch   # 1.0.0 → 1.0.1
npm version minor   # 1.0.1 → 1.1.0
npm version major   # 1.1.0 → 2.0.0

# Then deploy
.\deploy-theme.ps1
```

**IMPORTANT:** After deploying new version, update Template record in database:
```sql
-- In Django admin or PostgreSQL
UPDATE theme_templates
SET version = 'v1.0.1'
WHERE slug = 'sneakers';
```

---

## Manual Deployment (If Script Fails)

### Build:
```powershell
npm run build:theme
```

### Upload to S3:
```powershell
$VERSION = "1.0.0"  # Change this
aws s3 cp dist/bundle.iife.js "s3://huzilerz-themes/themes/sneakers/$VERSION/bundle.js" --content-type "application/javascript" --cache-control "public, max-age=31536000, immutable"
aws s3 cp dist/bundle.iife.js.map "s3://huzilerz-themes/themes/sneakers/$VERSION/bundle.js.map" --content-type "application/json" --cache-control "public, max-age=31536000, immutable"
```

### Invalidate CloudFront:
```powershell
aws cloudfront create-invalidation --distribution-id E2C7AGJ9F3E9JP --paths "/themes/sneakers/$VERSION/*"
```

---

## Verification Commands

### Check if file exists in S3:
```powershell
aws s3 ls s3://huzilerz-themes/themes/sneakers/1.0.0/
```

### Test CDN URL in browser:
```
https://dnvvhsr5crm69.cloudfront.net/themes/sneakers/1.0.0/bundle.js
```

### Check CloudFront cache status:
```powershell
# List recent invalidations
aws cloudfront list-invalidations --distribution-id E2C7AGJ9F3E9JP --max-items 5
```

---

## Troubleshooting

### Error: "Unable to locate credentials"
**Cause:** AWS CLI not configured
**Fix:** Run `aws configure` (see Prerequisites above)

### Error: "Access Denied" uploading to S3
**Cause:** Wrong AWS credentials or insufficient permissions
**Fix:** Verify credentials in .env match EC2 production credentials

### Build fails with module errors
**Cause:** Missing dependencies or TypeScript errors
**Fix:**
```powershell
npm install
npm run build:theme
```

### CloudFront still serves old version
**Cause:** Cache not invalidated or invalidation still in progress
**Wait:** Invalidations take 5-15 minutes
**Check:** Visit CDN URL directly (bypass browser cache): Add `?v=timestamp` to URL

---

## Important Notes

### What bundle.js Contains:
- ✅ React + Puck Renderer (displays pages)
- ✅ Theme components (NavBar, Hero, Products, etc.)
- ✅ Puck config (defines available sections)
- ✅ Apollo Client (fetches merchant data)
- ✅ Tailwind styles

### What bundle.js Does NOT Contain:
- ❌ Merchant's puck_data (layout/content) - fetched from backend
- ❌ Product data - fetched from backend
- ❌ Puck Editor (drag-and-drop) - that's in merchant admin panel

### Theme vs Data:
- **Theme (bundle.js):** Shared by ALL merchants, controlled by YOU
- **Data (puck_data):** Unique per merchant, stored in database
- **When merchant customizes:** Only puck_data changes, theme stays same
- **When you update theme:** Change version, all merchants get new bundle

---

## Quick Reference

| Task | Command |
|------|---------|
| Build only | `npm run build:theme` |
| Deploy (build + upload) | `.\deploy-theme.ps1` |
| Version bump (patch) | `npm version patch` |
| Configure AWS | `aws configure` |
| Test credentials | `aws s3 ls` |
| List S3 files | `aws s3 ls s3://huzilerz-themes/themes/sneakers/` |
| Manual upload | `aws s3 cp dist/bundle.iife.js s3://...` |

---

## Emergency Rollback

If new version breaks production:

```powershell
# Revert Template version in database to previous version
# In Django admin:
UPDATE theme_templates SET version = 'v1.0.0' WHERE slug = 'sneakers';

# Customers will immediately use old bundle
# (because URL changes back to old version path)
```

No need to delete new files - old version still exists in S3.
