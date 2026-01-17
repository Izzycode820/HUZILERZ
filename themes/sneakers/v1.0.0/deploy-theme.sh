#!/bin/bash

###############################################################################
# Theme Deployment Script
# Builds and uploads theme to S3 + CloudFront CDN
# Includes metadata files for S3-based theme discovery
###############################################################################

set -e  # Exit on error

# Configuration
S3_BUCKET="huzilerz-themes"
CLOUDFRONT_DISTRIBUTION_ID="E2C7AGJ9F3E9JP"
THEME_NAME="sneakers"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Theme Deployment Script${NC}"
echo -e "${BLUE}================================${NC}"

# Step 1: Get version from package.json
VERSION=$(node -p "require('./package.json').version")
echo -e "${GREEN}✓${NC} Theme version: ${VERSION}"

# Step 2: Build theme
echo -e "${BLUE}Building theme...${NC}"
npm run build:theme

if [ ! -f "dist/bundle.iife.js" ]; then
    echo -e "${RED}✗ Build failed: dist/bundle.iife.js not found${NC}"
    echo -e "${YELLOW}Checking dist directory contents...${NC}"
    ls -la dist/ 2>/dev/null || echo "dist/ directory not found"
    exit 1
fi

echo -e "${GREEN}✓${NC} Build complete: dist/bundle.iife.js"

# Step 3: Copy metadata files to dist for unified upload
echo -e "${BLUE}Copying metadata files to dist...${NC}"

# Copy theme-manifest.json (REQUIRED for S3 discovery)
if [ -f "theme-manifest.json" ]; then
    cp theme-manifest.json dist/
    echo -e "${GREEN}  ✓ theme-manifest.json${NC}"
else
    echo -e "${RED}ERROR: theme-manifest.json not found! Required for theme discovery.${NC}"
    exit 1
fi

# Copy puck.data.json (REQUIRED for editor)
if [ -f "puck.data.json" ]; then
    cp puck.data.json dist/
    echo -e "${GREEN}  ✓ puck.data.json${NC}"
else
    echo -e "${YELLOW}  ⚠ puck.data.json not found${NC}"
fi

# Copy screenshots folder (for preview images)
if [ -d "screenshots" ]; then
    cp -r screenshots dist/
    echo -e "${GREEN}  ✓ screenshots/${NC}"
elif [ -d "screenshot" ]; then
    cp -r screenshot dist/screenshots
    echo -e "${GREEN}  ✓ screenshot/ -> screenshots/${NC}"
else
    echo -e "${YELLOW}  ⚠ No screenshots folder found${NC}"
fi

# Step 4: Upload entire dist directory to S3
S3_PREFIX="${THEME_NAME}/${VERSION}"
S3_URI="s3://${S3_BUCKET}/${S3_PREFIX}/"
CDN_URL="https://cdn.huzilerz.com/${S3_PREFIX}"

echo -e "${BLUE}Uploading to S3...${NC}"
echo -e "${CYAN}  Destination: ${S3_URI}${NC}"

# Sync entire dist folder with appropriate content types
aws s3 sync dist/ "${S3_URI}" \
    --cache-control "public, max-age=31536000, immutable" \
    --metadata "theme=${THEME_NAME},version=${VERSION}" \
    --exclude "*.map"

# Upload maps separately with lower cache time (for debugging)
if [ -f "dist/bundle.iife.js.map" ]; then
    echo -e "${BLUE}Uploading sourcemaps...${NC}"
    aws s3 cp "dist/bundle.iife.js.map" "s3://${S3_BUCKET}/${S3_PREFIX}/bundle.iife.js.map" \
        --content-type "application/json" \
        --cache-control "public, max-age=604800"
fi

echo -e "${GREEN}✓${NC} Upload complete"

# Step 5: Invalidate CloudFront cache
echo -e "${BLUE}Invalidating CloudFront cache...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
    --paths "/${S3_PREFIX}/*" \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}✓${NC} CloudFront invalidation created: ${INVALIDATION_ID}"

# Step 6: Summary
echo -e ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Theme: ${THEME_NAME}"
echo -e "Version: ${VERSION}"
echo -e "S3 Path: s3://${S3_BUCKET}/${S3_PREFIX}/"
echo -e ""
echo -e "CDN URLs:"
echo -e "  Bundle:    ${CDN_URL}/bundle.iife.js"
echo -e "  CSS:       ${CDN_URL}/bundle.css"
echo -e "  Manifest:  ${CDN_URL}/theme-manifest.json"
echo -e ""
echo -e "Next steps:"
echo -e "1. SSH to backend EC2 and run: python manage.py sync_themes"
echo -e "2. Test at: https://your-store.huzilerz.com"
echo -e "3. Check admin for new theme version"
echo -e "${GREEN}================================${NC}"
