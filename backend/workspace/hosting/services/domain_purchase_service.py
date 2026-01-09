"""
Domain Purchase Service
Orchestrates domain purchase flow with mobile money payment (Cameroon market)
Handles: Domain search → Payment → Registrar purchase → DNS configuration
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from workspace.core.models import Workspace
from workspace.hosting.models import CustomDomain, DomainPurchase
from workspace.hosting.services.domain_registrar_service import DomainRegistrarService

logger = logging.getLogger(__name__)


class DomainPurchaseService:
    """
    Handle complete domain purchase workflow
    Cameroon market: Mobile Money payment flow (MTN, Orange)
    """

    # Exchange rate (update via settings or external API)
    @staticmethod
    def get_exchange_rate() -> Decimal:
        """
        Get current USD to FCFA exchange rate
        TODO: Integrate with live exchange rate API or admin settings
        """
        return Decimal(getattr(settings, 'USD_TO_FCFA_RATE', '600.00'))

    @staticmethod
    def calculate_price_fcfa(price_usd: Decimal) -> Decimal:
        """Calculate FCFA price from USD"""
        exchange_rate = DomainPurchaseService.get_exchange_rate()
        return (price_usd * exchange_rate).quantize(Decimal('0.01'))

    @classmethod
    def validate_purchase_eligibility(cls, user, workspace: Workspace) -> Dict[str, Any]:
        """
        Validate if user can purchase domains

        Args:
            user: User attempting purchase
            workspace: Target workspace

        Returns:
            dict: {eligible: bool, errors: list}
        """
        errors = []

        # 1. Check workspace ownership
        if workspace.owner != user:
            errors.append("You can only purchase domains for workspaces you own")

        # 2. Check subscription tier (Pro+ only)
        if not hasattr(user, 'subscription') or not user.subscription:
            errors.append("Active subscription required to purchase domains")
        else:
            subscription = user.subscription
            plan = subscription.plan

            # FREE and BEGINNING tiers cannot purchase domains
            if plan.tier in ['free', 'beginning']:
                errors.append(
                    f"Domain purchases are not available on {plan.name} plan. "
                    f"Upgrade to Pro or Enterprise to purchase custom domains."
                )

            # Check capabilities from HostingEnvironment (Source of Truth)
            if not hasattr(user, 'hosting_environment'):
                errors.append("Hosting environment not found.")
            else:
                hosting_env = user.hosting_environment
                
                # Check status
                if hosting_env.status not in ['active', 'grace_period', 'initializing']:
                     # also check subscription status as fallback/primary
                     if subscription.status not in ['active', 'grace_period']:
                        errors.append("Your subscription must be active to purchase domains")

                # Check if custom domains are allowed
                capabilities = hosting_env.capabilities or {}
                if not capabilities.get('custom_domain', False):
                    errors.append(
                        f"Custom domains are not available on your current plan. "
                        f"Upgrade to Pro or Enterprise to purchase custom domains."
                    )
                
                # Check domain limit if enforced in capabilities (optional/future)
                # limit = hosting_env.capabilities.get('custom_domain_limit', 0)
                # if limit > 0: ...


        return {
            'eligible': len(errors) == 0,
            'errors': errors
        }

    # Pricing Markup Configuration
    # Example: Cost $10 -> Retail $16 ($10 * 1.5 + $1)
    MARKUP_PERCENTAGE = Decimal('0.50')  # 50% Margin
    MARKUP_FIXED_FEE = Decimal('1.00')   # $1.00 Fixed Fee

    @classmethod
    def _apply_markup(cls, cost_price_usd: Decimal) -> Decimal:
        """
        Apply profit margin to registrar cost price
        Formula: Cost * (1 + %) + Fixed
        """
        if cost_price_usd is None:
            return cls.MARKUP_FIXED_FEE # Minimum price if cost is 0 (e.g. sandbox) ensure non-zero testing

        # Ensure Decimal
        cost = Decimal(str(cost_price_usd))

        # Apply Markup
        retail_price = (cost * (1 + cls.MARKUP_PERCENTAGE)) + cls.MARKUP_FIXED_FEE
        
        return retail_price.quantize(Decimal('0.01'))

    @classmethod
    def search_domain(cls, domain_name: str, registrar: str = 'namecheap') -> Dict[str, Any]:
        """
        Search for domain availability and pricing
        """
        try:
            # Initialize registrar service
            registrar_service = DomainRegistrarService(registrar=registrar)

            # Search domain
            search_result = registrar_service.search_domain(domain_name)

            if not search_result or not search_result.get('success'):
                return search_result or {'success': False, 'error': 'Registrar returned empty response'}
            
            # Create a copy to avoid mutating cache if applicable
            result = search_result.copy()

            # Apply Markup to Main Result
            cost_usd = result.get('price_usd', Decimal('0.00'))
            renewal_cost_usd = result.get('renewal_price_usd', cost_usd)
            
            retail_usd = cls._apply_markup(cost_usd)
            retail_renewal_usd = cls._apply_markup(renewal_cost_usd)
            
            # Update Result with Retail Prices
            result['price_usd'] = retail_usd
            result['renewal_price_usd'] = retail_renewal_usd
            
            # Convert to FCFA
            # exchange_rate = cls.get_exchange_rate() # Defined below
            
            # Calculate FCFA (using Retail USD)
            result['price_fcfa'] = cls.calculate_price_fcfa(retail_usd)
            result['renewal_price_fcfa'] = cls.calculate_price_fcfa(retail_renewal_usd)
            result['exchange_rate'] = cls.get_exchange_rate()
            result['currency_note'] = 'Prices include tax and service fees'

            # Apply Markup to Suggestions
            if 'suggestions' in result:
                for suggestion in result['suggestions']:
                    s_cost = suggestion.get('price_usd', Decimal('0.00'))
                    s_retail = cls._apply_markup(s_cost)
                    
                    suggestion['price_usd'] = s_retail
                    suggestion['price_fcfa'] = cls.calculate_price_fcfa(s_retail)

            return result

        except Exception as e:
            logger.error(f"Domain search failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    @transaction.atomic
    def initiate_purchase(cls, user, workspace: Workspace, domain_name: str,
                         contact_info: Dict[str, str], phone_number: str,
                         registrar: str = 'godaddy', years: int = 1,
                         preferred_provider: str = 'fapshi',
                         idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate domain purchase (Step 1: Before payment)

        Creates DomainPurchase record in 'pending' status
        User will then pay via mobile money via PaymentService
        Webhook will trigger actual purchase

        Args:
            user: Purchasing user
            workspace: Target workspace
            domain_name: Domain to purchase
            contact_info: WHOIS contact information (phone, address, city, state, postal_code, country)
            phone_number: User's mobile money phone number
            registrar: Registrar to use
            years: Registration period
            preferred_provider: Payment provider (fapshi, mtn, orange)
            idempotency_key: Optional UUID for preventing duplicate requests

        Returns:
            dict: {
                'success': bool,
                'purchase_id': UUID,
                'payment_intent_id': UUID,
                'amount_fcfa': Decimal,
                'payment_instructions': str
            }
        """
        # Validate eligibility
        eligibility = cls.validate_purchase_eligibility(user, workspace)
        if not eligibility['eligible']:
            return {
                'success': False,
                'errors': eligibility['errors']
            }

        try:
            # Get domain pricing
            registrar_service = DomainRegistrarService(registrar=registrar)
            availability = registrar_service.check_availability(domain_name)

            if not availability.get('success') or not availability.get('available'):
                return {
                    'success': False,
                    'errors': [f"Domain '{domain_name}' is not available for purchase"]
                }
            
            # Apply Pricing Markup (Cost -> Retail)
            cost_price_usd = availability['price_usd']
            price_usd = cls._apply_markup(cost_price_usd)
            price_fcfa = cls.calculate_price_fcfa(price_usd)
            exchange_rate = cls.get_exchange_rate()

            # Create CustomDomain record
            custom_domain = CustomDomain.objects.create(
                workspace=workspace,
                domain=domain_name,
                created_by=user,
                status='pending',
                purchased_via_platform=True,
                registrar_name=registrar,
                purchase_price_usd=price_usd, # Storing Retail Price
                purchase_price_fcfa=price_fcfa, 
                renewal_price_usd=price_usd, # Assuming same markup for renewal
                renewal_price_fcfa=price_fcfa,
                exchange_rate_at_purchase=exchange_rate
            )

            # Create DomainPurchase record
            domain_purchase = DomainPurchase.objects.create(
                custom_domain=custom_domain,
                user=user,
                workspace=workspace,
                domain_name=domain_name,
                registrar=registrar,
                price_usd=price_usd,
                price_fcfa=price_fcfa,
                exchange_rate=exchange_rate,
                payment_method='mobile_money',
                payment_status='pending',
                registration_period_years=years,
                contact_info=contact_info
            )

            # Create PaymentIntent via PaymentService
            from payments.services.payment_service import PaymentService

            payment_metadata = {
                'phone_number': phone_number,
                'domain_name': domain_name,
                'purchase_id': str(domain_purchase.id),
                'registrar': registrar,
                'years': years,
                'contact_info': contact_info
            }

            payment_result = PaymentService.create_payment(
                workspace_id=workspace.id,
                user=user,
                amount=int(price_fcfa),
                currency='XAF',
                purpose='domain',
                preferred_provider=preferred_provider,
                idempotency_key=idempotency_key,
                metadata=payment_metadata
            )

            if not payment_result['success']:
                raise ValidationError(f"Payment initiation failed: {payment_result.get('error')}")

            # Link PaymentIntent to DomainPurchase
            from payments.models import PaymentIntent
            payment_intent = PaymentIntent.objects.get(id=payment_result['payment_intent_id'])
            domain_purchase.payment_intent = payment_intent
            domain_purchase.save(update_fields=['payment_intent', 'updated_at'])

            logger.info(
                f"Domain purchase initiated: {domain_name} for user {user.id} "
                f"(Purchase ID: {domain_purchase.id}, PaymentIntent: {payment_intent.id})"
            )

            return {
                'success': True,
                'purchase': domain_purchase,
                'purchase_id': str(domain_purchase.id),
                'payment_intent_id': str(payment_intent.id),
                'domain_name': domain_name,
                'price_usd': float(price_usd),
                'price_fcfa': float(price_fcfa),
                'exchange_rate': float(exchange_rate),
                'payment_instructions': payment_result.get('instructions'),
                'redirect_url': payment_result.get('redirect_url'),
                'next_step': 'payment'
            }

        except Exception as e:
            logger.error(f"Failed to initiate domain purchase: {str(e)}", exc_info=True)
            return {
                'success': False,
                'errors': [f"Failed to initiate purchase: {str(e)}"]
            }

    @classmethod
    @transaction.atomic
    def complete_purchase(cls, purchase_id: str) -> Dict[str, Any]:
        """
        Complete domain purchase from registrar (Step 3: Buy from registrar)

        Called by Celery task after payment confirmation
        Performs actual purchase from Namecheap/GoDaddy

        Args:
            purchase_id: DomainPurchase UUID

        Returns:
            dict: Purchase result
        """
        try:
            domain_purchase = DomainPurchase.objects.select_related(
                'custom_domain', 'workspace'
            ).get(id=purchase_id)

            if domain_purchase.payment_status != 'processing':
                return {
                    'success': False,
                    'error': f"Invalid purchase status: {domain_purchase.payment_status}"
                }

            # Initialize registrar service
            registrar_service = DomainRegistrarService(registrar=domain_purchase.registrar)

            # Contact information (from purchase record + user profile)
            user = domain_purchase.user
            contact_info = {
                'first_name': user.first_name or 'User',
                'last_name': user.last_name or 'Name',
                'email': user.email,
                'phone': domain_purchase.contact_info.get('phone'),
                'address': domain_purchase.contact_info.get('address'),
                'city': domain_purchase.contact_info.get('city'),
                'state': domain_purchase.contact_info.get('state'),
                'zip': domain_purchase.contact_info.get('postal_code'),
                'country': domain_purchase.contact_info.get('country', 'CM')
            }

            # Purchase domain from registrar
            purchase_result = registrar_service.purchase_domain(
                domain_name=domain_purchase.domain_name,
                registration_years=domain_purchase.registration_period_years,
                contact_info=contact_info
            )

            if not purchase_result.get('success'):
                # Purchase failed - mark as failed
                error_msg = purchase_result.get('error', 'Unknown error')
                domain_purchase.mark_failed(error_msg)
                domain_purchase.custom_domain.status = 'failed'
                domain_purchase.custom_domain.save(update_fields=['status', 'updated_at'])

                logger.error(
                    f"Domain purchase from registrar failed: {domain_purchase.domain_name} - {error_msg}"
                )

                return {
                    'success': False,
                    'error': error_msg
                }

            # Purchase successful - update records
            domain_purchase.mark_completed(
                registrar_order_id=purchase_result['order_id'],
                expires_at=purchase_result['expires_at']
            )
            domain_purchase.registrar_response = purchase_result.get('registrar_response', {})
            domain_purchase.save(update_fields=['registrar_response', 'updated_at'])

            # Update CustomDomain
            custom_domain = domain_purchase.custom_domain
            custom_domain.status = 'verified'  # Auto-verified since we own it
            custom_domain.verified_at = timezone.now()
            custom_domain.registrar_domain_id = purchase_result['domain_id']
            custom_domain.expires_at = purchase_result['expires_at']
            custom_domain.next_renewal_date = custom_domain.calculate_next_renewal_date()
            custom_domain.save()

            logger.info(
                f"Domain purchase completed: {domain_purchase.domain_name} "
                f"(Order: {purchase_result['order_id']})"
            )

            # Trigger DNS auto-configuration for purchased domain
            from workspace.hosting.services.infrastructure_facade import InfrastructureFacade
            try:
                # Get workspace to determine target
                workspace = domain_purchase.workspace
                infrastructure = workspace.infrastructure.first()
                if infrastructure:
                    target_domain = f"{infrastructure.subdomain}.huzilerz.com"
                    dns_result = InfrastructureFacade.get_service().configure_custom_domain(
                        domain=domain_purchase.domain_name,
                        target=target_domain
                    )
                    logger.info(f"DNS configured for purchased domain {domain_purchase.domain_name}: {dns_result}")
            except Exception as e:
                logger.error(f"DNS auto-configuration failed for {domain_purchase.domain_name}: {str(e)}", exc_info=True)

            return {
                'success': True,
                'purchase_id': str(purchase_id),
                'domain_name': domain_purchase.domain_name,
                'order_id': purchase_result['order_id'],
                'expires_at': purchase_result['expires_at'].isoformat()
            }

        except DomainPurchase.DoesNotExist:
            logger.error(f"Domain purchase not found: {purchase_id}")
            return {
                'success': False,
                'error': 'Purchase not found'
            }

        except Exception as e:
            logger.error(f"Domain purchase completion failed: {str(e)}", exc_info=True)

            # Mark as failed
            try:
                domain_purchase.mark_failed(str(e))
            except:
                pass

            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def get_purchase_status(cls, purchase_id: str) -> Dict[str, Any]:
        """
        Get status of domain purchase

        Args:
            purchase_id: DomainPurchase UUID

        Returns:
            dict: Purchase status and details
        """
        try:
            domain_purchase = DomainPurchase.objects.select_related(
                'custom_domain'
            ).get(id=purchase_id)

            return {
                'success': True,
                'purchase_id': str(domain_purchase.id),
                'domain_name': domain_purchase.domain_name,
                'status': domain_purchase.payment_status,
                'price_fcfa': float(domain_purchase.price_fcfa),
                'payment_reference': domain_purchase.payment_reference,
                'created_at': domain_purchase.created_at.isoformat(),
                'completed_at': domain_purchase.completed_at.isoformat() if domain_purchase.completed_at else None,
                'error_message': domain_purchase.error_message if domain_purchase.error_message else None
            }

        except DomainPurchase.DoesNotExist:
            return {
                'success': False,
                'error': 'Purchase not found'
            }
