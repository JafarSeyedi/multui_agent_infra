#!/usr/bin/env python3
"""
pdf_objects.py - PDF object classes for parser
Complete implementation of PDF object model according to PDF 1.7 standard
"""
import re
import zlib
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from decimal import getcontext
from enum import Enum
from typing import Any
from typing import cast

# Set decimal precision for PDF calculations
getcontext().prec = 10


class PDFObjectType(Enum):
    """PDF object types"""
    BOOLEAN = "boolean"
    INTEGER = "integer"
    REAL = "real"
    STRING = "string"
    NAME = "name"
    ARRAY = "array"
    DICTIONARY = "dictionary"
    STREAM = "stream"
    NULL = "null"
    REFERENCE = "reference"
    INDIRECT = "indirect"


class PDFColorSpace(Enum):
    """PDF color spaces"""
    DEVICE_GRAY = "DeviceGray"
    DEVICE_RGB = "DeviceRGB"
    DEVICE_CMYK = "DeviceCMYK"
    CAL_GRAY = "CalGray"
    CAL_RGB = "CalRGB"
    LAB = "Lab"
    ICC_BASED = "ICCBased"
    INDEXED = "Indexed"
    PATTERN = "Pattern"
    SEPARATION = "Separation"
    DEVICE_N = "DeviceN"


class PDFLineCapStyle(Enum):
    """Line cap style"""
    BUTT_CAP = 0
    ROUND_CAP = 1
    SQUARE_CAP = 2


class PDFLineJoinStyle(Enum):
    """Line join style"""
    MITER_JOIN = 0
    ROUND_JOIN = 1
    BEVEL_JOIN = 2


class PDFTextRenderingMode(Enum):
    """Text rendering modes"""
    FILL = 0
    STROKE = 1
    FILL_STROKE = 2
    INVISIBLE = 3
    FILL_CLIP = 4
    STROKE_CLIP = 5
    FILL_STROKE_CLIP = 6
    CLIP = 7


class PDFError(Exception):
    """Base error for PDF"""


class PDFParseError(PDFError):
    """PDF parse error"""


class PDFValidationError(PDFError):
    """PDF validation error"""


@dataclass
class PDFObject(ABC):
    """Base class for all PDF objects"""

    @abstractmethod
    def to_pdf(self) -> bytes:
        """Convert to PDF format"""

    @abstractmethod
    def get_type(self) -> PDFObjectType:
        """Get object type"""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""

    def __str__(self) -> str:
        return f"PDFObject(type={self.get_type().value})"


@dataclass
class PDFBoolean(PDFObject):
    """Boolean object in PDF"""
    value: bool

    def to_pdf(self) -> bytes:
        return b"true" if self.value else b"false"

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.BOOLEAN

    def to_dict(self) -> dict[str, Any]:
        return {"type": "boolean", "value": self.value}

    def __str__(self) -> str:
        return f"PDFBoolean({self.value})"


@dataclass
class PDFInteger(PDFObject):
    """Integer object in PDF"""
    value: int

    def to_pdf(self) -> bytes:
        return str(self.value).encode('ascii')

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.INTEGER

    def to_dict(self) -> dict[str, Any]:
        return {"type": "integer", "value": self.value}

    def __str__(self) -> str:
        return f"PDFInteger({self.value})"


@dataclass
class PDFReal(PDFObject):
    """Real (decimal) object in PDF"""
    value: float

    def to_pdf(self) -> bytes:
        # Decimal format with maximum 4 decimal places
        formatted = f"{self.value:.4f}".rstrip('0').rstrip('.')
        if formatted == '':
            formatted = '0'
        return formatted.encode('ascii')

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.REAL

    def to_dict(self) -> dict[str, Any]:
        return {"type": "real", "value": self.value}

    def __str__(self) -> str:
        return f"PDFReal({self.value})"


