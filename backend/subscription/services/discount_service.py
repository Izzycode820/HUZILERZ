"""
Simplified Discount Service
Handles only yearly billing and template ownership bonuses
"""
from django.utils import timezone
from decimal import Decimal
import logging

from ..models import Discount

logger = logging.getLogger(__name__)

class DiscountService:
    """
    Simplified discount service - no more complex stacking
    """

    @classmethod
    def calculate_yearly_discount(cls, subscription_price, tier):
        """
        Calculate yearly billing discount
        Simple percentage-based discount
        """
        yearly_discount = Discount.get_yearly_discount()
        if not yearly_discount:
            return {
                'discount_amount': Decimal('0.00'),
                'discounted_price': subscription_price,
                'discount_percentage': 0
            }

        # Apply yearly discount
        discount_amount = subscription_price * (yearly_discount.percentage / 100)
        discounted_price = subscription_price - discount_amount

        return {
            'discount_amount': discount_amount,
            'discounted_price': discounted_price,
            'discount_percentage': yearly_discount.percentage,
            'discount_name': yearly_discount.name
        }

    @classmethod
    def apply_template_bonus(cls, user, subscription, template_id):
        """
        Apply template ownership bonus - 3 months free
        """
        template_bonus = Discount.get_template_bonus()
        if not template_bonus:
            logger.warning("No active template bonus found")
            return False

        # Check if user already used bonus for this template
        existing_bonus = UserDiscount.objects.filter(
            user=user,
            discount=template_bonus,
            template_id=template_id
        ).exists()

        if existing_bonus:
            logger.info(f"User {user.id} already used template bonus for {template_id}")
            return False

        # Apply bonus based on subscription status
        if subscription.status == 'active':
            # Extend current subscription
            cls._extend_subscription(subscription, template_bonus.bonus_months)
        else:
            # Reactivate with bonus months
            cls._reactivate_with_bonus(subscription, template_bonus.bonus_months)

        # Record the bonus usage
        UserDiscount.objects.create(
            user=user,
            discount=template_bonus,
            subscription=subscription,
            months_added=template_bonus.bonus_months,
            template_id=template_id
        )

        # Update user eligibility
        eligibility = user.trial_eligibility
        eligibility.add_owned_template(template_id)
        eligibility.use_template_bonus()

        logger.info(f"Applied template bonus: {template_bonus.bonus_months} months for user {user.id}")
        return True

    @classmethod
    def _extend_subscription(cls, subscription, months):
        """Extend active subscription by months"""
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        # Add months to expiry date
        subscription.expires_at += relativedelta(months=months)
        subscription.save()

        logger.info(f"Extended subscription {subscription.id} by {months} months")

    @classmethod
    def _reactivate_with_bonus(cls, subscription, months):
        """Reactivate expired subscription with bonus months"""
        from dateutil.relativedelta import relativedelta

        # Reactivate subscription
        subscription.status = 'active'
        subscription.expires_at = timezone.now() + relativedelta(months=months)
        subscription.save()

        logger.info(f"Reactivated subscription {subscription.id} with {months} months")

    @classmethod
    def get_available_discounts(cls, user, subscription_type='monthly'):
        """
        Get available discounts for user
        """
        discounts = []

        # Yearly billing discount
        if subscription_type == 'monthly':
            yearly_discount = Discount.get_yearly_discount()
            if yearly_discount:
                discounts.append({
                    'type': 'yearly_billing',
                    'name': yearly_discount.name,
                    'description': f'Save {yearly_discount.percentage}% with yearly billing',
                    'percentage': yearly_discount.percentage
                })

        # Template bonus availability
        template_bonus = Discount.get_template_bonus()
        if template_bonus and user.trial_eligibility.is_template_bonus_eligible:
            discounts.append({
                'type': 'template_bonus',
                'name': template_bonus.name,
                'description': f'Get {template_bonus.bonus_months} months free when you buy templates',
                'bonus_months': template_bonus.bonus_months
            })

        return discounts

    @classmethod
    def calculate_subscription_price(cls, base_price, billing_cycle='monthly', apply_yearly_discount=False):
        """
        Calculate final subscription price with applicable discounts
        """
        final_price = base_price

        if billing_cycle == 'yearly' and apply_yearly_discount:
            yearly_discount = cls.calculate_yearly_discount(base_price * 12, None)
            annual_price = yearly_discount['discounted_price']
            return {
                'monthly_price': base_price,
                'annual_price': annual_price,
                'annual_savings': yearly_discount['discount_amount'],
                'effective_monthly_price': annual_price / 12
            }

        return {
            'monthly_price': final_price,
            'annual_price': final_price * 12,
            'annual_savings': Decimal('0.00'),
            'effective_monthly_price': final_price
        }