from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ....models.base import BaseDocument
from ....models.usdm_models import USDMDocument
from ..base import BaseDocumentWriter
from ..base import WriteOptions
from .docx_builder import (
    build_comments_xml,
    build_document_xml,
    build_endnotes_xml,
    build_footnotes_xml,
    build_numbering_xml,
    build_styles_xml,
)
from .docx_image_handler import process_images
from .docx_zip_packager import (
    app_properties_xml,
    content_types_xml,
    core_properties_xml,
    custom_properties_xml,
    document_rels_xml,
    minimal_theme_xml,
    package_docx,
    rels_xml,
)


class DOCXWriter(BaseDocumentWriter):
    """
    Writer that converts USDMDocument objects to valid OOXML DOCX format.

    Orchestrates the full DOCX generation pipeline:
    1. Convert USDM to intermediate OOXML parts (XML strings)
    2. Package all parts into a ZIP file (.docx format)
    3. Return the ZIP as bytes

    The generated DOCX conforms to ECMA-376 and ISO/IEC 29500 standards.
    """

    name = "docx"

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)

    def get_supported_media_types(self) -> list[str]:
        """Return supported media types."""
        return ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".docx"]

    async def write(self, document: BaseDocument) -> bytes:
        """
        Convert a USDMDocument to DOCX bytes.

        Orchestrates the full generation pipeline:
        builds all OOXML XML parts, processes images,
        generates relationships, and packages into ZIP.

        Args:
            document: USDMDocument to convert.

        Returns:
            bytes: Valid .docx file content.

        Raises:
            DocumentWriteError: If conversion fails.
        """
        from ....models.exceptions import DocumentWriteError

        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("Document must be a USDMDocument instance")

        try:
            parts = self._build_all_parts(document)
            return package_docx(parts)
        except Exception as e:
            raise DocumentWriteError(f"Failed to write DOCX: {e}") from e

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """
        Write document as a stream of bytes.

        Args:
            document: USDMDocument to convert.

        Yields:
            bytes: The complete DOCX file as a single chunk.
        """
        from ....models.exceptions import DocumentWriteError

        try:
            data = await self.write(document)
            yield data
        except Exception as e:
            raise DocumentWriteError(f"Failed to stream DOCX: {e}") from e

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        """
        Write document to a file.

        Args:
            document: USDMDocument to convert.
            target: Output file path.
            options: Additional write options.
        """
        from ....models.exceptions import DocumentWriteError

        try:
            data = await self.write(document)
            target.write_bytes(data)
        except Exception as e:
            raise DocumentWriteError(f"Failed to write DOCX to file: {e}") from e

    def _build_all_parts(self, document: USDMDocument) -> dict[str, bytes]:
        """
        Build all OOXML parts for the DOCX package.

        Returns a dictionary mapping part names to their byte content.
        """
        parts: dict[str, bytes] = {}

        doc_xml = build_document_xml(document)
        styles_xml = build_styles_xml(document)
        numbering_xml = build_numbering_xml(document)

        image_info = process_images(document)
        images = image_info.get("images", {})
        image_rels = image_info.get("rels", [])

        has_footnotes = any(
            elem.element_type.name == "FOOTNOTE"
            for elem in document.logical_elements
        )
        has_endnotes = any(
            elem.element_type.name == "ENDNOTE"
            for elem in document.logical_elements
        )
        has_comments = any(
            elem.element_type.name == "COMMENT"
            for elem in document.logical_elements
        )

        footnotes_xml = ""
        endnotes_xml = ""
        comments_xml = ""

        if has_footnotes:
            footnotes_xml = build_footnotes_xml(document)
        if has_endnotes:
            endnotes_xml = build_endnotes_xml(document)
        if has_comments:
            comments_xml = build_comments_xml(document)

        core_xml = core_properties_xml(document)
        app_xml = app_properties_xml(document)
        theme_xml = minimal_theme_xml()
        rels = rels_xml()

        doc_rels_list: list[dict[str, str]] = []
        doc_rels_list.append({
            "id": "rId1",
            "type": "styles",
            "target": "styles.xml",
        })
        doc_rels_list.append({
            "id": "rId2",
            "type": "numbering",
            "target": "numbering.xml",
        })
        if has_footnotes:
            doc_rels_list.append({
                "id": "rId3",
                "type": "footnotes",
                "target": "footnotes.xml",
            })
        if has_endnotes:
            doc_rels_list.append({
                "id": "rId4",
                "type": "endnotes",
                "target": "endnotes.xml",
            })
        if has_comments:
            doc_rels_list.append({
                "id": "rId5",
                "type": "comments",
                "target": "comments.xml",
            })

        doc_rels_list.append({
            "id": "rId10",
            "type": "theme",
            "target": "theme/theme1.xml",
        })

        doc_rels_list.extend(image_rels)

        doc_rels_xml = document_rels_xml(doc_rels_list)

        ct_parts: dict[str, Any] = {
            "/word/document.xml": True,
            "/word/styles.xml": True,
            "/word/numbering.xml": True,
            "/word/theme/theme1.xml": True,
            "/docProps/core.xml": True,
            "/docProps/app.xml": True,
        }
        if has_footnotes:
            ct_parts["/word/footnotes.xml"] = True
        if has_endnotes:
            ct_parts["/word/endnotes.xml"] = True
        if has_comments:
            ct_parts["/word/comments.xml"] = True

        metadata = getattr(document, "metadata", {}) or {}
        if metadata.get("custom"):
            ct_parts["/docProps/custom.xml"] = True

        for _, info in images.items():
            ct_parts[f"/word/media/{info['filename']}"] = True

        ct_xml = content_types_xml(ct_parts)

        encoding = "utf-8"
        if self.options and self.options.encoding:
            encoding = self.options.encoding

        parts["[Content_Types].xml"] = ct_xml.encode(encoding)
        parts["_rels/.rels"] = rels.encode(encoding)
        parts["word/document.xml"] = doc_xml.encode(encoding)
        parts["word/styles.xml"] = styles_xml.encode(encoding)
        parts["word/numbering.xml"] = numbering_xml.encode(encoding)
        parts["word/_rels/document.xml.rels"] = doc_rels_xml.encode(encoding)
        parts["word/theme/theme1.xml"] = theme_xml.encode(encoding)
        parts["docProps/core.xml"] = core_xml.encode(encoding)
        parts["docProps/app.xml"] = app_xml.encode(encoding)

        if has_footnotes:
            parts["word/footnotes.xml"] = footnotes_xml.encode(encoding)
        if has_endnotes:
            parts["word/endnotes.xml"] = endnotes_xml.encode(encoding)
        if has_comments:
            parts["word/comments.xml"] = comments_xml.encode(encoding)

        for rel_id, info in images.items():
            parts[f"word/media/{info['filename']}"] = info["data"]

        if metadata.get("custom"):
            custom_xml = custom_properties_xml(metadata["custom"])
            parts["docProps/custom.xml"] = custom_xml.encode(encoding)

        return parts
