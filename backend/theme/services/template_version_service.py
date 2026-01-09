"""
Template Version Service for template developer operations.

This service handles GitHub-based template version management for template developers.
It should NOT be used for user customization rollbacks.
"""

import logging
from typing import Dict, Any, List
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Template, TemplateVersion, SyncLog
from .github_integration_service import GitHubIntegrationService

logger = logging.getLogger(__name__)


class TemplateVersionService:
    """
    Service for template developer operations with GitHub integration.
    
    This service is for:
    - Creating new template versions from GitHub
    - Managing template releases
    - Template developer rollbacks (GitHub revert commits)
    - Template version history
    """

    @staticmethod
    def create_version_from_github(
        template_id: str,
        commit_sha: str,
        version_name: str,
        user
    ) -> TemplateVersion:
        """
        Create a new template version from a GitHub commit.
        
        Args:
            template_id: UUID of template
            commit_sha: GitHub commit SHA
            version_name: Semantic version name (e.g., "1.2.3")
            user: User creating the version
            
        Returns:
            New TemplateVersion instance
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(
            f"Creating template version from GitHub: template={template_id}, "
            f"commit={commit_sha}, version={version_name}, user={user.id}"
        )
        
        try:
            template = Template.objects.get(id=template_id)
            
            # Validate GitHub configuration
            if not template.github_repo_owner or not template.github_repo_name:
                raise ValidationError(
                    "Template is not configured for GitHub integration"
                )
            
            # Get commit details from GitHub
            commit_details = GitHubIntegrationService.get_commit_details(
                repo_owner=template.github_repo_owner,
                repo_name=template.github_repo_name,
                commit_sha=commit_sha
            )
            
            # Create template version
            with transaction.atomic():
                version = TemplateVersion.objects.create(
                    template=template,
                    version=version_name,
                    status=TemplateVersion.STATUS_ACTIVE,
                    changelog=commit_details['message'],
                    git_commit_hash=commit_sha,
                    git_tag=f"v{version_name}",
                    cdn_path=f"themes/{template.slug}/{version_name}/",
                    created_by=user
                )
                
                # Update template version
                template.version = version_name
                template.save(update_fields=['version'])
                
                # Create sync log
                SyncLog.objects.create(
                    template=template,
                    triggered_by=user,
                    sync_type=SyncLog.SYNC_TYPE_MANUAL,
                    status=SyncLog.STATUS_COMPLETED,
                    source_version=commit_sha,
                    target_version=commit_sha,
                    cdn_path=version.cdn_path,
                    git_commit_hash=commit_sha,
                    git_tag=f"v{version_name}"
                )
                
                logger.info(
                    f"Successfully created template version {version.id} "
                    f"from GitHub commit {commit_sha}"
                )
                
                return version
                
        except Template.DoesNotExist:
            logger.warning(f"Template {template_id} not found")
            raise ValidationError("Template not found")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating template version: {e}", exc_info=True)
            raise ValidationError("Failed to create template version from GitHub")

    @staticmethod
    def get_template_version_history(
        template_id: str,
        limit: int = 50
    ) -> List[TemplateVersion]:
        """
        Get version history for a template.
        
        Args:
            template_id: UUID of template
            limit: Number of versions to return
            
        Returns:
            List of TemplateVersion instances
            
        Raises:
            ValidationError: If template not found
        """
        logger.info(f"Getting version history for template {template_id}")
        
        try:
            template = Template.objects.get(id=template_id)
            
            versions = TemplateVersion.objects.filter(
                template=template
            ).order_by('-created_at')[:limit]
            
            logger.info(f"Found {len(versions)} versions for template {template_id}")
            return list(versions)
            
        except Template.DoesNotExist:
            logger.warning(f"Template {template_id} not found")
            raise ValidationError("Template not found")

    @staticmethod
    def revert_template_version(
        template_id: str,
        target_version_id: str,
        user
    ) -> Dict[str, Any]:
        """
        Revert template to previous version (Template Developer Operation).
        
        This creates a GitHub revert commit and updates the template.
        Should only be used by template developers.
        
        Args:
            template_id: UUID of template
            target_version_id: UUID of version to revert to
            user: User performing revert
            
        Returns:
            Dictionary with revert results
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(
            f"Reverting template {template_id} to version {target_version_id} "
            f"by user {user.id}"
        )
        
        try:
            template = Template.objects.get(id=template_id)
            target_version = TemplateVersion.objects.get(
                id=target_version_id,
                template=template
            )
            
            # Validate GitHub configuration
            if not template.github_repo_owner or not template.github_repo_name:
                raise ValidationError(
                    "Template is not configured for GitHub integration"
                )
            
            # Validate target version has Git commit
            if not target_version.git_commit_hash:
                raise ValidationError(
                    "Target version must have a Git commit hash"
                )
            
            # Create GitHub revert commit
            revert_result = GitHubIntegrationService.create_revert_commit(
                repo_owner=template.github_repo_owner,
                repo_name=template.github_repo_name,
                commit_sha=target_version.git_commit_hash,
                user_email=user.email,
                user_name=user.get_full_name() or user.username
            )
            
            # Update template to target version
            template.version = target_version.version
            template.save(update_fields=['version'])
            
            # Create sync log
            sync_log = SyncLog.objects.create(
                template=template,
                triggered_by=user,
                sync_type=SyncLog.SYNC_TYPE_ROLLBACK,
                status=SyncLog.STATUS_COMPLETED,
                source_version=template.version,
                target_version=target_version.version,
                cdn_path=target_version.cdn_path,
                git_commit_hash=revert_result['revert_commit_sha'],
                git_tag=f"revert-{target_version.version}",
                metadata={
                    'revert_commit_url': revert_result.get('url', ''),
                    'target_version_id': str(target_version.id)
                }
            )
            
            logger.info(
                f"Successfully reverted template {template_id} to version "
                f"{target_version.version}"
            )
            
            return {
                'template': template,
                'target_version': target_version,
                'revert_commit': revert_result,
                'sync_log': sync_log
            }
            
        except (Template.DoesNotExist, TemplateVersion.DoesNotExist):
            logger.warning(
                f"Template {template_id} or version {target_version_id} not found"
            )
            raise ValidationError("Template or version not found")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error reverting template version: {e}", exc_info=True)
            raise ValidationError("Failed to revert template version")

    @staticmethod
    def get_github_commits(
        template_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent GitHub commits for a template.
        
        Args:
            template_id: UUID of template
            limit: Number of commits to return
            
        Returns:
            List of commit dictionaries
            
        Raises:
            ValidationError: If operation fails
        """
        logger.info(f"Getting GitHub commits for template {template_id}")
        
        try:
            template = Template.objects.get(id=template_id)
            
            if not template.github_repo_owner or not template.github_repo_name:
                raise ValidationError(
                    "Template is not configured for GitHub integration"
                )
            
            commits = GitHubIntegrationService.get_commit_history(
                repo_owner=template.github_repo_owner,
                repo_name=template.github_repo_name,
                branch=template.github_branch,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(commits)} GitHub commits")
            return commits
            
        except Template.DoesNotExist:
            logger.warning(f"Template {template_id} not found")
            raise ValidationError("Template not found")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting GitHub commits: {e}", exc_info=True)
            raise ValidationError("Failed to retrieve GitHub commits")