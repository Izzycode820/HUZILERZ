# Wildcard Domain Setup Guide for huzilerz.com

## Overview
- **Domain**: huzilerz.com (GoDaddy)
- **Backend**: CloudFront + EC2 (AWS)
- **Frontend**: Vercel (Free tier)
- **Goal**: *.huzilerz.com wildcard routing to backend, www.huzilerz.com to Vercel

---

## Step 1: Create Route53 Hosted Zone

### AWS Console → Route53

1. Go to **Route53** → **Hosted zones** → **Create hosted zone**
2. Enter:
   - **Domain name**: `huzilerz.com`
   - **Type**: Public hosted zone
3. Click **Create hosted zone**

4. **Save the NS records** (you'll need these for GoDaddy):
   ```
   ns-1234.awsdns-12.org
   ns-5678.awsdns-34.co.uk
   ns-9012.awsdns-56.com
   ns-3456.awsdns-78.net
   ```

---

## Step 2: Update GoDaddy Nameservers

### GoDaddy Dashboard

1. Log into **GoDaddy** → **My Products** → **Domains**
2. Click on **huzilerz.com** → **Manage DNS**
3. Scroll down to **Nameservers** → Click **Change**
4. Select **Enter my own nameservers (advanced)**
5. Enter all 4 NS records from Route53:
   ```
   ns-1234.awsdns-12.org
   ns-5678.awsdns-34.co.uk
   ns-9012.awsdns-56.com
   ns-3456.awsdns-78.net
   ```
6. Click **Save**

**Note**: DNS propagation takes 15 minutes - 48 hours (usually < 2 hours)

---

## Step 3: Request ACM Wildcard SSL Certificate

### AWS Console → Certificate Manager (us-east-1 REQUIRED for CloudFront)

**IMPORTANT**: Must be in **us-east-1** (N. Virginia) region!

1. Go to **Certificate Manager** → **Request certificate**
2. Select **Request a public certificate** → **Next**
3. Add domain names:
   - `*.huzilerz.com` (wildcard)
   - `huzilerz.com` (root domain)
4. Select **DNS validation**
5. Click **Request**

### Validate Certificate

1. Click on the new certificate → **Create records in Route53**
2. AWS will automatically add CNAME validation records to Route53
3. Click **Create records**
4. Wait 5-30 minutes for validation (status changes to "Issued")

**Tip**: Check status with:
```bash
aws acm list-certificates --region us-east-1
```

---

## Step 4: Update CloudFront Distribution

### AWS Console → CloudFront

1. Go to **CloudFront** → Select your distribution → **Edit**

### General Settings

1. **Alternate Domain Names (CNAMEs)**: Add:
   ```
   *.huzilerz.com
   huzilerz.com
   ```

2. **Custom SSL Certificate**: Select your new `*.huzilerz.com` certificate

3. Click **Save changes**

**Note**: CloudFront deployment takes 5-15 minutes

---

## Step 5: Create DNS Records in Route53

### AWS Console → Route53 → huzilerz.com Hosted Zone

### A) Wildcard Record (for tenant subdomains)

**Create Record**:
- **Name**: `*` (wildcard)
- **Type**: `A - IPv4 address`
- **Alias**: **Yes**
- **Alias Target**: Select your **CloudFront distribution**
  - Choose from dropdown: `d123456abcdef.cloudfront.net`
- **Routing Policy**: Simple routing
- Click **Create records**

This routes all `*.huzilerz.com` → CloudFront → EC2 backend

### B) Root Domain Record (optional)

**Create Record**:
- **Name**: (leave blank for root domain)
- **Type**: `A - IPv4 address`
- **Alias**: **Yes**
- **Alias Target**: Your **CloudFront distribution**
- Click **Create records**

This routes `huzilerz.com` → CloudFront

---

## Step 6: Configure Vercel Frontend DNS

You have 2 options:

### Option A: Frontend on subdomain (Recommended)

Use `www.huzilerz.com` or `app.huzilerz.com` for frontend

#### In Route53:
**Create Record**:
- **Name**: `www` (or `app`)
- **Type**: `CNAME`
- **Value**: `cname.vercel-dns.com`
- **TTL**: 300
- Click **Create records**

#### In Vercel Dashboard:
1. Go to your project → **Settings** → **Domains**
2. Add domain: `www.huzilerz.com`
3. Vercel will show DNS configuration (should match above)
4. Wait for verification

### Option B: Frontend on root domain

If you want frontend on `huzilerz.com`:

1. Remove the root A record from Step 5B
2. In Route53, create A records pointing to Vercel IPs:
   - **Name**: (blank)
   - **Type**: `A`
   - **Value**: `76.76.21.21` (check Vercel docs for current IPs)

**Note**: Option A is better because root domain can be used for marketing/landing pages

---

## Step 7: Verify Configuration

### Check DNS propagation:
```bash
# Check wildcard resolution
nslookup tenant1.huzilerz.com
nslookup tenant2.huzilerz.com

# Check root domain
nslookup huzilerz.com

# Check frontend subdomain
nslookup www.huzilerz.com
```

### Test HTTPS:
```bash
curl -I https://tenant1.huzilerz.com
curl -I https://www.huzilerz.com
```

---

## Architecture Summary

```
*.huzilerz.com (tenant subdomains)
    ↓
Route53 Wildcard A Record
    ↓
CloudFront Distribution (with wildcard SSL)
    ↓
EC2 Backend (Django tenant routing)


www.huzilerz.com (frontend)
    ↓
Route53 CNAME Record
    ↓
Vercel (handles SSL automatically)
```

---

## Troubleshooting

### Issue: Certificate validation stuck
- Ensure you're in **us-east-1** region
- Check Route53 has validation CNAME records
- Wait 30 minutes

### Issue: Subdomain not resolving
- Check CloudFront has `*.huzilerz.com` in CNAMEs
- Verify wildcard A record in Route53 points to CloudFront
- Wait for DNS propagation (up to 48 hours)

### Issue: SSL certificate error
- Ensure CloudFront is using the wildcard certificate
- Certificate must include both `*.huzilerz.com` and `huzilerz.com`
- CloudFront deployment can take 15 minutes

### Issue: Vercel domain not working
- Check CNAME points to `cname.vercel-dns.com`
- Verify domain is added in Vercel dashboard
- Wait for DNS propagation

---

## Next Steps After Setup

1. **Update Django ALLOWED_HOSTS**:
   ```python
   ALLOWED_HOSTS = [
       '.huzilerz.com',  # Allows all subdomains
       'huzilerz.com',
   ]
   ```

2. **Configure CORS** for Vercel frontend:
   ```python
   CORS_ALLOWED_ORIGINS = [
       'https://www.huzilerz.com',
       'https://app.huzilerz.com',
   ]

   CORS_ALLOWED_ORIGIN_REGEXES = [
       r'^https://.*\.huzilerz\.com$',  # Allow all subdomains
   ]
   ```

3. **Update Shopify App URLs** in Shopify Partner Dashboard:
   - App URL: `https://app.huzilerz.com` (or your chosen subdomain)
   - Allowed redirection URLs: `https://*.huzilerz.com/auth/callback`

---

## Estimated Timeline

- **Step 1-3**: 5 minutes (manual setup)
- **Step 3 (ACM validation)**: 5-30 minutes (automatic)
- **Step 4 (CloudFront deploy)**: 5-15 minutes (automatic)
- **Step 2 (GoDaddy nameserver propagation)**: 15 minutes - 48 hours
- **Total**: 30 minutes to 48 hours (typically < 2 hours)

---

## Cost Estimate (AWS)

- Route53 Hosted Zone: $0.50/month
- Route53 Queries: $0.40/million queries
- ACM Certificate: **FREE**
- CloudFront: Based on existing usage
- **Total New Cost**: ~$0.50-$1/month
