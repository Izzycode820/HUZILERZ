"""
Celery tasks for media processing

Provides background task processing for:
- Image variations (optimized, thumbnails)
- Video processing (transcoding, thumbnails)
- 3D model processing (optimization, previews)

Critical for media library performance
"""

from .media_tasks import process_image_variations
from .video_tasks import process_video_upload
from .model_tasks import process_3d_model_upload

__all__ = [
    'process_image_variations',
    'process_video_upload',
    'process_3d_model_upload',
]