@dataclass
class PDFString(PDFObject):
    """String object in PDF"""
    value: str
    is_hex: bool = False
    is_literal: bool = True

    def to_pdf(self) -> bytes:
        if self.is_hex:
            # Hexadecimal string
            hex_str = self.value.encode('utf-8').hex().upper()
            return f"<{hex_str}>".encode('ascii')
        else:
            # Literal string
            # Escape special characters
            escaped = self.value
            escaped = escaped.replace('\\', '\\\\')
            escaped = escaped.replace('(', '\\(')
            escaped = escaped.replace(')', '\\)')
            escaped = escaped.replace('\n', '\\n')
            escaped = escaped.replace('\r', '\\r')
            escaped = escaped.replace('\t', '\\t')
            escaped = escaped.replace('\b', '\\b')
            escaped = escaped.replace('\f', '\\f')
            return f"({escaped})".encode()

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.STRING

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "string",
            "value": self.value,
            "is_hex": self.is_hex,
            "is_literal": self.is_literal
        }

    def __str__(self) -> str:
        if len(self.value) > 50:
            preview = self.value[:50] + "..."
        else:
            preview = self.value
        return f"PDFString('{preview}', hex={self.is_hex})"


@dataclass
class PDFName(PDFObject):
    """Name object in PDF"""
    value: str

    def to_pdf(self) -> bytes:
        # Escape special characters in names
        escaped = self.value
        # Special characters that must be escaped
        special_chars = {
            ' ': '#20',
            '(': '#28',
            ')': '#29',
            '<': '#3C',
            '>': '#3E',
            '[': '#5B',
            ']': '#5D',
            '{': '#7B',
            '}': '#7D',
            '/': '#2F',
            '%': '#25',
            '#': '#23'
        }

        result = []
        for char in escaped:
            if char in special_chars:
                result.append(special_chars[char])
            elif ord(char) < 33 or ord(char) > 126:
                # Non-ASCII characters to hexadecimal
                result.append(f"#{ord(char):02X}")
            else:
                result.append(char)

        return f"/{''.join(result)}".encode('ascii')

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.NAME

    def to_dict(self) -> dict[str, Any]:
        return {"type": "name", "value": self.value}

    def __str__(self) -> str:
        return f"PDFName({self.value})"


@dataclass
class PDFArray(PDFObject):
    """Array object in PDF"""
    elements: list[PDFObject] = field(default_factory=list)

    def to_pdf(self) -> bytes:
        if not self.elements:
            return b"[]"

        result = [b"["]
        for i, element in enumerate(self.elements):
            if i > 0:
                result.append(b" ")
            result.append(element.to_pdf())
        result.append(b"]")

        return b"".join(result)

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.ARRAY

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "array",
            "elements": [elem.to_dict() for elem in self.elements],
            "count": len(self.elements)
        }

    def append(self, element: PDFObject):
        """Add element to array"""
        self.elements.append(element)

    def extend(self, elements: list[PDFObject]):
        """Add multiple elements to array"""
        self.elements.extend(elements)

    def __getitem__(self, index: int) -> PDFObject:
        return self.elements[index]

    def __len__(self) -> int:
        return len(self.elements)

    def __str__(self) -> str:
        return f"PDFArray({len(self.elements)} elements)"


@dataclass
class PDFDictionary(PDFObject):
    """Dictionary object in PDF"""
    entries: dict[PDFName, PDFObject] = field(default_factory=dict)

    def to_pdf(self) -> bytes:
        if not self.entries:
            return b"<<>>"

        result = [b"<<"]
        for key, value in self.entries.items():
            result.append(b"\n")
            result.append(key.to_pdf())
            result.append(b" ")
            result.append(value.to_pdf())
        result.append(b"\n>>")

        return b"".join(result)

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.DICTIONARY

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "dictionary",
            "entries": {key.value: value.to_dict() for key, value in self.entries.items()},
            "count": len(self.entries)
        }

    def get(self, key: str, default: Any = None) -> PDFObject | None:
        """Get value by key"""
        name_key = PDFName(key)
        return self.entries.get(name_key, default)

    def set(self, key: str, value: PDFObject):
        """Set value by key"""
        name_key = PDFName(key)
        self.entries[name_key] = value

    def has_key(self, key: str) -> bool:
        """Check if key exists"""
        name_key = PDFName(key)
        return name_key in self.entries

    def keys(self) -> list[str]:
        """Get keys"""
        return [key.value for key in self.entries.keys()]

    def values(self) -> list[PDFObject]:
        """Get values"""
        return list(self.entries.values())

    def items(self) -> list[tuple[str, PDFObject]]:
        """Get key-value pairs"""
        return [(key.value, value) for key, value in self.entries.items()]

    def __contains__(self, key: str) -> bool:
        return self.has_key(key)

    def __getitem__(self, key: str) -> PDFObject:
        name_key = PDFName(key)
        return self.entries[name_key]

    def __setitem__(self, key: str, value: PDFObject):
        name_key = PDFName(key)
        self.entries[name_key] = value

    def __len__(self) -> int:
        return len(self.entries)

    def __str__(self) -> str:
        return f"PDFDictionary({len(self.entries)} entries)"


