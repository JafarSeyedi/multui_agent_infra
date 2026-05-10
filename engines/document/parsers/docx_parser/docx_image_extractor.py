# engines/document/parsers/docx_parser/docx_image_extractor.py
"""
Image extractor for DOCX documents.
Extracts images from the word/media/ directory and maps them to relationship IDs.
"""
import base64
import hashlib
import os
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import PIL.ImageChops as PILImageChops
from PIL import Image as PILImage

from ...models.base import BinaryEncoding
from ...models.base import BinaryPayload
from ...models.media_types import MEDIA_TYPES
from ...models.media_types import MediaType


class DOCXImageExtractor:
    """
    Extracts and processes images from DOCX documents.
    
    Images in DOCX are stored in:
    - word/media/ directory (actual image files)
    - document.xml references via relationships (rId)
    - word/_rels/document.xml.rels maps rId to media path
    """

    # Supported image formats in DOCX
    SUPPORTED_IMAGE_MIME_TYPES = {
        'image/png': 'png',
        'image/jpeg': 'jpeg',
        'image/jpg': 'jpeg',
        'image/gif': 'gif',
        'image/bmp': 'bmp',
        'image/tiff': 'tiff',
        'image/x-emf': 'emf',
        'image/x-wmf': 'wmf',
        'image/svg+xml': 'svg',
        'image/webp': 'webp',
    }

    # MIME type detection by file extension
    EXTENSION_TO_MIME = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tif': 'image/tiff',
        '.tiff': 'image/tiff',
        '.emf': 'image/x-emf',
        '.wmf': 'image/x-wmf',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }

    def __init__(self, zip_file: ZipFile, encoding: BinaryEncoding = BinaryEncoding.BASE64):
        """
        Initialize the image extractor.
        
        Args:
            zip_file: Open ZipFile object for the DOCX archive
            encoding: Encoding method for binary data in payload
        """
        self.zip_file = zip_file
        self.encoding = encoding
        self._media_files: list[str] | None = None
        self._image_cache: dict[str, bytes] = {}

    # ============================================================
    # PUBLIC API
    # ============================================================

    def extract_all_images(self) -> dict[str, BinaryPayload]:
        """
        Extract all images from the document and return as BinaryPayload objects.
        
        Returns:
            Dictionary mapping relationship ID to BinaryPayload
        """
        images = {}

        # Get list of all media files
        media_files = self._get_media_files()

        for media_path in media_files:
            # Extract filename without path
            filename = os.path.basename(media_path)

            # Create a synthetic relationship ID based on filename
            # In practice, we'll map these via relationships in the main parser
            rel_id = self._filename_to_rel_id(filename)

            payload = self.extract_image_by_path(media_path)
            if payload:
                images[rel_id] = payload
                # Also store by full path for flexibility
                images[media_path] = payload

        return images

    def extract_image_by_rel_id(self, rel_id: str, relationships: dict[str, str]) -> BinaryPayload | None:
        """
        Extract a single image by its relationship ID.
        
        Args:
            rel_id: Relationship ID (e.g., 'rId4')
            relationships: Mapping of rel_id to target path
            
        Returns:
            BinaryPayload or None if extraction fails
        """
        if rel_id not in relationships:
            return None

        target = relationships[rel_id]

        # Target is usually 'media/image1.png'
        if target.startswith('media/'):
            return self.extract_image_by_path(f'word/{target}')

        return None

    def extract_image_by_path(self, path_in_zip: str) -> BinaryPayload | None:
        """
        Extract an image by its path inside the ZIP archive.
        
        Args:
            path_in_zip: Full path inside the DOCX archive (e.g., 'word/media/image1.png')
            
        Returns:
            BinaryPayload or None if extraction fails
        """
        # Check cache first
        if path_in_zip in self._image_cache:
            return self._create_payload(
                self._image_cache[path_in_zip],
                path_in_zip
            )

        try:
            # Read the image data
            image_data = self.zip_file.read(path_in_zip)

            # Cache for future use
            self._image_cache[path_in_zip] = image_data

            return self._create_payload(image_data, path_in_zip)

        except KeyError:
            # File not found in ZIP
            return None
        except Exception:
            return None

    def extract_images_from_drawing_elements(
        self,
        drawings: list[tuple[str, dict[str, str]]]
    ) -> dict[str, BinaryPayload]:
        """
        Extract images referenced in drawing elements.
        
        Args:
            drawings: List of (rel_id, properties) tuples from parsed document
            
        Returns:
            Dictionary mapping rel_id to BinaryPayload
        """
        images = {}

        for rel_id, props in drawings:
            payload = self.extract_image_by_rel_id(rel_id, props)
            if payload:
                images[rel_id] = payload

        return images

    def get_image_metadata(self, image_data: bytes) -> dict[str, Any]:
        """
        Extract metadata from image binary data.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with image metadata (dimensions, format, etc.)
        """
        metadata: dict[str, Any] = {}

        try:
            with BytesIO(image_data) as img_buffer:
                with PILImage.open(img_buffer) as img:
                    metadata['width'] = img.width
                    metadata['height'] = img.height
                    metadata['format'] = img.format
                    metadata['mode'] = img.mode

                    # Check if image has transparency
                    if img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info:
                        metadata['has_transparency'] = True

                    # Extract EXIF data if available
                    if hasattr(img, '_getexif') and img._getexif():
                        exif = img._getexif()
                        if exif:
                            metadata['exif'] = self._parse_exif(exif)
        except Exception:
            # PIL couldn't open the image, try basic detection
            metadata = self._detect_basic_image_info(image_data)

        return metadata

    def compare_images(self, image1: bytes, image2: bytes) -> float:
        """
        Compare two images and return similarity score (0.0 to 1.0).
        Useful for duplicate detection.
        
        Args:
            image1: First image bytes
            image2: Second image bytes
            
        Returns:
            Similarity score (1.0 = identical)
        """
        try:
            # Quick hash check first
            hash1 = hashlib.sha256(image1).hexdigest()
            hash2 = hashlib.sha256(image2).hexdigest()

            if hash1 == hash2:
                return 1.0

            # If hashes differ, do pixel comparison
            with BytesIO(image1) as buf1, BytesIO(image2) as buf2:
                img1 = PILImage.open(buf1).convert('RGB')
                img2 = PILImage.open(buf2).convert('RGB')

                # Resize to same dimensions for comparison
                if img1.size != img2.size:
                    img2 = img2.resize(img1.size, PILImage.Resampling.LANCZOS)

                diff = PILImageChops.difference(img1, img2)

                # Calculate difference percentage
                diff_data = list(diff.getdata())
                total_pixels = len(diff_data)
                identical_pixels = sum(1 for p in diff_data if p == (0, 0, 0))

                return identical_pixels / total_pixels if total_pixels > 0 else 0.0

        except Exception:
            # Fallback to hash comparison only
            return 1.0 if hash1 == hash2 else 0.0

    # ============================================================
    # PRIVATE HELPER METHODS
    # ============================================================

    def _get_media_files(self) -> list[str]:
        """Get list of all files in word/media/ directory."""
        if self._media_files is not None:
            return self._media_files

        media_files = []

        for file_info in self.zip_file.filelist:
            filename = file_info.filename

            # Check if file is in media directory
            if filename.startswith('word/media/') and not file_info.is_dir():
                media_files.append(filename)

        self._media_files = media_files
        return media_files

    def _filename_to_rel_id(self, filename: str) -> str:
        """Generate a synthetic relationship ID from filename."""
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]

        # Extract number if present (e.g., 'image1' -> '1')
        import re
        match = re.search(r'(\d+)$', name_without_ext)
        if match:
            return f'rIdImage{match.group(1)}'

        # Fallback to hash-based ID
        hash_val = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f'rIdImage_{hash_val}'

    def _create_payload(self, image_data: bytes, source_path: str) -> BinaryPayload:
        """
        Create a BinaryPayload from image data.
        
        Args:
            image_data: Raw image bytes
            source_path: Source path in ZIP (used for MIME detection)
            
        Returns:
            BinaryPayload object
        """
        # Detect MIME type
        mime_type = self._detect_mime_type(image_data, source_path)

        # Get media type from registry
        media_type = self._get_media_type(mime_type)

        # Get image metadata
        self.get_image_metadata(image_data)

        # Calculate hash
        sha256_hash = hashlib.sha256(image_data).hexdigest()

        # Encode data based on encoding method
        encoded_data = None
        bytes_content = None

        if self.encoding == BinaryEncoding.BASE64:
            encoded_data = base64.b64encode(image_data).decode('ascii')
        elif self.encoding == BinaryEncoding.RAW:
            encoded_data = image_data.hex()
        else:
            # Default to storing raw bytes
            bytes_content = image_data

        return BinaryPayload(
            media_type=media_type,
            encoding=self.encoding,
            bytes_content=bytes_content,
            data=encoded_data,
            size_bytes=len(image_data),
            sha256=sha256_hash,
            compressed=False,
            compression_algorithm=None,
            original_size=len(image_data)
        )

    def _detect_mime_type(self, image_data: bytes, source_path: str) -> str:
        """Detect MIME type from image data or file extension."""
        # Try extension first
        ext = os.path.splitext(source_path)[1].lower()
        if ext in self.EXTENSION_TO_MIME:
            return self.EXTENSION_TO_MIME[ext]

        # Try magic bytes detection
        if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif image_data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return 'image/gif'
        elif image_data.startswith(b'BM'):
            return 'image/bmp'
        elif image_data.startswith(b'II*\x00') or image_data.startswith(b'MM\x00*'):
            return 'image/tiff'
        elif image_data.startswith(b'<?xml') or image_data.startswith(b'<svg'):
            return 'image/svg+xml'
        elif image_data.startswith(b'RIFF') and image_data[8:12] == b'WEBP':
            return 'image/webp'

        # Default fallback
        return 'application/octet-stream'

    def _get_media_type(self, mime_type: str) -> MediaType:
        """Get MediaType object from MIME type."""
        # Try to get from registry
        for key, mt in MEDIA_TYPES.items():
            if mt.mime == mime_type:
                return mt

        # Fallback to binary type
        return MEDIA_TYPES['binary']

    def _detect_basic_image_info(self, image_data: bytes) -> dict[str, Any]:
        """Detect basic image info without PIL."""
        metadata: dict[str, Any] = {}

        # Detect format by magic bytes
        if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            metadata['format'] = 'PNG'
            # PNG dimensions are at offset 16-23
            if len(image_data) > 24:
                import struct
                width, height = struct.unpack('>II', image_data[16:24])
                metadata['width'] = width
                metadata['height'] = height

        elif image_data.startswith(b'\xff\xd8\xff'):
            metadata['format'] = 'JPEG'
            # JPEG dimensions require parsing markers
            dims = self._get_jpeg_dimensions(image_data)
            if dims:
                metadata['width'], metadata['height'] = dims

        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            metadata['format'] = 'GIF'
            if len(image_data) > 10:
                import struct
                width, height = struct.unpack('<HH', image_data[6:10])
                metadata['width'] = width
                metadata['height'] = height

        elif image_data.startswith(b'BM'):
            metadata['format'] = 'BMP'
            if len(image_data) > 26:
                import struct
                width, height = struct.unpack('<II', image_data[18:26])
                metadata['width'] = width
                metadata['height'] = height

        return metadata

    def _get_jpeg_dimensions(self, data: bytes) -> tuple[int, int] | None:
        """Extract dimensions from JPEG data."""
        # JPEG markers
        SOF0 = b'\xff\xc0'
        SOF2 = b'\xff\xc2'

        i = 0
        while i < len(data):
            if data[i:i+2] in (SOF0, SOF2):
                if i + 9 < len(data):
                    import struct
                    height, width = struct.unpack('>HH', data[i+5:i+9])
                    return width, height
                break

            # Skip to next marker
            if data[i] == 0xFF and data[i+1] != 0xDA:  # Not SOS marker
                if i + 4 < len(data):
                    length = struct.unpack('>H', data[i+2:i+4])[0]
                    i += length + 2
                else:
                    break
            else:
                i += 1

        return None

    def _parse_exif(self, exif_data: dict[Any, Any]) -> dict[str, Any]:
        """Parse EXIF data into a simpler dictionary."""
        parsed: dict[str, Any] = {}

        # Common EXIF tags
        tag_names = {
            271: 'make',
            272: 'model',
            306: 'datetime',
            315: 'artist',
            33432: 'copyright',
            34855: 'iso_speed',
            37377: 'shutter_speed',
            37378: 'aperture',
            37383: 'metering_mode',
            37385: 'flash',
            37386: 'focal_length',
            40962: 'exif_image_width',
            40963: 'exif_image_height',
        }

        for tag_id, value in exif_data.items():
            tag_name = tag_names.get(tag_id, f'tag_{tag_id}')

            # Convert bytes to string if needed
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='ignore').strip('\x00')
                except:
                    value = value.hex()

            parsed[tag_name] = value

        return parsed

    def get_image_as_base64(self, rel_id: str, relationships: dict[str, str]) -> str | None:
        """
        Convenience method to get image as base64 string.
        
        Args:
            rel_id: Relationship ID
            relationships: Relationship mapping
            
        Returns:
            Base64 encoded string or None
        """
        payload = self.extract_image_by_rel_id(rel_id, relationships)

        if payload:
            if payload.data:
                return payload.data
            elif payload.bytes_content:
                return base64.b64encode(payload.bytes_content).decode('ascii')

        return None

    def get_image_dimensions(self, rel_id: str, relationships: dict[str, str]) -> tuple[int, int] | None:
        """
        Get image dimensions.
        
        Args:
            rel_id: Relationship ID
            relationships: Relationship mapping
            
        Returns:
            Tuple of (width, height) or None
        """
        payload = self.extract_image_by_rel_id(rel_id, relationships)

        if payload:
            image_bytes = payload.bytes_content
            if image_bytes is None and payload.data and payload.encoding == BinaryEncoding.BASE64:
                try:
                    image_bytes = base64.b64decode(payload.data)
                except Exception:
                    image_bytes = None
            if image_bytes:
                metadata = self.get_image_metadata(image_bytes)
                width = metadata.get('width')
                height = metadata.get('height')
                if isinstance(width, int) and isinstance(height, int):
                    return (width, height)

        return None

    def clear_cache(self):
        """Clear the image cache to free memory."""
        self._image_cache.clear()
