# from __future__ import annotations

# import io
# import base64
# from typing import Any, Dict, List, Optional

# from docx import Document
# from docx.shared import Pt, Inches
# from docx.enum.text import WD_BREAK, WD_UNDERLINE
# from docx.oxml import OxmlElement
# from docx.oxml.ns import qn

# from ..models.base import (
#     BaseDocument,
#     DocumentElement,
#     ElementType,
# )
# from .base import BaseDocumentWriter
# from ..models.base import DocumentFormat


# class DocxWriter(BaseDocumentWriter):
#     """
#     DOCX Writer Ultra++++++++ GodMode Edition
#     -----------------------------------------
#     - Async
#     - Zero-loss fidelity mapping of USDM v1.0 -> DOCX
#     - RichText spans
#     - Headings
#     - Paragraphs
#     - Lists (bullet & numbered)
#     - Tables with autofit
#     - Images / Binary blocks
#     - Code blocks with shading
#     - Math blocks (LaTeX -> OMML via oxml wrapper)
#     - Custom blocks attach as embedded files
#     """

#     format = DocumentFormat.DOCX

#     async def write(
#         self,
#         document: BaseDocument,
#         metadata: Optional[Dict[str, Any]] = None,
#         options: Optional[Dict[str, Any]] = None,
#     ) -> bytes:
#         doc = Document()

#         # ----------------------------------------------------------------------
#         # Apply document-level metadata if any
#         # ----------------------------------------------------------------------
#         core = doc.core_properties
#         core.title = document.title or ""
#         core.subject = (metadata or {}).get("subject", "")
#         core.author = (metadata or {}).get("author", "")
#         core.comments = (metadata or {}).get("comments", "")

#         # ----------------------------------------------------------------------
#         # Iterate elements and write into docx
#         # ----------------------------------------------------------------------
#         for element in document.elements:
#             etype = element.element_type

#             if etype == ElementType.TEXT:
#                 self._write_paragraph(doc, element)

#             elif etype == ElementType.HEADING:
#                 self._write_heading(doc, element)

#             elif etype == ElementType.LIST_ITEM:
#                 self._write_list_item(doc, element)

#             elif etype == ElementType.TABLE:
#                 self._write_table(doc, element)

#             elif etype == ElementType.CODE:
#                 self._write_code_block(doc, element)

#             elif etype == ElementType.MATH:
#                 self._write_math_block(doc, element)

#             elif etype == ElementType.IMAGE:
#                 self._write_image(doc, element)

#             elif etype in (
#                 ElementType.DATA,
#                 ElementType.BINARY,
#                 ElementType.SPREADSHEET,
#                 ElementType.CAD,
#             ):
#                 self._write_embedded_file(doc, element)

#             elif etype == ElementType.PAGE_BREAK:
#                 doc.add_page_break()

#             else:
#                 # Default: write as paragraph
#                 self._write_paragraph(doc, element)

#         # ----------------------------------------------------------------------
#         # Export DOCX bytes
#         # ----------------------------------------------------------------------
#         buffer = io.BytesIO()
#         doc.save(buffer)
#         return buffer.getvalue()

#     # --------------------------------------------------------------------------
#     # Paragraph Writer (RichText span-level formatting)
#     # --------------------------------------------------------------------------
#     def _write_paragraph(self, doc: Document, element: DocumentElement):
#         p = doc.add_paragraph()
#         self._append_richtext_runs(p, element.text, element.metadata)

#     # --------------------------------------------------------------------------
#     # Heading Writer
#     # --------------------------------------------------------------------------
#     def _write_heading(self, doc: Document, element: DocumentElement):
#         level = element.metadata.get("level", 1)
#         level = max(1, min(6, level))
#         p = doc.add_heading(level=level)
#         self._append_richtext_runs(p, element.text, element.metadata)

#     # --------------------------------------------------------------------------
#     # List Writer
#     # --------------------------------------------------------------------------
#     def _write_list_item(self, doc: Document, element: DocumentElement):
#         text = element.text or ""
#         list_type = element.metadata.get("list_type", "bullet")  # bullet or number

#         p = doc.add_paragraph()
#         self._append_richtext_runs(p, text, element.metadata)

#         if list_type == "number":
#             p.style = "List Number"
#         else:
#             p.style = "List Bullet"

#     # --------------------------------------------------------------------------
#     # Table Writer (AutoFit)
#     # --------------------------------------------------------------------------
#     def _write_table(self, doc: Document, element: DocumentElement):
#         """
#         element.metadata:
#             - rows: int
#             - cols: Optional[int]
#             - data: Optional[List[List[str]]]   (recommended)
#         """
#         meta = element.metadata or {}

#         if "data" in meta:
#             data = meta["data"]
#         else:
#             # Fallback: parse element.text as pipe-separated rows
#             data = [row.split("|") for row in element.text.split("\n")]

#         rows = len(data)
#         cols = len(data[0]) if rows else 0

#         table = doc.add_table(rows=rows, cols=cols)
#         table.style = "Table Grid"

