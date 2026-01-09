# Subscription System Implementation Plan

## Current System Analysis vs New Requirements

### Current System Strengths (Keep These):
✅ **Models**: Comprehensive subscription, payment, usage tracking, feature management
✅ **Services**: SubscriptionService, PaymentService, TrialService, UsageTrackingService
✅ **Views**: Full API coverage for subscription, payment, trial, pricing
✅ **Infrastructure**: Manual renewal, grace period, Cameroon optimization
✅ **Security**: JWT authentication, multi-tenant support

### Changes Required Based on Requirements:

## 1. TRIAL PRICING STRUCTURE UPDATE

### Files to Modify:
- `subscription/models/trial.py` - TrialConfiguration model
- `subscription/models/subscription.py` - Add trial pricing constants

### Current Logic:
- Generic trial pricing based on percentage discounts
- Complex trial conversion offers

### New Logic:
- **Fixed Trial Pricing**:
  - Beginning: 2k FCFA for 1 month (vs 10k full)
  - Pro: 5k FCFA for 2 months (vs 25k full) 
  - Enterprise: 10k FCFA for 3 months (vs 50k full)

### Implementation:
```python
# Update TrialConfiguration model
TRIAL_PRICING = {
    'beginning': {'price': 2000, 'duration_days': 30, 'full_price': 10000},
    'pro': {'price': 5000, 'duration_days': 60, 'full_price': 25000},
    'enterprise': {'price': 10000, 'duration_days': 90, 'full_price': 50000}
}
```

## 2. USER MODEL EXTENSION FOR TRIAL TRACKING

### Files to Modify:
- `authentication/models.py` (User model)
- Create migration file

### Current Logic:
- Trial tracking through separate Trial model only

### New Logic:
- Add direct fields to User model for performance
- JWT claims integration

### Implementation:
```python
# Add to User model
trial_used = models.BooleanField(default=False)
template_bonus_months_remaining = models.IntegerField(default=0)
trial_eligible_until = models.DateTimeField(null=True, blank=True)
```

## 3. JWT CLAIMS SERVICE UPDATE

### Files to Modify:
- `subscription/services/subscription_claims_service.py`
- Update JWT generation logic

### Current Logic:
- Basic subscription status in JWT

### New Logic:
- Enhanced trial claims for frontend performance

### Implementation:
```python
# Add to JWT claims
{
    "trial_eligible": not user.trial_used,
    "trial_status": "unused|active|expired|converted",
    "subscription_tier": get_user_subscription_tier(user),
    "template_bonus_months": user.template_bonus_months_remaining
}
```

## 4. DISCOUNT SYSTEM SIMPLIFICATION

### Files to Modify:
- `subscription/services/discount_service.py`
- `subscription/models/discounts.py`
- Remove: BaseDiscount, UserDiscount, DiscountStack, SeasonalDiscount

### Current Logic:
- Complex stacking discount system
- New user discounts, template bonuses, seasonal discounts

### New Logic:
- **Only Two Discounts**:
  1. **Yearly Discount**: Monthly vs Annual pricing toggle
  2. **Template Ownership**: 3 months free per template purchase

### Implementation:
```python
# Simplified DiscountService
class DiscountService:
    @staticmethod
    def calculate_yearly_discount(base_price, is_yearly=False):
        return base_price * 0.15 if is_yearly else 0
    
    @staticmethod
    def apply_template_bonus(user, months=3):
        user.template_bonus_months_remaining += months
        user.save()
```

## 5. TEMPLATE PURCHASE AUTOMATION

### Files to Modify:
- `subscription/models/marketplace.py` - Add Django signals
- `subscription/services/subscription_service.py` - Template bonus logic

### Current Logic:
- Manual template purchase processing

### New Logic:
- **Automatic 3-month bonus** via Django signals
- **Three scenarios**:
  - Free user → 3 months free immediately
  - Active subscriber → 3 months added to plan end
  - Expired subscriber → 3 months free without payment

### Implementation:
```python
@receiver(post_save, sender=TemplatePurchase)
def apply_template_bonus(sender, instance, created, **kwargs):
    if created:
        SubscriptionService.apply_template_bonus(
            user=instance.buyer,
            template_purchase=instance
        )
```

## 6. SEPARATE PRICING ENDPOINTS

### Files to Modify:
- `subscription/views/pricing_views.py`
- `subscription/urls.py`

### Current Logic:
- Single pricing endpoint for all users

### New Logic:
- **Separate endpoints** for security:
  - `/api/pricing/trial/` (authenticated - shows trial pricing)
  - `/api/pricing/full/` (public - shows full pricing)
  - Dynamic response based on user trial status

### Implementation:
```python
# New endpoints
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_trial_pricing(request):
    if request.user.trial_used:
        return Response({'error': 'Trial already used'}, 400)
    return Response(trial_pricing_data)

def get_full_pricing(request):
    return Response(full_pricing_data)
```

## 7. FRONTEND DATA STRUCTURE UPDATE

### Files to Modify:
- All pricing API responses
- Add monthly/yearly toggle support

### Current Logic:
- Static pricing data

### New Logic:
- **Dynamic responses** based on:
  - User authentication status
  - Trial eligibility
  - Current subscription status
  - Monthly/yearly preference

## Files Summary - Exact Changes Needed:

### HIGH PRIORITY (Core Changes):
1. `subscription/models/trial.py` - Update pricing structure
2. `authentication/models.py` - Add trial tracking fields
3. `subscription/services/subscription_claims_service.py` - JWT claims
4. `subscription/services/discount_service.py` - Simplify logic
5. `subscription/views/pricing_views.py` - Separate endpoints

### MEDIUM PRIORITY (Enhancement):
6. `subscription/models/marketplace.py` - Django signals
7. `subscription/services/subscription_service.py` - Template bonus logic
8. Migration files for model changes

### LOW PRIORITY (Cleanup):
9. Remove unused discount models
10. Update tests
11. API documentation updates

This plan provides exact file-by-file implementation strategy based on current system analysis, new requirements, and research best practices.