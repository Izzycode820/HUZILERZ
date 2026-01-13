#!/bin/bash

###############################################################################
# Theme Deployment Script
# Builds and uploads theme to S3 + CloudFront CDN
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

if [ ! -f "dist/entry.js" ]; then
    echo -e "${RED}✗ Build failed: dist/entry.js not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Build complete: dist/entry.js"

# Step 3: Upload to S3
S3_PATH="themes/${THEME_NAME}/${VERSION}/bundle.js"
S3_URI="s3://${S3_BUCKET}/${S3_PATH}"
CDN_URL="https://cdn.huzilerz.com/${S3_PATH}"

echo -e "${BLUE}Uploading to S3...${NC}"
aws s3 cp dist/entry.js "${S3_URI}" \
    --content-type "application/javascript" \
    --cache-control "public, max-age=31536000, immutable" \
    --metadata "theme=${THEME_NAME},version=${VERSION}"

echo -e "${GREEN}✓${NC} Uploaded to: ${S3_URI}"

# Step 4: Also upload sourcemap
if [ -f "dist/entry.js.map" ]; then
    echo -e "${BLUE}Uploading sourcemap...${NC}"
    aws s3 cp dist/entry.js.map "s3://${S3_BUCKET}/themes/${THEME_NAME}/${VERSION}/bundle.js.map" \
        --content-type "application/json" \
        --cache-control "public, max-age=31536000, immutable"
    echo -e "${GREEN}✓${NC} Sourcemap uploaded"
fi

# Step 5: Invalidate CloudFront cache (only if updating existing version)
echo -e "${BLUE}Invalidating CloudFront cache...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
    --paths "/themes/${THEME_NAME}/${VERSION}/*" \
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
echo -e "CDN URL: ${CDN_URL}"
echo -e ""
echo -e "Next steps:"
echo -e "1. Update your database to use this theme version"
echo -e "2. Test at: https://your-store.huzilerz.com"
echo -e "3. Monitor CloudFront cache hit rate"
echo -e "${GREEN}================================${NC}"
