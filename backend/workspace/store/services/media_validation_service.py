"""
Media Validation Service

Enforces business rules for media attachments to products
- Maximum 5 videos per product
- Maximum 2 3D models per product
- Unlimited images per product
"""

from typing import List, Dict, Any
from django.core.exceptions import ValidationError
from medialib.models import MediaUpload
import logging

logger = logging.getLogger(__name__)


class MediaValidationService:
    """
    Service for validating media limits before attaching to products

    Usage:
        validator = MediaValidationService()
        validator.validate_product_media(media_ids)
    """

    # Media limits per product
    MAX_VIDEOS = 5
    MAX_3D_MODELS = 2
    # Images = unlimited

    def validate_product_media(
        self,
        media_ids: List[str],
        product_id: str = None,
        workspace = None
    ) -> Dict[str, Any]:
        """
        Validate media IDs can be attached to a product

        Args:
            media_ids: List of MediaUpload IDs to attach
            product_id: Optional - for updates, excludes existing media from count
            workspace: Optional - workspace object for scoping validation (SECURITY)

        Returns:
            Dict with validation result:
            {
                'valid': bool,
                'error': str (if invalid),
                'counts': {'images': int, 'videos': int, '3d_models': int}
            }

        Raises:
            ValidationError: If limits exceeded
        """
        if not media_ids:
            return {'valid': True, 'counts': {'images': 0, 'videos': 0, '3d_models': 0}}

        try:
            # Fetch all media records with workspace validation
            query_filters = {
                'id__in': media_ids,
                'deleted_at__isnull': True
            }

            # SECURITY: Validate workspace ownership if provided
            if workspace:
                query_filters['workspace'] = workspace

            media_records = MediaUpload.objects.filter(**query_filters)

            if len(media_records) != len(media_ids):
                if workspace:
                    raise ValidationError(
                        "One or more media IDs not found, deleted, or don't belong to this workspace"
                    )
                else:
                    raise ValidationError("One or more media IDs not found or deleted")

            # Count by media type
            counts = {
                'images': 0,
                'videos': 0,
                '3d_models': 0
            }

            for media in media_records:
                media_type = media.media_type

                if media_type == 'image':
                    counts['images'] += 1
                elif media_type == 'video':
                    counts['videos'] += 1
                elif media_type == '3d_model':
                    counts['3d_models'] += 1

            # If updating existing product, add current counts
            if product_id:
                from workspace.store.models import Product, ProductMediaGallery

                try:
                    product = Product.objects.get(id=product_id)

                    # Get existing media counts (excluding the ones being replaced)
                    existing_gallery = ProductMediaGallery.objects.filter(
                        product=product
                    ).exclude(
                        media_id__in=media_ids
                    ).select_related('media')

                    for item in existing_gallery:
                        media_type = item.media.media_type
                        if media_type == 'image':
                            counts['images'] += 1
                        elif media_type == 'video':
                            counts['videos'] += 1
                        elif media_type == '3d_model':
                            counts['3d_models'] += 1

                except Product.DoesNotExist:
                    pass  # New product, no existing media

            # Validate limits
            if counts['videos'] > self.MAX_VIDEOS:
                raise ValidationError(
                    f"Maximum {self.MAX_VIDEOS} videos allowed per product. "
                    f"You're trying to add {counts['videos']} videos."
                )

            if counts['3d_models'] > self.MAX_3D_MODELS:
                raise ValidationError(
                    f"Maximum {self.MAX_3D_MODELS} 3D models allowed per product. "
                    f"You're trying to add {counts['3d_models']} 3D models."
                )

            logger.info(
                f"Media validation passed: {counts['images']} images, "
                f"{counts['videos']} videos, {counts['3d_models']} 3D models"
            )

            return {
                'valid': True,
                'counts': counts
            }

        except ValidationError as e:
            logger.warning(f"Media validation failed: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'counts': counts if 'counts' in locals() else {}
            }
        except Exception as e:
            logger.error(f"Media validation error: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': f"Validation failed: {str(e)}",
                'counts': {}
            }

    def validate_featured_media(
        self,
        media_id: str,
        allowed_types: List[str] = None,
        workspace = None
    ) -> Dict[str, Any]:
        """
        Validate featured media (single image)

        Args:
            media_id: MediaUpload ID
            allowed_types: List of allowed media types (default: ['image'])
            workspace: Optional - workspace object for scoping validation (SECURITY)

        Returns:
            Dict with validation result
        """
        if allowed_types is None:
            allowed_types = ['image']

        try:
            query_filters = {
                'id': media_id,
                'deleted_at__isnull': True
            }

            # SECURITY: Validate workspace ownership if provided
            if workspace:
                query_filters['workspace'] = workspace

            media = MediaUpload.objects.get(**query_filters)

            if media.media_type not in allowed_types:
                raise ValidationError(
                    f"Featured media must be one of: {', '.join(allowed_types)}. "
                    f"Got: {media.media_type}"
                )

            return {'valid': True, 'media': media}

        except MediaUpload.DoesNotExist:
            return {
                'valid': False,
                'error': 'Media not found or deleted'
            }
        except ValidationError as e:
            return {
                'valid': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Featured media validation error: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': f"Validation failed: {str(e)}"
            }


# Global instance
media_validator = MediaValidationService()