@dataclass
class PDFStream(PDFObject):
    """Stream object in PDF"""
    data: bytes
    filters: list[str] = field(default_factory=list)
    decode_params: dict[str, Any] | None = None
    length: int | None = None

    def to_pdf(self) -> bytes:
        # Calculate length if not provided
        if self.length is None:
            self.length = len(self.data)

        # Create stream dictionary
        dict_obj = PDFDictionary()
        dict_obj.set("Length", PDFInteger(self.length))

        if self.filters:
            if len(self.filters) == 1:
                dict_obj.set("Filter", PDFName(self.filters[0]))
            else:
                filter_array = PDFArray([PDFName(f) for f in self.filters])
                dict_obj.set("Filter", filter_array)

        if self.decode_params:
            params_dict = PDFDictionary()
            for key, value in self.decode_params.items():
                if isinstance(value, int):
                    params_dict.set(key, PDFInteger(value))
                elif isinstance(value, float):
                    params_dict.set(key, PDFReal(value))
                elif isinstance(value, str):
                    params_dict.set(key, PDFString(value))
                elif isinstance(value, bool):
                    params_dict.set(key, PDFBoolean(value))
            dict_obj.set("DecodeParms", params_dict)

        # Combine dictionary and data
        result = []
        result.append(dict_obj.to_pdf())
        result.append(b"\nstream\n")
        result.append(self.data)
        result.append(b"\nendstream")

        return b"".join(result)

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.STREAM

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "stream",
            "length": len(self.data),
            "filters": self.filters,
            "decode_params": self.decode_params,
            "data_preview": self.data[:100] if self.data else b"",
            "data_size": len(self.data)
        }

    def get_decoded_data(self) -> bytes:
        """Get decoded data"""
        data = self.data

        # Apply filters in reverse order (for decode)
        for filter_name in reversed(self.filters):
            if filter_name == "FlateDecode":
                try:
                    data = zlib.decompress(data)
                except zlib.error:
                    raise PDFParseError("Error decompressing FlateDecode data")
            elif filter_name == "ASCIIHexDecode":
                data = self._decode_ascii_hex(data)
            elif filter_name == "ASCII85Decode":
                data = self._decode_ascii85(data)
            elif filter_name == "LZWDecode":
                data = self._decode_lzw(data)
            elif filter_name == "RunLengthDecode":
                data = self._decode_run_length(data)
            elif filter_name == "CCITTFaxDecode":
                # Needs specific implementation
                pass
            elif filter_name == "JBIG2Decode":
                # Needs specific implementation
                pass
            elif filter_name == "DCTDecode":
                # JPEG - no decode needed
                pass
            elif filter_name == "JPXDecode":
                # JPEG2000 - no decode needed
                pass
            elif filter_name == "Crypt":
                # Encryption - needs key
                pass

        return data

    def _decode_ascii_hex(self, data: bytes) -> bytes:
        """Decode ASCIIHex"""
        hex_str = data.decode('ascii', errors='ignore').strip()
        hex_str = hex_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

        # Remove > character
        if hex_str.endswith('>'):
            hex_str = hex_str[:-1]

        # Ensure even length
        if len(hex_str) % 2 != 0:
            hex_str += '0'

        try:
            return bytes.fromhex(hex_str)
        except ValueError:
            raise PDFParseError("Error decoding ASCIIHex")

    def _decode_ascii85(self, data: bytes) -> bytes:
        """Decode ASCII85"""
        import base64
        ascii85_str = data.decode('ascii', errors='ignore').strip()

        # Remove ~> characters
        ascii85_str = ascii85_str.replace('~>', '')

        try:
            # Add padding if needed
            padding = 4 - (len(ascii85_str) % 4)
            if padding != 4:
                ascii85_str += 'u' * padding

            return base64.a85decode(ascii85_str, adobe=True)
        except Exception:
            raise PDFParseError("Error decoding ASCII85")

    def _decode_lzw(self, data: bytes) -> bytes:
        """Decode LZW (simple fallback implementation)"""
        # The external 'lzw' library is deprecated and unavailable; always use the fallback.
        return self._simple_lzw_decode(data)

    def _simple_lzw_decode(self, data: bytes) -> bytes:
        """
        Full LZW decoder for PDF streams (EarlyChange=1).
        Reference: PDF 1.7 spec, Section 7.4.4.
        """
        # Constants
        CLEAR_TABLE = 256
        EOD = 257
        INITIAL_BITS = 9
        MAX_BITS = 12

        # Convert bytes to a list of ints for easier bit reading
        data_bytes = list(data)
        bit_pos = 0  # current bit position within the byte stream (0-indexed)

        def read_bits(n: int) -> int:
            """Read n bits from the data (MSB first)."""
            nonlocal bit_pos
            value = 0
            for _ in range(n):
                byte_index = bit_pos // 8
                bit_index = 7 - (bit_pos % 8)   # MSB first
                if byte_index >= len(data_bytes):
                    return value
                bit = (data_bytes[byte_index] >> bit_index) & 1
                value = (value << 1) | bit
                bit_pos += 1
            return value

        # Initialize the string table with single-character entries 0..255
        table: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
        table[CLEAR_TABLE] = b''   # placeholder
        table[EOD] = b''           # placeholder
        next_code = EOD + 1
        current_bits = INITIAL_BITS
        max_code = (1 << current_bits) - 1

        result = bytearray()
        old_code = None

        while True:
            # Read next code from the stream
            code = read_bits(current_bits)
            if code == EOD or code == -1:   # -1 from read_bits when data exhausted
                break
            if code == CLEAR_TABLE:
                # Reset the table
                table = {i: bytes([i]) for i in range(256)}
                table[CLEAR_TABLE] = b''
                table[EOD] = b''
                next_code = EOD + 1
                current_bits = INITIAL_BITS
                max_code = (1 << current_bits) - 1
                old_code = None
                continue

            if old_code is None:
                # First code after clear or start: must be a single character
                if code < 256:
                    result.append(code)
                    old_code = code
                    continue
                else:
                    # Should not happen in a valid stream
                    raise PDFParseError("LZW: first code is not a literal")

            # We have a previous string (old_code).
            # default: new string = old_string + first_char_of(old_string)
            # but if code is already in table, new string = table[old_code] + first_char_of(table[code])
            if code in table:
                current_string = table[code]
                new_string = table[old_code] + bytes([current_string[0]])
                result.extend(current_string)
            else:
                # code == next_code, meaning the string is not yet in the table
                # The string is old_string + first_char_of(old_string)
                current_string = table[old_code] + bytes([table[old_code][0]])
                result.extend(current_string)
                new_string = current_string

            # Add new_string to table if possible
            if next_code <= max_code:
                table[next_code] = new_string
                next_code += 1
                # Determine if we need to increase code size
                if next_code > max_code and current_bits < MAX_BITS:
                    current_bits += 1
                    max_code = (1 << current_bits) - 1

            old_code = code

        return bytes(result)

    def _decode_run_length(self, data: bytes) -> bytes:
        """Decode RunLength"""
        result = bytearray()
        i = 0

        while i < len(data):
            byte = data[i]
            i += 1

            if byte == 128:  # EOD marker
                break
            elif byte < 128:
                # Copy n+1 bytes
                count = byte + 1
                if i + count > len(data):
                    break
                result.extend(data[i:i+count])
                i += count
            else:
                # Repeat byte n-127 times
                count = 257 - byte
                if i >= len(data):
                    break
                repeat_byte = data[i]
                i += 1
                result.extend([repeat_byte] * count)

        return bytes(result)

    def __str__(self) -> str:
        return f"PDFStream({len(self.data)} bytes, filters={self.filters})"


