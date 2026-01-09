"""
Domain Management GraphQL Queries - AUTHENTICATED + WORKSPACE SCOPED

Clean, focused queries matching UI flows exactly
"""

import graphene
from graphql import GraphQLError
from ..types.domain_types import (
    DomainType,
    CustomDomainDetailType,
    DomainSearchResponseType,
    DomainPurchaseStatusType,
    DomainRenewalStatusType,
    SubdomainValidationType
)
from workspace.hosting.models import CustomDomain, DomainPurchase, DomainRenewal, WorkspaceInfrastructure


class DomainManagementQueries(graphene.ObjectType):
    """
    Domain queries matching UI requirements exactly

    Flow 1: List all domains (default + custom)
    Flow 2: Subdomain validation for change modal
    Flow 3-4: Custom domain detail for verification polling
    Flow 5: Domain search with pagination
    Flow 6: Purchase status tracking
    """

    # Flow 1: Main domains list page
    domains = graphene.List(
        DomainType,
        workspace_id=graphene.ID(required=True),
        description="Get all domains (default subdomain + custom domains)"
    )

    # Flow 2: Change subdomain validation
    validate_subdomain = graphene.Field(
        SubdomainValidationType,
        subdomain=graphene.String(required=True),
        description="Check if subdomain is available"
    )

    # Flow 3-4: Custom domain detail for verification polling
    custom_domain = graphene.Field(
        CustomDomainDetailType,
        domain_id=graphene.ID(required=True),
        description="Get custom domain with DNS/TLS status (for polling)"
    )

    # Flow 5: Domain search for buy flow
    search_domains = graphene.Field(
        DomainSearchResponseType,
        query=graphene.String(required=True),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        description="Search domains with pagination"
    )

    # Flow 6: Purchase status tracking
    purchase_status = graphene.Field(
        DomainPurchaseStatusType,
        purchase_id=graphene.ID(required=True),
        description="Track domain purchase progress"
    )

    # Renewal status tracking
    renewal_status = graphene.Field(
        DomainRenewalStatusType,
        renewal_id=graphene.ID(required=True),
        description="Track domain renewal progress"
    )

    def resolve_domains(self, info, workspace_id):
        """
        Get all domains for workspace (Flow 1)
        Returns: Default subdomain + all custom domains

        UI displays:
        - Domain name
        - Type (default/custom)
        - Status badge (Connected/Pending/Invalid DNS)
        - Primary label
        """
        workspace = info.context.workspace

        if str(workspace.id) != workspace_id:
            raise GraphQLError("Unauthorized")

        domains = []

        # Get default subdomain from infrastructure
        try:
            infrastructure = WorkspaceInfrastructure.objects.get(workspace=workspace)
            # Check if subdomain already includes .huzilerz.com
            subdomain = infrastructure.subdomain
            if not subdomain.endswith('.huzilerz.com'):
                subdomain = f"{subdomain}.huzilerz.com"

            # Calculate remaining changes
            changes_remaining = infrastructure.subdomain_changes_limit - infrastructure.subdomain_changes_count

            domains.append(DomainType(
                id=None,
                domain=subdomain,
                type='default',
                status='connected',
                is_primary=True,
                managed_by=None,
                added_at=None,
                subdomain_changes_remaining=changes_remaining,
                subdomain_changes_limit=infrastructure.subdomain_changes_limit
            ))
        except WorkspaceInfrastructure.DoesNotExist:
            pass

        # Get all custom domains
        custom_domains = CustomDomain.objects.filter(
            workspace=workspace
        ).order_by('-created_at')

        for cd in custom_domains:
            # Map internal status to UI status
            if cd.status == 'active':
                status = 'connected'
            elif cd.status == 'pending':
                status = 'pending'
            elif cd.status == 'failed' or cd.status == 'suspended':
                status = 'invalid_dns'
            else:
                status = 'pending'

            domains.append(DomainType(
                id=str(cd.id),
                domain=cd.domain,
                type='custom',
                status=status,
                is_primary=False,  # Only default is primary for now
                managed_by=cd.registrar_name,
                added_at=cd.created_at
            ))

        return domains

    def resolve_validate_subdomain(self, info, subdomain):
        """
        Validate subdomain availability (Flow 2)
        Used in "Change subdomain" modal

        Returns: availability + validation errors
        """
        workspace = info.context.workspace

        from workspace.hosting.services.subdomain_service import SubdomainService

        validation = SubdomainService.validate_subdomain(subdomain)

        return SubdomainValidationType(
            available=validation['valid'],
            subdomain=validation.get('normalized_subdomain'),
            full_domain=f"{validation.get('normalized_subdomain')}.huzilerz.com" if validation['valid'] else None,
            errors=validation['errors']
        )

    def resolve_custom_domain(self, info, domain_id):
        """
        Get custom domain detail (Flow 3-4)
        Used for verification polling and DNS configuration display

        Frontend polls this every 12 seconds to check:
        - DNS status
        - TLS status
        """
        workspace = info.context.workspace

        try:
            domain = CustomDomain.objects.get(id=domain_id)

            if domain.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized")

            return domain

        except CustomDomain.DoesNotExist:
            raise GraphQLError("Domain not found")

    def resolve_search_domains(self, info, query, page=1, page_size=10):
        """
        Search domains with pagination (Flow 5)

        UI shows:
        - Search input
        - Availability message
        - Suggested domains (if unavailable)
        - Other extensions with pagination
        """
        workspace = info.context.workspace

        from workspace.hosting.services.domain_registrar_service import DomainRegistrarService

        registrar = DomainRegistrarService(registrar='godaddy')
        result = registrar.search_domain(query)

        if not result.get('success'):
            raise GraphQLError(result.get('error', 'Search failed'))

        # Format suggestions
        suggestions = []
        all_suggestions = result.get('suggestions', [])

        # Categorize: first 3 are "suggested", rest are "other"
        for idx, suggestion in enumerate(all_suggestions):
            category = 'suggested' if idx < 3 else 'other'

            price_usd = suggestion.get('price_usd', 0)
            suggestions.append({
                'domain': suggestion['domain'],
                'available': suggestion.get('available', True),
                'price_usd': float(price_usd),
                'price_per_year': f"${price_usd:.2f} USD / year",
                'category': category
            })

        # Pagination
        total = len(suggestions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_suggestions = suggestions[start_idx:end_idx]

        from ..types.domain_types import DomainSearchResultType

        return {
            'query': query,
            'available': result.get('available', False),
            'suggestions': [DomainSearchResultType(**s) for s in paginated_suggestions],
            'total': total,
            'page': page,
            'page_size': page_size,
            'has_next_page': end_idx < total
        }

    def resolve_purchase_status(self, info, purchase_id):
        """
        Track purchase progress (Flow 6)

        Statuses: pending → processing → completed
        """
        workspace = info.context.workspace

        try:
            purchase = DomainPurchase.objects.get(id=purchase_id)

            if purchase.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized")

            return purchase

        except DomainPurchase.DoesNotExist:
            return None

    def resolve_renewal_status(self, info, renewal_id):
        """
        Track renewal progress

        Statuses: pending_payment → processing → completed
        """
        workspace = info.context.workspace

        try:
            renewal = DomainRenewal.objects.select_related('custom_domain').get(id=renewal_id)

            if renewal.custom_domain.workspace.id != workspace.id:
                raise GraphQLError("Unauthorized")

            return renewal

        except DomainRenewal.DoesNotExist:
            raise GraphQLError("Renewal not found")
