"""
Subdomain Management Service
Handles huzilerz.com subdomain operations (free for all tiers)
"""
import re
import logging
from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from django.utils import timezone
from workspace.core.models import Workspace
from workspace.hosting.models import WorkspaceInfrastructure, DeployedSite, SubdomainHistory

logger = logging.getLogger(__name__)


class SubdomainService:
    """
    Manage subdomains under huzilerz.com
    All tiers get free subdomain: {subdomain}.huzilerz.com
    """

    # Reserved subdomains that cannot be used
    RESERVED_SUBDOMAINS = {
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

    # Subdomain validation regex
    SUBDOMAIN_REGEX = re.compile(r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$')

    @classmethod
    def validate_subdomain(cls, subdomain: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate subdomain format and availability

        Args:
            subdomain: Proposed subdomain (without .huzilerz.com)
            workspace_id: Workspace ID to exclude from availability check (optional)

        Returns:
            dict: {valid: bool, errors: list, warnings: list}
        """
        errors = []
        warnings = []

        # 1. Length validation
        if len(subdomain) < 3:
            errors.append("Subdomain must be at least 3 characters long")
        if len(subdomain) > 63:
            errors.append("Subdomain must not exceed 63 characters")

        # 2. Format validation (alphanumeric + hyphens, DNS-compliant)
        subdomain_lower = subdomain.lower()
        if not cls.SUBDOMAIN_REGEX.match(subdomain_lower):
            errors.append(
                "Subdomain must contain only lowercase letters, numbers, and hyphens. "
                "Cannot start or end with a hyphen."
            )

        # 3. Reserved subdomain check
        if subdomain_lower in cls.RESERVED_SUBDOMAINS:
            errors.append(f"'{subdomain}' is a reserved subdomain and cannot be used")

        # 4. Availability check (database)
        if not errors:  # Only check if format is valid
            is_available, availability_msg = cls.check_availability(subdomain_lower, workspace_id)
            if not is_available:
                errors.append(availability_msg)

        # 5. Best practice warnings
        if subdomain_lower.startswith('test-') or subdomain_lower.startswith('demo-'):
            warnings.append(
                "Subdomain starts with 'test-' or 'demo-'. Consider a more professional name for production use."
            )

        if '--' in subdomain_lower:
            warnings.append("Subdomain contains consecutive hyphens. This may look unprofessional.")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'normalized_subdomain': subdomain_lower if len(errors) == 0 else None
        }

    @classmethod
    def check_availability(cls, subdomain: str, exclude_workspace_id: Optional[str] = None) -> tuple[bool, str]:
        """
        Check if subdomain is available

        Args:
            subdomain: Normalized subdomain to check
            exclude_workspace_id: Workspace ID to exclude from check (for allowing user to keep their own subdomain)

        Returns:
            tuple: (is_available: bool, message: str)
        """
        # Check SubdomainHistory first - once used, forever reserved
        if SubdomainHistory.objects.filter(subdomain=subdomain).exists():
            # Exception: Allow if this is the workspace's current subdomain
            if exclude_workspace_id:
                current_infra = WorkspaceInfrastructure.objects.filter(
                    workspace_id=exclude_workspace_id,
                    subdomain=subdomain
                ).exists()
                if current_infra:
                    return True, "This is your current subdomain"

            return False, f"Subdomain '{subdomain}' has been used before and is no longer available"

        # Check WorkspaceInfrastructure
        if WorkspaceInfrastructure.objects.filter(subdomain=subdomain).exists():
            return False, f"Subdomain '{subdomain}' is already taken"

        # Check DeployedSite (both auto and custom subdomains)
        if DeployedSite.objects.filter(subdomain=subdomain).exists():
            return False, f"Subdomain '{subdomain}' is already taken"

        if DeployedSite.objects.filter(custom_subdomain=subdomain).exists():
            return False, f"Subdomain '{subdomain}' is already taken"

        return True, "Subdomain is available"

    @classmethod
    @transaction.atomic
    def change_subdomain(cls, workspace: Workspace, new_subdomain: str, changed_by=None) -> Dict[str, Any]:
        """
        Change workspace subdomain with history tracking and change limits

        Args:
            workspace: Workspace to update
            new_subdomain: New subdomain to assign
            changed_by: User initiating the change (optional)

        Returns:
            dict: Operation result with new URLs and remaining changes
        """
        try:
            # Get workspace infrastructure
            infrastructure = workspace.infrastructure
            old_subdomain = infrastructure.subdomain

            # Check if user is trying to keep same subdomain (no-op, don't count as change)
            if old_subdomain == new_subdomain.lower():
                return {
                    'success': True,
                    'old_subdomain': old_subdomain,
                    'new_subdomain': old_subdomain,
                    'new_live_url': f"https://{old_subdomain}.huzilerz.com",
                    'new_preview_url': f"https://{old_subdomain}.preview.huzilerz.com",
                    'changes_remaining': infrastructure.subdomain_changes_limit - infrastructure.subdomain_changes_count,
                    'warnings': ['Subdomain unchanged']
                }

            # Check change limit
            if infrastructure.subdomain_changes_count >= infrastructure.subdomain_changes_limit:
                return {
                    'success': False,
                    'errors': [
                        f"You have reached the maximum number of subdomain changes ({infrastructure.subdomain_changes_limit}). "
                        "Contact support if you need to change your subdomain."
                    ]
                }

            # Validate new subdomain (pass workspace_id to allow checking current subdomain)
            validation = cls.validate_subdomain(new_subdomain, str(workspace.id))

            if not validation['valid']:
                return {
                    'success': False,
                    'errors': validation['errors'],
                    'warnings': validation['warnings']
                }

            normalized_subdomain = validation['normalized_subdomain']

            # Mark old subdomain as changed in history
            old_history = SubdomainHistory.objects.filter(
                workspace=workspace,
                subdomain=old_subdomain,
                used_until__isnull=True
            ).first()

            if old_history:
                old_history.mark_changed(changed_by=changed_by, reason='Changed to new subdomain')

            # Create new history record
            SubdomainHistory.objects.create(
                workspace=workspace,
                subdomain=normalized_subdomain,
                changed_by=changed_by
            )

            # Update infrastructure subdomain and change tracking
            infrastructure.subdomain = normalized_subdomain
            infrastructure.subdomain_changes_count += 1
            infrastructure.last_subdomain_change_at = timezone.now()
            infrastructure.save(update_fields=[
                'subdomain',
                'subdomain_changes_count',
                'last_subdomain_change_at',
                'updated_at'
            ])

            # Update deployed site if exists
            deployed_site = workspace.deployed_sites.first()
            if deployed_site:
                deployed_site.custom_subdomain = normalized_subdomain
                deployed_site.save(update_fields=['custom_subdomain', 'updated_at'])

            changes_remaining = infrastructure.subdomain_changes_limit - infrastructure.subdomain_changes_count

            logger.info(
                f"Subdomain changed for workspace {workspace.id}: "
                f"{old_subdomain} -> {normalized_subdomain} "
                f"(Changes remaining: {changes_remaining})"
            )

            return {
                'success': True,
                'old_subdomain': old_subdomain,
                'new_subdomain': normalized_subdomain,
                'new_live_url': f"https://{normalized_subdomain}.huzilerz.com",
                'new_preview_url': f"https://{normalized_subdomain}.preview.huzilerz.com",
                'changes_remaining': changes_remaining,
                'warnings': validation['warnings']
            }

        except Exception as e:
            logger.error(f"Failed to change subdomain for workspace {workspace.id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'errors': [f"Failed to change subdomain: {str(e)}"]
            }

    @classmethod
    def suggest_subdomains(cls, base_name: str, count: int = 5) -> list[str]:
        """
        Suggest available subdomains based on a base name

        Args:
            base_name: Base name for suggestions (e.g., "mystore")
            count: Number of suggestions to return

        Returns:
            list: Available subdomain suggestions
        """
        # Normalize base name
        base = re.sub(r'[^a-z0-9-]', '', base_name.lower())
        base = re.sub(r'-+', '-', base).strip('-')

        if len(base) < 3:
            base = "store"

        suggestions = []
        suffixes = ['shop', 'store', 'online', 'web', 'site', '237', 'cm', 'app']

        # Try base name first
        if cls.check_availability(base)[0]:
            suggestions.append(base)

        # Try with suffixes
        for suffix in suffixes:
            if len(suggestions) >= count:
                break

            variants = [
                f"{base}-{suffix}",
                f"{base}{suffix}",
            ]

            for variant in variants:
                if len(suggestions) >= count:
                    break

                # Validate and check availability
                validation = cls.validate_subdomain(variant)
                if validation['valid'] and variant not in suggestions:
                    suggestions.append(variant)

        # Try with numbers if still not enough
        if len(suggestions) < count:
            for i in range(1, 100):
                variant = f"{base}{i}"
                validation = cls.validate_subdomain(variant)
                if validation['valid']:
                    suggestions.append(variant)
                    if len(suggestions) >= count:
                        break

        return suggestions[:count]

    @classmethod
    def get_subdomain_info(cls, subdomain: str) -> Dict[str, Any]:
        """
        Get information about a subdomain

        Args:
            subdomain: Subdomain to query

        Returns:
            dict: Subdomain information
        """
        try:
            infrastructure = WorkspaceInfrastructure.objects.select_related(
                'workspace', 'pool'
            ).get(subdomain=subdomain)

            return {
                'exists': True,
                'subdomain': subdomain,
                'workspace_id': str(infrastructure.workspace.id),
                'workspace_name': infrastructure.workspace.name,
                'tier': infrastructure.tier_type,
                'status': infrastructure.status,
                'live_url': f"https://{subdomain}.huzilerz.com",
                'preview_url': f"https://{subdomain}.preview.huzilerz.com"
            }

        except WorkspaceInfrastructure.DoesNotExist:
            return {
                'exists': False,
                'subdomain': subdomain,
                'available': cls.check_availability(subdomain)[0]
            }