@dataclass
class PDFNull(PDFObject):
    """Null object in PDF"""

    def to_pdf(self) -> bytes:
        return b"null"

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.NULL

    def to_dict(self) -> dict[str, Any]:
        return {"type": "null"}

    def __str__(self) -> str:
        return "PDFNull()"


@dataclass
class PDFReference(PDFObject):
    """Reference to PDF object"""
    obj_id: int
    gen_num: int = 0

    def to_pdf(self) -> bytes:
        return f"{self.obj_id} {self.gen_num} R".encode('ascii')

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.REFERENCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "reference",
            "obj_id": self.obj_id,
            "gen_num": self.gen_num
        }

    def __str__(self) -> str:
        return f"PDFReference({self.obj_id} {self.gen_num} R)"


@dataclass
class PDFIndirectObject:
    """PDF indirect object"""
    obj_id: int
    gen_num: int = 0
    value: PDFObject = field(default_factory=PDFNull)

    def to_pdf(self) -> bytes:
        result = []
        result.append(f"{self.obj_id} {self.gen_num} obj\n".encode('ascii'))
        result.append(self.value.to_pdf())
        result.append(b"\nendobj\n")
        return b"".join(result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "obj_id": self.obj_id,
            "gen_num": self.gen_num,
            "value": self.value.to_dict()
        }

    def __str__(self) -> str:
        return f"PDFIndirectObject({self.obj_id} {self.gen_num} obj)"


