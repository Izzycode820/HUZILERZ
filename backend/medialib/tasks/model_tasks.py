"""
3D Model Processing Background Tasks

Handles automatic 3D model processing:
- Validate model format and integrity
- Generate preview renders (multiple angles)
- Optimize for web viewing (reduce polygons, compress textures)
- Convert to web-friendly glTF format

User Experience:
1. User drags and drops 3D model
2. Original saves immediately
3. Background: Preview images generated, model optimized
4. User sees preview thumbnails and can view 3D model
"""

from celery import shared_task
import logging
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile
import os
import json

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def process_3d_model_upload(self, upload_id: str, original_file_path: str):
    """
    Background task to process uploaded 3D models

    This is triggered automatically after model upload - user does nothing.

    Args:
        upload_id: MediaUpload record ID
        original_file_path: Path to original uploaded 3D model

    Returns:
        Dict with success status and metadata

    Process:
        1. Download model to temp location
        2. Validate model format and integrity
        3. Extract metadata (vertices, faces, materials)
        4. Generate preview renders (front, side, top views)
        5. Optimize model for web (if needed)
        6. Convert to glTF if not already
        7. Upload variations to storage
        8. Update MediaUpload record
        9. Mark status as 'completed'

    Requirements:
        - For production: Use 3D processing libraries (trimesh, pygltflib)
        - Or: Use cloud 3D processing service
        - Or: Use Blender CLI for advanced processing

    Current Implementation:
        - Basic validation and metadata extraction
        - Preview generation placeholder (requires 3D rendering library)
        - Ready for integration with 3D processing libraries
    """
    try:
        from medialib.models.media_upload_model import MediaUpload
        from medialib.services.upload_tracker import upload_tracker
        from medialib.services.model_service import model_3d_upload_service

        logger.info(f"Starting 3D model processing for upload {upload_id}")

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

        # Get file extension to determine format
        file_extension = original_file_path.split('.')[-1].lower()

        # Initialize metadata
        metadata = {
            'format': file_extension,
            'processed': False,
            'note': '3D model uploaded successfully'
        }

        # Use model_service for validation and metadata extraction
        logger.info("Processing 3D model with model_service")

        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download model to temp location
            temp_model_path = os.path.join(temp_dir, f'model.{file_extension}')

            with default_storage.open(original_file_path, 'rb') as f:
                with open(temp_model_path, 'wb') as temp_f:
                    temp_f.write(f.read())

            # Use model_service to extract metadata
            from django.core.files import File
            with open(temp_model_path, 'rb') as model_file:
                django_file = File(model_file, name=f'model.{file_extension}')
                validation_result = model_3d_upload_service.validate_model(django_file)

                if validation_result.get('valid'):
                    # Extract metadata from validation result
                    model_metadata = {
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
                        'complexity': model_3d_upload_service.estimate_complexity(validation_result),
                        'processed': True
                    }
                    metadata.update(model_metadata)
                    logger.info(f"Extracted 3D model metadata: {model_metadata}")

                    # Set dimensions if available
                    if validation_result.get('bounds'):
                        bounds = validation_result.get('bounds')
                        # Calculate bounding box dimensions
                        if bounds and len(bounds) == 2:
                            width = abs(bounds[1][0] - bounds[0][0])
                            height = abs(bounds[1][1] - bounds[0][1])
                            upload.metadata['dimensions'] = {
                                'width': width,
                                'height': height,
                                'depth': abs(bounds[1][2] - bounds[0][2])
                            }

                    # Generate preview images (placeholder - requires 3D rendering)
                    # For now, we can use the old function if available
                    preview_paths = _generate_3d_previews(
                        temp_model_path, upload, original_file_path
                    )

                    if preview_paths:
                        logger.info(f"Created {len(preview_paths)} preview images")
                        metadata['preview_images'] = preview_paths
                else:
                    logger.warning(f"3D model validation failed: {validation_result.get('error')}")
                    metadata['note'] = f"Validation issue: {validation_result.get('error', 'Unknown error')}"

        # Update metadata in database
        upload.metadata.update(metadata)
        upload.status = 'completed'

        from django.utils import timezone
        upload.processed_at = timezone.now()
        upload.save()

        logger.info(f"Successfully processed 3D model for upload {upload_id}")

        return {
            'success': True,
            'upload_id': upload_id,
            'metadata': metadata
        }

    except Exception as exc:
        logger.error(f"3D model processing failed for {upload_id}: {str(exc)}", exc_info=True)

        # Update status to failed
        try:
            from medialib.services.upload_tracker import upload_tracker
            upload_tracker.update_upload_status(upload_id, status='failed')
        except:
            pass

        # Retry on failure (up to 2 times)
        raise self.retry(exc=exc, countdown=120)


def _check_trimesh_available() -> bool:
    """
    Check if trimesh library is available

    Returns:
        True if trimesh is available, False otherwise

    Note:
        Install with: pip install trimesh[easy]
    """
    try:
        import trimesh
        return True
    except ImportError:
        return False


