"""
3D Model Upload and Processing Service

Handles 3D model file validation, metadata extraction, and processing orchestration.

Features:
- File format validation (GLB, GLTF, OBJ, FBX, USDZ)
- File size limits
- Metadata extraction (vertices, faces, materials, textures)
- Model integrity validation
"""

from typing import Dict, Any, Optional
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
import logging
import json

logger = logging.getLogger(__name__)


class Model3DUploadService:
    """
    Service for 3D model file uploads with validation and metadata extraction

    Features:
    - Format validation (GLB, GLTF, OBJ, FBX, USDZ)
    - File size limits
    - Model integrity checks
    - Metadata extraction (when possible)
    """

    # Supported 3D model formats
    SUPPORTED_FORMATS = ['glb', 'gltf', 'obj', 'fbx', 'usdz']

    # File size limits (bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MIN_FILE_SIZE = 100  # 100 bytes

    def __init__(self):
        self.trimesh_available = self._check_trimesh_availability()

    def _check_trimesh_availability(self) -> bool:
        """Check if trimesh library is available"""
        try:
            import trimesh
            return True
        except ImportError:
            logger.warning("Trimesh not available - 3D model metadata extraction will be limited")
            return False

    def validate_model(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate 3D model file and extract metadata

        Args:
            file: Uploaded 3D model file

        Returns:
            Dict with validation result and metadata:
            {
                'valid': bool,
                'error': str (if invalid),
                'format': str,
                'vertices': int,
                'faces': int,
                'materials': int,
                'textures': int,
                'file_type': str
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
                    'error': f"Unsupported 3D model format: {extension}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
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

            # Format-specific validation
            metadata = {}
            if extension == 'gltf':
                metadata = self._validate_gltf(file)
            elif extension == 'glb':
                metadata = self._validate_glb(file)
            elif extension == 'obj':
                metadata = self._validate_obj(file)
            elif self.trimesh_available:
                # Try to validate with trimesh for other formats
                metadata = self._validate_with_trimesh(file)

            return {
                'valid': True,
                'format': extension,
                **metadata
            }

        except Exception as e:
            logger.error(f"3D model validation failed: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': f"Validation failed: {str(e)}"
            }

    def _validate_gltf(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate glTF JSON format

        Args:
            file: glTF file

        Returns:
            Dict with metadata
        """
        try:
            # Read file content
            content = file.read()
            file.seek(0)  # Reset for later use

            # Try to parse as JSON
            gltf_data = json.loads(content.decode('utf-8'))

            # Basic glTF structure validation
            if 'asset' not in gltf_data:
                raise ValidationError("Invalid glTF: missing 'asset' property")

            metadata = {
                'file_type': 'gltf',
                'gltf_version': gltf_data.get('asset', {}).get('version', 'unknown'),
                'meshes': len(gltf_data.get('meshes', [])),
                'materials': len(gltf_data.get('materials', [])),
                'textures': len(gltf_data.get('textures', [])),
                'images': len(gltf_data.get('images', [])),
                'nodes': len(gltf_data.get('nodes', [])),
            }

            return metadata

        except json.JSONDecodeError:
            raise ValidationError("Invalid glTF: not valid JSON")
        except Exception as e:
            logger.warning(f"glTF metadata extraction failed: {e}")
            return {'file_type': 'gltf'}

    def _validate_glb(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate GLB binary format

        Args:
            file: GLB file

        Returns:
            Dict with metadata
        """
        try:
            # Read magic header (first 4 bytes)
            magic = file.read(4)
            file.seek(0)  # Reset

            # GLB magic number: 0x46546C67 ("glTF" in ASCII)
            if magic != b'glTF':
                raise ValidationError("Invalid GLB: incorrect magic number")

            # If trimesh is available, extract more metadata
            if self.trimesh_available:
                metadata = self._validate_with_trimesh(file)
                metadata['file_type'] = 'glb'
                return metadata

            return {'file_type': 'glb'}

        except Exception as e:
            logger.warning(f"GLB validation failed: {e}")
            return {'file_type': 'glb'}

    def _validate_obj(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate OBJ format

        Args:
            file: OBJ file

        Returns:
            Dict with metadata
        """
        try:
            # Count vertices and faces
            vertices = 0
            faces = 0
            materials = set()

            content = file.read()
            file.seek(0)  # Reset

            # Try to decode as text
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')

            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('v '):
                    vertices += 1
                elif line.startswith('f '):
                    faces += 1
                elif line.startswith('usemtl '):
                    materials.add(line.split()[1] if len(line.split()) > 1 else 'default')

            return {
                'file_type': 'obj',
                'vertices': vertices,
                'faces': faces,
                'materials': len(materials)
            }

        except Exception as e:
            logger.warning(f"OBJ validation failed: {e}")
            return {'file_type': 'obj'}

    def _validate_with_trimesh(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate and extract metadata using trimesh library

        Args:
            file: 3D model file

        Returns:
            Dict with metadata
        """
        try:
            import trimesh
            import tempfile
            import os

            # Save to temp file for trimesh
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file.name.split(".")[-1]}') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Reset file pointer for later use
            file.seek(0)

            try:
                # Load mesh with trimesh
                mesh = trimesh.load(temp_path)

                metadata = {}

                # Handle scene vs single mesh
                if isinstance(mesh, trimesh.Scene):
                    # Scene with multiple meshes
                    total_vertices = 0
                    total_faces = 0
                    geometries = 0

                    for geom in mesh.geometry.values():
                        if hasattr(geom, 'vertices'):
                            total_vertices += len(geom.vertices)
                        if hasattr(geom, 'faces'):
                            total_faces += len(geom.faces)
                        geometries += 1

                    metadata = {
                        'vertices': total_vertices,
                        'faces': total_faces,
                        'geometries': geometries,
                        'bounds': mesh.bounds.tolist() if hasattr(mesh, 'bounds') else None
                    }
                else:
                    # Single mesh
                    metadata = {
                        'vertices': len(mesh.vertices) if hasattr(mesh, 'vertices') else 0,
                        'faces': len(mesh.faces) if hasattr(mesh, 'faces') else 0,
                        'is_watertight': mesh.is_watertight if hasattr(mesh, 'is_watertight') else False,
                        'bounds': mesh.bounds.tolist() if hasattr(mesh, 'bounds') else None
                    }

                return metadata

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

        except ImportError:
            return {}
        except Exception as e:
            logger.warning(f"Trimesh validation failed: {e}")
            return {}

    def estimate_complexity(self, metadata: Dict[str, Any]) -> str:
        """
        Estimate model complexity based on metadata

        Args:
            metadata: Model metadata dict

        Returns:
            Complexity level: 'low', 'medium', 'high', 'very_high'
        """
        vertices = metadata.get('vertices', 0)
        faces = metadata.get('faces', 0)

        # Calculate total polygon count
        total_polygons = max(vertices, faces)

        if total_polygons < 10000:
            return 'low'
        elif total_polygons < 50000:
            return 'medium'
        elif total_polygons < 200000:
            return 'high'
        else:
            return 'very_high'


# Global instance
model_3d_upload_service = Model3DUploadService()