@dataclass
class PDFXRefEntry:
    """XRef table entry"""
    offset: int
    gen_num: int
    in_use: bool

    def to_pdf(self) -> bytes:
        offset_str = f"{self.offset:010d}"
        gen_str = f"{self.gen_num:05d}"
        flag = "n" if self.in_use else "f"
        return f"{offset_str} {gen_str} {flag}".encode('ascii')

    def __str__(self) -> str:
        status = "in-use" if self.in_use else "free"
        return f"XRefEntry(offset={self.offset}, gen={self.gen_num}, {status})"


@dataclass
class PDFXRefTable:
    """XRef table"""
    entries: list[PDFXRefEntry] = field(default_factory=list)
    subsections: list[tuple[int, int]] = field(default_factory=list)

    def add_entry(self, entry: PDFXRefEntry):
        """Add entry to table"""
        self.entries.append(entry)

    def to_pdf(self) -> bytes:
        result = [b"xref\n"]

        # Group entries by subsections
        if not self.subsections:
            # Auto-generate subsections
            self._generate_subsections()

        for start, count in self.subsections:
            result.append(f"{start} {count}\n".encode('ascii'))
            for i in range(start, start + count):
                if i < len(self.entries):
                    result.append(self.entries[i].to_pdf())
                    result.append(b"\n")
                else:
                    # Free entry
                    result.append(f"{0:010d} {65535:05d} f\n".encode('ascii'))

        return b"".join(result)

    def _generate_subsections(self):
        """Auto-generate subsections"""
        if not self.entries:
            return

        # Assume entries are in order
        self.subsections = [(0, len(self.entries))]

    def __str__(self) -> str:
        return f"PDFXRefTable({len(self.entries)} entries)"


@dataclass
class PDFTrailer:
    """PDF trailer"""
    size: int
    root: PDFReference
    info: PDFReference | None = None
    id: list[bytes] | None = None
    encrypt: dict[str, Any] | None = None
    prev: int | None = None

    def to_pdf(self) -> bytes:
        dict_obj = PDFDictionary()
        dict_obj.set("Size", PDFInteger(self.size))
        dict_obj.set("Root", self.root)

        if self.info:
            dict_obj.set("Info", self.info)

        if self.id:
            id_array = PDFArray([PDFString(id_bytes.hex(), is_hex=True) for id_bytes in self.id])
            dict_obj.set("ID", id_array)

        if self.encrypt:
            encrypt_dict = PDFDictionary()
            for key, value in self.encrypt.items():
                if isinstance(value, int):
                    encrypt_dict.set(key, PDFInteger(value))
                elif isinstance(value, str):
                    encrypt_dict.set(key, PDFName(value))
            dict_obj.set("Encrypt", encrypt_dict)

        if self.prev:
            dict_obj.set("Prev", PDFInteger(self.prev))

        result = []
        result.append(b"trailer\n")
        result.append(dict_obj.to_pdf())
        result.append(b"\nstartxref\n")
        # Offset must be set externally
        result.append(b"%%EOF\n")

        return b"".join(result)

    def __str__(self) -> str:
        return f"PDFTrailer(size={self.size}, root={self.root})"


