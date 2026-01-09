"""
Domain Management GraphQL Mutations - AUTHENTICATED + WORKSPACE SCOPED

Cameroon market domain management with mobile money payments
All mutations require authentication and workspace ownership
"""

import graphene
from graphql import GraphQLError
from django.core.exceptions import ValidationError
from django.db import transaction
from ..types.domain_types import (
    CustomDomainType,
    DomainPurchaseType,
    DomainRenewalType
)
from ..types.domain_inputs import (
    PurchaseDomainInput,
    RenewDomainInput,
    ChangeSubdomainInput,
    ConnectCustomDomainInput
)
import logging

logger = logging.getLogger(__name__)


class PurchaseDomain(graphene.Mutation):
    """
    Initiate domain purchase (Cameroon mobile money flow)

    Creates DomainPurchase record → User pays via MTN/Orange → Webhook completes purchase
    Uses DomainPurchaseService.initiate_purchase()
    """

    class Arguments:
        input = PurchaseDomainInput(required=True)

    success = graphene.Boolean()
    purchase = graphene.Field(DomainPurchaseType)
    payment_instructions = graphene.String()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate workspace ownership
            if str(workspace.id) != input.workspace_id:
                raise GraphQLError("Unauthorized: Workspace ownership validation failed")

            from workspace.hosting.services.domain_purchase_service import DomainPurchaseService

            # Prepare contact info for WHOIS registration
            contact_info = {
                'phone': input.phone,
                'address': input.address,
                'city': input.city,
                'state': input.state,
                'postal_code': input.postal_code,
                'country': input.country
            }

            # Initiate purchase (creates pending DomainPurchase record)
            # Use godaddy explicitly as standard registrar
            result = DomainPurchaseService.initiate_purchase(
                user=user,
                workspace=workspace,
                domain_name=input.domain,
                contact_info=contact_info,
                phone_number=input.phone,  # Use contact phone for mobile money payment
                years=input.registration_period_years,
                registrar='godaddy'
            )

            if not result.get('success'):
                 return PurchaseDomain(
                     success=False, 
                     error=result['errors'][0] if result.get('errors') else "Purchase initiation failed"
                 )

            return PurchaseDomain(
                success=True,
                purchase=result['purchase'],
                payment_instructions=result['payment_instructions'],
                message=f"Domain purchase initiated. Please check your phone for the payment prompt."
            )

        except ValidationError as e:
            return PurchaseDomain(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Purchase domain mutation failed: {str(e)}", exc_info=True)
            return PurchaseDomain(
                success=False,
                error=f"Failed to initiate purchase: {str(e)}"
            )


class PrepareDomainCheckout(graphene.Mutation):
    """
    Prepare domain purchase checkpoint
    Returns AUTHORITATIVE pricing from backend (Source of Truth)
    """

    class Arguments:
        domain = graphene.String(required=True)
        workspace_id = graphene.ID(required=True)

    success = graphene.Boolean()
    domain_name = graphene.String()
    price_usd = graphene.Float()
    price_fcfa = graphene.Float()
    exchange_rate = graphene.Float()
    registration_period_years = graphene.Int()
    currency = graphene.String()
    available = graphene.Boolean()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, domain, workspace_id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate workspace ownership
            if str(workspace.id) != workspace_id:
                raise GraphQLError("Unauthorized: Workspace ownership validation failed")

            from workspace.hosting.services.domain_purchase_service import DomainPurchaseService

            # Validate eligibility first
            eligibility = DomainPurchaseService.validate_purchase_eligibility(user, workspace)
            if not eligibility['eligible']:
                return PrepareDomainCheckout(
                    success=False,
                    error=eligibility['errors'][0] if eligibility['errors'] else "Not eligible for purchase"
                )

            # Get authoritative pricing (fresh search)
            # We assume godaddy as default registrar for pricing check (namecheap not implemented)
            search_result = DomainPurchaseService.search_domain(domain, registrar='godaddy')

            if not search_result.get('success'):
                return PrepareDomainCheckout(
                    success=False,
                    error=search_result.get('error', 'Failed to fetch domain pricing')
                )

            if not search_result.get('available'):
                return PrepareDomainCheckout(
                    success=False,
                    available=False,
                    domain_name=domain,
                    error=f"Domain {domain} is no longer available"
                )

            return PrepareDomainCheckout(
                success=True,
                available=True,
                domain_name=domain,
                price_usd=float(search_result['price_usd']),
                price_fcfa=float(search_result['price_fcfa']),
                exchange_rate=float(search_result['exchange_rate']),
                registration_period_years=1,
                currency="XAF"
            )

        except Exception as e:
            logger.error(f"Prepare domain checkout failed: {str(e)}", exc_info=True)
            return PrepareDomainCheckout(
                success=False,
                error=f"Failed to prepare checkout: {str(e)}"
            )


class RenewDomain(graphene.Mutation):
    """
    Initiate domain renewal (Cameroon mobile money flow)

    Creates DomainRenewal record → User pays via MTN/Orange → Webhook completes renewal
    Uses DomainRenewalService.initiate_renewal()
    """

    class Arguments:
        input = RenewDomainInput(required=True)

    success = graphene.Boolean()
    renewal = graphene.Field(DomainRenewalType)
    payment_instructions = graphene.String()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from workspace.hosting.models import CustomDomain
            try:
                domain = CustomDomain.objects.get(id=input.domain_id)
            except CustomDomain.DoesNotExist:
                raise GraphQLError("Domain not found")

            if domain.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Domain does not belong to your workspace")

            from workspace.hosting.services.domain_renewal_service import DomainRenewalService

            # Initiate renewal (creates pending DomainRenewal record)
            result = DomainRenewalService.initiate_renewal(
                domain_id=input.domain_id,
                user=user,
                renewal_period_years=input.renewal_period_years
            )

            return RenewDomain(
                success=True,
                renewal=result['renewal'],
                payment_instructions=result['payment_instructions'],
                message=f"Domain renewal initiated. Please complete payment via Mobile Money."
            )

        except ValidationError as e:
            return RenewDomain(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Renew domain mutation failed: {str(e)}", exc_info=True)
            return RenewDomain(
                success=False,
                error=f"Failed to initiate renewal: {str(e)}"
            )


class ChangeSubdomain(graphene.Mutation):
    """
    Change workspace subdomain (e.g., mystore.huzilerz.com)

    Free for all tiers - uses SubdomainService
    Atomic update across WorkspaceInfrastructure and DeployedSite
    Tracks subdomain history and enforces change limits (2 changes max)
    """

    class Arguments:
        input = ChangeSubdomainInput(required=True)

    success = graphene.Boolean()
    new_subdomain = graphene.String()
    live_url = graphene.String()
    preview_url = graphene.String()
    changes_remaining = graphene.Int()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate workspace ownership
            if str(workspace.id) != input.workspace_id:
                raise GraphQLError("Unauthorized: Workspace ownership validation failed")

            from workspace.hosting.services.subdomain_service import SubdomainService

            # Change subdomain (atomic update with history tracking)
            result = SubdomainService.change_subdomain(
                workspace=workspace,
                new_subdomain=input.subdomain,
                changed_by=user
            )

            if not result['success']:
                return ChangeSubdomain(
                    success=False,
                    error=result.get('errors', ['Unknown error'])[0] if result.get('errors') else 'Failed to change subdomain'
                )

            changes_remaining = result.get('changes_remaining', 0)
            message = f"Subdomain changed to '{result['new_subdomain']}'"
            if changes_remaining > 0:
                message += f". You have {changes_remaining} change(s) remaining."
            elif changes_remaining == 0:
                message += ". This was your final subdomain change."

            return ChangeSubdomain(
                success=True,
                new_subdomain=result['new_subdomain'],
                live_url=result['new_live_url'],
                preview_url=result['new_preview_url'],
                changes_remaining=changes_remaining,
                message=message
            )

        except ValidationError as e:
            return ChangeSubdomain(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Change subdomain mutation failed: {str(e)}", exc_info=True)
            return ChangeSubdomain(
                success=False,
                error=f"Failed to change subdomain: {str(e)}"
            )


class ConnectCustomDomain(graphene.Mutation):
    """
    Connect externally-owned custom domain

    User must configure DNS records externally
    System verifies DNS and provisions SSL (Shopify 2-step flow)
    """

    class Arguments:
        input = ConnectCustomDomainInput(required=True)

    success = graphene.Boolean()
    domain = graphene.Field(CustomDomainType)
    dns_records = graphene.JSONString()
    verification_instructions = graphene.JSONString()  # Dict with step-by-step instructions
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate workspace ownership
            if str(workspace.id) != input.workspace_id:
                raise GraphQLError("Unauthorized: Workspace ownership validation failed")

            from workspace.hosting.services.custom_domain_service import CustomDomainService
            from workspace.hosting.models import DeployedSite

            # Get deployed site for this workspace
            try:
                deployed_site = DeployedSite.objects.get(
                    workspace=workspace,
                    status='active'
                )
            except DeployedSite.DoesNotExist:
                raise GraphQLError("No active deployed site found. Please publish a theme first.")

            # Connect custom domain (uses add_custom_domain service)
            result = CustomDomainService.add_custom_domain(
                workspace=workspace,
                deployed_site=deployed_site,
                domain=input.domain,
                user=user
            )

            return ConnectCustomDomain(
                success=True,
                domain=result['custom_domain'],
                dns_records=result['dns_records'],
                verification_instructions=result['verification_instructions'],
                message=f"Custom domain '{input.domain}' added. Please configure DNS records to verify ownership."
            )

        except ValidationError as e:
            return ConnectCustomDomain(success=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Connect custom domain mutation failed: {str(e)}", exc_info=True)
            return ConnectCustomDomain(
                success=False,
                error=f"Failed to connect custom domain: {str(e)}"
            )


class VerifyCustomDomain(graphene.Mutation):
    """
    Manually trigger domain verification

    Use case: User configured DNS and wants immediate verification
    (instead of waiting for 15-min auto-verification Celery task)
    """

    class Arguments:
        domain_id = graphene.ID(required=True)

    success = graphene.Boolean()
    domain = graphene.Field(CustomDomainType)
    verified = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, domain_id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # Validate ownership
            from workspace.hosting.models import CustomDomain
            try:
                domain = CustomDomain.objects.get(id=domain_id)
            except CustomDomain.DoesNotExist:
                raise GraphQLError("Domain not found")

            if domain.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized: Domain does not belong to your workspace")

            from workspace.hosting.services.custom_domain_service import CustomDomainService

            # Verify domain (checks DNS TXT record)
            result = CustomDomainService.verify_domain(
                custom_domain_id=domain_id,
                user=user
            )

            # Refresh domain object to get updated status
            domain.refresh_from_db()

            return VerifyCustomDomain(
                success=True,
                domain=domain,
                verified=result.get('verified', False),
                message=result.get('message', 'Domain verification complete')
            )

        except ValidationError as e:
            return VerifyCustomDomain(success=False, verified=False, error=str(e))
        except GraphQLError:
            raise
        except Exception as e:
            logger.error(f"Verify domain mutation failed: {str(e)}", exc_info=True)
            return VerifyCustomDomain(
                success=False,
                verified=False,
                error=f"Failed to verify domain: {str(e)}"
            )


class DomainManagementMutations(graphene.ObjectType):
    """
    Domain management mutations collection

    Cameroon market: Mobile money payments + manual renewals
    All mutations require authentication + workspace scoping
    """

    purchase_domain = PurchaseDomain.Field()
    prepare_domain_checkout = PrepareDomainCheckout.Field()
    renew_domain = RenewDomain.Field()
    change_subdomain = ChangeSubdomain.Field()
    connect_custom_domain = ConnectCustomDomain.Field()
    verify_custom_domain = VerifyCustomDomain.Field()
