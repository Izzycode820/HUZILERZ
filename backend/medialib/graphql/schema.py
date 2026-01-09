"""
MediaLib GraphQL Schema

Exports queries and mutations for media management
Can be imported by any app that needs media functionality
"""

import graphene
from .queries.media_queries import MediaQueries
from .mutations.media_mutations import MediaMutations


class Query(MediaQueries, graphene.ObjectType):
    """
    MediaLib Query

    Provides media library queries:
    - recent_media: Get recent uploads for media picker
    """
    pass


class Mutation(MediaMutations, graphene.ObjectType):
    """
    MediaLib Mutation

    Provides media upload/management mutations:
    - upload_media: Upload file (auto-detects image/video/3D model)
    - upload_media_from_url: Import from external URL
    - delete_media: Delete media by ID
    - reuse_media: Attach existing media to new entity
    """
    pass


# Standalone schema (if needed for separate endpoint)
schema = graphene.Schema(query=Query, mutation=Mutation)