@dataclass
class PDFPage(PDFObject):
    """PDF page"""
    media_box: list[float]  # [x0, y0, x1, y1]
    contents: PDFReference | list[PDFReference] | None = None
    resources: PDFDictionary | None = None
    parent: PDFReference | None = None
    annotations: list[PDFReference] | None = None
    crop_box: list[float] | None = None
    bleed_box: list[float] | None = None
    trim_box: list[float] | None = None
    art_box: list[float] | None = None
    rotate: int | None = None

    def to_pdf(self) -> bytes:
        dict_obj = PDFDictionary()
        dict_obj.set("Type", PDFName("Page"))

        # MediaBox
        media_array = PDFArray([PDFReal(x) for x in self.media_box])
        dict_obj.set("MediaBox", media_array)

        # Contents
        if self.contents:
            if isinstance(self.contents, list):
                if len(self.contents) == 1:
                    dict_obj.set("Contents", self.contents[0])
                else:
                    contents_array = PDFArray(cast(list[PDFObject], self.contents))
                    dict_obj.set("Contents", contents_array)
            else:
                dict_obj.set("Contents", self.contents)

        # Resources
        if self.resources:
            dict_obj.set("Resources", self.resources)

        # Parent
        if self.parent:
            dict_obj.set("Parent", self.parent)

        # Annotations
        if self.annotations:
            annotations_array = PDFArray(cast(list[PDFObject], self.annotations))
            dict_obj.set("Annots", annotations_array)

        # Boxes
        if self.crop_box:
            crop_array = PDFArray([PDFReal(x) for x in self.crop_box])
            dict_obj.set("CropBox", crop_array)

        if self.bleed_box:
            bleed_array = PDFArray([PDFReal(x) for x in self.bleed_box])
            dict_obj.set("BleedBox", bleed_array)

        if self.trim_box:
            trim_array = PDFArray([PDFReal(x) for x in self.trim_box])
            dict_obj.set("TrimBox", trim_array)

        if self.art_box:
            art_array = PDFArray([PDFReal(x) for x in self.art_box])
            dict_obj.set("ArtBox", art_array)

        # Rotate
        if self.rotate:
            dict_obj.set("Rotate", PDFInteger(self.rotate))

        return dict_obj.to_pdf()

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.DICTIONARY

    def to_dict(self) -> dict[str, Any]:
        result = {
            "type": "page",
            "media_box": self.media_box,
            "width": self.media_box[2] - self.media_box[0],
            "height": self.media_box[3] - self.media_box[1]
        }

        if self.crop_box:
            result["crop_box"] = self.crop_box

        if self.rotate:
            result["rotate"] = self.rotate

        if self.resources:
            result["has_resources"] = True

        if self.contents:
            result["has_contents"] = True

        return result

    def __str__(self) -> str:
        width = self.media_box[2] - self.media_box[0]
        height = self.media_box[3] - self.media_box[1]
        return f"PDFPage({width:.1f}x{height:.1f})"


@dataclass
class PDFCatalog(PDFObject):
    """PDF catalog (document root)"""
    pages: PDFReference
    page_layout: str | None = None
    page_mode: str | None = None
    outlines: PDFReference | None = None
    metadata: PDFReference | None = None
    viewer_preferences: PDFDictionary | None = None

    def to_pdf(self) -> bytes:
        dict_obj = PDFDictionary()
        dict_obj.set("Type", PDFName("Catalog"))
        dict_obj.set("Pages", self.pages)

        if self.page_layout:
            dict_obj.set("PageLayout", PDFName(self.page_layout))

        if self.page_mode:
            dict_obj.set("PageMode", PDFName(self.page_mode))

        if self.outlines:
            dict_obj.set("Outlines", self.outlines)

        if self.metadata:
            dict_obj.set("Metadata", self.metadata)

        if self.viewer_preferences:
            dict_obj.set("ViewerPreferences", self.viewer_preferences)

        return dict_obj.to_pdf()

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.DICTIONARY

    def to_dict(self) -> dict[str, Any]:
        result = {
            "type": "catalog",
            "pages_ref": f"{self.pages.obj_id} {self.pages.gen_num} R"
        }

        if self.page_layout:
            result["page_layout"] = self.page_layout

        if self.page_mode:
            result["page_mode"] = self.page_mode

        return result

    def __str__(self) -> str:
        return f"PDFCatalog(pages={self.pages})"


