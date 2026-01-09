"""
Production-Grade Image Upload Service

Features:
- File type validation (PNG, JPEG, WebP, GIF)
- File size limits (configurable per environment)
- Image dimension validation
- Secure file naming
- Multiple storage backends (local filesystem, S3)
- Image optimization and resizing
- Error handling and logging
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageUploadService:
    """
    Production-grade image upload service with validation and optimization
    """

    # Allowed image formats and their MIME types
    ALLOWED_EXTENSIONS = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'gif': 'image/gif'
    }

    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'development': 10 * 1024 * 1024,  # 10MB for dev
        'production': 5 * 1024 * 1024,    # 5MB for production
    }

    # Maximum image dimensions
    MAX_DIMENSIONS = {
        'width': 4096,
        'height': 4096
    }

    def __init__(self):
        self.environment = 'development' if settings.DEBUG else 'production'
        self.max_file_size = self.MAX_FILE_SIZES[self.environment]

    def validate_image(self, uploaded_file: UploadedFile) -> Dict[str, Any]:
        """
        Validate uploaded image file

        Args:
            uploaded_file: Django UploadedFile instance

        Returns:
            Dict with validation result and image info

        Raises:
            ValidationError: If image fails validation
        """
        try:
            # Check file extension
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS.keys())}"
                )

            # Check file size
            if uploaded_file.size > self.max_file_size:
                raise ValidationError(
                    f"File too large. Maximum size: {self.max_file_size // (1024 * 1024)}MB"
                )

            # Check if file is empty
            if uploaded_file.size == 0:
                raise ValidationError("File is empty")

            # Validate image dimensions and format using PIL
            try:
                with Image.open(uploaded_file) as img:
                    # Check image format
                    if img.format not in ['JPEG', 'PNG', 'WEBP', 'GIF']:
                        raise ValidationError("Invalid image format")

                    # Check dimensions
                    width, height = img.size
                    if width > self.MAX_DIMENSIONS['width'] or height > self.MAX_DIMENSIONS['height']:
                        raise ValidationError(
                            f"Image dimensions too large. Maximum: {self.MAX_DIMENSIONS['width']}x{self.MAX_DIMENSIONS['height']}"
                        )

                    # Return image info
                    return {
                        'valid': True,
                        'width': width,
                        'height': height,
                        'format': img.format.lower(),
                        'size': uploaded_file.size,
                        'extension': file_extension
                    }

            except Exception as e:
                raise ValidationError(f"Invalid image file: {str(e)}")

        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Image validation failed: {str(e)}")

    def generate_unique_filename(self, original_filename: str, workspace_id: str) -> str:
        """
        Generate secure unique filename

        Args:
            original_filename: Original uploaded filename
            workspace_id: Workspace ID for organization

        Returns:
            Unique filename with UUID
        """
        file_extension = original_filename.split('.')[-1].lower()
        unique_id = uuid.uuid4().hex

        # Sanitize filename
        safe_name = ''.join(c for c in original_filename.split('.')[0] if c.isalnum() or c in ('-', '_'))

        return f"workspace_{workspace_id}/{safe_name}_{unique_id[:8]}.{file_extension}"

    def optimize_image(self, image_path: str, max_width: int = 1200, quality: int = 85) -> str:
        """
        Optimize image for web delivery

        Args:
            image_path: Path to original image
            max_width: Maximum width for resizing
            quality: JPEG/WebP quality (1-100)

        Returns:
            Path to optimized image
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Resize if larger than max width
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Generate optimized filename
                optimized_path = image_path.replace(f".{img.format.lower()}", f"_optimized.{img.format.lower()}")

                # Save optimized image
                if img.format == 'JPEG':
                    img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
                elif img.format == 'PNG':
                    img.save(optimized_path, 'PNG', optimize=True)
                elif img.format == 'WEBP':
                    img.save(optimized_path, 'WEBP', quality=quality)
                else:
                    # For GIF and other formats, just copy
                    img.save(optimized_path)

                return optimized_path

        except Exception as e:
            logger.error(f"Image optimization failed: {str(e)}", exc_info=True)
            # Return original path if optimization fails
            return image_path

    def upload_image(self, uploaded_file: UploadedFile, workspace_id: str) -> Dict[str, Any]:
        """
        Upload and process image file

        Args:
            uploaded_file: Django UploadedFile instance
            workspace_id: Workspace ID for organization

        Returns:
            Dict with upload result and file info
        """
        try:
            # Validate image
            validation_result = self.validate_image(uploaded_file)

            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result.get('error', 'Image validation failed')
                }

            # Generate unique filename
            filename = self.generate_unique_filename(uploaded_file.name, workspace_id)

            # Create upload directory if it doesn't exist
            upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / f'workspace_{workspace_id}'
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Save original file
            file_path = upload_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Optimize image
            optimized_path = self.optimize_image(str(file_path))

            # Generate URLs
            original_url = f"{settings.MEDIA_URL}uploads/{filename}"
            optimized_url = original_url.replace(f".{validation_result['extension']}", f"_optimized.{validation_result['extension']}")

            return {
                'success': True,
                'original_url': original_url,
                'optimized_url': optimized_url,
                'filename': filename,
                'width': validation_result['width'],
                'height': validation_result['height'],
                'size': validation_result['size'],
                'format': validation_result['format']
            }

        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"Image upload failed: {str(e)}"
            }

    def delete_image(self, image_url: str) -> bool:
        """
        Delete uploaded image file

        Args:
            image_url: URL of image to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Extract filename from URL
            filename = image_url.replace(settings.MEDIA_URL, '')
            file_path = Path(settings.MEDIA_ROOT) / filename

            # Delete file if it exists
            if file_path.exists():
                file_path.unlink()

                # Also try to delete optimized version
                optimized_path = str(file_path).replace(f".{file_path.suffix}", f"_optimized{file_path.suffix}")
                if Path(optimized_path).exists():
                    Path(optimized_path).unlink()

                return True

            return False

        except Exception as e:
            logger.error(f"Image deletion failed: {str(e)}", exc_info=True)
            return False

    def get_image_urls(self, media_upload) -> Dict[str, Any]:
        """
        Get all image variation URLs with WebP support

        Args:
            media_upload: MediaUpload instance

        Returns:
            Dict with all image URLs (JPEG + WebP variants)
        """
        from .storage_service import storage_service

        workspace_id = str(media_upload.workspace_id)

        urls = {
            'original': storage_service.get_cdn_url(workspace_id, media_upload.file_path)
        }

        # Optimized versions (JPEG + WebP)
        if media_upload.optimized_path:
            urls['optimized'] = storage_service.get_cdn_url(workspace_id, media_upload.optimized_path)

        if media_upload.metadata and 'optimized_webp_path' in media_upload.metadata:
            urls['optimized_webp'] = storage_service.get_cdn_url(
                workspace_id, media_upload.metadata['optimized_webp_path']
            )

        # Thumbnail versions (JPEG + WebP)
        if media_upload.thumbnail_path:
            urls['thumbnail'] = storage_service.get_cdn_url(workspace_id, media_upload.thumbnail_path)

        if media_upload.metadata and 'thumbnail_webp_path' in media_upload.metadata:
            urls['thumbnail_webp'] = storage_service.get_cdn_url(
                workspace_id, media_upload.metadata['thumbnail_webp_path']
            )

        # Tiny thumbnail versions (JPEG + WebP)
        if media_upload.metadata and 'tiny_thumbnail_path' in media_upload.metadata:
            urls['tiny'] = storage_service.get_cdn_url(
                workspace_id, media_upload.metadata['tiny_thumbnail_path']
            )

        if media_upload.metadata and 'tiny_webp_path' in media_upload.metadata:
            urls['tiny_webp'] = storage_service.get_cdn_url(
                workspace_id, media_upload.metadata['tiny_webp_path']
            )

        return urls

    def generate_picture_html(
        self,
        media_upload,
        size: str = 'optimized',
        alt: str = '',
        css_class: str = '',
        loading: str = 'lazy'
    ) -> str:
        """
        Generate HTML <picture> element with automatic WebP fallback

        Industry Standard 2025:
        - WebP first (97% browser support, 25-34% smaller)
        - JPEG fallback for old browsers (<3%)

        Args:
            media_upload: MediaUpload instance
            size: 'optimized', 'thumbnail', or 'tiny'
            alt: Alt text for accessibility
            css_class: CSS class names
            loading: 'lazy' (default) or 'eager' for above-the-fold images

        Returns:
            HTML string with <picture> element

        Example:
            <picture>
              <source srcset="...webp" type="image/webp">
              <img src="...jpg" alt="Product" loading="lazy">
            </picture>
        """
        urls = self.get_image_urls(media_upload)

        # Select URLs based on size
        if size == 'thumbnail':
            webp_url = urls.get('thumbnail_webp')
            jpeg_url = urls.get('thumbnail') or urls['original']
        elif size == 'tiny':
            webp_url = urls.get('tiny_webp')
            jpeg_url = urls.get('tiny') or urls['original']
        else:  # optimized
            webp_url = urls.get('optimized_webp')
            jpeg_url = urls.get('optimized') or urls['original']

        # Generate HTML
        html = '<picture>\n'
        if webp_url:
            html += f'  <source srcset="{webp_url}" type="image/webp">\n'
        html += f'  <img src="{jpeg_url}" alt="{alt}" class="{css_class}" loading="{loading}">\n'
        html += '</picture>'

        return html


# Global instance for easy access
image_upload_service = ImageUploadService()