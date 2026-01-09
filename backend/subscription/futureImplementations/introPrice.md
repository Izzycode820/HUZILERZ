================================================================================
INTRO PRICING MODELS - IMPLEMENTATION GUIDE
================================================================================

CURRENT: OPTION A - Fixed-Duration Intro (Simpler, Active)
-----------------------------------------------------------
Intro pricing is ONE custom-duration period, then switches to regular cycles.

How it works:
- User gets intro period of ANY duration (e.g., 28 days, 18 days, 90 days)
- After intro expires, all future cycles use regular pricing at standard duration
- intro_cycles_remaining is always 1
- intro_duration_days can be any value (28, 18, 90, etc.)

Example (Pro tier):
  Day 0-28:  Intro period @ 2,500 XAF (28 days)
  Day 29-58: Regular cycle @ 25,000 XAF (30 days)
  Day 59+:   Regular cycles @ 25,000 XAF (30 days each)

Files to check:
- plans.yaml: intro.price, intro.duration_days
- initiate_subscription: intro_cycles_remaining = 1
- activate_subscription_from_payment: Decrements intro_cycles_remaining

FUTURE: OPTION B - Multi-Cycle Intro (More Flexible, Not Implemented)
----------------------------------------------------------------------
Intro pricing applied for N regular billing cycles at standard duration.

How it would work:
- Intro pricing for multiple STANDARD cycles (e.g., 3 months @ 30 days each)
- Each cycle duration is always 30 days (monthly) or 365 days (yearly)
- Remove intro_duration_days concept entirely
- Add intro_cycles_count to plans.yaml (e.g., 3 for "first 3 months")
- Auto-set intro_cycles_remaining on subscription creation

Example (Pro tier with 3-month intro):
  Month 1: @ 2,500 XAF (30 days) - intro_cycles_remaining = 3 → 2
  Month 2: @ 2,500 XAF (30 days) - intro_cycles_remaining = 2 → 1
  Month 3: @ 2,500 XAF (30 days) - intro_cycles_remaining = 1 → 0
  Month 4+: @ 25,000 XAF (30 days) - Regular pricing forever

To implement Option B:
1. Update plans.yaml:
   - Remove: intro.duration_days
   - Add: intro.cycles_count (e.g., 3)

2. Update initiate_subscription (line ~158):
   - Change: intro_cycles_remaining = plan.intro_cycles_count
   - Change: cycle_duration_days = 30 (monthly) or 365 (yearly)

3. Update activate_subscription_from_payment:
   - Already decrements intro_cycles_remaining (line 379-386)
   - Already switches to regular when exhausted

4. Update GraphQL billing_overview query:
   - Already calculates next bill based on intro_cycles_remaining (line 104-121)

5. Update initiate_manual_renewal:
   - Already checks intro_cycles_remaining for pricing (line 708-715)

Note: Option B requires standardized cycle durations (no custom 28-day intros).
      All intro cycles must match regular cycle duration (30 or 365 days).

================================================================================