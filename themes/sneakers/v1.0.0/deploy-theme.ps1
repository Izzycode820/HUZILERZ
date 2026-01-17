# PowerShell Theme Deployment Script
# Builds and uploads theme to S3 + CloudFront CDN
# Includes metadata files for S3-based theme discovery

$ErrorActionPreference = "Stop"

# Configuration
$S3_BUCKET = "huzilerz-themes"
$CLOUDFRONT_DISTRIBUTION_ID = "E2C7AGJ9F3E9JP"
$THEME_NAME = "sneakers"

Write-Host "================================" -ForegroundColor Blue
Write-Host "Theme Deployment Script" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue

# Step 1: Get version from package.json
$package = Get-Content -Path "package.json" | ConvertFrom-Json
$VERSION = $package.version
Write-Host "Theme version: $VERSION" -ForegroundColor Green

# Step 2: Build theme
Write-Host "Building theme..." -ForegroundColor Blue
npm run build:theme

if (-not (Test-Path "dist/bundle.iife.js")) {
    Write-Host "Build failed: dist/bundle.iife.js not found" -ForegroundColor Red
    Write-Host "Checking dist directory contents..." -ForegroundColor Yellow
    if (Test-Path "dist") {
        Get-ChildItem "dist" | ForEach-Object { Write-Host "  - $($_.Name)" }
    }
    exit 1
}

Write-Host "Build complete: dist/bundle.iife.js" -ForegroundColor Green

# Step 3: Copy metadata files to dist for unified upload
Write-Host "Copying metadata files to dist..." -ForegroundColor Blue

# Copy theme-manifest.json (REQUIRED for S3 discovery)
if (Test-Path "theme-manifest.json") {
    Copy-Item "theme-manifest.json" "dist/"
    Write-Host "  - theme-manifest.json" -ForegroundColor Green
} else {
    Write-Host "ERROR: theme-manifest.json not found! Required for theme discovery." -ForegroundColor Red
    exit 1
}

# Copy puck.data.json (REQUIRED for editor)
if (Test-Path "puck.data.json") {
    Copy-Item "puck.data.json" "dist/"
    Write-Host "  - puck.data.json" -ForegroundColor Green
} else {
    Write-Host "WARNING: puck.data.json not found" -ForegroundColor Yellow
}

# Copy screenshots folder (for preview images)
if (Test-Path "screenshots") {
    Copy-Item "screenshots" "dist/" -Recurse -Force
    Write-Host "  - screenshots/" -ForegroundColor Green
} elseif (Test-Path "screenshot") {
    Copy-Item "screenshot" "dist/screenshots" -Recurse -Force
    Write-Host "  - screenshot/ -> screenshots/" -ForegroundColor Green
} else {
    Write-Host "WARNING: No screenshots folder found" -ForegroundColor Yellow
}

# Step 4: Upload entire dist directory to S3
$S3_PREFIX = "$THEME_NAME/$VERSION"
$S3_URI = "s3://$S3_BUCKET/$S3_PREFIX/"
$CDN_URL = "https://cdn.huzilerz.com/$S3_PREFIX"

Write-Host "Uploading to S3..." -ForegroundColor Blue
Write-Host "  Destination: $S3_URI" -ForegroundColor Cyan

# Sync entire dist folder with appropriate content types
aws s3 sync dist/ $S3_URI `
    --cache-control "public, max-age=31536000, immutable" `
    --metadata "theme=$THEME_NAME,version=$VERSION" `
    --exclude "*.map"

# Upload maps separately with lower cache time (for debugging)
if (Test-Path "dist/bundle.iife.js.map") {
    Write-Host "Uploading sourcemaps..." -ForegroundColor Blue
    aws s3 cp "dist/bundle.iife.js.map" "s3://$S3_BUCKET/$S3_PREFIX/bundle.iife.js.map" `
        --content-type "application/json" `
        --cache-control "public, max-age=604800"
}

Write-Host "Upload complete" -ForegroundColor Green

# Step 5: Invalidate CloudFront cache
Write-Host "Invalidating CloudFront cache..." -ForegroundColor Blue
$INVALIDATION_OUTPUT = aws cloudfront create-invalidation `
    --distribution-id $CLOUDFRONT_DISTRIBUTION_ID `
    --paths "/$S3_PREFIX/*" `
    --query "Invalidation.Id" `
    --output text

Write-Host "CloudFront invalidation created: $INVALIDATION_OUTPUT" -ForegroundColor Green

# Step 6: Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Theme: $THEME_NAME"
Write-Host "Version: $VERSION"
Write-Host "S3 Path: s3://$S3_BUCKET/$S3_PREFIX/"
Write-Host ""
Write-Host "CDN URLs:"
Write-Host "  Bundle:    $CDN_URL/bundle.iife.js"
Write-Host "  CSS:       $CDN_URL/bundle.css"
Write-Host "  Manifest:  $CDN_URL/theme-manifest.json"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. SSH to backend EC2 and run: python manage.py sync_themes"
Write-Host "2. Test at: https://your-store.huzilerz.com"
Write-Host "3. Check admin for new theme version"
Write-Host "================================" -ForegroundColor Green

