"""
PDF Optimization Module
Reduces file size and improves performance
"""
import hashlib
import logging
import re
import zlib
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import cast

from PIL import Image


logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Optimization levels"""
    NONE = "none"           # No optimization
    FAST = "fast"           # Fast optimization
    BALANCED = "balanced"   # Balanced
    MAXIMUM = "maximum"     # Maximum optimization


@dataclass
class OptimizationOptions:
    """Optimization options"""
    level: OptimizationLevel = OptimizationLevel.BALANCED
    compress_images: bool = True          # Compress images
    compress_streams: bool = True         # Compress streams
    remove_unused: bool = True            # Remove unused objects
    merge_fonts: bool = False             # Merge fonts
    linearize: bool = False               # Linearize for web
    remove_metadata: bool = False         # Remove metadata
    downscale_images: bool = False        # Downscale images
    image_quality: int = 85               # Image quality (0-100)
    remove_duplicates: bool = True        # Remove duplicate data


class PDFOptimizer:
    """PDF Optimizer"""

    def __init__(self, options: OptimizationOptions | None = None):
        self.options = options or OptimizationOptions()
        self.stats = {
            'original_size': 0,
            'optimized_size': 0,
            'compression_ratio': 1.0,
            'objects_removed': 0,
            'images_optimized': 0,
            'streams_compressed': 0
        }

    def optimize(self, pdf_data: bytes) -> bytes:
        """Optimize PDF"""
        self.stats['original_size'] = len(pdf_data)

        if self.options.level == OptimizationLevel.NONE:
            return pdf_data

        # Parse PDF into parts
        pdf_parts = self._parse_pdf_structure(pdf_data)

        # Apply optimizations
        optimized_parts = self._apply_optimizations(pdf_parts)

        # Reassemble PDF
        optimized_data = self._assemble_pdf(optimized_parts)

        self.stats['optimized_size'] = len(optimized_data)
        if self.stats['original_size'] > 0:
            self.stats['compression_ratio'] = self.stats['optimized_size'] / self.stats['original_size']

        return optimized_data

    def _parse_pdf_structure(self, pdf_data: bytes) -> dict[str, Any]:
        """Parse PDF structure"""
        # This is a simple implementation
        # In practice, a full PDF parser is needed

        parts = {
            'header': b'',
            'objects': [],
            'xref': b'',
            'trailer': b'',
            'startxref': b''
        }

        # Find header
        header_match = re.search(rb'%PDF-\d\.\d', pdf_data)
        if header_match:
            parts['header'] = pdf_data[:header_match.end()]
            remaining = pdf_data[header_match.end():]
        else:
            parts['header'] = b'%PDF-1.7\n'
            remaining = pdf_data

        # Find startxref
        startxref_match = re.search(rb'startxref\s+(\d+)', remaining)
        if startxref_match:
            parts['startxref'] = remaining[startxref_match.start():]
            remaining = remaining[:startxref_match.start()]

        # Find trailer
        trailer_match = re.search(rb'trailer\s*<<.*?>>', remaining, re.DOTALL)
        if trailer_match:
            parts['trailer'] = remaining[trailer_match.start():]
            remaining = remaining[:trailer_match.start()]

        # Find xref
        xref_match = re.search(rb'xref\s+\d+\s+\d+.*?\n', remaining, re.DOTALL)
        if xref_match:
            parts['xref'] = remaining[xref_match.start():]
            remaining = remaining[:xref_match.start()]

        # Extract objects (simple)
        # In real implementation, a full parser is needed
        parts['objects_data'] = remaining

        return parts

    def _apply_optimizations(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """Apply optimizations"""
        optimized_parts = pdf_parts.copy()

        # Compress streams
        if self.options.compress_streams:
            optimized_parts = self._compress_streams(optimized_parts)

        # Optimize images
        if self.options.compress_images:
            optimized_parts = self._optimize_images(optimized_parts)

        # Remove unused objects
        if self.options.remove_unused:
            optimized_parts = self._remove_unused_objects(optimized_parts)

        # Remove duplicate data
        if self.options.remove_duplicates:
            optimized_parts = self._remove_duplicates(optimized_parts)

        # Remove metadata
        if self.options.remove_metadata:
            optimized_parts = self._remove_metadata(optimized_parts)

        # Linearize for web
        if self.options.linearize:
            optimized_parts = self._linearize_pdf(optimized_parts)

        return optimized_parts

    def _compress_streams(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """Compress streams"""
        # Find and compress streams
        pattern = rb'stream\s*\n(.*?)\n\s*endstream'
        objects_data = pdf_parts.get('objects_data', b'')

        def compress_stream(match):
            stream_data = match.group(1)
            try:
                # Compress with zlib
                compressed = zlib.compress(stream_data, level=zlib.Z_BEST_COMPRESSION)
                return b'stream\n' + compressed + b'\nendstream'
            except Exception:
                return match.group(0)

        compressed_data = re.sub(pattern, compress_stream, objects_data, flags=re.DOTALL)

        pdf_parts['objects_data'] = compressed_data
        self.stats['streams_compressed'] += 1

        return pdf_parts

    def _optimize_images(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """
        Optimize images in PDF with capabilities:
        1. Downscale images
        2. Compress with optimal algorithms
        3. Remove unnecessary metadata
        4. Convert non-optimal formats
        
        Args:
            pdf_parts: Dictionary containing PDF parts
            
        Returns:
            Optimized pdf_parts
        """
        try:
            if 'objects' not in pdf_parts:
                logger.warning("PDF has no objects for image optimization")
                return pdf_parts

            objects = pdf_parts['objects']
            optimized_count = 0
            total_size_before = 0
            total_size_after = 0

            # Optimization stats
            self.stats['images_optimized'] = 0
            self.stats['images_downscaled'] = 0
            self.stats['images_converted'] = 0
            self.stats['size_reduction_bytes'] = 0
            self.stats['size_reduction_percent'] = 0.0

            # Optimization options
            options = getattr(self, 'optimization_options', {
                'downscale_images': True,
                'max_image_width': 1920,
                'max_image_height': 1080,
                'jpeg_quality': 85,
                'compress_png': True,
                'remove_metadata': True,
                'convert_rgb_to_cmyk': False,
                'dpi_threshold': 300
            })

            # Process each object
            for i, obj in enumerate(objects):
                if self._is_image_object(obj):
                    original_size = self._get_object_size(obj)
                    total_size_before += original_size

                    # Optimize image
                    optimized_obj = self._optimize_single_image(obj, options)

                    if optimized_obj:
                        new_size = self._get_object_size(optimized_obj)
                        size_reduction = original_size - new_size

                        if size_reduction > 0:
                            objects[i] = optimized_obj
                            optimized_count += 1
                            total_size_after += new_size

                            # Update stats
                            self.stats['images_optimized'] += 1
                            self.stats['size_reduction_bytes'] += size_reduction

                            logger.debug(f"Image optimized: {size_reduction} bytes reduction")

            # Calculate reduction percentage
            if total_size_before > 0:
                reduction_percent = ((total_size_before - total_size_after) / total_size_before) * 100
                self.stats['size_reduction_percent'] = round(reduction_percent, 2)

                logger.info(
                    f"Image optimization complete: {optimized_count} images, "
                    f"{self.stats['size_reduction_bytes']:,} bytes reduction "
                    f"({self.stats['size_reduction_percent']}%)"
                )

            pdf_parts['objects'] = objects
            return pdf_parts

        except Exception as e:
            logger.error(f"Error optimizing images: {e}", exc_info=True)
            return pdf_parts


    def _is_image_object(self, obj: dict) -> bool:
        """
        Check if object is an image in PDF
        
        Args:
            obj: PDF object
            
        Returns:
            True if object is an image
        """
        try:
            # Check by subtype
            if obj.get('type') == 'xobject':
                subtype = obj.get('subtype', '')
                return subtype.lower() == '/image'

            # Check in metadata
            metadata = obj.get('metadata', {})
            if '/Subtype' in metadata:
                return metadata['/Subtype'] == '/Image'

            # Check in value
            value = obj.get('value', '')
            if isinstance(value, str):
                return '/Subtype /Image' in value or '/Filter /DCTDecode' in value

            return False
        except Exception:
            return False


    def _get_object_size(self, obj: dict) -> int:
        """
        Calculate object size
        
        Args:
            obj: PDF object
            
        Returns:
            Size in bytes
        """
        try:
            # Stream size
            if 'stream' in obj:
                stream_data = obj['stream']
                if isinstance(stream_data, bytes):
                    return len(stream_data)
                elif isinstance(stream_data, str):
                    return len(stream_data.encode('utf-8'))

            # Value size
            if 'value' in obj:
                value = obj['value']
                if isinstance(value, bytes):
                    return len(value)
                elif isinstance(value, str):
                    return len(value.encode('utf-8'))

            # Approximate size
            return len(str(obj).encode('utf-8'))
        except Exception:
            return 0


    def _optimize_single_image(self, image_obj: dict, options: dict) -> dict | None:
        """
        Optimize a single image
        
        Args:
            image_obj: Image object
            options: Optimization options
            
        Returns:
            Optimized object or None
        """
        try:
            # Extract image data
            image_data, image_info = self._extract_image_data(image_obj)
            if not image_data:
                return None

            # Detect image format
            image_format = self._detect_image_format(image_info)

            # Process by format
            processed_data = None

            if image_format == 'JPEG':
                processed_data = self._optimize_jpeg_image(
                    image_data, image_info, options
                )
            elif image_format == 'PNG':
                processed_data = self._optimize_png_image(
                    image_data, image_info, options
                )
            elif image_format == 'TIFF':
                processed_data = self._optimize_tiff_image(
                    image_data, image_info, options
                )
            elif image_format == 'JBIG2':
                processed_data = self._optimize_jbig2_image(
                    image_data, image_info, options
                )
            elif image_format == 'CCITT':
                processed_data = self._optimize_ccitt_image(
                    image_data, image_info, options
                )
            else:
                # Other formats - Generic compression
                processed_data = self._compress_generic_image(
                    image_data, image_info, options
                )

            if processed_data:
                # Create optimized object
                optimized_obj = self._create_optimized_image_object(
                    image_obj, processed_data, image_info, image_format
                )
                return optimized_obj

            return None

        except Exception as e:
            logger.warning(f"Error optimizing image: {e}")
            return None


    def _extract_image_data(self, image_obj: dict) -> tuple[bytes | None, dict]:
        """
        Extract image data from PDF object
        
        Args:
            image_obj: PDF image object
            
        Returns:
            (image data, image info)
        """
        try:
            image_info: dict[str, Any] = {}

            # Extract from stream
            if 'stream' in image_obj:
                stream_data = image_obj['stream']
                if isinstance(stream_data, bytes):
                    image_data = stream_data
                else:
                    image_data = str(stream_data).encode('utf-8')
            # Extract from value
            elif 'value' in image_obj:
                value = image_obj['value']
                if isinstance(value, bytes):
                    image_data = value
                else:
                    image_data = str(value).encode('utf-8')
            else:
                return None, {}

            # Extract info from metadata
            metadata = image_obj.get('metadata', {})

            # Dimensions
            if '/Width' in metadata and '/Height' in metadata:
                image_info['width'] = int(metadata['/Width'])
                image_info['height'] = int(metadata['/Height'])

            # Color space
            if '/ColorSpace' in metadata:
                image_info['colorspace'] = metadata['/ColorSpace']

            # Bit depth
            if '/BitsPerComponent' in metadata:
                image_info['bits_per_component'] = int(metadata['/BitsPerComponent'])

            # Filter
            if '/Filter' in metadata:
                image_info['filter'] = metadata['/Filter']

            # DPI
            if '/Width' in metadata and '/Height' in metadata:
                # Calculate approximate DPI
                if '/UserUnit' in metadata:
                    user_unit = float(metadata['/UserUnit'])
                    image_info['dpi'] = int(72 * user_unit)
                else:
                    image_info['dpi'] = 72  # Default

            return image_data, image_info

        except Exception as e:
            logger.warning(f"Error extracting image data: {e}")
            return None, {}


    def _detect_image_format(self, image_info: dict) -> str:
        """
        Detect image format
        
        Args:
            image_info: Image info
            
        Returns:
            Image format
        """
        filter_type = image_info.get('filter', '')

        if '/DCTDecode' in str(filter_type):
            return 'JPEG'
        elif '/FlateDecode' in str(filter_type):
            return 'PNG'
        elif '/CCITTFaxDecode' in str(filter_type):
            return 'CCITT'
        elif '/JBIG2Decode' in str(filter_type):
            return 'JBIG2'
        elif '/JPXDecode' in str(filter_type):
            return 'JPEG2000'
        else:
            # Try detecting from data
            return 'UNKNOWN'


    def _optimize_jpeg_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes | None:
        """
        Optimize JPEG image
        
        Args:
            image_data: Image data
            image_info: Image info
            options: Optimization options
            
        Returns:
            Optimized data
        """
        try:
            from PIL import Image
            import io

            # Open image
            img = cast(Image.Image, Image.open(io.BytesIO(image_data)))

            # Downscale if needed
            if options.get('downscale_images', True):
                img = self._downscale_image(img, image_info, options)
                self.stats['images_downscaled'] += 1

            # Remove metadata
            if options.get('remove_metadata', True):
                # Remove EXIF and other metadata
                img_data = list(img.getdata())
                img = cast(Image.Image, Image.new(img.mode, img.size))
                img.putdata(img_data)

            # Save with optimal quality
            output = io.BytesIO()
            quality = options.get('jpeg_quality', 85)

            # Convert to RGB if needed
            if img.mode not in ['RGB', 'L']:
                if img.mode == 'RGBA':
                    # Create white background for RGBA images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = cast(Image.Image, background)
                else:
                    img = cast(Image.Image, img.convert('RGB'))

            img.save(output, format='JPEG', quality=quality, optimize=True)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"Error optimizing JPEG: {e}")
            return image_data  # Return original data on error


    def _optimize_png_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes | None:
        """
        Optimize PNG image
        
        Args:
            image_data: Image data
            image_info: Image info
            options: Optimization options
            
        Returns:
            Optimized data
        """
        try:
            from PIL import Image
            import io

            # Open image
            img = cast(Image.Image, Image.open(io.BytesIO(image_data)))

            # Downscale if needed
            if options.get('downscale_images', True):
                img = self._downscale_image(img, image_info, options)
                self.stats['images_downscaled'] += 1

            # Reduce color depth if possible
            if img.mode in ['RGBA', 'RGB']:
                # Check if image uses only 256 colors
                colors = img.getcolors(maxcolors=256)
                if colors and len(colors) <= 256:
                    img = cast(Image.Image, img.convert('P', palette=Image.Palette.ADAPTIVE, colors=256))
                    self.stats['images_converted'] += 1

            # Save with optimal compression
            output = io.BytesIO()

            # PNG compression settings
            png_info: dict[str, Any] = {
                'optimize': True,
            }

            if options.get('compress_png', True):
                # zlib compression level
                png_info['compress_level'] = 9  # Maximum compression

            img.save(output, format='PNG', **png_info)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"Error optimizing PNG: {e}")
            return image_data


    def _optimize_tiff_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes | None:
        """
        Optimize TIFF image
        
        Args:
            image_data: Image data
            image_info: Image info
            options: Optimization options
            
        Returns:
            Optimized data
        """
        try:
            from PIL import Image
            import io

            # Open image
            img = cast(Image.Image, Image.open(io.BytesIO(image_data)))

            # Downscale if needed
            if options.get('downscale_images', True):
                img = self._downscale_image(img, image_info, options)
                self.stats['images_downscaled'] += 1

            # Convert to JPEG if quality is acceptable
            if options.get('convert_tiff_to_jpeg', True):
                output = io.BytesIO()
                quality = options.get('jpeg_quality', 85)

                # Convert to RGB
                if img.mode not in ['RGB', 'L']:
                    img = cast(Image.Image, img.convert('RGB'))

                img.save(output, format='JPEG', quality=quality, optimize=True)
                self.stats['images_converted'] += 1

                return output.getvalue()

            # Or compress TIFF
            output = io.BytesIO()
            img.save(output, format='TIFF', compression='tiff_lzw')

            return output.getvalue()

        except Exception as e:
            logger.warning(f"Error optimizing TIFF: {e}")
            return image_data


    def _optimize_jbig2_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes:
        """
        Optimize JBIG2 image
        (JBIG2 is already compressed, only check size)
        
        Args:
            image_data: Image data
            image_info: Image info
            options: Optimization options
            
        Returns:
            Optimized data
        """
        # JBIG2 is already highly compressed
        # We can only check if downscaling is needed
        return image_data


    def _optimize_ccitt_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes:
        """
        Optimize CCITT (fax) image
        
        Args:
            image_data: Image data
            image_info: Image info
            options: Optimization options
            
        Returns:
            Optimized data
        """
        # CCITT is optimal for black-and-white documents
        # Usually doesn't need further optimization
        return image_data


    def _compress_generic_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes:
        """
        Generic compression for unknown formats
        
        Args:
            image_data: Image data
            image_info: Image info
            options: Optimization options
            
        Returns:
            Compressed data
        """
        try:
            # Use zlib for generic compression
            compressed = zlib.compress(image_data, level=9)

            # Only if compression was effective
            if len(compressed) < len(image_data):
                return compressed

            return image_data
        except Exception:
            return image_data


    def _downscale_image(self, img: Image.Image, image_info: dict, options: dict) -> Image.Image:
        """
        Downscale image
        
        Args:
            img: PIL Image object
            image_info: Image info
            options: Optimization options
            
        Returns:
            Downscaled image
        """
        try:
            width, height = img.size
            max_width = options.get('max_image_width', 1920)
            max_height = options.get('max_image_height', 1080)
            dpi_threshold = options.get('dpi_threshold', 300)

            # Check DPI
            current_dpi = image_info.get('dpi', 72)
            if current_dpi > dpi_threshold:
                # Calculate scale factor
                scale_factor = dpi_threshold / current_dpi
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
            else:
                # Check dimensions
                if width > max_width or height > max_height:
                    # Calculate ratio
                    width_ratio = max_width / width
                    height_ratio = max_height / height
                    scale_factor = min(width_ratio, height_ratio)

                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                else:
                    return img

            # Ensure minimum size
            new_width = max(new_width, 100)
            new_height = max(new_height, 100)

            # Resize with high-quality filter
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        except Exception as e:
            logger.warning(f"Error downscaling image: {e}")
            return img


    def _create_optimized_image_object(self, original_obj: dict,
                                    optimized_data: bytes,
                                    image_info: dict,
                                    image_format: str) -> dict:
        """
        Create optimized image object
        
        Args:
            original_obj: Original object
            optimized_data: Optimized data
            image_info: Image info
            image_format: Image format
            
        Returns:
            Optimized object
        """
        # Create copy of original object
        optimized_obj = original_obj.copy()

        # Update stream
        if 'stream' in optimized_obj:
            optimized_obj['stream'] = optimized_data
        elif 'value' in optimized_obj:
            optimized_obj['value'] = optimized_data

        # Update metadata
        metadata = optimized_obj.get('metadata', {}).copy()

        # Update size
        metadata['/Length'] = len(optimized_data)

        # Update filter based on format
        if image_format == 'JPEG':
            metadata['/Filter'] = '/DCTDecode'
        elif image_format == 'PNG':
            metadata['/Filter'] = '/FlateDecode'

        # Update dimensions if changed
        if 'width' in image_info and 'height' in image_info:
            metadata['/Width'] = image_info['width']
            metadata['/Height'] = image_info['height']

        # Remove unnecessary metadata
        if 'remove_metadata' in getattr(self, 'optimization_options', {}):
            keys_to_remove = ['/Metadata', '/PieceInfo', '/StructParent', '/ID']
            for key in keys_to_remove:
                metadata.pop(key, None)

        optimized_obj['metadata'] = metadata

        # Add optimization flag
        optimized_obj['optimized'] = True
        optimized_obj['original_size'] = self._get_object_size(original_obj)
        optimized_obj['optimized_size'] = len(optimized_data)

        return optimized_obj

    def _remove_unused_objects(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """Remove unused objects"""
        # Analyze references and find unused objects
        # This simple implementation only removes specific objects

        objects_data = pdf_parts.get('objects_data', b'')

        # Find objects
        object_pattern = rb'(\d+\s+\d+\s+obj.*?endobj)'
        objects = re.findall(object_pattern, objects_data, re.DOTALL)

        # Simple analysis (more complex in practice)
        used_objects = set()

        # Find references
        ref_pattern = rb'(\d+\s+\d+\s+R)'
        for obj in objects:
            refs = re.findall(ref_pattern, obj)
            for ref in refs:
                used_objects.add(ref.decode('utf-8').split()[0])

        # Remove unused objects
        kept_objects = []
        for obj in objects:
            obj_match = re.match(rb'(\d+)\s+\d+\s+obj', obj)
            if obj_match:
                obj_num = obj_match.group(1).decode('utf-8')
                if obj_num in used_objects or self._is_root_object(obj):
                    kept_objects.append(obj)
                else:
                    self.stats['objects_removed'] += 1

        pdf_parts['objects_data'] = b'\n'.join(kept_objects)
        return pdf_parts

    def _is_root_object(self, obj_data: bytes) -> bool:
        """Check if object is a root object"""
        root_patterns = [
            rb'/Type\s*/Catalog',
            rb'/Pages\s+\d+\s+\d+\s+R',
            rb'/Outlines',
            rb'/AcroForm'
        ]

        for pattern in root_patterns:
            if re.search(pattern, obj_data):
                return True

        return False

    def _remove_duplicates(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """Remove duplicate data"""
        # Identify and remove duplicate objects
        # This simple implementation only removes identical objects

        objects_data = pdf_parts.get('objects_data', b'')

        object_pattern = rb'(\d+\s+\d+\s+obj.*?endobj)'
        objects = re.findall(object_pattern, objects_data, re.DOTALL)

        # Remove duplicates
        unique_objects = []
        seen_hashes = set()

        for obj in objects:
            obj_hash = hashlib.md5(obj).hexdigest()
            if obj_hash not in seen_hashes:
                seen_hashes.add(obj_hash)
                unique_objects.append(obj)
            else:
                self.stats['objects_removed'] += 1

        pdf_parts['objects_data'] = b'\n'.join(unique_objects)
        return pdf_parts

    def _remove_metadata(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """Remove metadata"""
        # Remove Info dictionary and XMP metadata
        objects_data = pdf_parts.get('objects_data', b'')

        # Remove Info objects
        info_pattern = rb'\d+\s+\d+\s+obj\s*<<\s*/Type\s*/Metadata.*?endobj'
        objects_data = re.sub(info_pattern, b'', objects_data, flags=re.DOTALL)

        # Remove XMP
        xmp_pattern = rb'<x:xmpmeta.*?</x:xmpmeta>'
        objects_data = re.sub(xmp_pattern, b'', objects_data, flags=re.DOTALL | re.IGNORECASE)

        pdf_parts['objects_data'] = objects_data
        return pdf_parts

    def _linearize_pdf(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """
        Linearize PDF for faster web loading
        
        Implementation based on PDF 1.4+ Linearization standard
        RFC: https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf
        Section: Annex F (Linearized PDF)
        
        Args:
            pdf_parts: Dictionary containing PDF parts
            
        Returns:
            Linearized pdf_parts
        """
        try:
            # 1. Check PDF structure
            if 'objects' not in pdf_parts or not pdf_parts['objects']:
                logger.warning("PDF has no objects for linearization")
                return pdf_parts

            objects = pdf_parts['objects']
            total_objects = len(objects)

            # 2. Create Linearization Dictionary (first object)
            linearization_value: dict[str, Any] = {
                'Type': '/Linearization',
                'L': pdf_parts.get('file_size', 0),
                'H': [0, 0],
                'O': 1,
                'E': 0,
                'N': total_objects,
                'T': 0,
                'P': 0
            }
            linearization_dict: dict[str, Any] = {
                'obj_num': 1,
                'generation': 0,
                'type': 'dict',
                'value': linearization_value
            }

            # 3. Identify pages and sort
            pages = []
            page_objects = []
            other_objects = []

            for obj in objects:
                if obj.get('type') == 'page':
                    pages.append(obj)
                    page_objects.append(obj)
                else:
                    other_objects.append(obj)

            # 4. Sort objects for linearization
            # Order: Linearization Dict → Root → Pages → Resources → Content → Other
            sorted_objects = []

            # 4.1. Linearization Dictionary (always object 1)
            sorted_objects.append(linearization_dict)

            # 4.2. Root object
            root_obj = next((obj for obj in objects if obj.get('type') == 'catalog'), None)
            if root_obj:
                sorted_objects.append(root_obj)
                other_objects.remove(root_obj)

            # 4.3. Pages objects
            sorted_objects.extend(page_objects)

            # 4.4. Page resources
            resource_objects = [obj for obj in other_objects if obj.get('type') in ['font', 'xobject', 'colorspace']]
            sorted_objects.extend(resource_objects)
            for obj in resource_objects:
                other_objects.remove(obj)

            # 4.5. Page contents
            content_objects = [obj for obj in other_objects if obj.get('type') == 'content']
            sorted_objects.extend(content_objects)
            for obj in content_objects:
                other_objects.remove(obj)

            # 4.6. Other objects
            sorted_objects.extend(other_objects)

            # 5. Update object numbers
            for i, obj in enumerate(sorted_objects, 1):
                obj['obj_num'] = i

            # 6. Create Hint Tables
            hint_tables = self._create_hint_tables(sorted_objects, pages)

            # 7. Create Hint Stream
            hint_stream = self._create_hint_stream(hint_tables)
            hint_stream_obj = {
                'obj_num': len(sorted_objects) + 1,
                'generation': 0,
                'type': 'stream',
                'value': hint_stream,
                'metadata': {
                    'Length': len(hint_stream),
                    'Filter': '/FlateDecode'
                }
            }

            sorted_objects.append(hint_stream_obj)

            # 8. Update Linearization Dictionary with Hint Stream info
            linearization_value['H'] = [
                self._calculate_object_offset(hint_stream_obj, sorted_objects),
                len(hint_stream)
            ]

            # 9. Update page information
            if pages:
                first_page = pages[0]
                linearization_value['P'] = first_page['obj_num']
                linearization_value['T'] = self._calculate_object_offset(first_page, sorted_objects)

            # 10. Create linearized header
            # Use standard comments instead of Chinese characters
            linearized_header = b'%PDF-1.7\n%EOF\n%Linearized-1.0\n'

            # 11. Update pdf_parts
            pdf_parts['header'] = linearized_header
            pdf_parts['objects'] = sorted_objects
            pdf_parts['linearized'] = True

            # 12. Recalculate offsets for xref table
            pdf_parts['xref_offsets'] = self._calculate_xref_offsets(sorted_objects, len(linearized_header))

            logger.info(f"PDF linearized with {len(sorted_objects)} objects")
            return pdf_parts

        except Exception as e:
            logger.error(f"Error linearizing PDF: {e}", exc_info=True)
            # Return original PDF on error
            return pdf_parts


    def _create_hint_tables(self, objects: list[dict], pages: list[dict]) -> dict[str, list]:
        """
        Create Hint Tables for linearization
        
        Hint Tables contain information for optimal page loading.
        
        Args:
            objects: List of sorted objects
            pages: List of page objects
            
        Returns:
            Dictionary containing hint tables
        """
        hint_tables: dict[str, list[list[int]]] = {
            'primary': [],  # Primary Hint Table
            'overflow': []  # Overflow Hint Table
        }

        # Calculate offsets for each page
        page_offsets = []
        for page in pages:
            offset = self._calculate_object_offset(page, objects)
            length = self._calculate_object_length(page)
            page_offsets.append({
                'offset': offset,
                'length': length,
                'obj_num': page['obj_num']
            })

        # Create Primary Hint Table
        # Format: [object_number, offset, length] for each page
        for page_info in page_offsets:
            hint_tables['primary'].append([
                page_info['obj_num'],
                page_info['offset'],
                page_info['length']
            ])

        # Create Overflow Hint Table (for additional info)
        # Contains shared objects info between pages
        shared_objects = self._identify_shared_objects(objects, pages)
        for shared_obj in shared_objects:
            offset = self._calculate_object_offset(shared_obj, objects)
            length = self._calculate_object_length(shared_obj)
            hint_tables['overflow'].append([
                shared_obj['obj_num'],
                offset,
                length,
                len(shared_obj.get('shared_pages', []))
            ])

        return hint_tables


    def _create_hint_stream(self, hint_tables: dict[str, list]) -> bytes:
        """
        Create Hint Stream as bytes
        
        Args:
            hint_tables: Hint tables
            
        Returns:
            Hint stream bytes
        """
        import struct
        import zlib

        # Hint data structure
        hint_data = bytearray()

        # Primary Hint Table
        primary_table = hint_tables['primary']
        hint_data.extend(struct.pack('>I', len(primary_table)))  # Number of pages

        for entry in primary_table:
            # object number, offset, length
            hint_data.extend(struct.pack('>III', entry[0], entry[1], entry[2]))

        # Overflow Hint Table
        overflow_table = hint_tables['overflow']
        hint_data.extend(struct.pack('>I', len(overflow_table)))  # Number of shared objects

        for entry in overflow_table:
            # object number, offset, length, page_count
            hint_data.extend(struct.pack('>IIIH', entry[0], entry[1], entry[2], entry[3]))

        # Compress with zlib
        compressed_data = zlib.compress(hint_data)

        return compressed_data


    def _calculate_object_offset(self, obj: dict, all_objects: list[dict]) -> int:
        """
        Calculate object offset in file
        
        Args:
            obj: Target object
            all_objects: List of all objects
            
        Returns:
            Offset in bytes
        """
        # This is a simple implementation
        # In a real implementation, exact offset should be calculated
        base_offset = 100  # Header and other info offset

        # Find object index
        try:
            obj_index = all_objects.index(obj)
            # Assume: each object takes about 500 bytes
            return base_offset + (obj_index * 500)
        except ValueError:
            return base_offset


    def _calculate_object_length(self, obj: dict) -> int:
        """
        Calculate object length
        
        Args:
            obj: Target object
            
        Returns:
            Length in bytes
        """
        # Approximate length calculation based on object type
        obj_type = obj.get('type', 'unknown')

        if obj_type == 'page':
            return 200  # Approximate page object length
        elif obj_type == 'content':
            content = obj.get('value', '')
            return len(str(content).encode('utf-8')) + 100
        elif obj_type == 'font':
            return 300
        elif obj_type == 'stream':
            stream_data = obj.get('value', b'')
            return len(stream_data) + 50
        else:
            return 100


    def _identify_shared_objects(self, objects: list[dict], pages: list[dict]) -> list[dict]:
        """
        Identify shared objects between pages
        
        Args:
            objects: All objects
            pages: Page objects
            
        Returns:
            List of shared objects
        """
        shared_objects = []

        # Resources shared between pages (fonts, images, ...)
        resource_types = ['font', 'xobject', 'colorspace', 'pattern']

        for obj in objects:
            if obj.get('type') in resource_types:
                # Check if used in more than one page
                used_in_pages = []

                for page in pages:
                    page_resources = page.get('resources', {})
                    resource_refs = []

                    if 'Font' in page_resources:
                        resource_refs.extend(page_resources['Font'].values())
                    if 'XObject' in page_resources:
                        resource_refs.extend(page_resources['XObject'].values())
                    if 'ColorSpace' in page_resources:
                        resource_refs.extend(page_resources['ColorSpace'].values())

                    if obj['obj_num'] in resource_refs:
                        used_in_pages.append(page['obj_num'])

                if len(used_in_pages) > 1:
                    obj['shared_pages'] = used_in_pages
                    shared_objects.append(obj)

        return shared_objects


    def _calculate_xref_offsets(self, objects: list[dict], header_length: int) -> list[int]:
        """
        Calculate offsets for xref table
        
        Args:
            objects: Sorted objects
            header_length: Header length
            
        Returns:
            List of offsets
        """
        offsets = []
        current_offset = header_length

        for obj in objects:
            offsets.append(current_offset)
            # Calculate current object length
            obj_length = self._calculate_object_length(obj)
            current_offset += obj_length

        return offsets

    def _assemble_pdf(self, pdf_parts: dict[str, Any]) -> bytes:
        """Reassemble PDF"""
        parts = [
            pdf_parts.get('header', b'%PDF-1.7\n'),
            pdf_parts.get('objects_data', b''),
            pdf_parts.get('xref', b''),
            pdf_parts.get('trailer', b''),
            pdf_parts.get('startxref', b'')
        ]

        return b''.join(parts)

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get optimization statistics"""
        return self.stats.copy()
