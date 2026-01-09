"""
Unified Media Service

Single interface for handling all media types (images, videos, 3D models)
Orchestrates storage, processing, and tracking

Architecture:
    MediaService (this file)
        ├── StorageService (file storage)
        ├── ImageUploadService (image processing)
        ├── VideoHandler (video processing) [future]
        ├── Model3DHandler (3D model processing) [future]
        └── UploadTracker (tracking and audit)
"""

from typing import Dict, Any, Optional, List, Literal
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
import logging
import hashlib
import requests
from urllib.parse import urlparse
import os

from .storage_service import storage_service, MediaType, VersionType
from .image_service import image_upload_service
from .upload_tracker import upload_tracker
from medialib.models.media_upload_model import MediaUpload

logger = logging.getLogger(__name__)


class MediaService:
    """
    Unified service for all media operations

    Features:
    - Automatic media type detection
    - Unified upload interface for all media types
    - Processing pipeline (validation -> storage -> optimization -> tracking)
    - User attribution and audit trail
    - Support for images, videos, and 3D models

    Usage (NEW FK-based pattern - Shopify style):
        media_service = MediaService()

        # 1. Upload media (entity-agnostic)
        result = media_service.upload_media(
            file=uploaded_file,
            workspace_id="abc123",
            user_id="user_001"
        )

        # 2. Attach to entity via FK
        product.featured_media_id = result['upload_id']
        product.save()
    """

    # Supported file extensions by media type
    MEDIA_TYPE_EXTENSIONS = {
        'images': ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'],
        'videos': ['mp4', 'webm', 'mov', 'avi', 'mkv'],
        '3d_models': ['glb', 'gltf', 'obj', 'fbx', 'usdz'],
        'documents': ['pdf', 'doc', 'docx']
    }

    # MIME type mappings
    MIME_TYPES = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'gif': 'image/gif',
        'svg': 'image/svg+xml',
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'mkv': 'video/x-matroska',
        'glb': 'model/gltf-binary',
        'gltf': 'model/gltf+json',
        'obj': 'model/obj',
        'fbx': 'application/octet-stream',
        'usdz': 'model/vnd.usdz+zip',
        'pdf': 'application/pdf',
    }

    def __init__(self):
        self.storage = storage_service
        self.image_service = image_upload_service
        self.tracker = upload_tracker

        # Lazy import to avoid circular dependencies
        from .video_service import video_upload_service
        from .model_service import model_3d_upload_service
        self.video_service = video_upload_service
        self.model_service = model_3d_upload_service

    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content for deduplication"""
        return hashlib.sha256(file_content).hexdigest()

    def find_duplicate_file(self, workspace_id: str, file_hash: str) -> Optional[MediaUpload]:
        """
        Check if file with same hash already exists in workspace (for deduplication)

        In FK-based system, we return any completed, non-deleted upload with same hash.
        The same media can be reused by multiple entities via featured_media_id.

        Returns None if:
        - No duplicate found
        - Duplicate exists but is soft-deleted
        - Duplicate exists but not completed
        """
        try:
            # Find any completed upload with same hash that is not soft-deleted
            return MediaUpload.objects.filter(
                workspace_id=workspace_id,
                file_hash=file_hash,
                status='completed',
                deleted_at__isnull=True
            ).first()

        except Exception as e:
            logger.warning(f"Duplicate check failed: {str(e)}")
            return None

    def detect_media_type(self, filename: str) -> Optional[MediaType]:
        """
        Detect media type from filename extension

        Args:
            filename: Original filename

        Returns:
            Media type or None if unsupported
        """
        extension = filename.split('.')[-1].lower()

        for media_type, extensions in self.MEDIA_TYPE_EXTENSIONS.items():
            if extension in extensions:
                return media_type

        return None

    def get_mime_type(self, filename: str) -> str:
        """
        Get MIME type from filename

        Args:
            filename: Original filename

        Returns:
            MIME type string
        """
        extension = filename.split('.')[-1].lower()
        return self.MIME_TYPES.get(extension, 'application/octet-stream')

    def upload_media(
        self,
        file: UploadedFile,
        workspace_id: str,
        user_id: str,
        process_variations: bool = True
    ) -> Dict[str, Any]:
        """
        Upload media file with automatic type detection and processing (entity-agnostic)

        Args:
            file: Uploaded file
            workspace_id: Workspace ID
            user_id: User who uploaded
            process_variations: Whether to create optimized/thumbnail versions

        Returns:
            Dict with upload result including upload_id for FK attachment

        NEW Flow:
            1. Upload media -> Returns upload_id
            2. Attach to entity -> entity.featured_media_id = upload_id

        Example:
            result = media_service.upload_media(file, workspace_id, user_id)
            product.featured_media_id = result['upload_id']

        Raises:
            ValidationError: If file validation fails
        """
        try:
            # Check storage limit before upload
            from django.contrib.auth import get_user_model
            from subscription.services.gating import check_storage_limit
            
            User = get_user_model()
            try:
                user = User.objects.select_related('hosting_environment').get(id=user_id)
                file_size_bytes = file.size
                
                allowed, error_msg, usage_info = check_storage_limit(user, file_size_bytes)
                if not allowed:
                    return {
                        'success': False,
                        'error': error_msg,
                        'storage_info': usage_info
                    }
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found for storage check")
                # Continue without storage check if user not found (edge case)
                user = None

            # Detect media type
            media_type = self.detect_media_type(file.name)
            if not media_type:
                raise ValidationError(f"Unsupported file type: {file.name}")

            # Get MIME type
            mime_type = self.get_mime_type(file.name)

            # Route to appropriate handler based on media type
            if media_type == 'images':
                result = self._handle_image_upload(
                    file, workspace_id, user_id, process_variations
                )
            elif media_type == 'videos':
                result = self._handle_video_upload(
                    file, workspace_id, user_id
                )
            elif media_type == '3d_models':
                result = self._handle_3d_model_upload(
                    file, workspace_id, user_id
                )
            else:
                result = self._handle_generic_upload(
                    file, workspace_id, user_id, media_type, mime_type
                )

            # Update storage usage after successful upload
            if result.get('success') and user and hasattr(user, 'hosting_environment'):
                try:
                    file_size_gb = file.size / (1024 ** 3)
                    user.hosting_environment.increment_storage_usage(file_size_gb)
                    logger.info(f"Storage usage incremented by {file_size_gb:.6f}GB for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to update storage usage: {e}")
                    # Don't fail the upload if storage tracking fails

            return result

        except Exception as e:
            logger.error(f"Media upload failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"Media upload failed: {str(e)}"
            }

    def upload_media_from_url(
        self,
        url: str,
        workspace_id: str,
        user_id: str,
        process_variations: bool = True,
        timeout: int = 30,
        max_file_size: int = 100 * 1024 * 1024  # 100MB default
    ) -> Dict[str, Any]:
        """
        Upload media from external URL (images, videos, 3D models) - entity-agnostic

        Args:
            url: External URL to download media from
            workspace_id: Workspace ID
            user_id: User who initiated the upload
            process_variations: Whether to create optimized/thumbnail versions
            timeout: Request timeout in seconds
            max_file_size: Maximum file size in bytes

        Returns:
            Dict with upload result including upload_id for FK attachment

        Raises:
            ValidationError: If URL is invalid or download fails
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValidationError("Invalid URL format")

            if parsed_url.scheme not in ['http', 'https']:
                raise ValidationError("Only HTTP and HTTPS URLs are supported")

            logger.info(f"Downloading media from URL: {url}")

            # Download file with streaming to handle large files
            response = requests.get(
                url,
                stream=True,
                timeout=timeout,
                headers={'User-Agent': 'MediaLib/1.0'}
            )
            response.raise_for_status()

            # Check file size from headers
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_file_size:
                raise ValidationError(f"File too large: {int(content_length)} bytes (max: {max_file_size})")

            # Get filename from URL or Content-Disposition header
            filename = None
            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                # Try to extract filename from Content-Disposition
                import re
                filename_match = re.findall('filename="?([^"]+)"?', content_disposition)
                if filename_match:
                    filename = filename_match[0]

            if not filename:
                # Extract from URL path
                filename = os.path.basename(parsed_url.path)

            if not filename or '.' not in filename:
                # Try to get from content-type
                content_type = response.headers.get('content-type', '')
                extension = self._get_extension_from_mime(content_type)
                if not extension:
                    raise ValidationError("Cannot determine file type from URL")
                filename = f"download.{extension}"

            # Download content with size limit
            content = b''
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > max_file_size:
                        raise ValidationError(f"File too large: exceeds {max_file_size} bytes")
                    content += chunk

            logger.info(f"Downloaded {downloaded_size} bytes from {url}")

            # Create Django file object from downloaded content
            file = ContentFile(content, name=filename)

            # Use existing upload_media method to process the downloaded file
            return self.upload_media(
                file=file,
                workspace_id=workspace_id,
                user_id=user_id,
                process_variations=process_variations
            )

        except requests.RequestException as e:
            logger.error(f"Failed to download from URL {url}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to download from URL: {str(e)}"
            }
        except ValidationError as e:
            logger.error(f"URL upload validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"URL upload failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"URL upload failed: {str(e)}"
            }

    def _get_extension_from_mime(self, mime_type: str) -> Optional[str]:
        """
        Get file extension from MIME type

        Args:
            mime_type: MIME type string

        Returns:
            File extension or None
        """
        mime_to_ext = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
            'image/gif': 'gif',
            'image/svg+xml': 'svg',
            'video/mp4': 'mp4',
            'video/webm': 'webm',
            'video/quicktime': 'mov',
            'model/gltf-binary': 'glb',
            'model/gltf+json': 'gltf',
        }
        return mime_to_ext.get(mime_type.split(';')[0].strip().lower())

    def _handle_image_upload(
        self,
        file: UploadedFile,
        workspace_id: str,
        user_id: str,
        process_variations: bool
    ) -> Dict[str, Any]:
        """Handle image uploads with validation and optimization (entity-agnostic)"""
        try:
            # Validate image using ImageUploadService
            validation_result = self.image_service.validate_image(file)

            if not validation_result['valid']:
                raise ValidationError("Image validation failed")

            # Reset file pointer after validation
            file.seek(0)

            # Calculate file hash for deduplication
            file_content = file.read()
            file_hash = self.calculate_file_hash(file_content)
            file.seek(0)  # Reset after reading for hash

            # Check for duplicate file in workspace
            duplicate = self.find_duplicate_file(workspace_id, file_hash)
            if duplicate:
                logger.info(f"Duplicate file detected: {file_hash}, reusing existing upload")
                return {
                    'success': True,
                    'message': 'File already exists, reused existing upload',
                    'upload_id': str(duplicate.id),
                    'file_url': duplicate.file_url,
                    'deduplicated': True
                }

            # NEW FLOW: Create MediaUpload record FIRST to get upload_id
            upload_record = self.tracker.track_upload(
                workspace_id=workspace_id,
                user_id=user_id,
                media_type='image',
                original_filename=file.name,
                file_size=file.size,
                mime_type=self.get_mime_type(file.name),
                file_hash=file_hash,
                width=validation_result.get('width'),
                height=validation_result.get('height'),
                metadata={
                    'format': validation_result.get('format')
                },
                status='pending'  # Will update after file save
            )

            upload_id = str(upload_record.id)

            # Save original image using upload_id
            original_result = self.storage.save_media(
                workspace_id=workspace_id,
                upload_id=upload_id,
                media_type='images',
                version='original',
                file=file,
                filename=file.name
            )

            if not original_result['success']:
                # Cleanup: Delete upload record if file save fails
                upload_record.delete()
                raise ValidationError(original_result.get('error', 'Storage failed'))

            # Update MediaUpload with file paths using tracker
            upload_record = self.tracker.update_file_paths(
                upload_id=upload_id,
                file_path=original_result['file_path'],
                file_url=original_result['file_url']
            )

            # Update metadata
            upload_record.metadata['storage_backend'] = original_result.get('storage_backend')
            upload_record.save(update_fields=['metadata'])

            result = {
                'success': True,
                'upload_id': upload_id,
                'media_type': 'image',
                'original': {
                    'file_path': original_result['file_path'],
                    'file_url': original_result['file_url'],
                    'width': validation_result['width'],
                    'height': validation_result['height'],
                },
                'file_size': file.size,
                'uploaded_by': user_id
            }

            # Process optimized and thumbnail versions asynchronously
            if process_variations:
                from medialib.tasks.media_tasks import process_image_variations

                # Queue background task for image variations
                process_image_variations.delay(
                    upload_id,
                    original_result['file_path']
                )

                logger.info(f"Image variations processing queued for {upload_id}")

                # Mark as processing (will be updated to completed by background task)
                self.tracker.update_upload_status(
                    upload_id=upload_id,
                    status='processing'
                )
            else:
                # No variations requested, mark as completed immediately
                self.tracker.update_upload_status(
                    upload_id=upload_id,
                    status='completed'
                )

            return result

        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}", exc_info=True)
            raise

    def _handle_video_upload(
        self,
        file: UploadedFile,
        workspace_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle video uploads with automatic background processing (entity-agnostic)

        Processing (automatic in background):
        - Extract metadata (duration, resolution, codec)
        - Generate thumbnail from video frame
        - Transcode to web-friendly formats if needed
        """
        logger.info(f"Video upload: {file.name}")

        # Validate video using VideoUploadService
        validation_result = self.video_service.validate_video(file)

        if not validation_result['valid']:
            raise ValidationError(f"Video validation failed: {validation_result.get('error', 'Unknown error')}")

        # Reset file pointer after validation
        file.seek(0)

        # NEW FLOW: Create MediaUpload record FIRST to get upload_id
        upload_record = self.tracker.track_upload(
            workspace_id=workspace_id,
            user_id=user_id,
            media_type='video',
            original_filename=file.name,
            file_size=file.size,
            mime_type=self.get_mime_type(file.name),
            width=validation_result.get('width'),
            height=validation_result.get('height'),
            metadata={
                'duration': validation_result.get('duration'),
                'codec': validation_result.get('codec'),
                'bitrate': validation_result.get('bitrate'),
                'fps': validation_result.get('fps'),
                'format': validation_result.get('format')
            },
            status='pending'
        )

        upload_id = str(upload_record.id)

        # Save original video file using upload_id
        result = self.storage.save_media(
            workspace_id=workspace_id,
            upload_id=upload_id,
            media_type='videos',
            version='original',
            file=file,
            filename=file.name
        )

        if not result['success']:
            # Cleanup: Delete upload record if file save fails
            upload_record.delete()
            raise ValidationError(result.get('error', 'Storage failed'))

        # Update MediaUpload with file paths using tracker
        upload_record = self.tracker.update_file_paths(
            upload_id=upload_id,
            file_path=result['file_path'],
            file_url=result['file_url']
        )

        # Update metadata
        upload_record.metadata['storage_backend'] = result.get('storage_backend')
        upload_record.save(update_fields=['metadata'])

        # Queue background video processing task
        from medialib.tasks.video_tasks import process_video_upload

        process_video_upload.delay(
            upload_id,
            result['file_path']
        )

        logger.info(f"Video processing queued for {upload_id}")

        # Mark as processing (will be updated by background task)
        self.tracker.update_upload_status(
            upload_id=upload_id,
            status='processing'
        )

        return {
            'success': True,
            'upload_id': upload_id,
            'media_type': 'video',
            'file_url': result['file_url'],
            'file_size': file.size,
            'status': 'processing'
        }

    def _handle_3d_model_upload(
        self,
        file: UploadedFile,
        workspace_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle 3D model uploads with automatic background processing (entity-agnostic)

        Processing (automatic in background):
        - Validate model format and integrity
        - Extract metadata (vertices, faces, materials)
        - Generate preview renders from multiple angles
        - Optimize model for web viewing
        - Convert to glTF format if needed
        """
        logger.info(f"3D model upload: {file.name}")

        # Validate 3D model using Model3DUploadService
        validation_result = self.model_service.validate_model(file)

        if not validation_result['valid']:
            raise ValidationError(f"3D model validation failed: {validation_result.get('error', 'Unknown error')}")

        # Reset file pointer after validation
        file.seek(0)

        # NEW FLOW: Create MediaUpload record FIRST to get upload_id
        upload_record = self.tracker.track_upload(
            workspace_id=workspace_id,
            user_id=user_id,
            media_type='3d_model',
            original_filename=file.name,
            file_size=file.size,
            mime_type=self.get_mime_type(file.name),
            metadata={
                'format': validation_result.get('format'),
                'file_type': validation_result.get('file_type'),
                'vertices': validation_result.get('vertices'),
                'faces': validation_result.get('faces'),
                'materials': validation_result.get('materials'),
                'textures': validation_result.get('textures'),
                'geometries': validation_result.get('geometries'),
                'is_watertight': validation_result.get('is_watertight'),
                'bounds': validation_result.get('bounds'),
                'gltf_version': validation_result.get('gltf_version'),
                'complexity': self.model_service.estimate_complexity(validation_result)
            },
            status='pending'
        )

        upload_id = str(upload_record.id)

        # Save original model file using upload_id
        result = self.storage.save_media(
            workspace_id=workspace_id,
            upload_id=upload_id,
            media_type='3d_models',
            version='original',
            file=file,
            filename=file.name
        )

        if not result['success']:
            # Cleanup: Delete upload record if file save fails
            upload_record.delete()
            raise ValidationError(result.get('error', 'Storage failed'))

        # Update MediaUpload with file paths using tracker
        upload_record = self.tracker.update_file_paths(
            upload_id=upload_id,
            file_path=result['file_path'],
            file_url=result['file_url']
        )

        # Update metadata
        upload_record.metadata['storage_backend'] = result.get('storage_backend')
        upload_record.save(update_fields=['metadata'])

        # Queue background 3D model processing task
        from medialib.tasks.model_tasks import process_3d_model_upload

        process_3d_model_upload.delay(
            upload_id,
            result['file_path']
        )

        logger.info(f"3D model processing queued for {upload_id}")

        # Mark as processing (will be updated by background task)
        self.tracker.update_upload_status(
            upload_id=upload_id,
            status='processing'
        )

        return {
            'success': True,
            'upload_id': str(upload_record.id),
            'media_type': '3d_model',
            'file_url': result['file_url'],
            'file_size': file.size,
            'status': 'processing'
        }

    def _handle_generic_upload(
        self,
        file: UploadedFile,
        workspace_id: str,
        user_id: str,
        media_type: MediaType,
        mime_type: str
    ) -> Dict[str, Any]:
        """Handle generic file uploads (documents, etc.) - entity-agnostic"""
        # NEW FLOW: Create MediaUpload record FIRST to get upload_id
        upload_record = self.tracker.track_upload(
            workspace_id=workspace_id,
            user_id=user_id,
            media_type=media_type,
            original_filename=file.name,
            file_size=file.size,
            mime_type=mime_type,
            status='pending'
        )

        upload_id = str(upload_record.id)

        # Save file using upload_id
        result = self.storage.save_media(
            workspace_id=workspace_id,
            upload_id=upload_id,
            media_type=media_type,
            version='original',
            file=file,
            filename=file.name
        )

        if not result['success']:
            # Cleanup: Delete upload record if file save fails
            upload_record.delete()
            raise ValidationError(result.get('error', 'Storage failed'))

        # Update MediaUpload with file paths
        upload_record.file_path = result['file_path']
        upload_record.file_url = result['file_url']
        upload_record.save(update_fields=['file_path', 'file_url'])

        # Mark as completed
        self.tracker.update_upload_status(
            upload_id=upload_id,
            status='completed'
        )

        return {
            'success': True,
            'upload_id': upload_id,
            'media_type': media_type,
            'file_url': result['file_url'],
            'file_size': file.size
        }


# Global instance for easy access
media_service = MediaService()
