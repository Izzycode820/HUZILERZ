"""
Image Processing Background Tasks

Handles automatic image optimization and thumbnail generation:
- Creates optimized web versions (1200px, 85% quality)
- Generates thumbnails for product cards (300px)
- Generates tiny thumbnails for lists (150px)
- All processing happens asynchronously after upload

User Experience:
1. User drags and drops image
2. Original saves immediately (user sees it)
3. 5-10 seconds later: Optimized versions appear automatically
4. Product pages load fast with optimized images
"""

from celery import shared_task
from PIL import Image
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging
import io

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_variations(self, upload_id: str, original_file_path: str):
    """
    Background task to create optimized and thumbnail versions of uploaded images

    This is triggered automatically after image upload - user does nothing.

    Args:
        upload_id: MediaUpload record ID
        original_file_path: Path to original uploaded image

    Returns:
        Dict with success status and created variation paths

    Process:
        1. Load original image from storage
        2. Create optimized version (1200px max, 85% quality)
        3. Create thumbnail (300px square)
        4. Create tiny thumbnail (150px square)
        5. Save all variations to storage
        6. Update MediaUpload record with paths
        7. Mark status as 'completed'
    """
    try:
        from medialib.models.media_upload_model import MediaUpload
        from medialib.services.storage_service import storage_service
        from medialib.services.upload_tracker import upload_tracker

        logger.info(f"Starting image variation processing for upload {upload_id}")

        # Get upload record
        try:
            upload = MediaUpload.objects.get(id=upload_id)
        except MediaUpload.DoesNotExist:
            logger.error(f"Upload {upload_id} not found")
            return {'success': False, 'error': 'Upload not found'}

        # Check if file exists in storage
        if not default_storage.exists(original_file_path):
            logger.error(f"Original file not found: {original_file_path}")
            upload_tracker.update_upload_status(upload_id, status='failed')
            return {'success': False, 'error': 'Original file not found'}

        # Open original image
        with default_storage.open(original_file_path, 'rb') as f:
            image_data = f.read()

        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (for RGBA, P mode images)
        if img.mode in ('RGBA', 'P', 'LA'):
            # Create white background
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        original_width, original_height = img.size

        # Prepare variations to create
        variations = {}

        # 1. OPTIMIZED VERSION (1200px max width, 85% quality)
        # Used for: Product detail pages, main display
        if original_width > 1200 or original_height > 1200:
            optimized_img = _create_optimized_version(img, max_size=1200, quality=85)

            # Save JPEG version
            optimized_path = _save_variation(
                upload, optimized_img, 'optimized', original_file_path, format='JPEG'
            )
            variations['optimized'] = optimized_path
            logger.info(f"Created optimized JPEG: {optimized_path}")

            # Save WebP version (25-34% smaller, 97% browser support)
            optimized_webp_path = _save_variation(
                upload, optimized_img, 'optimized', original_file_path, format='WEBP'
            )
            variations['optimized_webp'] = optimized_webp_path
            logger.info(f"Created optimized WebP: {optimized_webp_path}")
        else:
            # If image is already small, use original as optimized
            variations['optimized'] = original_file_path
            logger.info(f"Image already optimal size, skipping optimization")

        # 2. THUMBNAIL (300px square)
        # Used for: Product cards, grid views
        thumbnail_img = _create_thumbnail(img, size=300)

        # Save JPEG version
        thumbnail_path = _save_variation(
            upload, thumbnail_img, 'thumbnail', original_file_path, format='JPEG'
        )
        variations['thumbnail'] = thumbnail_path
        logger.info(f"Created thumbnail JPEG: {thumbnail_path}")

        # Save WebP version
        thumbnail_webp_path = _save_variation(
            upload, thumbnail_img, 'thumbnail', original_file_path, format='WEBP'
        )
        variations['thumbnail_webp'] = thumbnail_webp_path
        logger.info(f"Created thumbnail WebP: {thumbnail_webp_path}")

        # 3. TINY THUMBNAIL (150px square)
        # Used for: List views, mini previews
        tiny_img = _create_thumbnail(img, size=150)

        # Save JPEG version
        tiny_path = _save_variation(
            upload, tiny_img, 'tiny', original_file_path, format='JPEG'
        )
        variations['tiny'] = tiny_path
        logger.info(f"Created tiny JPEG: {tiny_path}")

        # Save WebP version
        tiny_webp_path = _save_variation(
            upload, tiny_img, 'tiny', original_file_path, format='WEBP'
        )
        variations['tiny_webp'] = tiny_webp_path
        logger.info(f"Created tiny WebP: {tiny_webp_path}")

        # Update MediaUpload record with variation paths
        upload.optimized_path = variations.get('optimized')
        upload.thumbnail_path = variations.get('thumbnail')

        # Store WebP and tiny variations in metadata
        if not upload.metadata:
            upload.metadata = {}

        if 'optimized_webp' in variations:
            upload.metadata['optimized_webp_path'] = variations['optimized_webp']
        if 'thumbnail_webp' in variations:
            upload.metadata['thumbnail_webp_path'] = variations['thumbnail_webp']
        if 'tiny' in variations:
            upload.metadata['tiny_thumbnail_path'] = variations['tiny']
        if 'tiny_webp' in variations:
            upload.metadata['tiny_webp_path'] = variations['tiny_webp']

        upload.status = 'completed'
        from django.utils import timezone
        upload.processed_at = timezone.now()
        upload.save()

        logger.info(f"Successfully processed image variations for upload {upload_id}")

        return {
            'success': True,
            'upload_id': upload_id,
            'variations': variations
        }

    except Exception as exc:
        logger.error(f"Image variation processing failed for {upload_id}: {str(exc)}", exc_info=True)

        # Update status to failed
        try:
            from medialib.services.upload_tracker import upload_tracker
            upload_tracker.update_upload_status(upload_id, status='failed')
        except:
            pass

        # Retry on failure (up to 3 times)
        raise self.retry(exc=exc, countdown=60)


