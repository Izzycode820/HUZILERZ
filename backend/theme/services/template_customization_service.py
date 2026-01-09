from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError
from ..models import Template, TemplateCustomization
from workspace.core.models import Workspace
import logging
import json

logger = logging.getLogger(__name__)


class TemplateCustomizationService:
    """Service for template customization business logic with error handling"""

    @staticmethod
    def clone_template_to_workspace(template_id, workspace_id, user):
        """
        Clone a template to workspace with error handling and validation

        Args:
            template_id: ID of template to clone
            workspace_id: ID of workspace to clone to
            user: User performing the operation

        Returns:
            TemplateCustomization instance

        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Cloning template {template_id} to workspace {workspace_id} by user {user.id}")

            # Validate inputs
            if not template_id or not workspace_id:
                raise ValidationError("Template ID and Workspace ID are required")

            # Get template and workspace with error handling
            try:
                template = Template.objects.get(id=template_id, status__in=['published', 'active'])
            except Template.DoesNotExist:
                logger.warning(f"Template {template_id} not found or not available")
                raise ValidationError("Template not found or not available")

            try:
                workspace = Workspace.objects.get(id=workspace_id)
            except Workspace.DoesNotExist:
                logger.warning(f"Workspace {workspace_id} not found")
                raise ValidationError("Workspace not found")

            # Check workspace compatibility
            if workspace.type not in template.workspace_types:
                logger.warning(f"Workspace type {workspace.type} not compatible with template {template.name}")
                raise ValidationError(
                    f"Template {template.name} is not compatible with workspace type {workspace.type}"
                )

            # Check theme library limit capability
            from subscription.services.gating import check_theme_library_limit
            allowed, error_msg = check_theme_library_limit(workspace)
            if not allowed:
                raise ValidationError(error_msg)

            # Get template version instance (optional for now)
            template_version = template.versions.filter(status='active').first() if hasattr(template, 'versions') else None

            # Create customization with atomic transaction
            with transaction.atomic():
                customization = TemplateCustomization.objects.create(
                    workspace=workspace,
                    template=template,
                    template_version=template_version,
                    theme_name=template.name,  # Use template name as initial theme name
                    puck_config=template.puck_config or {},
                    puck_data=template.puck_data or {},
                    is_active=False,  # Draft by default
                    created_by=user,
                    last_modified_by=user
                )

                # Update DeployedSite with template reference (subdomain already assigned on workspace creation)
                from workspace.hosting.models import DeployedSite
                try:
                    deployed_site = DeployedSite.objects.get(workspace=workspace)
                    # Set template reference (but don't link customization yet - only on publish)
                    if not deployed_site.template:
                        deployed_site.template = template
                        deployed_site.save(update_fields=['template'])
                        logger.info(f"Linked template '{template.name}' to DeployedSite for workspace {workspace.name}")

                    # UNIFIED SEO: Sync initial SEO from template's puck_data to DeployedSite
                    # This sets defaults so UI forms have initial values
                    puck_data = template.puck_data or {}
                    root_props = puck_data.get('root', {}).get('props', {})
                    page_title = root_props.get('pageTitle', '').strip()
                    page_description = root_props.get('pageDescription', '').strip()

                    seo_fields_to_update = []
                    if page_title and not deployed_site.seo_title:
                        deployed_site.seo_title = page_title[:60]  # Respect max length
                        seo_fields_to_update.append('seo_title')
                    if page_description and not deployed_site.seo_description:
                        deployed_site.seo_description = page_description[:160]
                        seo_fields_to_update.append('seo_description')

                    if seo_fields_to_update:
                        deployed_site.save(update_fields=seo_fields_to_update)
                        logger.info(
                            f"Synced initial SEO from template to DeployedSite for workspace {workspace.name} "
                            f"(fields: {', '.join(seo_fields_to_update)})"
                        )

                except DeployedSite.DoesNotExist:
                    logger.warning(f"DeployedSite not found for workspace {workspace.id} - subdomain may not be assigned")

                logger.info(f"Successfully created customization {customization.id} for workspace {workspace_id}")
                return customization

        except ValidationError:
            # Re-raise validation errors
            raise
        except DatabaseError as e:
            logger.error(f"Database error cloning template {template_id}: {e}")
            raise ValidationError("Database error occurred while cloning template")
        except Exception as e:
            logger.error(f"Unexpected error cloning template {template_id}: {e}")
            raise ValidationError("An unexpected error occurred")

    @staticmethod
    def save_customizations(customization_id, puck_config, puck_data, user):
        """
        Save customizations for a specific theme with error handling

        Args:
            customization_id: ID of customization to update
            puck_config: Updated Puck configuration
            puck_data: Updated Puck data (page content)
            user: User performing the operation

        Returns:
            Updated TemplateCustomization instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Saving customizations for theme {customization_id} by user {user.id}")

            # Validate inputs
            if not customization_id:
                raise ValidationError("Customization ID is required")

            # Validate JSON data
            if puck_config:
                try:
                    json.dumps(puck_config)
                except (TypeError, ValueError) as e:
                    raise ValidationError(f"Invalid Puck configuration: {e}")

            if puck_data:
                try:
                    json.dumps(puck_data)
                except (TypeError, ValueError) as e:
                    raise ValidationError(f"Invalid Puck data: {e}")

            # Get customization by ID
            try:
                customization = TemplateCustomization.objects.get(id=customization_id)
            except TemplateCustomization.DoesNotExist:
                logger.warning(f"Theme customization {customization_id} not found")
                raise ValidationError("Theme customization not found")

            # Update with atomic transaction
            with transaction.atomic():
                # Update Puck config and data
                if puck_config is not None:
                    customization.puck_config = puck_config
                if puck_data is not None:
                    customization.puck_data = puck_data

                customization.last_modified_by = user
                customization.save()

                logger.info(f"Successfully saved customizations for theme {customization_id}")

            # CRITICAL: Only invalidate cache if theme is ACTIVE (published)
            # Draft themes don't need invalidation since they're not live
            # This prevents unnecessary CDN invalidations during editing
            if customization.is_active:
                try:
                    from workspace.hosting.tasks import invalidate_workspace_cache_async

                    # Queue async invalidation with 5s delay (debounce rapid saves)
                    # Debouncing prevents cache stampede when user makes multiple quick edits
                    invalidate_workspace_cache_async.apply_async(
                        args=[str(customization.workspace.id), "theme_edit"],
                        countdown=5  # Wait 5s before invalidating
                    )

                    logger.info(
                        f"Queued cache invalidation for active theme {customization_id} "
                        f"(workspace {customization.workspace.id}, debounced 5s)"
                    )
                except Exception as cache_error:
                    # Cache invalidation failure is NON-CRITICAL - theme is already saved
                    # Log warning but don't fail the save operation
                    logger.warning(
                        f"Cache invalidation queue failed (non-critical) for theme {customization_id}: "
                        f"{str(cache_error)}"
                    )

                # UNIFIED SEO: Sync SEO changes from puck_data to DeployedSite
                # Only sync if theme is active (published) and puck_data was updated
                if puck_data is not None:
                    try:
                        from workspace.hosting.models import DeployedSite

                        deployed_site = DeployedSite.objects.get(workspace=customization.workspace)
                        
                        # Extract SEO from puck_data
                        root_props = puck_data.get('root', {}).get('props', {})
                        page_title = root_props.get('pageTitle', '').strip()
                        page_description = root_props.get('pageDescription', '').strip()

                        seo_fields_to_update = []
                        
                        # Sync title if changed and not empty
                        if page_title and page_title != deployed_site.seo_title:
                            deployed_site.seo_title = page_title[:60]
                            seo_fields_to_update.append('seo_title')
                        
                        # Sync description if changed and not empty
                        if page_description and page_description != deployed_site.seo_description:
                            deployed_site.seo_description = page_description[:160]
                            seo_fields_to_update.append('seo_description')

                        if seo_fields_to_update:
                            deployed_site.save(update_fields=seo_fields_to_update)
                            logger.info(
                                f"Synced SEO from Puck to DeployedSite for workspace {customization.workspace.id} "
                                f"(fields: {', '.join(seo_fields_to_update)})"
                            )

                    except DeployedSite.DoesNotExist:
                        logger.warning(
                            f"Cannot sync SEO - DeployedSite not found for workspace {customization.workspace.id}"
                        )
                    except Exception as seo_error:
                        # SEO sync failure is NON-CRITICAL - theme is already saved
                        logger.warning(
                            f"SEO sync failed (non-critical) for theme {customization_id}: {str(seo_error)}"
                        )

            return customization

        except ValidationError:
            raise
        except DatabaseError as e:
            logger.error(f"Database error saving customizations for theme {customization_id}: {e}")
            raise ValidationError("Database error occurred while saving customizations")
        except Exception as e:
            logger.error(f"Unexpected error saving customizations for theme {customization_id}: {e}")
            raise ValidationError("An unexpected error occurred")



    @staticmethod
    def publish_theme(customization_id, user):
        """
        Publish a theme (make it active for workspace)

        Args:
            customization_id: ID of customization to publish
            user: User performing the operation

        Returns:
            Published TemplateCustomization instance

        Raises:
            ValidationError: If validation fails or deployment not allowed
        """
        try:
            logger.info(f"Publishing theme {customization_id} by user {user.id}")

            # Get customization by ID
            try:
                customization = TemplateCustomization.objects.get(id=customization_id)
            except TemplateCustomization.DoesNotExist:
                raise ValidationError("Theme customization not found")

            # CRITICAL: Check deployment capability (free tier gating)
            # HostingEnvironment must exist (created during signup via provision_hosting_environment task)
            workspace = customization.workspace

            try:
                hosting_env = workspace.owner.hosting_environment
            except AttributeError:
                logger.error(
                    f"HostingEnvironment not found for workspace {workspace.id} owner {workspace.owner.id}. "
                    f"This should have been created during signup."
                )
                raise ValidationError(
                    "Your account is not fully provisioned. Please contact support."
                )

            # Check deployment capability (gating: free tier cannot publish)
            if not hosting_env.is_deployment_allowed:
                logger.warning(
                    f"Theme publish blocked for workspace {workspace.id} - "
                    f"deployment_allowed=False (user must upgrade to paid tier)"
                )
                raise ValidationError(
                    "Publishing themes requires a paid subscription. "
                    "Upgrade to Beginner tier or higher to make your theme live."
                )

            logger.info(f"Deployment capability verified for workspace {workspace.id}")

            # Publish (model handles unpublishing others)
            with transaction.atomic():
                customization.publish(user=user)

                # Update DeployedSite status to active and link customization (pointer change)
                from workspace.hosting.models import DeployedSite
                try:
                    deployed_site = DeployedSite.objects.get(workspace=customization.workspace)
                    deployed_site.customization = customization
                    deployed_site.status = 'active'  # Make site live
                    deployed_site.save(update_fields=['customization', 'status'])
                    logger.info(
                        f"DeployedSite activated for workspace '{customization.workspace.name}' "
                        f"with theme '{customization.theme_name}'"
                    )
                except DeployedSite.DoesNotExist:
                    logger.error(f"DeployedSite not found for workspace {customization.workspace.id}")

            # CRITICAL: Invalidate CDN cache after publish (outside transaction to avoid rollback issues)
            # Theme publish must invalidate cache so users see new theme immediately
            try:
                from workspace.hosting.services.cdn_cache_service import CDNCacheService

                cache_result = CDNCacheService.invalidate_workspace_cache(
                    workspace_id=str(customization.workspace.id)
                )

                # Check if invalidation succeeded (absence of error = success in mock/dev mode)
                if cache_result.get('success') is not False:
                    logger.info(
                        f"CDN cache invalidated for workspace {customization.workspace.id} after theme publish"
                    )
                else:
                    # Cache invalidation failed but theme is still published (non-critical)
                    logger.warning(
                        f"CDN cache invalidation failed (non-critical): {cache_result.get('error')} "
                        f"- theme is published but may take time to appear"
                    )
            except Exception as cache_error:
                # Cache invalidation exception is NON-CRITICAL - theme is already published
                logger.warning(
                    f"CDN cache invalidation exception (non-critical) for workspace {customization.workspace.id}: "
                    f"{str(cache_error)} - theme is published but may take time to appear"
                )

            # OPTIMIZATION: Warm critical routes after invalidation to prevent cache stampede
            # This pre-populates CDN edge cache so first visitors don't hit origin
            try:
                from workspace.hosting.models import DeployedSite
                from workspace.hosting.tasks import warm_cache_async

                # Get deployed site for URL construction
                deployed_site = DeployedSite.objects.get(workspace=customization.workspace)

                # Construct base URL (subdomain or custom domain)
                if deployed_site.custom_domain and deployed_site.custom_domain_verified:
                    base_url = f"https://{deployed_site.custom_domain}"
                else:
                    base_url = f"https://{deployed_site.subdomain}.huzilerz.com"

                # Critical routes to warm (homepage is most important)
                critical_urls = [
                    f"{base_url}/",  # Homepage - always warm this first
                ]

                # Optionally add product listing if workspace is e-commerce
                # This can be expanded based on workspace type
                if hasattr(customization.workspace, 'workspace_type'):
                    if customization.workspace.workspace_type in ['ecommerce', 'marketplace']:
                        critical_urls.append(f"{base_url}/products")

                # Queue async cache warming with 2s delay (wait for invalidation to propagate)
                # Non-blocking - runs in background
                warm_cache_async.apply_async(
                    args=[str(customization.workspace.id), critical_urls],
                    countdown=2  # Wait 2s for CDN invalidation to propagate
                )

                logger.info(
                    f"Queued cache warming for workspace {customization.workspace.id} "
                    f"({len(critical_urls)} critical URLs)"
                )

            except DeployedSite.DoesNotExist:
                logger.warning(
                    f"Cannot warm cache - DeployedSite not found for workspace {customization.workspace.id}"
                )
            except Exception as warm_error:
                # Cache warming failure is NON-CRITICAL - theme is already published and cache will warm naturally
                logger.warning(
                    f"Cache warming queue failed (non-critical) for workspace {customization.workspace.id}: "
                    f"{str(warm_error)}"
                )

            logger.info(f"Successfully published theme {customization.id}")
            return customization

        except ValidationError:
            raise
        except DatabaseError as e:
            logger.error(f"Database error publishing theme {customization_id}: {e}")
            raise ValidationError("Database error occurred while publishing theme")
        except Exception as e:
            logger.error(f"Unexpected error publishing theme {customization_id}: {e}")
            raise ValidationError("An unexpected error occurred")

    @staticmethod
    def publish_for_deployment(workspace_id, user):
        """
        Publish theme during hosting deployment flow (idempotent)

        Called by hosting module when deploying site.
        Handles both cases:
        - If theme already active → returns it (idempotent)
        - If no active theme → publishes the first available draft

        Args:
            workspace_id: ID of workspace to publish theme for
            user: User performing deployment

        Returns:
            Published TemplateCustomization instance

        Raises:
            ValidationError: If no theme found or validation fails
        """
        try:
            logger.info(f"Publishing theme for deployment - workspace {workspace_id} by user {user.id}")

            # Check if already has active theme (idempotent)
            active_customization = TemplateCustomization.objects.filter(
                workspace_id=workspace_id,
                is_active=True
            ).first()

            if active_customization:
                logger.info(f"Theme already published for workspace {workspace_id} - skipping (idempotent)")
                return active_customization

            # No active theme - get most recently edited draft
            draft_customization = TemplateCustomization.objects.filter(
                workspace_id=workspace_id
            ).order_by('-last_edited_at').first()

            if not draft_customization:
                raise ValidationError(
                    f"No theme found for workspace {workspace_id}. User must clone a theme first."
                )

            # Publish the draft
            logger.info(f"Publishing draft theme {draft_customization.id} for deployment")
            return TemplateCustomizationService.publish_theme(
                customization_id=draft_customization.id,
                user=user
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error publishing theme for deployment (workspace {workspace_id}): {e}", exc_info=True)
            raise ValidationError(f"Failed to publish theme for deployment: {str(e)}")



    @staticmethod
    def get_workspace_themes(workspace_id, user):
        """
        Get all themes (customizations) for a specific workspace

        Args:
            workspace_id: ID of workspace
            user: User making the request

        Returns:
            QuerySet of TemplateCustomization instances for the workspace

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting themes for workspace {workspace_id} by user {user.id}")

            # Validate inputs
            if not workspace_id:
                raise ValidationError("Workspace ID is required")

            # Get workspace with error handling
            try:
                workspace = Workspace.objects.get(id=workspace_id)
            except Workspace.DoesNotExist:
                logger.warning(f"Workspace {workspace_id} not found")
                raise ValidationError("Workspace not found")

            # Get ALL themes for this workspace (published + drafts) with performance optimization
            # Using select_related to avoid N+1 queries for template and workspace data
            workspace_themes = TemplateCustomization.objects.filter(
                workspace=workspace
            ).select_related(
                'template', 'workspace'
            ).order_by('-is_active', '-last_edited_at')  # Active first, then by edit time

            logger.info(f"Found {workspace_themes.count()} themes for workspace {workspace_id}")
            return workspace_themes

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting themes for workspace {workspace_id}: {e}")
            raise ValidationError("Error retrieving workspace themes")

    @staticmethod
    def delete_theme(customization_id, user):
        """
        Delete a theme from user's library.
        Cannot delete active (published) theme.

        Args:
            customization_id: ID of customization to delete
            user: User performing the operation

        Returns:
            Boolean success

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Deleting theme {customization_id} by user {user.id}")

            # Get customization
            try:
                customization = TemplateCustomization.objects.get(id=customization_id)
            except TemplateCustomization.DoesNotExist:
                raise ValidationError("Theme not found")

            # Use model's delete method (handles active check)
            customization.delete()

            logger.info(f"Successfully deleted theme {customization_id}")
            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error deleting theme {customization_id}: {e}")
            raise ValidationError("An unexpected error occurred")

    @staticmethod
    def duplicate_theme(customization_id, new_name, user):
        """
        Duplicate a theme for experimentation.

        Args:
            customization_id: ID of customization to duplicate
            new_name: Name for the duplicate (optional)
            user: User performing the operation

        Returns:
            New TemplateCustomization instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Duplicating theme {customization_id} by user {user.id}")

            # Get original customization
            try:
                original = TemplateCustomization.objects.get(id=customization_id)
            except TemplateCustomization.DoesNotExist:
                raise ValidationError("Theme not found")

            # Check theme library limit capability
            from subscription.services.gating import check_theme_library_limit
            allowed, error_msg = check_theme_library_limit(original.workspace)
            if not allowed:
                raise ValidationError(error_msg)

            # Use model's duplicate method
            duplicate = original.duplicate(new_name=new_name, user=user)

            logger.info(f"Successfully duplicated theme {customization_id} → {duplicate.id}")
            return duplicate

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error duplicating theme {customization_id}: {e}")
            raise ValidationError("An unexpected error occurred")

    @staticmethod
    def rename_theme(customization_id, new_name, user):
        """
        Rename a theme.

        Args:
            customization_id: ID of customization to rename
            new_name: New theme name
            user: User performing the operation

        Returns:
            Updated TemplateCustomization instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Renaming theme {customization_id} to '{new_name}' by user {user.id}")

            # Validate inputs
            if not new_name or not new_name.strip():
                raise ValidationError("Theme name is required")

            # Get customization
            try:
                customization = TemplateCustomization.objects.get(id=customization_id)
            except TemplateCustomization.DoesNotExist:
                raise ValidationError("Theme not found")

            # Update name
            customization.theme_name = new_name.strip()
            customization.last_modified_by = user
            customization.save(update_fields=['theme_name', 'last_modified_by'])

            logger.info(f"Successfully renamed theme {customization_id}")
            return customization

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error renaming theme {customization_id}: {e}")
            raise ValidationError("An unexpected error occurred")

    @staticmethod
    def get_active_theme(workspace_id):
        """
        Get the currently published (active) theme for a workspace.

        Args:
            workspace_id: ID of workspace

        Returns:
            TemplateCustomization instance or None

        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Getting active theme for workspace {workspace_id}")

            # Get workspace
            try:
                workspace = Workspace.objects.get(id=workspace_id)
            except Workspace.DoesNotExist:
                raise ValidationError("Workspace not found")

            # Get active theme
            active_theme = TemplateCustomization.objects.filter(
                workspace=workspace,
                is_active=True
            ).select_related('template').first()

            if active_theme:
                logger.info(f"Found active theme {active_theme.id} for workspace {workspace_id}")
            else:
                logger.info(f"No active theme for workspace {workspace_id}")

            return active_theme

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting active theme for workspace {workspace_id}: {e}")
            raise ValidationError("An unexpected error occurred")