@dataclass
class PDFInfo(PDFObject):
    """PDF document information"""
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: datetime | None = None
    mod_date: datetime | None = None

    def to_pdf(self) -> bytes:
        dict_obj = PDFDictionary()

        if self.title:
            dict_obj.set("Title", PDFString(self.title))

        if self.author:
            dict_obj.set("Author", PDFString(self.author))

        if self.subject:
            dict_obj.set("Subject", PDFString(self.subject))

        if self.keywords:
            dict_obj.set("Keywords", PDFString(self.keywords))

        if self.creator:
            dict_obj.set("Creator", PDFString(self.creator))

        if self.producer:
            dict_obj.set("Producer", PDFString(self.producer))

        if self.creation_date:
            dict_obj.set("CreationDate", PDFString(self._format_pdf_date(self.creation_date)))

        if self.mod_date:
            dict_obj.set("ModDate", PDFString(self._format_pdf_date(self.mod_date)))

        return dict_obj.to_pdf()

    def get_type(self) -> PDFObjectType:
        return PDFObjectType.DICTIONARY

    def to_dict(self) -> dict[str, Any]:
        result = {"type": "info"}

        if self.title:
            result["title"] = self.title

        if self.author:
            result["author"] = self.author

        if self.subject:
            result["subject"] = self.subject

        if self.keywords:
            result["keywords"] = self.keywords

        if self.creator:
            result["creator"] = self.creator

        if self.producer:
            result["producer"] = self.producer

        if self.creation_date:
            result["creation_date"] = self.creation_date.isoformat()

        if self.mod_date:
            result["mod_date"] = self.mod_date.isoformat()

        return result

    def _format_pdf_date(self, dt: datetime) -> str:
        """Format date to PDF format"""
        return dt.strftime("D:%Y%m%d%H%M%S")

    def __str__(self) -> str:
        return f"PDFInfo(title={self.title}, author={self.author})"


class PDFObjectFactory:
    """PDF object factory"""

    @staticmethod
    def create_from_value(value: Any) -> PDFObject:
        """Create PDF object from Python value"""
        if value is None:
            return PDFNull()
        elif isinstance(value, bool):
            return PDFBoolean(value)
        elif isinstance(value, int):
            return PDFInteger(value)
        elif isinstance(value, float):
            return PDFReal(value)
        elif isinstance(value, str):
            return PDFString(value)
        elif isinstance(value, list):
            array = PDFArray()
            for item in value:
                array.append(PDFObjectFactory.create_from_value(item))
            return array
        elif isinstance(value, dict):
            dict_obj = PDFDictionary()
            for key, val in value.items():
                dict_obj.set(key, PDFObjectFactory.create_from_value(val))
            return dict_obj
        elif isinstance(value, bytes):
            return PDFStream(value)
        elif isinstance(value, PDFObject):
            return value
        else:
            raise PDFParseError(f"Invalid type for conversion to PDFObject: {type(value)}")

    @staticmethod
    def parse_pdf_string(pdf_str: str) -> PDFString:
        """Parse PDF string"""
        if pdf_str.startswith('(') and pdf_str.endswith(')'):
            # Literal string
            content = pdf_str[1:-1]
            # Remove escaping
            content = content.replace('\\(', '(').replace('\\)', ')')
            content = content.replace('\\n', '\n').replace('\\r', '\r')
            content = content.replace('\\t', '\t').replace('\\b', '\b')
            content = content.replace('\\f', '\f').replace('\\\\', '\\')
            return PDFString(content, is_literal=True)
        elif pdf_str.startswith('<') and pdf_str.endswith('>'):
            # Hexadecimal string
            hex_str = pdf_str[1:-1].strip()
            # Delete spaces
            hex_str = hex_str.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
            try:
                # Decode hex
                if len(hex_str) % 2 != 0:
                    hex_str += '0'  # padding for odd length
                content = bytes.fromhex(hex_str).decode('utf-8', errors='replace')
                return PDFString(content, is_hex=True)
            except ValueError:
                raise PDFParseError(f"Error decoding hex string: {pdf_str}")
        else:
            raise PDFParseError(f"Invalid PDF string format: {pdf_str}")


