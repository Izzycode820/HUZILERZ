"""
Video Upload and Processing Service

Handles video file validation, metadata extraction, and processing orchestration.

Features:
- File format validation
- File size and duration limits
- Metadata extraction (resolution, duration, codec)
- Background processing coordination
"""

from typing import Dict, Any, Optional
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
import logging
import subprocess
import json
import os

logger = logging.getLogger(__name__)


class VideoUploadService:
    """
    Service for video file uploads with validation and metadata extraction

    Features:
    - Format validation (MP4, WebM, MOV, AVI, MKV)
    - File size limits
    - Duration validation
    - Resolution detection
    - Codec information extraction
    """

    # Supported video formats
    SUPPORTED_FORMATS = ['mp4', 'webm', 'mov', 'avi', 'mkv']

    # File size limits (bytes)
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    MIN_FILE_SIZE = 1024  # 1KB

    # Duration limits (seconds)
    MAX_DURATION = 3600  # 1 hour
    MIN_DURATION = 0.1  # 0.1 seconds

    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg_availability()

    def _check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available on the system"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("FFmpeg not available - video metadata extraction will be limited")
            return False

    def validate_video(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate video file and extract metadata

        Args:
            file: Uploaded video file

        Returns:
            Dict with validation result and metadata:
            {
                'valid': bool,
                'error': str (if invalid),
                'duration': float (seconds),
                'width': int,
                'height': int,
                'codec': str,
                'format': str,
                'bitrate': int,
                'fps': float
            }

        Raises:
            ValidationError: If file validation fails
        """
        try:
            # Check file extension
            if not file.name:
                raise ValidationError("Filename is required")

            extension = file.name.split('.')[-1].lower()
            if extension not in self.SUPPORTED_FORMATS:
                return {
                    'valid': False,
                    'error': f"Unsupported video format: {extension}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                }

            # Check file size
            if file.size > self.MAX_FILE_SIZE:
                return {
                    'valid': False,
                    'error': f"File too large: {file.size} bytes (max: {self.MAX_FILE_SIZE})"
                }

            if file.size < self.MIN_FILE_SIZE:
                return {
                    'valid': False,
                    'error': f"File too small: {file.size} bytes (min: {self.MIN_FILE_SIZE})"
                }

            # Extract metadata using FFmpeg if available
            metadata = {}
            if self.ffmpeg_available:
                metadata = self._extract_video_metadata(file)

                # Validate duration
                duration = metadata.get('duration', 0)
                if duration > self.MAX_DURATION:
                    return {
                        'valid': False,
                        'error': f"Video too long: {duration}s (max: {self.MAX_DURATION}s)"
                    }

                if duration < self.MIN_DURATION and duration > 0:
                    return {
                        'valid': False,
                        'error': f"Video too short: {duration}s (min: {self.MIN_DURATION}s)"
                    }

            return {
                'valid': True,
                'format': extension,
                **metadata
            }

        except Exception as e:
            logger.error(f"Video validation failed: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': f"Validation failed: {str(e)}"
            }

    def _extract_video_metadata(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Extract video metadata using FFprobe

        Args:
            file: Video file

        Returns:
            Dict with video metadata
        """
        try:
            # Save temp file for FFprobe
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file.name.split(".")[-1]}') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Reset file pointer for later use
            file.seek(0)

            try:
                # Run FFprobe to get video info
                result = subprocess.run(
                    [
                        'ffprobe',
                        '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format',
                        '-show_streams',
                        temp_path
                    ],
                    capture_output=True,
                    timeout=30,
                    text=True
                )

                if result.returncode != 0:
                    logger.warning(f"FFprobe failed: {result.stderr}")
                    return {}

                data = json.loads(result.stdout)

                # Extract video stream info
                video_stream = next(
                    (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                    None
                )

                if not video_stream:
                    return {}

                # Extract format info
                format_info = data.get('format', {})

                metadata = {
                    'duration': float(format_info.get('duration', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'fps': self._extract_fps(video_stream)
                }

                return metadata

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}", exc_info=True)
            return {}

    def _extract_fps(self, video_stream: Dict) -> float:
        """Extract FPS from video stream info"""
        try:
            # Try r_frame_rate first (more accurate)
            r_frame_rate = video_stream.get('r_frame_rate', '0/1')
            if '/' in r_frame_rate:
                num, den = r_frame_rate.split('/')
                if int(den) > 0:
                    return float(num) / float(den)

            # Fallback to avg_frame_rate
            avg_frame_rate = video_stream.get('avg_frame_rate', '0/1')
            if '/' in avg_frame_rate:
                num, den = avg_frame_rate.split('/')
                if int(den) > 0:
                    return float(num) / float(den)

            return 0.0
        except Exception:
            return 0.0

    def generate_thumbnail(self, video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
        """
        Generate thumbnail from video frame

        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail
            timestamp: Timestamp in seconds to extract frame from

        Returns:
            True if successful, False otherwise
        """
        if not self.ffmpeg_available:
            logger.warning("FFmpeg not available - cannot generate thumbnail")
            return False

        try:
            result = subprocess.run(
                [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(timestamp),
                    '-vframes', '1',
                    '-vf', 'scale=640:-1',  # Scale to 640px width, maintain aspect ratio
                    '-y',  # Overwrite output file
                    output_path
                ],
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Thumbnail generation failed: {result.stderr.decode()}")
                return False

            return True

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {str(e)}", exc_info=True)
            return False


# Global instance
video_upload_service = VideoUploadService()
