# Shared Analytics Components

## Tier-based Analytics Implementation:
**Free:** No analytics  
**Side Huzilerz:** Basic analytics  
**Boss:** Extended analytics (90-day window)  
**Enterprise:** Advanced analytics (unlimited history, cohorts, exports)

## Components to be implemented:

### 1. WebsiteAnalytics.tsx
**Tracks deployed template performance:**
- Traffic trends and visitor counts
- Page views and bounce rates  
- Conversion funnel analysis
- Geographic visitor distribution
- Device and browser analytics

### 2. ProfileAnalytics.tsx
**Tracks business profile/public slug performance:**  
**Tier: Boss+**
- Profile visit statistics
- CTA click-through rates
- Contact form submissions
- Social media click tracking
- Lead generation metrics

### 3. RevenueAnalytics.tsx
**Store:** Order value, product performance  
**Blog:** Ad revenue, sponsorship income  
**Services:** Booking revenue, service performance
- Revenue trends and forecasting
- Top performing products/content/services
- Customer lifetime value
- Revenue breakdown by source

### 4. AdvancedAnalytics.tsx
**Enterprise Only:**
- Cohort analysis and retention
- Custom event tracking
- Raw data export (CSV/Excel)
- API access for analytics data
- Multi-site comparison analytics

### 5. AnalyticsDashboard.tsx
- Unified analytics dashboard
- Customizable widget layout
- Real-time vs historical data toggle
- Export functionality (tier-restricted)

### 6. TierUpgradePrompt.tsx
- Analytics feature comparison
- Upgrade prompts for locked features
- Tier-specific feature highlights