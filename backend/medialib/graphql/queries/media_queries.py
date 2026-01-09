"""
Media Queries for GraphQL API

Provides queries for media library features (recent uploads, media picker)
"""

import graphene
from medialib.graphql.types.media_types import MediaUploadType
from medialib.services.upload_tracker import upload_tracker


class MediaQueries(graphene.ObjectType):
    """
    Media-related queries for Shopify-style media picker
    """

    recent_media = graphene.List(
        MediaUploadType,
        limit=graphene.Int(default_value=50),
        media_type=graphene.String(description="Filter by media type: image, video, 3d_model"),
        search=graphene.String(description="Search by filename"),
        sort_by=graphene.String(description="Sort by: date, name, size (default: date)"),
        sort_order=graphene.String(description="Sort order: asc, desc (default: desc)"),
        description="Get recent media uploads for current workspace (for media picker)"
    )

    def resolve_recent_media(
        self,
        info,
        limit=50,
        media_type=None,
        search=None,
        sort_by="date",
        sort_order="desc"
    ):
        """
        Get recent media uploads for the workspace with search and filters

        Args:
            limit: Maximum number of uploads to return (default 50)
            media_type: Optional filter by media type
            search: Search by filename
            sort_by: Sort by field (date, name, size)
            sort_order: Sort order (asc, desc)

        Returns:
            List of MediaUpload objects
        """
        workspace = info.context.workspace
        user = info.context.user

        # Get recent uploads for this user in this workspace
        recent_uploads = upload_tracker.get_user_uploads(
            workspace_id=str(workspace.id),
            user_id=str(user.id),
            limit=limit,
            media_type=media_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return recent_uploads