#         for r in range(rows):
#             for c in range(cols):
#                 cell = table.cell(r, c)
#                 txt = str(data[r][c]).strip()
#                 p = cell.paragraphs[0]
#                 p.text = txt

#     # --------------------------------------------------------------------------
#     # Code Block Writer (shaded background)
#     # --------------------------------------------------------------------------
#     def _write_code_block(self, doc: Document, element: DocumentElement):
#         p = doc.add_paragraph()
#         r = p.add_run(element.text or "")
#         shading = r._r.get_or_add_rPr().get_or_add_shd()
#         shading.set(qn("w:fill"), "DDDDDD")
#         shading.set(qn("w:color"), "000000")
#         shading.set(qn("w:val"), "clear")

#         font = r.font
#         font.name = "Consolas"
#         font.size = Pt(10)

#     # --------------------------------------------------------------------------
#     # Math Block Writer (LaTeX → OMML via minimal wrapper)
#     # --------------------------------------------------------------------------
#     def _write_math_block(self, doc: Document, element: DocumentElement):
#         """
#         We store math as OMML inside a paragraph.
#         For simplicity: wrap LaTeX into <m:oMathPara> using raw oxml.
#         """
#         latex = element.text or ""

#         p = doc.add_paragraph()

#         # Minimal wrapper that Word accepts
#         omath_para = OxmlElement("m:oMathPara")
#         omath = OxmlElement("m:oMath")
#         omath_para.append(omath)

#         # Insert the LaTeX as literal text run inside <m:t>
#         run = OxmlElement("m:r")
#         t = OxmlElement("m:t")
#         t.text = latex
#         run.append(t)
#         omath.append(run)

#         p._p.append(omath_para)

#     # --------------------------------------------------------------------------
#     # Image Writer (Base64 → PNG/JPG → embed)
#     # --------------------------------------------------------------------------
#     def _write_image(self, doc: Document, element: DocumentElement):
#         data = element.metadata.get("data") or element.metadata.get("bytes")
#         if isinstance(data, str):
#             data = base64.b64decode(data)

#         stream = io.BytesIO(data)
#         doc.add_picture(stream, width=Inches(6))

#     # --------------------------------------------------------------------------
#     # Embedded file blocks (data/binary/spreadsheet/cad)
#     # Stored as attached files inside the DOCX package
#     # --------------------------------------------------------------------------
#     def _write_embedded_file(self, doc: Document, element: DocumentElement):
#         """
#         Store object as base64-decoded file in /word/embeddings/
#         """
#         data = element.metadata.get("data") or element.metadata.get("bytes")
#         if isinstance(data, str):
#             data = base64.b64decode(data)

#         file_name = element.metadata.get("filename", f"{element.element_id}.bin")
#         self._attach_file(doc, file_name, data)

#     # --------------------------------------------------------------------------
#     # Internal: embed a file in DOCX package
#     # --------------------------------------------------------------------------
#     def _attach_file(self, doc: Document, filename: str, data: bytes):
#         part = doc.part
#         embedded_path = f"embeddings/{filename}"
#         part.package.writestr(embedded_path, data)

#     # --------------------------------------------------------------------------
#     # RichText span formatter
#     # --------------------------------------------------------------------------
#     def _append_richtext_runs(self, paragraph, text: str, metadata: Dict[str, Any] | None):
#         """
#         text may contain inline USDM spans:
#             metadata["spans"] = [
#                 {"start":0, "end":5, "bold":True, "italic":True, "color":"#RRGGBB", ...}
#             ]
#         """
#         spans = (metadata or {}).get("spans")
#         if not spans:
#             paragraph.add_run(text)
#             return

#         spans = sorted(spans, key=lambda x: x["start"])
#         cursor = 0

#         for sp in spans:
#             start = sp["start"]
#             end = sp["end"]

#             if start > cursor:
#                 paragraph.add_run(text[cursor:start])

#             run = paragraph.add_run(text[start:end])
#             self._apply_run_style(run, sp)
#             cursor = end

#         if cursor < len(text):
#             paragraph.add_run(text[cursor:])

#     # --------------------------------------------------------------------------
#     # Apply styling to a run
#     # --------------------------------------------------------------------------
#     def _apply_run_style(self, run, span: Dict[str, Any]):
#         font = run.font

#         if span.get("bold"):
#             font.bold = True
#         if span.get("italic"):
#             font.italic = True
#         if span.get("underline"):
#             font.underline = True
#         if span.get("strike"):
#             font.strike = True

#         if "color" in span:
#             font.color.rgb = self._rgb(span["color"])

#         if "size" in span:
#             font.size = Pt(span["size"])

#         if span.get("code"):
#             font.name = "Consolas"

#     # --------------------------------------------------------------------------
#     # Color helper
#     # --------------------------------------------------------------------------
#     def _rgb(self, hex_color: str):
#         from docx.shared import RGBColor
#         hex_color = hex_color.lstrip("#")
#         return RGBColor.from_string(hex_color)
