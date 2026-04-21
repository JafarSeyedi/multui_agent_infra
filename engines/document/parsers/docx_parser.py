# from __future__ import annotations

# import io
# import base64
# from typing import Any, Dict, List, Optional

# from docx import Document as WordDocument
# from docx.text.run import Run
# from docx.table import Table

# from engines.document.models.base import DocumentFormat, BaseDocument, DocumentElement, ElementType
# from .base import BaseDocumentParser
# from .models import ParseOptions


# class DocxParser(BaseDocumentParser):

#     name = "docx"
#     supported_extensions = (".docx",)

#     async def parse_bytes(
#         self,
#         data: bytes,
#         document_id: str,
#         source_name: str,
#         metadata: Optional[Dict[str, Any]] = None,
#         options: Optional[ParseOptions] = None,
#     ) -> BaseDocument:
#         try:
#             doc = WordDocument(io.BytesIO(data))
#         except Exception as exc:
#             raise RuntimeError(f"Failed to read DOCX data: {exc}") from exc

#         elements: List[DocumentElement] = []
#         text_parts: List[str] = []

#         # ----------------------------------------------------------------------
#         # Parse paragraphs (heading, lists, text, math)
#         # ----------------------------------------------------------------------
#         for index, paragraph in enumerate(doc.paragraphs):
#             if not paragraph.text.strip() and not paragraph.runs:
#                 continue

#             style_name = paragraph.style.name if paragraph.style else ""
#             element_type, level, list_type = self._detect_paragraph_type(style_name)

#             text = paragraph.text.strip()
#             if not text:
#                 continue

#             meta = {
#                 "style": style_name,
#                 "level": level,
#             }

#             # extract richtext spans
#             spans = self._extract_spans(paragraph)
#             if spans:
#                 meta["spans"] = spans

#             if list_type:
#                 meta["list_type"] = list_type

#             elements.append(
#                 DocumentElement(
#                     element_id=f"{document_id}:paragraph:{index}",
#                     element_type=element_type,
#                     text=text,
#                     metadata=meta,
#                 )
#             )
#             text_parts.append(text)

#         # ----------------------------------------------------------------------
#         # Parse tables
#         # ----------------------------------------------------------------------
#         if options is None or getattr(options, "extract_tables", True):
#             for t_index, table in enumerate(doc.tables):
#                 tbl_data = self._extract_table_data(table)
#                 if not tbl_data:
#                     continue

#                 tbl_meta = {
#                     "rows": len(tbl_data),
#                     "cols": len(tbl_data[0]) if tbl_data else 0,
#                     "data": tbl_data,
#                 }

#                 table_text = "\n".join(
#                     [" | ".join(row) for row in tbl_data]
#                 ).strip()

#                 elements.append(
#                     DocumentElement(
#                         element_id=f"{document_id}:table:{t_index}",
#                         element_type=ElementType.TABLE,
#                         text=table_text,
#                         metadata=tbl_meta,
#                     )
#                 )
#                 text_parts.append(table_text)

#         # ----------------------------------------------------------------------
#         # Check for images/embedded objects
#         # ----------------------------------------------------------------------
#         if options is None or getattr(options, "extract_images", True):
#             img_index = 0
#             for rel in doc.part.rels.values():
#                 if "image" in rel.reltype:
#                     try:
#                         img_data = rel.target_part.blob
#                         b64 = base64.b64encode(img_data).decode("utf-8")
#                         elements.append(
#                             DocumentElement(
#                                 element_id=f"{document_id}:image:{img_index}",
#                                 element_type=ElementType.IMAGE,
#                                 text="EmbeddedImage",
#                                 metadata={
#                                     "data": b64,
#                                     "format": rel.target_ref.split(".")[-1],
#                                 },
#                             )
#                         )
#                         img_index += 1
#                     except Exception:
#                         continue

#         # ----------------------------------------------------------------------
#         # Collect document title and finalize BaseDocument
#         # ----------------------------------------------------------------------
#         title = source_name.rsplit(".", 1)[0]
#         return BaseDocument(
#             document_id=document_id,
#             title=title,
#             source_name=source_name,
#             text="\n\n".join(text_parts),
#             format=DocumentFormat.DOCX,
#             elements=elements,
#             metadata=metadata or {},
#         )

#     # --------------------------------------------------------------------------
#     # Internal helpers
#     # --------------------------------------------------------------------------
#     def _detect_paragraph_type(self, style_name: str):
#         """
#         Detect paragraph type based on style naming conventions.
#         """
#         style_lower = style_name.lower()

#         if style_lower.startswith("heading"):
#             try:
#                 level = int(style_lower.replace("heading", "").strip())
#             except ValueError:
#                 level = 1
#             return ElementType.HEADING, level, None

#         if "list bullet" in style_lower:
#             return ElementType.LIST_ITEM, None, "bullet"

#         if "list number" in style_lower or "numbered" in style_lower:
#             return ElementType.LIST_ITEM, None, "number"

#         if "math" in style_lower:
#             return ElementType.MATH, None, None

#         return ElementType.TEXT, None, None

#     def _extract_spans(self, paragraph) -> List[Dict[str, Any]]:
#         spans: List[Dict[str, Any]] = []
#         current_index = 0

#         for run in paragraph.runs:
#             if not run.text:
#                 continue

#             text_len = len(run.text)
#             span = {
#                 "start": current_index,
#                 "end": current_index + text_len,
#             }

#             # styling flags
#             if run.bold:
#                 span["bold"] = True
#             if run.italic:
#                 span["italic"] = True
#             if run.underline in (True, 1):
#                 span["underline"] = True
#             if run.strike:
#                 span["strike"] = True

#             color = getattr(run.font.color, "rgb", None)
#             if color:
#                 span["color"] = f"#{str(color)}"

#             if run.font.size:
#                 span["size"] = run.font.size.pt

#             font_name = run.font.name
#             if font_name and "consolas" in font_name.lower():
#                 span["code"] = True

#             spans.append(span)
#             current_index += text_len

#         return spans

#     def _extract_table_data(self, table: Table) -> List[List[str]]:
#         rows: List[List[str]] = []
#         for row in table.rows:
#             rdata: List[str] = []
#             for cell in row.cells:
#                 txt = cell.text.strip()
#                 rdata.append(txt)
#             if any(rdata):
#                 rows.append(rdata)
#         return rows
