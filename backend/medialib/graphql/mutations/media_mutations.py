"""
Media Upload Mutations

Handles direct media uploads (pre-upload before entity creation)
Shopify-style: Upload first, attach to entity later
"""

import graphene
from graphene_file_upload.scalars import Upload
from medialib.services.media_service import media_service
from medialib.graphql.types.media_types import MediaUploadType, MediaURLType, MediaUploadResultType
import logging

logger = logging.getLogger(__name__)


class UploadMedia(graphene.Mutation):
    """
    Upload media file with automatic processing (NEW FK-based system)

    Flow:
    1. Upload media → Get upload_id
    2. Attach to entity → entity.featured_media_id = upload_id

    Process:
    1. User selects file in UI
    2. Immediately upload to backend (entity-agnostic)
    3. Return upload_id and preview URL
    4. User can attach to product/category later via FK

    Benefits:
    - Images persist even if user cancels entity creation
    - Immediately available in "Recent uploads"
    - Real upload progress feedback
    - Can reuse across multiple entities (just set FK)
    """

    class Arguments:
        file = Upload(required=True, description="File to upload (image, video, 3D model)")
        process_variations = graphene.Boolean(
            default_value=True,
            description="Generate optimized/thumbnail versions"
        )

    success = graphene.Boolean()
    upload = graphene.Field(MediaUploadType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, file, process_variations=True):
        workspace = info.context.workspace
        user = info.context.user

        try:
            # NEW: Entity-agnostic upload
            result = media_service.upload_media(
                file=file,
                workspace_id=str(workspace.id),
                user_id=str(user.id),
                process_variations=process_variations
            )

            if not result['success']:
                return UploadMedia(
                    success=False,
                    error=result.get('error', 'Upload failed')
                )

            # Get the upload record
            from medialib.models.media_upload_model import MediaUpload
            upload_record = MediaUpload.objects.get(id=result['upload_id'])

            return UploadMedia(
                success=True,
                upload=upload_record,
                message=f"File uploaded successfully - attach to entity via featured_media_id"
            )

        except Exception as e:
            logger.error(f"Media upload mutation failed: {str(e)}", exc_info=True)
            return UploadMedia(
                success=False,
                error=f"Upload failed: {str(e)}"
            )


class UploadMediaFromUrl(graphene.Mutation):
    """
    Upload media from URL (download and store)

    Process:
    1. Download file from URL
    2. Validate and process
    3. Store in MediaUpload table
    """

    class Arguments:
        url = graphene.String(required=True, description="URL of the media file")
        filename = graphene.String(description="Optional filename override")

    success = graphene.Boolean()
    upload = graphene.Field(MediaUploadType)
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, url, filename=None):
        workspace = info.context.workspace
        user = info.context.user

        try:
            import requests
            from django.core.files.uploadedfile import SimpleUploadedFile
            from urllib.parse import urlparse
            import os

            # Download file from URL
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Determine filename
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or 'downloaded_file'

            # Get content type
            content_type = response.headers.get('content-type', 'application/octet-stream')

            # Create Django UploadedFile
            file_content = response.content
            uploaded_file = SimpleUploadedFile(
                name=filename,
                content=file_content,
                content_type=content_type
            )

            # Upload using media service (entity-agnostic)
            result = media_service.upload_media(
                file=uploaded_file,
                workspace_id=str(workspace.id),
                user_id=str(user.id),
                process_variations=True
            )

            if not result['success']:
                return UploadMediaFromUrl(
                    success=False,
                    error=result.get('error', 'Upload failed')
                )

            # Get the upload record
            from medialib.models.media_upload_model import MediaUpload
            upload_record = MediaUpload.objects.get(id=result['upload_id'])

            return UploadMediaFromUrl(
                success=True,
                upload=upload_record,
                message=f"File downloaded and uploaded successfully"
            )

        except requests.RequestException as e:
            logger.error(f"Failed to download from URL: {str(e)}")
            return UploadMediaFromUrl(
                success=False,
                error=f"Failed to download file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"URL upload mutation failed: {str(e)}", exc_info=True)
            return UploadMediaFromUrl(
                success=False,
                error=f"Upload failed: {str(e)}"
            )


class DeleteMedia(graphene.Mutation):
    """
    Delete media upload (soft delete)

    User can manually manage their storage
    """

    class Arguments:
        upload_id = graphene.String(required=True, description="Upload ID to delete")

    success = graphene.Boolean()
    message = graphene.String()
    error = graphene.String()

    @staticmethod
    def mutate(root, info, upload_id):
        workspace = info.context.workspace
        user = info.context.user

        try:
            from medialib.models.media_upload_model import MediaUpload

            # Get upload (workspace-scoped for security)
            upload = MediaUpload.objects.get(
                id=upload_id,
                workspace_id=str(workspace.id),
                deleted_at__isnull=True
            )

            # Hard delete - signal will clean up physical files
            # Shopify-style: immediate removal, signal handles file cleanup
            upload.delete()

            logger.info(f"Media hard deleted: {upload_id} by user {user.id}")

            return DeleteMedia(
                success=True,
                message="Media deleted successfully"
            )

        except MediaUpload.DoesNotExist:
            return DeleteMedia(
                success=False,
                error="Media not found or access denied"
            )
        except Exception as e:
            logger.error(f"Media deletion failed: {str(e)}", exc_info=True)
            return DeleteMedia(
                success=False,
                error=f"Deletion failed: {str(e)}"
            )


class MediaMutations(graphene.ObjectType):
    """
    Media-related mutations for Files and Media feature
    """
    upload_media = UploadMedia.Field()
    upload_media_from_url = UploadMediaFromUrl.Field()
    delete_media = DeleteMedia.Field()
