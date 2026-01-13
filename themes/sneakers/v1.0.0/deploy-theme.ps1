# PowerShell Theme Deployment Script
# Builds and uploads theme to S3 + CloudFront CDN

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

# Step 3: Upload to S3
$S3_PATH = "themes/$THEME_NAME/$VERSION/bundle.js"
$S3_URI = "s3://$S3_BUCKET/$S3_PATH"
$CDN_URL = "https://cdn.huzilerz.com/$S3_PATH"

Write-Host "Uploading to S3..." -ForegroundColor Blue
aws s3 cp dist/bundle.iife.js $S3_URI --content-type "application/javascript" --cache-control "public, max-age=31536000, immutable" --metadata "theme=$THEME_NAME,version=$VERSION"

Write-Host "Uploaded to: $S3_URI" -ForegroundColor Green

# Step 4: Also upload sourcemap
if (Test-Path "dist/bundle.iife.js.map") {
    Write-Host "Uploading sourcemap..." -ForegroundColor Blue
    aws s3 cp dist/bundle.iife.js.map "s3://$S3_BUCKET/themes/$THEME_NAME/$VERSION/bundle.js.map" --content-type "application/json" --cache-control "public, max-age=31536000, immutable"
    Write-Host "Sourcemap uploaded" -ForegroundColor Green
}

# Step 5: Invalidate CloudFront cache
Write-Host "Invalidating CloudFront cache..." -ForegroundColor Blue
$INVALIDATION_OUTPUT = aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/themes/$THEME_NAME/$VERSION/*" --query "Invalidation.Id" --output text

Write-Host "CloudFront invalidation created: $INVALIDATION_OUTPUT" -ForegroundColor Green

# Step 6: Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Theme: $THEME_NAME"
Write-Host "Version: $VERSION"
Write-Host "CDN URL: $CDN_URL"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Update your database to use this theme version"
Write-Host "2. Test at: https://your-store.huzilerz.com"
Write-Host "3. Monitor CloudFront cache hit rate"
Write-Host "================================" -ForegroundColor Green
