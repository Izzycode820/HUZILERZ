import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
from subscription.models import Subscription, SubscriptionPlan

try:
    u = User.objects.get(email='test@example.com')
    print('User:', u.email)
    try:
        sub = u.subscription
        print('Subscription:', sub.plan.tier, sub.status)
    except:
        print('No subscription')
except User.DoesNotExist:
    print('User not found')

free_plan = SubscriptionPlan.objects.filter(tier='free').first()
print('Free plan exists:', bool(free_plan))
if free_plan:
    print('Free plan name:', free_plan.name)