def _create_optimized_version(img: Image.Image, max_size: int = 1200, quality: int = 85) -> Image.Image:
    """
    Create optimized version of image for web display

    Args:
        img: PIL Image object
        max_size: Maximum width or height
        quality: JPEG quality (1-100)

    Returns:
        Optimized PIL Image object
    """
    width, height = img.size

    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        if width > max_size:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            return img
    else:
        if height > max_size:
            new_height = max_size
            new_width = int(width * (max_size / height))
        else:
            return img

    # Resize using high-quality Lanczos resampling
    optimized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return optimized


def _create_thumbnail(img: Image.Image, size: int = 300) -> Image.Image:
    """
    Create square thumbnail with smart cropping

    Args:
        img: PIL Image object
        size: Square size (width = height)

    Returns:
        Thumbnail PIL Image object
    """
    width, height = img.size

    # Calculate crop box to create square from center
    if width > height:
        # Landscape - crop sides
        left = (width - height) // 2
        top = 0
        right = left + height
        bottom = height
    else:
        # Portrait - crop top/bottom
        left = 0
        top = (height - width) // 2
        right = width
        bottom = top + width

    # Crop to square
    img_cropped = img.crop((left, top, right, bottom))

    # Resize to target size
    thumbnail = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

    return thumbnail


def _save_variation(upload, img: Image.Image, variation_type: str, original_path: str, format: str = 'JPEG') -> str:
    """
    Save image variation to storage in specified format

    Args:
        upload: MediaUpload instance
        img: PIL Image object to save
        variation_type: 'optimized', 'thumbnail', or 'tiny'
        original_path: Path to original file
        format: 'JPEG' or 'WEBP'

    Returns:
        Path to saved variation
    """
    # Generate variation path based on original path
    # Example: tenants/workspace_abc/products/product_xyz/images/original/file.jpg
    #       -> tenants/workspace_abc/products/product_xyz/images/optimized/file.jpg
    #       -> tenants/workspace_abc/products/product_xyz/images/optimized/file.webp

    path_parts = original_path.split('/')

    # Replace 'original' with variation type
    if 'original' in path_parts:
        version_index = path_parts.index('original')
        path_parts[version_index] = variation_type
    else:
        # If no 'original' in path, insert variation type before filename
        path_parts.insert(-1, variation_type)

    # Change file extension based on format
    filename = path_parts[-1]
    filename_without_ext = '.'.join(filename.split('.')[:-1])

    if format == 'WEBP':
        path_parts[-1] = f"{filename_without_ext}.webp"
    else:
        path_parts[-1] = f"{filename_without_ext}.jpg"

    variation_path = '/'.join(path_parts)

    # Convert image to bytes
    img_io = io.BytesIO()

    # Save with appropriate format and optimization
    if format == 'WEBP':
        # WebP: 25-34% smaller than JPEG, 97% browser support
        img.save(img_io, format='WEBP', quality=85, method=6)  # method=6 = best compression
    else:
        # JPEG: Fallback for older browsers
        img.save(img_io, format='JPEG', quality=85, optimize=True)

    img_io.seek(0)

    # Save to storage
    default_storage.save(variation_path, ContentFile(img_io.read()))

    return variation_path
