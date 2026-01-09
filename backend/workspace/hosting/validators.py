"""
Domain and Subdomain Validators
Production-grade validation for domain operations
"""
import re
from typing import Dict, Any
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


class DomainValidator:
    """
    Validate domain names according to RFC 1035 and ICANN standards
    Prevents malicious/invalid domains from being registered
    """

    # Valid TLDs for domain purchases
    ALLOWED_TLDS = {
        # Generic TLDs (common)
        '.com', '.net', '.org', '.shop', '.store', '.online', '.site',
        '.app', '.dev', '.io', '.co', '.biz', '.info',
        # Country TLDs (Africa focus)
        '.cm',  # Cameroon
        '.africa',
        # E-commerce TLDs
        '.shopping', '.boutique', '.market', '.deals',
    }

    # Blacklisted domains (phishing/malicious patterns)
    BLACKLISTED_PATTERNS = [
        r'.*paypal.*',
        r'.*stripe.*',
        r'.*bank.*',
        r'.*login.*secure.*',
        r'.*verify.*account.*',
        r'.*huzilerz.*',  # Can't register domains containing our brand
        r'.*admin.*panel.*',
    ]

    # Domain format regex (RFC 1035 compliant)
    DOMAIN_REGEX = re.compile(
        r'^(?=.{1,253}$)'  # Total length max 253 chars
        r'(?!-)'  # Cannot start with hyphen
        r'([a-z0-9-]{1,63}\.)*'  # Subdomains
        r'[a-z0-9-]{1,63}'  # Domain name
        r'(?<!-)'  # Cannot end with hyphen
        r'\.[a-z]{2,}$',  # TLD
        re.IGNORECASE
    )

    @classmethod
    def validate(cls, domain: str) -> Dict[str, Any]:
        """
        Comprehensive domain validation

        Args:
            domain: Domain to validate (e.g., "mystore.com")

        Returns:
            dict: {valid: bool, errors: list, warnings: list, normalized: str}
        """
        errors = []
        warnings = []

        # Normalize domain (lowercase, strip whitespace)
        normalized = domain.lower().strip()

        # Remove protocol if present
        if normalized.startswith('http://') or normalized.startswith('https://'):
            normalized = normalized.split('://', 1)[1]

        # Remove trailing slash
        normalized = normalized.rstrip('/')

        # Remove www prefix for validation (but preserve in normalized)
        domain_without_www = normalized.replace('www.', '', 1)

        # 1. Length validation
        if len(normalized) < 4:  # Minimum: a.co (4 chars)
            errors.append("Domain must be at least 4 characters long")

        if len(normalized) > 253:
            errors.append("Domain must not exceed 253 characters")

        # 2. Format validation (RFC 1035)
        if not cls.DOMAIN_REGEX.match(domain_without_www):
            errors.append(
                "Invalid domain format. Domain must contain only letters, numbers, hyphens, "
                "and a valid TLD (e.g., .com, .net, .shop)"
            )

        # 3. TLD validation
        tld_valid = False
        domain_tld = None
        for tld in cls.ALLOWED_TLDS:
            if normalized.endswith(tld):
                tld_valid = True
                domain_tld = tld
                break

        if not tld_valid:
            supported_tlds = ', '.join(sorted(cls.ALLOWED_TLDS)[:10])
            errors.append(
                f"Unsupported TLD. Supported TLDs include: {supported_tlds}, etc."
            )

        # 4. Blacklist check (security)
        for pattern in cls.BLACKLISTED_PATTERNS:
            if re.match(pattern, normalized, re.IGNORECASE):
                errors.append(
                    "This domain contains restricted keywords and cannot be registered"
                )
                break

        # 5. Best practice warnings
        if normalized.startswith('www.'):
            warnings.append(
                "Domain starts with 'www'. You may want to register the root domain instead."
            )

        if '-' in domain_without_www.split('.')[0]:
            warnings.append(
                "Domain contains hyphens. Consider a simpler domain for better memorability."
            )

        if len(domain_without_www.split('.')[0]) > 15:
            warnings.append(
                "Domain name is quite long. Shorter domains are easier to remember and type."
            )

        # 6. Numeric-only check
        domain_part = domain_without_www.split('.')[0]
        if domain_part.replace('-', '').isdigit():
            warnings.append(
                "Domain is entirely numeric. Consider adding letters for better branding."
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized': normalized if len(errors) == 0 else None,
            'tld': domain_tld
        }

    @classmethod
    def validate_dns_format(cls, domain: str) -> bool:
        """
        Quick DNS format check (for DNS record validation)

        Args:
            domain: Domain to check

        Returns:
            bool: True if valid DNS format
        """
        return bool(cls.DOMAIN_REGEX.match(domain.lower()))


