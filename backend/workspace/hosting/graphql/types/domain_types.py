"""
Domain Management GraphQL Types

Matches UI requirements exactly - no bloat
"""

import graphene
from graphene_django import DjangoObjectType
from workspace.hosting.models import CustomDomain, DomainPurchase, DomainRenewal, WorkspaceInfrastructure
from .common_types import BaseConnection


class DomainType(graphene.ObjectType):
    """
    Unified domain type for main domains list
    Represents both default subdomain and custom domains
    """
    id = graphene.ID()
    domain = graphene.String(required=True)
    type = graphene.String(required=True)  # 'default' or 'custom'
    status = graphene.String(required=True)  # 'connected', 'pending', 'invalid_dns', 'expired'
    is_primary = graphene.Boolean(required=True)

    # Only for custom domains
    managed_by = graphene.String()
    added_at = graphene.DateTime()

    # Subdomain change tracking (only for default domain)
    subdomain_changes_remaining = graphene.Int()
    subdomain_changes_limit = graphene.Int()


class DNSRecordType(graphene.ObjectType):
    """DNS record for domain configuration"""
    type = graphene.String(required=True)  # 'A', 'CNAME', 'TXT'
    name = graphene.String(required=True)  # '@', 'www', '_huzilerz-verify'
    current_value = graphene.String()
    update_to = graphene.String()
    action = graphene.String(required=True)  # 'remove', 'add', 'update'


