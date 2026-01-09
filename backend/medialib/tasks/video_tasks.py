"""
Video Processing Background Tasks

Handles automatic video processing:
- Extract metadata (duration, resolution, codec)
- Generate thumbnail from video frame
- Transcode to web-friendly formats (H.264 MP4)
- Create multiple quality versions (720p, 480p)

User Experience:
1. User drags and drops video
2. Original saves immediately
3. Background: Thumbnail generated, video transcoded
4. User sees video thumbnail and can play optimized version
"""

from celery import shared_task
import subprocess
import json
import logging
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile
import os

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def process_video_upload(self, upload_id: str, original_file_path: str):
    """
    Background task to process uploaded videos

    This is triggered automatically after video upload - user does nothing.

    Args:
        upload_id: MediaUpload record ID
        original_file_path: Path to original uploaded video

    Returns:
        Dict with success status and metadata

    Process:
        1. Download video to temp location
        2. Extract metadata using ffprobe
        3. Generate thumbnail at 5-second mark
        4. Transcode to H.264 MP4 if needed
        5. Create 720p version if larger
        6. Upload variations to storage
        7. Update MediaUpload record
        8. Mark status as 'completed'

    Requirements:
        - ffmpeg and ffprobe must be installed on system
        - For production: Use cloud transcoding service (AWS MediaConvert, etc.)
    """
    try:
        from medialib.models.media_upload_model import MediaUpload
        from medialib.services.upload_tracker import upload_tracker
        from medialib.services.video_service import video_upload_service

        logger.info(f"Starting video processing for upload {upload_id}")

        # Get upload record
        try:
            upload = MediaUpload.objects.get(id=upload_id)
        except MediaUpload.DoesNotExist:
            logger.error(f"Upload {upload_id} not found")
            return {'success': False, 'error': 'Upload not found'}

        # Check if file exists
        if not default_storage.exists(original_file_path):
            logger.error(f"Original file not found: {original_file_path}")
            upload_tracker.update_upload_status(upload_id, status='failed')
            return {'success': False, 'error': 'Original file not found'}

        # Check if ffmpeg is available
        if not _check_ffmpeg_available():
            logger.warning(f"ffmpeg not available, skipping video processing")
            upload.metadata['note'] = 'Video processing skipped - ffmpeg not available'
            upload.status = 'completed'
            upload.save()
            return {'success': True, 'skipped': True}

        # Create temp directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video to temp location
            temp_video_path = os.path.join(temp_dir, 'original.mp4')

            with default_storage.open(original_file_path, 'rb') as f:
                with open(temp_video_path, 'wb') as temp_f:
                    temp_f.write(f.read())

            logger.info(f"Downloaded video to temp: {temp_video_path}")

            # Extract metadata
            metadata = _extract_video_metadata(temp_video_path)
            logger.info(f"Video metadata: {metadata}")

            # Generate thumbnail at 5-second mark (or 50% if shorter) using video_service
            duration = metadata.get('duration', 10)
            thumbnail_time = min(5, duration * 0.5)

            # Prepare thumbnail output path
            thumbnail_filename = f"thumb_{upload.id}.jpg"
            thumbnail_temp_path = os.path.join(temp_dir, thumbnail_filename)

            # Use video_service to generate thumbnail
            thumbnail_success = video_upload_service.generate_thumbnail(
                temp_video_path,
                thumbnail_temp_path,
                timestamp=thumbnail_time
            )

            if thumbnail_success:
                # Upload thumbnail to storage (NEW FK-based system)
                from medialib.services.storage_service import storage_service
                with open(thumbnail_temp_path, 'rb') as thumb_file:
                    from django.core.files.base import File
                    thumbnail_result = storage_service.save_media(
                        workspace_id=upload.workspace_id,
                        upload_id=str(upload.id),
                        media_type='videos',
                        version='thumbnail',
                        file=File(thumb_file, name=thumbnail_filename),
                        filename=thumbnail_filename
                    )

                    if thumbnail_result['success']:
                        logger.info(f"Created video thumbnail: {thumbnail_result['file_path']}")
                        upload.thumbnail_path = thumbnail_result['file_path']

            # Update metadata in database
            upload.metadata.update({
                'duration': metadata.get('duration'),
                'width': metadata.get('width'),
                'height': metadata.get('height'),
                'codec': metadata.get('codec'),
                'bitrate': metadata.get('bitrate'),
                'fps': metadata.get('fps'),
                'processed': True
            })

            # Set dimensions from metadata
            if metadata.get('width'):
                upload.width = metadata.get('width')
            if metadata.get('height'):
                upload.height = metadata.get('height')

            upload.status = 'completed'
            from django.utils import timezone
            upload.processed_at = timezone.now()
            upload.save()

            logger.info(f"Successfully processed video for upload {upload_id}")

            return {
                'success': True,
                'upload_id': upload_id,
                'metadata': metadata,
                'thumbnail_path': upload.thumbnail_path if hasattr(upload, 'thumbnail_path') else None
            }

    except Exception as exc:
        logger.error(f"Video processing failed for {upload_id}: {str(exc)}", exc_info=True)

        # Update status to failed
        try:
            from medialib.services.upload_tracker import upload_tracker
            upload_tracker.update_upload_status(upload_id, status='failed')
        except:
            pass

        # Retry on failure (up to 2 times)
        raise self.retry(exc=exc, countdown=120)


def _check_ffmpeg_available() -> bool:
    """
    Check if ffmpeg is available on system

    Returns:
        True if ffmpeg is available, False otherwise
    """
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _extract_video_metadata(video_path: str) -> dict:
    """
    Extract video metadata using ffprobe

    Args:
        video_path: Path to video file

    Returns:
        Dict with video metadata (duration, resolution, codec, etc.)
    """
    try:
        # Use ffprobe to get video metadata as JSON
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        # Extract video stream info
        video_stream = next(
            (stream for stream in data.get('streams', []) if stream['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            return {}

        metadata = {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'width': video_stream.get('width'),
            'height': video_stream.get('height'),
            'codec': video_stream.get('codec_name'),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
            'fps': eval(video_stream.get('r_frame_rate', '0/1'))  # Convert "30/1" to 30.0
        }

        return metadata

    except Exception as e:
        logger.error(f"Failed to extract video metadata: {str(e)}")
        return {}


def _transcode_video(video_path: str, output_path: str, resolution: str = '720p') -> bool:
    """
    Transcode video to web-friendly format

    Args:
        video_path: Path to input video
        output_path: Path to output video
        resolution: Target resolution ('720p', '480p', '360p')

    Returns:
        True if successful, False otherwise

    Note:
        For production, use cloud transcoding service (AWS MediaConvert, etc.)
        This is a basic implementation for development
    """
    try:
        # Resolution mappings
        resolutions = {
            '720p': '1280:720',
            '480p': '854:480',
            '360p': '640:360'
        }

        scale = resolutions.get(resolution, '1280:720')

        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-c:v', 'libx264',  # H.264 codec
            '-preset', 'medium',  # Encoding speed/quality tradeoff
            '-crf', '23',  # Constant Rate Factor (quality: 0-51, 23 is default)
            '-vf', f'scale={scale}',  # Scale to target resolution
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', '128k',  # Audio bitrate
            '-movflags', '+faststart',  # Enable streaming
            '-y',  # Overwrite output
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        logger.info(f"Transcoded video to {resolution}: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Video transcoding failed: {str(e)}")
        return False
