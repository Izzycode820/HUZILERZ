"""
MediaLib GraphQL Types

URL-based GraphQL types for media system (Shopify pattern)
Returns URLs instead of full objects for better performance
"""

import graphene
from graphene_django import DjangoObjectType
from medialib.models.media_upload_model import MediaUpload


class MediaUploadType(DjangoObjectType):
    """
    Media Upload GraphQL Type - URL-focused design

    Returns:
    - Direct URLs (not nested objects)
    - Minimal metadata
    - Optimized for frontend consumption
    """

    # Override to return direct URL strings
    url = graphene.String(description="Primary media URL (CDN)")
    thumbnail_url = graphene.String(description="Thumbnail URL (for images/videos)")
    optimized_url = graphene.String(description="Optimized version URL (for images)")

    class Meta:
        model = MediaUpload
        fields = [
            'id',
            'media_type',
            'original_filename',
            'file_size',
            'mime_type',
            'width',
            'height',
            'status',
            'uploaded_at',
            'metadata',
        ]

    def resolve_url(self, info):
        """Return primary file URL"""
        return self.file_url or ''

    def resolve_thumbnail_url(self, info):
        """Return thumbnail URL"""
        if self.thumbnail_path:
            from medialib.services.storage_service import storage_service
            return storage_service.get_cdn_url(str(self.workspace_id), self.thumbnail_path)
        return None

    def resolve_optimized_url(self, info):
        """Return optimized version URL"""
        if self.optimized_path:
            from medialib.services.storage_service import storage_service
            return storage_service.get_cdn_url(str(self.workspace_id), self.optimized_path)
        return None


class MediaURLType(graphene.ObjectType):
    """
    Simple media URL type for mutations (Shopify pattern)

    Returned by mutations to provide minimal response:
    - id: For future reference
    - url: For immediate display
    """

    id = graphene.ID(required=True, description="Media upload ID")
    url = graphene.String(required=True, description="Primary media URL")
    thumbnail_url = graphene.String(description="Thumbnail URL (if available)")
    media_type = graphene.String(required=True, description="Media type (image, video, 3d_model)")
    status = graphene.String(required=True, description="Processing status (pending, processing, completed, failed)")


class MediaUploadResultType(graphene.ObjectType):
    """
    Result type for upload mutations

    Returns:
    - success: Boolean indicating if upload succeeded
    - error: Error message if failed
    - media: Media object if successful
    """

    success = graphene.Boolean(required=True)
    error = graphene.String()
    media = graphene.Field(MediaURLType)