def _extract_3d_metadata(model_path: str) -> dict:
    """
    Extract 3D model metadata using trimesh

    Args:
        model_path: Path to 3D model file

    Returns:
        Dict with model metadata (vertices, faces, materials, bounds, etc.)
    """
    try:
        import trimesh

        # Load model
        mesh = trimesh.load(model_path, force='mesh')

        # Extract metadata
        metadata = {
            'vertices': len(mesh.vertices) if hasattr(mesh, 'vertices') else 0,
            'faces': len(mesh.faces) if hasattr(mesh, 'faces') else 0,
            'is_watertight': mesh.is_watertight if hasattr(mesh, 'is_watertight') else False,
            'is_empty': mesh.is_empty if hasattr(mesh, 'is_empty') else True,
        }

        # Get bounding box
        if hasattr(mesh, 'bounds'):
            bounds = mesh.bounds
            metadata['bounds'] = {
                'min': bounds[0].tolist(),
                'max': bounds[1].tolist()
            }

            # Calculate dimensions
            dimensions = bounds[1] - bounds[0]
            metadata['dimensions'] = {
                'width': float(dimensions[0]),
                'height': float(dimensions[1]),
                'depth': float(dimensions[2])
            }

        # Get material count
        if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
            metadata['has_materials'] = True
        else:
            metadata['has_materials'] = False

        logger.info(f"Extracted 3D metadata: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Failed to extract 3D metadata: {str(e)}")
        return {}


def _generate_3d_previews(model_path: str, upload, original_path: str) -> list:
    """
    Generate preview images of 3D model from multiple angles

    Args:
        model_path: Path to 3D model file
        upload: MediaUpload instance
        original_path: Path to original model file

    Returns:
        List of paths to generated preview images

    Note:
        Requires trimesh with rendering backend (pyrender, pyglet, etc.)
        Install with: pip install trimesh[easy] pyrender
    """
    try:
        import trimesh
        import numpy as np

        # Try to import rendering backend
        try:
            import pyrender
            has_renderer = True
        except ImportError:
            logger.warning("pyrender not available, skipping preview generation")
            has_renderer = False

        if not has_renderer:
            return []

        # Load model
        mesh = trimesh.load(model_path)

        # Define camera angles for preview renders
        # (azimuth, elevation, name)
        angles = [
            (0, 0, 'front'),
            (90, 0, 'side'),
            (0, 90, 'top'),
            (45, 30, 'angle')
        ]

        preview_paths = []

        # Create preview path base
        path_parts = original_path.split('/')
        if 'original' in path_parts:
            version_index = path_parts.index('original')
            path_parts[version_index] = 'previews'
        else:
            path_parts.insert(-1, 'previews')

        base_name = path_parts[-1].rsplit('.', 1)[0]

        # Generate preview for each angle
        for azimuth, elevation, angle_name in angles:
            try:
                # Render preview image
                preview_image = _render_preview(mesh, azimuth, elevation)

                if preview_image is None:
                    continue

                # Create preview filename
                path_parts[-1] = f"{base_name}_{angle_name}.jpg"
                preview_path = '/'.join(path_parts)

                # Save to storage
                default_storage.save(preview_path, ContentFile(preview_image))

                preview_paths.append({
                    'angle': angle_name,
                    'path': preview_path
                })

                logger.info(f"Generated preview: {angle_name} at {preview_path}")

            except Exception as e:
                logger.error(f"Failed to generate {angle_name} preview: {str(e)}")
                continue

        return preview_paths

    except Exception as e:
        logger.error(f"Failed to generate 3D previews: {str(e)}")
        return []


def _render_preview(mesh, azimuth: float, elevation: float, resolution: int = 512) -> bytes:
    """
    Render 3D model preview from specific angle

    Args:
        mesh: Trimesh mesh object
        azimuth: Horizontal rotation angle (degrees)
        elevation: Vertical rotation angle (degrees)
        resolution: Image resolution (width and height)

    Returns:
        JPEG image bytes, or None if rendering failed

    Note:
        This is a placeholder implementation.
        Real implementation requires pyrender and OpenGL context.
    """
    try:
        import pyrender
        import numpy as np
        from PIL import Image
        import io

        # Create pyrender scene
        scene = pyrender.Scene()

        # Add mesh to scene
        mesh_pyrender = pyrender.Mesh.from_trimesh(mesh)
        scene.add(mesh_pyrender)

        # Set up camera
        camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)

        # Calculate camera position based on angles
        distance = np.linalg.norm(mesh.bounds[1] - mesh.bounds[0]) * 1.5
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(elevation)

        camera_pos = np.array([
            distance * np.cos(elevation_rad) * np.sin(azimuth_rad),
            distance * np.sin(elevation_rad),
            distance * np.cos(elevation_rad) * np.cos(azimuth_rad)
        ])

        scene.add(camera, pose=_look_at(camera_pos, np.zeros(3), np.array([0, 1, 0])))

        # Add lighting
        light = pyrender.DirectionalLight(color=np.ones(3), intensity=2.0)
        scene.add(light, pose=np.eye(4))

        # Render
        renderer = pyrender.OffscreenRenderer(resolution, resolution)
        color, _ = renderer.render(scene)

        # Convert to PIL Image
        img = Image.fromarray(color)

        # Convert to JPEG bytes
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)

        return img_io.read()

    except Exception as e:
        logger.error(f"Preview rendering failed: {str(e)}")
        return None


def _look_at(eye, target, up):
    """
    Create a look-at transformation matrix

    Args:
        eye: Camera position
        target: Point to look at
        up: Up vector

    Returns:
        4x4 transformation matrix
    """
    import numpy as np

    f = target - eye
    f = f / np.linalg.norm(f)

    s = np.cross(f, up)
    s = s / np.linalg.norm(s)

    u = np.cross(s, f)

    m = np.eye(4)
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[:3, 3] = eye

    return m