class CustomDomainType(DjangoObjectType):
    """
    Base custom domain type
    Used for mutation returns - simple fields only
    """
    id = graphene.ID(required=True)

    class Meta:
        model = CustomDomain
        fields = (
            'id',
            'domain',
            'status',
            'verified_at',
            'ssl_enabled',
            'ssl_provisioned_at',
            'created_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)


class CustomDomainDetailType(DjangoObjectType):
    """
    Custom domain detail view
    Used for verification polling and DNS configuration display
    """
    id = graphene.ID(required=True)

    # Status indicators
    dns_status = graphene.String(required=True)  # 'valid', 'invalid', 'pending'
    tls_status = graphene.String(required=True)  # 'provisioned', 'not_provisioned', 'provisioning'

    # DNS configuration
    dns_records_to_remove = graphene.List(DNSRecordType)
    dns_records_to_add = graphene.List(DNSRecordType)
    dns_records_to_update = graphene.List(DNSRecordType)

    class Meta:
        model = CustomDomain
        fields = (
            'id',
            'domain',
            'status',
            'registrar_name',
            'created_at',
            'verified_at',
            'ssl_enabled',
            'ssl_provisioned_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    def resolve_dns_status(self, info):
        """Map internal status to UI status"""
        if self.status == 'active':
            return 'valid'
        elif self.status == 'pending':
            return 'pending'
        return 'invalid'

    def resolve_tls_status(self, info):
        """Check TLS certificate status"""
        if self.ssl_enabled and self.ssl_provisioned_at:
            return 'provisioned'
        elif self.status == 'active':
            return 'provisioning'
        return 'not_provisioned'

    def resolve_dns_records_to_remove(self, info):
        """Parse dns_records to extract records to remove"""
        if not self.dns_records or not isinstance(self.dns_records, dict):
            return []

        remove_records = self.dns_records.get('remove', [])
        return [
            DNSRecordType(
                type=rec.get('type'),
                name=rec.get('name'),
                current_value=rec.get('value'),
                update_to=None,
                action='remove'
            )
            for rec in remove_records
        ]

    def resolve_dns_records_to_add(self, info):
        """Parse dns_records to extract records to add"""
        if not self.dns_records or not isinstance(self.dns_records, dict):
            return []

        add_records = self.dns_records.get('add', [])
        return [
            DNSRecordType(
                type=rec.get('type'),
                name=rec.get('name'),
                current_value=None,
                update_to=rec.get('value'),
                action='add'
            )
            for rec in add_records
        ]

    def resolve_dns_records_to_update(self, info):
        """Parse dns_records to extract records to update"""
        if not self.dns_records or not isinstance(self.dns_records, dict):
            return []

        update_records = self.dns_records.get('update', [])
        return [
            DNSRecordType(
                type=rec.get('type'),
                name=rec.get('name'),
                current_value=rec.get('current_value'),
                update_to=rec.get('update_to'),
                action='update'
            )
            for rec in update_records
        ]


class DomainSearchResultType(graphene.ObjectType):
    """Domain search result item for buy domain flow"""
    domain = graphene.String(required=True)
    available = graphene.Boolean(required=True)
    price_usd = graphene.Float(required=True)
    price_per_year = graphene.String(required=True)  # Formatted: "$16.00 USD / year"
    category = graphene.String(required=True)  # 'suggested' or 'other'


class DomainSearchResponseType(graphene.ObjectType):
    """Complete domain search response with pagination"""
    query = graphene.String(required=True)
    available = graphene.Boolean(required=True)
    suggestions = graphene.List(DomainSearchResultType, required=True)
    total = graphene.Int(required=True)
    page = graphene.Int(required=True)
    page_size = graphene.Int(required=True)
    has_next_page = graphene.Boolean(required=True)


class DomainPurchaseType(DjangoObjectType):
    """
    Domain purchase type for mutations
    Simple return type with essential fields
    """
    id = graphene.ID(required=True)

    class Meta:
        model = DomainPurchase
        fields = (
            'id',
            'domain_name',
            'price_fcfa',
            'payment_status',
            'created_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)


class DomainPurchaseStatusType(DjangoObjectType):
    """
    Domain purchase status type for queries
    Extended type with all tracking fields
    """
    id = graphene.ID(required=True)
    status = graphene.String(required=True)  # 'pending', 'processing', 'completed', 'failed'

    class Meta:
        model = DomainPurchase
        fields = (
            'id',
            'domain_name',
            'price_fcfa',
            'payment_status',
            'error_message',
            'created_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    def resolve_status(self, info):
        return self.payment_status


class DomainRenewalType(DjangoObjectType):
    """
    Domain renewal type for mutations
    Simple return type with essential fields
    """
    id = graphene.ID(required=True)

    # Computed status fields
    is_pending_payment = graphene.Boolean()
    is_completed = graphene.Boolean()
    is_failed = graphene.Boolean()

    class Meta:
        model = DomainRenewal
        fields = (
            'id',
            'domain_name',
            'renewal_price_fcfa',
            'renewal_status',
            'created_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    def resolve_is_pending_payment(self, info):
        return self.renewal_status == 'pending_payment'

    def resolve_is_completed(self, info):
        return self.renewal_status == 'completed'

    def resolve_is_failed(self, info):
        return self.renewal_status == 'failed'


class DomainRenewalStatusType(DjangoObjectType):
    """
    Domain renewal status type for queries
    Extended type with all tracking fields
    """
    id = graphene.ID(required=True)
    status = graphene.String(required=True)  # 'pending_payment', 'processing', 'completed', 'failed'
    payment_status = graphene.String()  # Alias for consistency with DomainPurchaseType

    class Meta:
        model = DomainRenewal
        fields = (
            'id',
            'domain_name',
            'renewal_price_fcfa',
            'renewal_status',
            'previous_expiry_date',
            'new_expiry_date',
            'renewed_at',
            'error_message',
            'created_at',
        )
        interfaces = (graphene.relay.Node,)
        connection_class = BaseConnection

    def resolve_id(self, info):
        return str(self.id)

    def resolve_status(self, info):
        return self.renewal_status

    def resolve_payment_status(self, info):
        """Alias for renewal_status - for consistency with purchase flow"""
        return self.renewal_status


class SubdomainValidationType(graphene.ObjectType):
    """Subdomain availability validation result"""
    available = graphene.Boolean(required=True)
    subdomain = graphene.String()
    full_domain = graphene.String()  # e.g., "mystore.huzilerz.com"
    errors = graphene.List(graphene.String)