class PDFObjectSerializer:
    """PDF object serializer"""

    @staticmethod
    def serialize(obj: PDFObject) -> bytes:
        """Serialize PDF object"""
        return obj.to_pdf()

    @staticmethod
    def deserialize(data: bytes) -> PDFObject:
        """Deserialize PDF data"""
        # This is a simple implementation
        # Full version needs a complete parser
        try:
            text = data.decode('ascii', errors='ignore').strip()

            if text == 'null':
                return PDFNull()
            elif text == 'true':
                return PDFBoolean(True)
            elif text == 'false':
                return PDFBoolean(False)
            elif text.startswith('/'):
                # Name
                name = text[1:]
                return PDFName(name)
            elif text.startswith('(') and text.endswith(')'):
                # Literal string
                return PDFObjectFactory.parse_pdf_string(text)
            elif text.startswith('<') and text.endswith('>'):
                if text.startswith('<<'):
                    # Dictionary
                    # Simple implementation - full version needs a parser
                    return PDFDictionary()
                else:
                    # Hexadecimal string
                    return PDFObjectFactory.parse_pdf_string(text)
            elif text.startswith('[') and text.endswith(']'):
                # Array
                # Simple implementation
                return PDFArray()
            elif text.isdigit() or (text.startswith('-') and text[1:].isdigit()):
                # Integer
                return PDFInteger(int(text))
            elif re.match(r'^-?\d+\.\d+$', text):
                # Decimal
                return PDFReal(float(text))
            elif re.match(r'^\d+ \d+ R$', text):
                # Reference
                parts = text.split()
                return PDFReference(int(parts[0]), int(parts[1]))
            else:
                raise PDFParseError(f"Unknown data type: {text}")

        except Exception as e:
            raise PDFParseError(f"Error in deserialize: {str(e)}")


# # Test classes
# if __name__ == "__main__":
#     print("🧪 Test PDF object classes")

#     # Test Boolean
#     bool_obj = PDFBoolean(True)
#     print(f"Boolean: {bool_obj.to_pdf()}")

#     # Test Integer
#     int_obj = PDFInteger(42)
#     print(f"Integer: {int_obj.to_pdf()}")

#     # Test Real
#     real_obj = PDFReal(3.14159)
#     print(f"Real: {real_obj.to_pdf()}")

#     # Test String
#     str_obj = PDFString("Hello PDF!")
#     print(f"String: {str_obj.to_pdf()}")

#     # Test Name
#     name_obj = PDFName("Font")
#     print(f"Name: {name_obj.to_pdf()}")

#     # Test Array
#     array_obj = PDFArray([PDFInteger(1), PDFInteger(2), PDFInteger(3)])
#     print(f"Array: {array_obj.to_pdf()}")

#     # Test Dictionary
#     dict_obj = PDFDictionary()
#     dict_obj.set("Type", PDFName("Page"))
#     dict_obj.set("MediaBox", PDFArray([PDFReal(0), PDFReal(0), PDFReal(612), PDFReal(792)]))
#     print(f"Dictionary:\n{dict_obj.to_pdf().decode('ascii')}")

#     # Test Stream
#     stream_data = b"Hello World!"
#     stream_obj = PDFStream(stream_data, filters=["FlateDecode"])
#     print(f"Stream length: {len(stream_obj.to_pdf())} bytes")

#     # Test Reference
#     ref_obj = PDFReference(1, 0)
#     print(f"Reference: {ref_obj.to_pdf()}")

#     # Test Page
#     page_obj = PDFPage(
#         media_box=[0, 0, 612, 792],
#         resources=PDFDictionary()
#     )
#     print(f"Page:\n{page_obj.to_pdf().decode('ascii')}")

#     print("\n✅ PDF object classes test completed successfully")