class SubdomainValidator:
    """
    Validate subdomains for huzilerz.com
    Stricter than domain validation (internal use)
    """

    # Reserved subdomains (system use)
    RESERVED = {
        'www', 'api', 'admin', 'app', 'cdn', 'staging', 'dev', 'test',
        'mail', 'email', 'smtp', 'ftp', 'ssh', 'ssl', 'secure',
        'dashboard', 'console', 'portal', 'status', 'support',
        'blog', 'help', 'docs', 'documentation', 'community',
        'store', 'shop', 'marketplace', 'payment', 'checkout',
        'account', 'billing', 'invoice', 'subscription', 'pricing',
        'webhook', 'callback', 'notify', 'notifications',
        'static', 'assets', 'media', 'uploads', 'files',
        'preview', 'demo', 'example', 'sample', 'template'
    }

    # Subdomain regex (alphanumeric + hyphens only)
    SUBDOMAIN_REGEX = re.compile(r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$')

    @classmethod
    def validate(cls, subdomain: str) -> Dict[str, Any]:
        """
        Validate subdomain format

        Args:
            subdomain: Subdomain to validate (without .huzilerz.com)

        Returns:
            dict: {valid: bool, errors: list, warnings: list, normalized: str}
        """
        errors = []
        warnings = []

        # Normalize
        normalized = subdomain.lower().strip()

        # 1. Length validation
        if len(normalized) < 3:
            errors.append("Subdomain must be at least 3 characters long")

        if len(normalized) > 63:
            errors.append("Subdomain must not exceed 63 characters (DNS limit)")

        # 2. Format validation
        if not cls.SUBDOMAIN_REGEX.match(normalized):
            errors.append(
                "Subdomain must contain only lowercase letters, numbers, and hyphens. "
                "Cannot start or end with a hyphen."
            )

        # 3. Reserved check
        if normalized in cls.RESERVED:
            errors.append(f"'{subdomain}' is a reserved subdomain and cannot be used")

        # 4. Best practice warnings
        if normalized.startswith('test-') or normalized.startswith('demo-'):
            warnings.append(
                "Subdomain starts with 'test-' or 'demo-'. Consider a professional name for production."
            )

        if '--' in normalized:
            warnings.append("Subdomain contains consecutive hyphens. This may look unprofessional.")

        if normalized.isdigit():
            warnings.append("Subdomain is entirely numeric. Consider adding letters for better branding.")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized': normalized if len(errors) == 0 else None
        }


class TierPermissionValidator:
    """
    Validate subscription tier permissions for domain/hosting features
    """

    @classmethod
    def validate_custom_domain_purchase(cls, user) -> Dict[str, Any]:
        """
        Check if user can purchase custom domains

        Args:
            user: User to validate

        Returns:
            dict: {allowed: bool, reason: str, tier: str}
        """
        if not hasattr(user, 'subscription') or not user.subscription:
            return {
                'allowed': False,
                'reason': 'no_subscription',
                'message': 'Active subscription required to purchase domains',
                'upgrade_url': '/pricing'
            }

        subscription = user.subscription
        plan = subscription.plan

        # Only Pro+ can purchase domains
        if plan.tier in ['free', 'beginning']:
            return {
                'allowed': False,
                'reason': 'tier_insufficient',
                'tier': plan.tier,
                'message': f'Domain purchases require Pro or Enterprise plan. You are on {plan.name}.',
                'upgrade_url': '/pricing'
            }

        # Check subscription status
        if subscription.status not in ['active', 'grace_period']:
            return {
                'allowed': False,
                'reason': 'subscription_inactive',
                'tier': plan.tier,
                'message': f'Your subscription is {subscription.status}. Please renew to purchase domains.',
                'upgrade_url': '/billing'
            }

        return {
            'allowed': True,
            'tier': plan.tier,
            'custom_domains_limit': plan.custom_domains
        }

    @classmethod
    def validate_subdomain_change(cls, user) -> Dict[str, Any]:
        """
        Check if user can change subdomain (all tiers allowed)

        Args:
            user: User to validate

        Returns:
            dict: {allowed: bool}
        """
        # All tiers can change subdomain (it's free)
        if not hasattr(user, 'subscription') or not user.subscription:
            return {
                'allowed': False,
                'reason': 'no_subscription',
                'message': 'Active subscription required'
            }

        subscription = user.subscription

        if subscription.status not in ['active', 'grace_period']:
            return {
                'allowed': False,
                'reason': 'subscription_inactive',
                'message': 'Subscription must be active to manage subdomains'
            }

        return {'allowed': True}


def validate_domain_name(domain: str) -> str:
    """
    Django model validator for domain names

    Args:
        domain: Domain to validate

    Raises:
        ValidationError: If domain is invalid

    Returns:
        str: Normalized domain
    """
    validation = DomainValidator.validate(domain)

    if not validation['valid']:
        raise ValidationError('; '.join(validation['errors']))

    return validation['normalized']


def validate_subdomain_name(subdomain: str) -> str:
    """
    Django model validator for subdomains

    Args:
        subdomain: Subdomain to validate

    Raises:
        ValidationError: If subdomain is invalid

    Returns:
        str: Normalized subdomain
    """
    validation = SubdomainValidator.validate(subdomain)

    if not validation['valid']:
        raise ValidationError('; '.join(validation['errors']))

    return validation['normalized']
