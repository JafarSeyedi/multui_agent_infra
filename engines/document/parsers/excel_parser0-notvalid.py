# # engines/document/parsers/excel.py

# from __future__ import annotations

# from typing import Any, Dict, Iterable, Sequence, Optional
# from pathlib import Path
# from abc import ABC
# import io
# import zipfile
# import xml.etree.ElementTree as ET

# from .base import BaseDocumentParser
# from engines.document.models.base import (
#     # این ایمپورت‌ها را با توجه به ساختار واقعی پروژه تنظیم کن
#     Workbook,
#     Worksheet,
#     Relationship,
#     RelationshipCollection,
#     WorkbookProperties,
#     # ممکن است تعریف BaseDocument / ParseOptions در ماژول دیگری باشد
#     BaseDocument,
#     ParseOptions,
# )


# # در صورت نیاز به namespace map
# # در Excel XML معمولا:
# # - workbook: http://schemas.openxmlformats.org/spreadsheetml/2006/main
# # - relationships: http://schemas.openxmlformats.org/package/2006/relationships
# NS = {
#     "wb": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
#     "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
# }


# class ExcelParser(BaseDocumentParser):
#     """
#     Parser برای فایل‌های Excel (XLSX) که خروجی آن یک Workbook مدل‌شده
#     بر اساس esdm_models.py است.
#     """

#     name: str = "excel"
#     supported_extensions: Sequence[str] = (".xlsx",)

# async def parse_bytes(
#     self,
#     data: bytes,
#     document_id: str,
#     source_name: str,
#     metadata: Dict[str, Any] | None = None,
#     options: ParseOptions | None = None,
# ) -> BaseDocument:

#     import io
#     import zipfile
#     import xml.etree.ElementTree as ET
#     from engines.document.models.base import BaseDocument

#     metadata = metadata or {}

#     with zipfile.ZipFile(io.BytesIO(data)) as zf:

#         # ------------------------------------------------------------------
#         # 1) Package-level Relationships  (_rels/.rels)
#         # ------------------------------------------------------------------
#         package_rels = self._parse_package_relationships(zf)

#         # ------------------------------------------------------------------
#         # 2) Locate Workbook Path
#         # ------------------------------------------------------------------
#         workbook_path = self._find_main_workbook_path(package_rels)
#         if not workbook_path or workbook_path not in zf.namelist():
#             raise ValueError("Main workbook.xml not found in XLSX package.")

#         # ------------------------------------------------------------------
#         # 3) Workbook-level Relationships  (xl/_rels/workbook.xml.rels)
#         # ------------------------------------------------------------------
#         workbook_rels_path = self._rels_path_for(workbook_path)
#         workbook_rels = self._parse_part_relationships(zf, workbook_rels_path)

#         # ------------------------------------------------------------------
#         # 4) Parse workbook.xml → Workbook model (properties + sheets)
#         # ------------------------------------------------------------------
#         workbook = self._parse_workbook_core(
#             zf=zf,
#             workbook_path=workbook_path,
#             workbook_rels=workbook_rels,
#             document_id=document_id,
#             source_name=source_name,
#         )

#         # ------------------------------------------------------------------
#         # 5) Parse Shared Strings
#         # ------------------------------------------------------------------
#         shared_strings_path = None
#         for rel in workbook_rels.relationships:
#             if "sharedStrings" in rel.type:
#                 shared_strings_path = self._resolve_workbook_relative_target(rel.target)
#                 break

#         workbook.shared_strings = self._parse_shared_strings(zf, shared_strings_path)

#         # ------------------------------------------------------------------
#         # 6) Parse Styles (NumberFormats, Fonts, Fills, CellXfs)
#         # ------------------------------------------------------------------
#         styles_path = None
#         for rel in workbook_rels.relationships:
#             if "styles" in rel.type:
#                 styles_path = self._resolve_workbook_relative_target(rel.target)
#                 break

#         styles = self._parse_styles(zf, styles_path)
#         workbook.number_formats = styles["number_formats"]
#         workbook.fonts = styles["fonts"]
#         workbook.fills = styles["fills"]
#         workbook.cell_xfs = styles["cell_xfs"]

#         # ------------------------------------------------------------------
#         # 7) Parse Worksheets (content + extended features)
#         # ------------------------------------------------------------------
#         for ws_model in workbook.sheets:
#             if not ws_model.path or ws_model.path not in zf.namelist():
#                 continue

#             sheet_xml = zf.read(ws_model.path)
#             sheet_root = ET.fromstring(sheet_xml)

#             # ---- 7.1 Parse main worksheet content (cells, rows, dims, merges...)
#             self._parse_worksheet_content(
#                 zf=zf,
#                 sheet_path=ws_model.path,
#                 ws_model=ws_model,
#                 sheet_root=sheet_root,
#             )

#             # ---- 7.2 Hyperlinks
#             ws_model.hyperlinks = self._parse_sheet_hyperlinks(
#                 zf, ws_model.path, sheet_root
#             )

#             # ---- 7.3 AutoFilter
#             ws_model.auto_filter = self._parse_auto_filter(sheet_root)

#             # ---- 7.4 Data Validations
#             ws_model.data_validations = self._parse_data_validations(sheet_root)

#             # ---- 7.5 Conditional Formatting
#             ws_model.conditional_formatting = self._parse_conditional_formatting(
#                 sheet_root
#             )

#             # ---- 7.6 Tables (ListObjects)
#             ws_model.tables = self._parse_tables(zf, ws_model.path, sheet_root)

#             # ---- 7.7 Drawings (Images)
#             ws_model.images = self._parse_drawings(zf, ws_model.path, sheet_root)

#             # ---- 7.8 Charts
#             # Drawings may contain charts
#             for img in ws_model.images:
#                 if img.path and img.path.endswith(".xml"):
#                     ws_model.charts.extend(self._parse_charts(zf, img.path))

#         # ------------------------------------------------------------------
#         # 8) Final Style Application
#         # ------------------------------------------------------------------
#         self._apply_styles_to_workbook(workbook)

#         # ------------------------------------------------------------------
#         # 9) Wrap into BaseDocument
#         # ------------------------------------------------------------------
#         return BaseDocument(
#             id=document_id,
#             source_name=source_name,
#             content=workbook,
#             metadata=metadata,
#         )

#     # ------------------------------------------------------------------
#     # ۱) Relationships helpers
#     # ------------------------------------------------------------------

#     def _parse_package_relationships(
#         self, zf: zipfile.ZipFile
#     ) -> RelationshipCollection:
#         """
#         فایل `_rels/.rels` را می‌خواند و روابط سطح پکیج (مثل Main Workbook) را برمی‌گرداند.
#         """
#         rels_path = "_rels/.rels"
#         if rels_path not in zf.namelist():
#             return RelationshipCollection(relationships=[])

#         data = zf.read(rels_path)
#         root = ET.fromstring(data)

#         relationships: list[Relationship] = []
#         for rel_el in root.findall("rel:Relationship", NS):
#             r_id = rel_el.get("Id")
#             r_type = rel_el.get("Type")
#             target = rel_el.get("Target")
#             if not (r_id and r_type and target):
#                 continue

#             relationships.append(
#                 Relationship(
#                     id=r_id,
#                     type=r_type,
#                     target=target,
#                     # اگر در مدل Relationship فیلدهای دیگری (target_mode و ...) داری، اضافه کن
#                 )
#             )

#         return RelationshipCollection(relationships=relationships)

#     def _parse_part_relationships(
#         self,
#         zf: zipfile.ZipFile,
#         rels_path: str,
#     ) -> RelationshipCollection:
#         """
#         یک part خاص (مثل `xl/workbook.xml`) را گرفته و فایل روابط مرتبط با آن
#         (مثل `xl/_rels/workbook.xml.rels`) را می‌خواند.
#         """
#         if rels_path not in zf.namelist():
#             return RelationshipCollection(relationships=[])

#         data = zf.read(rels_path)
#         root = ET.fromstring(data)

#         relationships: list[Relationship] = []
#         for rel_el in root.findall("rel:Relationship", NS):
#             r_id = rel_el.get("Id")
#             r_type = rel_el.get("Type")
#             target = rel_el.get("Target")
#             if not (r_id and r_type and target):
#                 continue

#             relationships.append(
#                 Relationship(
#                     id=r_id,
#                     type=r_type,
#                     target=target,
#                     # احتمالاً نیاز به resolve کردن relative target داریم
#                 )
#             )

#         return RelationshipCollection(relationships=relationships)

#     def _rels_path_for(self, part_path: str) -> str:
#         """
#         مسیر فایل روابط یک part را برمی‌گرداند.
#         مثال: `xl/workbook.xml` -> `xl/_rels/workbook.xml.rels`
#         """
#         part = Path(part_path)
#         return str(part.parent / "_rels" / f"{part.name}.rels")

#     def _find_main_workbook_path(
#         self, package_rels: RelationshipCollection
#     ) -> Optional[str]:
#         """
#         از بین روابط package، آن رابطه‌ای که نوعش workbook است را پیدا کرده
#         و target آن را (معمولاً `xl/workbook.xml`) برمی‌گرداند.
#         """
#         # نوع استاندارد workbook:
#         #  "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
#         # ممکن است در مدل RelationshipCollection تو فانکشنی برای فیلتر کردن type داشته باشی، اینجا مستقیم می‌نویسم.
#         MAIN_WB_TYPE = (
#             "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
#         )

#         for rel in package_rels.relationships:
#             if rel.type == MAIN_WB_TYPE:
#                 # target معمولا نسبی است، مثل "xl/workbook.xml"
#                 return rel.target

#         return None

#     # ------------------------------------------------------------------
#     # ۲) Workbook core parsing
#     # ------------------------------------------------------------------

#     def _parse_workbook_core(
#         self,
#         zf: zipfile.ZipFile,
#         workbook_path: str,
#         workbook_rels: RelationshipCollection,
#         document_id: str,
#         source_name: str,
#     ) -> Workbook:
#         """
#         فایل `xl/workbook.xml` را می‌خواند، properties و sheets را پارس می‌کند
#         و یک Workbook با لیست Worksheet (بدون سلول‌ها) برمی‌گرداند.
#         """
#         data = zf.read(workbook_path)
#         root = ET.fromstring(data)

#         # Workbook properties
#         wb_props = self._parse_workbook_properties(root)

#         # Sheets
#         sheets = self._parse_sheets_list(
#             root=root,
#             workbook_rels=workbook_rels,
#         )

#         # ساختن شیء Workbook
#         wb = Workbook(
#             # فرض می‌گیرم این فیلدها در مدل Workbook وجود دارند؛ اگر نام‌شان متفاوت است، تنظیم کن
#             document_id=document_id,
#             source_name=source_name,
#             properties=wb_props,
#             sheets=sheets,
#             relationships=workbook_rels,
#             # shared_strings, styles, named_ranges و ... در پارت بعدی اضافه خواهند شد
#         )
#         return wb

#     def _parse_workbook_properties(self, root: ET.Element) -> WorkbookProperties:
#         """
#         تگ‌های `workbookPr`, `fileVersion`, یا سایر metadataهای سطح workbook را
#         به WorkbookProperties نگاشت می‌کند. این پیاده‌سازی حداقلی است و
#         می‌توان آن را با توجه به فیلدهای موجود در esdm_models.py توسعه داد.
#         """
#         # نمونه: <workbookPr date1904="false" backupFile="false" .../>
#         wb_pr_el = root.find("wb:workbookPr", NS)

#         if wb_pr_el is None:
#             # اگر مدل WorkbookProperties مقدار default دارد، از آن استفاده کن
#             return WorkbookProperties()

#         # چند نمونه از attributeها
#         date1904 = wb_pr_el.get("date1904") == "1" or wb_pr_el.get("date1904") == "true"
#         backup_file = (
#             wb_pr_el.get("backupFile") == "1" or wb_pr_el.get("backupFile") == "true"
#         )

#         # این قسمت را باید با امضای واقعی WorkbookProperties وفق بدهی
#         # مثلا:
#         props = WorkbookProperties(
#             date1904=date1904,
#             backup_file=backup_file,
#             # سایر فیلدها را در صورت وجود اضافه کن
#         )
#         return props

#     def _parse_sheets_list(
#         self,
#         root: ET.Element,
#         workbook_rels: RelationshipCollection,
#     ) -> list[Worksheet]:
#         """
#         تگ `<sheets>` در workbook.xml را خوانده و برای هر sheet یک شیء Worksheet
#         خالی (بدون سلول) می‌سازد. mapping بین sheetId/relationship و مسیر فایل
#         در پارت بعدی برای پارس خود شیت‌ها استفاده می‌شود.
#         """
#         sheets_el = root.find("wb:sheets", NS)
#         if sheets_el is None:
#             return []

#         worksheets: list[Worksheet] = []
#         for sheet_el in sheets_el.findall("wb:sheet", NS):
#             name = sheet_el.get("name") or ""
#             sheet_id = sheet_el.get("sheetId") or ""
#             r_id = sheet_el.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")

#             # پیدا کردن رابطه‌ای که این شیت به آن اشاره می‌کند
#             sheet_target_path = None
#             if r_id:
#                 for rel in workbook_rels.relationships:
#                     if rel.id == r_id:
#                         sheet_target_path = self._resolve_workbook_relative_target(rel.target)
#                         break

#             ws = Worksheet(
#                 name=name,
#                 sheet_id=sheet_id,
#                 path=sheet_target_path,  # برای استفاده در مرحله پارس سلول‌ها
#                 # سایر فیلدها مثل dimensions, rows و ... بعدا پر می‌شوند
#             )
#             worksheets.append(ws)

#         return worksheets

#     def _resolve_workbook_relative_target(self, target: str) -> str:
#         """
#         مسیر target شیت را نسبت به workbook برمی‌گرداند.
#         معمولاً target به شکل 'worksheets/sheet1.xml' است و تحت فولدر 'xl' قرار دارد.
#         اگر workbook_path همیشه 'xl/workbook.xml' باشد، می‌توانیم مستقیم 'xl/' را اضافه کنیم.
#         برای general بودن، می‌توانیم کمی هوشمندانه‌تر عمل کنیم، ولی این نسخه ساده است.
#         """
#         # نسخه ساده: اگر target خودش 'xl/' ندارد، به آن prefix 'xl/' می‌دهیم.
#         if not target.startswith("xl/"):
#             return f"xl/{target}"
#         return target

#     # ------------------------------------------------------------------
#     # PART 2: SharedStrings
#     # ------------------------------------------------------------------

#     def _parse_shared_strings(
#         self,
#         zf: zipfile.ZipFile,
#         shared_strings_path: str | None,
#     ):
#         """
#         SharedStrings.xml را خوانده و SharedStrings مدل esdm_models.py را برمی‌گرداند.
#         """
#         from engines.document.models.base import SharedStrings  # اگر قبلاً import نشده است

#         if not shared_strings_path or shared_strings_path not in zf.namelist():
#             return SharedStrings(strings=[])

#         data = zf.read(shared_strings_path)
#         root = ET.fromstring(data)

#         strings: list[str] = []

#         # iter تا si ها
#         for si in root.findall("wb:si", NS):
#             text = self._extract_text_from_si(si)
#             strings.append(text)

#         return SharedStrings(strings=strings)

#     def _extract_text_from_si(self, si_el: ET.Element) -> str:
#         """
#         استخراج متن از si که ممکن است:
#         - <t> ساده
#         - Rich Text: چندین <r><t>...
#         را شامل شود.
#         """
#         # حالت ساده:
#         t = si_el.find("wb:t", NS)
#         if t is not None:
#             return t.text or ""

#         # حالت rich text:
#         parts = []
#         for r in si_el.findall("wb:r", NS):
#             t_el = r.find("wb:t", NS)
#             if t_el is not None and t_el.text:
#                 parts.append(t_el.text)

#         return "".join(parts)


#     # ------------------------------------------------------------------
#     # PART 2: Styles (NumberFormats, Fonts, Fills)
#     # ------------------------------------------------------------------

#     def _parse_styles(
#         self,
#         zf: zipfile.ZipFile,
#         styles_path: str | None,
#     ) -> dict:
#         """
#         فایل xl/styles.xml را به ساختارهای مدل تبدیل می‌کند:

#         خروجی:
#             {
#                 "number_formats": List[NumberFormat],
#                 "fonts": List[Font],
#                 "fills": List[PatternFill],
#                 "cell_xfs": List[dict],   # پارت ۳ برای نگاشت به سلول‌ها استفاده می‌شود
#             }
#         """

#         from engines.document.models.base.esdm_models import (   # اسم ماژول را با مسیر واقعی خودت هماهنگ کن
#             NumberFormat,
#             Font,
#             FontUnderline,
#             PatternFill,
#             PatternType,
#         )

#         # اگر استایل‌ها اصلاً وجود ندارند، خروجی خالی ولی سازگار برمی‌گردانیم
#         if not styles_path or styles_path not in zf.namelist():
#             return {
#                 "number_formats": [],
#                 "fonts": [],
#                 "fills": [],
#                 "cell_xfs": [],
#             }

#         xml_bytes = zf.read(styles_path)
#         root = ET.fromstring(xml_bytes)

#         # -----------------------
#         # 1) Number Formats
#         # -----------------------
#         number_formats: list[NumberFormat] = []
#         num_fmts_el = root.find("wb:numFmts", NS)
#         if num_fmts_el is not None:
#             for num_fmt_el in num_fmts_el.findall("wb:numFmt", NS):
#                 num_fmt_id_raw = num_fmt_el.get("numFmtId")
#                 fmt_code = num_fmt_el.get("formatCode", "")

#                 if num_fmt_id_raw is None:
#                     continue

#                 try:
#                     num_fmt_id = int(num_fmt_id_raw)
#                 except ValueError:
#                     continue

#                 number_formats.append(
#                     NumberFormat(
#                         id=num_fmt_id,
#                         format_code=fmt_code,
#                     )
#                 )

#         # -----------------------
#         # 2) Fonts
#         # -----------------------
#         fonts: list[Font] = []
#         fonts_el = root.find("wb:fonts", NS)
#         if fonts_el is not None:
#             for font_el in fonts_el.findall("wb:font", NS):
#                 # مقدارهای پیش‌فرض مطابق مدل
#                 name = "Calibri"
#                 size = 11.0
#                 bold = False
#                 italic = False
#                 underline = FontUnderline.NONE
#                 strike = False
#                 color: Optional[str] = None
#                 charset: Optional[int] = None
#                 family: Optional[int] = None
#                 scheme: Optional[str] = None

#                 # name
#                 name_el = font_el.find("wb:name", NS)
#                 if name_el is not None and name_el.get("val") is not None:
#                     name = name_el.get("val")

#                 # size (sz)
#                 size_el = font_el.find("wb:sz", NS)
#                 if size_el is not None and size_el.get("val") is not None:
#                     try:
#                         size = float(size_el.get("val"))
#                     except ValueError:
#                         pass

#                 # bold
#                 if font_el.find("wb:b", NS) is not None:
#                     bold = True

#                 # italic
#                 if font_el.find("wb:i", NS) is not None:
#                     italic = True

#                 # underline
#                 u_el = font_el.find("wb:u", NS)
#                 if u_el is not None:
#                     # اگر attribute نداشت، طبق استاندارد Excel معنای "single" دارد
#                     raw_u = u_el.get("val", "single")
#                     # نگاشت به Enum؛ اگر مقدار ناشناخته بود، NONE
#                     try:
#                         underline = FontUnderline(raw_u)
#                     except ValueError:
#                         underline = FontUnderline.NONE

#                 # strike-through
#                 if font_el.find("wb:strike", NS) is not None:
#                     strike = True

#                 # color – در مدل یک hex string ساده است؛ در XML ترکیب theme/indexed/rgb ممکن است
#                 color_el = font_el.find("wb:color", NS)
#                 if color_el is not None:
#                     # اگر rgb هست، همان را می‌گیریم؛ در غیر این صورت شاید بخواهیم theme/indexed را بعداً map کنیم
#                     if "rgb" in color_el.attrib:
#                         color = color_el.get("rgb")
#                     elif "theme" in color_el.attrib:
#                         # می‌توانیم یک نشانه‌ی ساده ذخیره کنیم؛ ولی چون مدل فقط str است،
#                         # یک رشته‌ی pseudo-کد شده ذخیره می‌کنیم تا اطلاعات از دست نرود.
#                         color = f"theme:{color_el.get('theme')}"
#                     elif "indexed" in color_el.attrib:
#                         color = f"indexed:{color_el.get('indexed')}"

#                 # charset
#                 charset_el = font_el.find("wb:charset", NS)
#                 if charset_el is not None and charset_el.get("val") is not None:
#                     try:
#                         charset = int(charset_el.get("val"))
#                     except ValueError:
#                         pass

#                 # family
#                 family_el = font_el.find("wb:family", NS)
#                 if family_el is not None and family_el.get("val") is not None:
#                     try:
#                         family = int(family_el.get("val"))
#                     except ValueError:
#                         pass

#                 # scheme (minor/major/none)
#                 scheme_el = font_el.find("wb:scheme", NS)
#                 if scheme_el is not None and scheme_el.get("val") is not None:
#                     scheme = scheme_el.get("val")

#                 fonts.append(
#                     Font(
#                         name=name,
#                         size=size,
#                         bold=bold,
#                         italic=italic,
#                         underline=underline,
#                         strike=strike,
#                         color=color,
#                         charset=charset,
#                         family=family,
#                         scheme=scheme,
#                     )
#                 )

#         # -----------------------
#         # 3) Fills (PatternFill)
#         # -----------------------
#         fills: list[PatternFill] = []
#         fills_el = root.find("wb:fills", NS)
#         if fills_el is not None:
#             for fill_el in fills_el.findall("wb:fill", NS):
#                 pattern_type = PatternType.NONE
#                 fg_color: Optional[str] = None
#                 bg_color: Optional[str] = None

#                 pattern_el = fill_el.find("wb:patternFill", NS)
#                 if pattern_el is not None:
#                     raw_pattern = pattern_el.get("patternType", "none")
#                     try:
#                         pattern_type = PatternType(raw_pattern)
#                     except ValueError:
#                         pattern_type = PatternType.NONE

#                     fg_el = pattern_el.find("wb:fgColor", NS)
#                     if fg_el is not None:
#                         # مشابه فونت: rgb اولویت دارد
#                         if "rgb" in fg_el.attrib:
#                             fg_color = fg_el.get("rgb")
#                         elif "theme" in fg_el.attrib:
#                             fg_color = f"theme:{fg_el.get('theme')}"
#                         elif "indexed" in fg_el.attrib:
#                             fg_color = f"indexed:{fg_el.get('indexed')}"

#                     bg_el = pattern_el.find("wb:bgColor", NS)
#                     if bg_el is not None:
#                         if "rgb" in bg_el.attrib:
#                             bg_color = bg_el.get("rgb")
#                         elif "theme" in bg_el.attrib:
#                             bg_color = f"theme:{bg_el.get('theme')}"
#                         elif "indexed" in bg_el.attrib:
#                             bg_color = f"indexed:{bg_el.get('indexed')}"

#                 fills.append(
#                     PatternFill(
#                         pattern_type=pattern_type,
#                         fg_color=fg_color,
#                         bg_color=bg_color,
#                     )
#                 )

#         # -----------------------
#         # 4) Cell XFs (فقط خواندن خام؛ مپ کردن در پارت ۳)
#         # -----------------------
#         cell_xfs: list[dict] = []
#         cell_xfs_el = root.find("wb:cellXfs", NS)
#         if cell_xfs_el is not None:
#             for xf_el in cell_xfs_el.findall("wb:xf", NS):
#                 # در پارت ۳ از این‌ها برای استخراج styleIndex و نگاشت به
#                 # fontId / fillId / numFmtId استفاده می‌کنیم
#                 cell_xfs.append(xf_el.attrib.copy())

#         return {
#             "number_formats": number_formats,
#             "fonts": fonts,
#             "fills": fills,
#             "cell_xfs": cell_xfs,
#         }
#     # ----------------------------------------------------------------------
#     # PART 3: Worksheet Parsing (FULL, SELF-CONTAINED)
#     # ----------------------------------------------------------------------

#     def _parse_worksheet(
#         self,
#         zf: zipfile.ZipFile,
#         sheet_path: str,
#         workbook,
#     ):
#         """
#         فایل sheetX.xml را پارس می‌کند و یک Worksheet مدل esdm_models.py برمی‌گرداند.
#         """

#         from engines.document.models.base.esdm_models import (
#             Worksheet,
#             WorksheetProperties,
#             Row,
#             Cell,
#             MergedCellRange,
#         )

#         xml = zf.read(sheet_path)
#         root = ET.fromstring(xml)

#         # ------------------------
#         # Properties – در منابع اکسل: sheetPr
#         # ------------------------
#         sheet_pr = root.find("wb:sheetPr", NS)
#         props = WorksheetProperties()
#         if sheet_pr is not None:
#             if sheet_pr.get("codeName"):
#                 props.code_name = sheet_pr.get("codeName")

#         # ------------------------
#         # Dimensions – مثل "A1:D20"
#         # ------------------------
#         dimensions = self._parse_sheet_dimensions(root)

#         # ------------------------
#         # Columns – <cols><col .../>
#         # ------------------------
#         columns = self._parse_sheet_cols(root)

#         # ------------------------
#         # Rows + Cells
#         # ------------------------
#         rows_map = self._parse_sheet_rows_and_cells(
#             root,
#             workbook.shared_strings,
#             workbook.number_formats,
#             workbook.fonts,
#             workbook.fills,
#             workbook.cell_xfs,
#         )

#         # ------------------------
#         # MergeCells
#         # ------------------------
#         merges = self._parse_merge_cells(root)

#         ws = Worksheet(
#             name=None,   # در پارت ۱ هنگام ساخت، نام و id داده شده بود؛ اینجا فقط داده‌های داخل sheet را پر می‌کنیم
#             sheet_id=None,
#             properties=props,
#         )
#         ws.dimensions = dimensions
#         ws.columns = columns
#         ws.rows = rows_map
#         ws.merged_cells = merges

#         # Hyperlinks
#         ws.hyperlinks = self._parse_sheet_hyperlinks(zf, sheet_path, root)

#         # AutoFilter
#         ws.auto_filter = self._parse_auto_filter(root)

#         # DataValidations
#         ws.data_validations = self._parse_data_validations(root)

#         # Conditional Formatting
#         ws.conditional_formatting = self._parse_conditional_formatting(root)

#         # Tables
#         ws.tables = self._parse_tables(zf, sheet_path, root)

#         # Images / Drawings
#         ws.images = self._parse_drawings(zf, sheet_path, root)

#         return ws


#     # ----------------------------------------------------------------------
#     # Parse <dimension> A1:D20
#     # ----------------------------------------------------------------------
#     def _parse_sheet_dimensions(self, root):
#         dim_el = root.find("wb:dimension", NS)
#         if dim_el is None:
#             return None
#         ref = dim_el.get("ref")
#         return ref


#     # ----------------------------------------------------------------------
#     # Parse <cols> and <col ... />
#     # ----------------------------------------------------------------------
#     def _parse_sheet_cols(self, root):
#         from engines.document.models.base.esdm_models import Column

#         cols_el = root.find("wb:cols", NS)
#         if cols_el is None:
#             return []

#         columns = []
#         for col_el in cols_el.findall("wb:col", NS):
#             min_c = int(col_el.get("min", "1"))
#             max_c = int(col_el.get("max", "1"))
#             width = col_el.get("width")
#             hidden = col_el.get("hidden") == "1"

#             col = Column(
#                 start=min_c,
#                 end=max_c,
#                 width=float(width) if width else None,
#                 hidden=hidden,
#             )
#             columns.append(col)
#         return columns


#     # ----------------------------------------------------------------------
#     # Parse rows + cells
#     # ----------------------------------------------------------------------
#     def _parse_sheet_rows_and_cells(
#         self,
#         root,
#         shared_strings,
#         number_formats,
#         fonts,
#         fills,
#         cell_xfs,
#     ):
#         from engines.document.models.base.esdm_models import Row, Cell

#         rows_el = root.find("wb:sheetData", NS)
#         if rows_el is None:
#             return {}

#         rows_map = {}  # key = row index, value = Row model

#         for row_el in rows_el.findall("wb:row", NS):
#             r_raw = row_el.get("r")
#             if not r_raw:
#                 continue

#             r = int(r_raw)
#             row_obj = Row(index=r)

#             # ---- cells ----
#             for c_el in row_el.findall("wb:c", NS):
#                 cell_ref = c_el.get("r")
#                 if not cell_ref:
#                     continue

#                 # Style index (xfId)
#                 xf_idx = c_el.get("s")
#                 if xf_idx is not None:
#                     try:
#                         xf_idx = int(xf_idx)
#                     except:
#                         xf_idx = None

#                 # Type: s=shared string, b=bool, n=number, str=formula string, inlineStr
#                 cell_value = self._read_cell_value(
#                     c_el,
#                     shared_strings,
#                 )

#                 cell = Cell(
#                     coordinate=cell_ref,
#                     value=cell_value,
#                 )

#                 # later: style mapping (numFmt, font, fill) – پارت ۴
#                 # فعلاً styleIndex را نگه می‌داریم
#                 cell.style_index = xf_idx

#                 row_obj.cells[cell_ref] = cell

#             rows_map[r] = row_obj

#         return rows_map


#     # ----------------------------------------------------------------------
#     # Read <c> value, with shared strings and inline strings
#     # ----------------------------------------------------------------------
#     def _read_cell_value(self, c_el, shared_strings):
#         t = c_el.get("t")

#         # inline strings
#         if t == "inlineStr":
#             is_el = c_el.find("wb:is", NS)
#             if is_el is not None:
#                 t_el = is_el.find("wb:t", NS)
#                 if t_el is not None:
#                     return t_el.text
#             return None

#         # shared string
#         if t == "s":
#             v_el = c_el.find("wb:v", NS)
#             if v_el is None:
#                 return None
#             try:
#                 idx = int(v_el.text)
#                 return shared_strings.strings[idx] if shared_strings and idx < len(shared_strings.strings) else None
#             except:
#                 return None

#         # boolean
#         if t == "b":
#             v_el = c_el.find("wb:v", NS)
#             if v_el is None:
#                 return None
#             return v_el.text == "1"

#         # formula string "str"
#         if t == "str":
#             v_el = c_el.find("wb:v", NS)
#             return v_el.text if v_el is not None else None

#         # default: numeric or text
#         v_el = c_el.find("wb:v", NS)
#         if v_el is None:
#             return None

#         txt = v_el.text
#         if txt is None:
#             return None

#         # try convert to number
#         try:
#             if "." in txt:
#                 return float(txt)
#             return int(txt)
#         except:
#             return txt


#     # ----------------------------------------------------------------------
#     # Parse merged cells
#     # ----------------------------------------------------------------------
#     def _parse_merge_cells(self, root):
#         from engines.document.models.base.esdm_models import MergedCellRange

#         merge_el = root.find("wb:mergeCells", NS)
#         if merge_el is None:
#             return []

#         merges = []
#         for mc in merge_el.findall("wb:mergeCell", NS):
#             ref = mc.get("ref")
#             if ref:
#                 merges.append(
#                     MergedCellRange(range=ref)
#                 )
#         return merges

#     # ----------------------------------------------------------------------
#     # PART 4: Style Mapping & Cell Enrichment
#     # ----------------------------------------------------------------------

#     def _apply_styles_to_workbook(self, workbook):
#         """
#         این متد پس از پارس کامل شیت‌ها، روی سلول‌ها پیمایش کرده و
#         ایندکس‌های استایل را به اشیاء واقعی (Font, Fill, NumberFormat) تبدیل می‌کند.
#         """
        
#         # دسترسی به لیست‌ها
#         fonts = workbook.fonts
#         fills = workbook.fills
#         num_fmts_map = {nf.id: nf for nf in workbook.number_formats}
        
#         # سلول‌های built-in اکسل (ایندکس‌های پیش‌فرض)
#         # برخی ایندکس‌ها داخلی هستند و در numFmts تعریف نشده‌اند
#         DEFAULT_NUM_FORMATS = {
#             0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00",
#             9: "0%", 10: "0.00%", 11: "0.00E+00", 12: "# ?/?", 14: "mm-dd-yy",
#         }

#         for ws in workbook.worksheets:
#             for r_idx, row in ws.rows.items():
#                 for coord, cell in row.cells.items():
#                     if cell.style_index is None:
#                         continue
                    
#                     xf_idx = cell.style_index
#                     if xf_idx >= len(workbook.cell_xfs):
#                         continue
                        
#                     xf = workbook.cell_xfs[xf_idx]
                    
#                     # 1) Font
#                     font_id = int(xf.get("fontId", 0))
#                     if font_id < len(fonts):
#                         cell.font = fonts[font_id]
                        
#                     # 2) Fill
#                     fill_id = int(xf.get("fillId", 0))
#                     if fill_id < len(fills):
#                         cell.fill = fills[fill_id]
                        
#                     # 3) Number Format
#                     num_fmt_id = int(xf.get("numFmtId", 0))
#                     if num_fmt_id in num_fmts_map:
#                         cell.number_format = num_fmts_map[num_fmt_id]
#                     elif num_fmt_id in DEFAULT_NUM_FORMATS:
#                         from engines.document.models.base.esdm_models import NumberFormat
#                         cell.number_format = NumberFormat(
#                             id=num_fmt_id, 
#                             format_code=DEFAULT_NUM_FORMATS[num_fmt_id]
#                         )

#     def _parse_cell_formulas(self, row_el, row_obj):
#         """
#         این متد برای استخراج فرمول‌ها استفاده می‌شود.
#         می‌توانی این را در پارت ۳ در حلقه سلول‌ها فراخوانی کنی.
#         """
#         for c_el in row_el.findall("wb:c", NS):
#             f_el = c_el.find("wb:f", NS)
#             if f_el is not None:
#                 cell_ref = c_el.get("r")
#                 if cell_ref in row_obj.cells:
#                     row_obj.cells[cell_ref].formula = f_el.text


#     # ----------------------------------------------------------------------
#     # PART 5-A: Parse Hyperlinks
#     # ----------------------------------------------------------------------

#     def _parse_sheet_hyperlinks(self, zf, sheet_path, ws_root):
#         """
#         hyperlink ها معمولاً به صورت <hyperlink ref="A1" r:id="rId5" />
#         و مسیر واقعی در sheetX.xml.rels ذخیره می‌شود.
#         """

#         import os
#         from engines.document.models.base.esdm_models import Hyperlink

#         # مسیر فایل .rels مختص شیت
#         folder = os.path.dirname(sheet_path)
#         rels_path = f"{folder}/_rels/{os.path.basename(sheet_path)}.rels"

#         rels_map = {}

#         if rels_path in zf.namelist():
#             rels_xml = ET.fromstring(zf.read(rels_path))
#             for rel in rels_xml.findall("rel:Relationship", NS_REL):
#                 rId = rel.get("Id")
#                 target = rel.get("Target")
#                 rels_map[rId] = target

#         # حالا hyperlink ها در خود sheet
#         h_container = ws_root.find("wb:hyperlinks", NS)
#         result = []

#         if h_container is not None:
#             for h in h_container.findall("wb:hyperlink", NS):
#                 cell_ref = h.get("ref")
#                 rId = h.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
#                 tooltip = h.get("tooltip")

#                 if rId and rId in rels_map:
#                     target = rels_map[rId]
#                     result.append(Hyperlink(ref=cell_ref, target=target, tooltip=tooltip))

#         return result

#     # ----------------------------------------------------------------------
#     # PART 5-B: Parse AutoFilter
#     # ----------------------------------------------------------------------

#     def _parse_auto_filter(self, ws_root):
#         """
#         AutoFilter معمولاً در <autoFilter ref="A1:D1"> قرار دارد.
#         """
#         from engines.document.models.base.esdm_models import AutoFilter

#         af = ws_root.find("wb:autoFilter", NS)
#         if af is None:
#             return None

#         ref = af.get("ref")
#         if not ref:
#             return None

#         return AutoFilter(ref=ref)

#     # ----------------------------------------------------------------------
#     # PART 5-C: Parse DataValidations
#     # ----------------------------------------------------------------------

#     def _parse_data_validations(self, ws_root):
#         """
#         کل بلوک <dataValidations> را پارس می‌کند.
#         """
#         from engines.document.models.base.esdm_models import DataValidation

#         dv_container = ws_root.find("wb:dataValidations", NS)
#         if dv_container is None:
#             return []

#         result = []

#         for dv_el in dv_container.findall("wb:dataValidation", NS):
#             dv = DataValidation(
#                 sqref=dv_el.get("sqref"),
#                 type=dv_el.get("type"),
#                 operator=dv_el.get("operator"),
#                 allow_blank=dv_el.get("allowBlank") == "1",
#                 show_input_message=dv_el.get("showInputMessage") == "1",
#                 show_error_message=dv_el.get("showErrorMessage") == "1",
#                 prompt_title=dv_el.get("promptTitle"),
#                 prompt=dv_el.get("prompt"),
#                 error_title=dv_el.get("errorTitle"),
#                 error=dv_el.get("error"),
#             )

#             f1 = dv_el.find("wb:formula1", NS)
#             f2 = dv_el.find("wb:formula2", NS)
#             dv.formula1 = f1.text if f1 is not None else None
#             dv.formula2 = f2.text if f2 is not None else None

#             result.append(dv)

#         return result

#     # ----------------------------------------------------------------------
#     # PART 6-A: Conditional Formatting
#     # ----------------------------------------------------------------------

#     def _parse_conditional_formatting(self, ws_root):
#         from engines.document.models.base.esdm_models import ConditionalFormatting, ConditionalRule

#         result = []

#         for cf in ws_root.findall("wb:conditionalFormatting", NS):
#             sqref = cf.get("sqref")
#             rules = []

#             for rule_el in cf.findall("wb:cfRule", NS):
#                 rule = ConditionalRule(
#                     type=rule_el.get("type"),
#                     operator=rule_el.get("operator"),
#                     priority=int(rule_el.get("priority", "0")),
#                 )

#                 formulas = []
#                 for f in rule_el.findall("wb:formula", NS):
#                     formulas.append(f.text)

#                 rule.formulas = formulas
#                 rules.append(rule)

#             result.append(
#                 ConditionalFormatting(
#                     sqref=sqref,
#                     rules=rules
#                 )
#             )

#         return result

#     # ----------------------------------------------------------------------
#     # PART 6-B: Tables (ListObjects)
#     # ----------------------------------------------------------------------

#     def _parse_tables(self, zf, sheet_path, ws_root):
#         import os
#         from engines.document.models.base.esdm_models import Table, TableColumn

#         folder = os.path.dirname(sheet_path)
#         rels_path = f"{folder}/_rels/{os.path.basename(sheet_path)}.rels"

#         table_paths = []

#         if rels_path in zf.namelist():
#             rels_root = ET.fromstring(zf.read(rels_path))
#             for rel in rels_root.findall("rel:Relationship", NS_REL):
#                 if rel.get("Type", "").endswith("/table"):
#                     target = rel.get("Target")
#                     table_paths.append(f"xl/{target.lstrip('/')}")

#         tables = []

#         for tp in table_paths:
#             if tp not in zf.namelist():
#                 continue

#             root = ET.fromstring(zf.read(tp))

#             ref = root.get("ref")
#             name = root.get("name")
#             display_name = root.get("displayName")

#             cols = []
#             cols_el = root.find("wb:tableColumns", NS)
#             if cols_el is not None:
#                 for col_el in cols_el.findall("wb:tableColumn", NS):
#                     cols.append(
#                         TableColumn(
#                             id=int(col_el.get("id")),
#                             name=col_el.get("name"),
#                         )
#                     )

#             tables.append(
#                 Table(
#                     name=name,
#                     display_name=display_name,
#                     ref=ref,
#                     columns=cols,
#                 )
#             )

#         return tables

#     # ----------------------------------------------------------------------
#     # PART 6-C: Drawings (Images)
#     # ----------------------------------------------------------------------

#     def _parse_drawings(self, zf, sheet_path, ws_root):
#         import os
#         from engines.document.models.base.esdm_models import Image

#         drawing_el = ws_root.find("wb:drawing", NS)
#         if drawing_el is None:
#             return []

#         rId = drawing_el.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
#         if not rId:
#             return []

#         folder = os.path.dirname(sheet_path)
#         rels_path = f"{folder}/_rels/{os.path.basename(sheet_path)}.rels"

#         if rels_path not in zf.namelist():
#             return []

#         rels_root = ET.fromstring(zf.read(rels_path))
#         drawing_target = None

#         for rel in rels_root.findall("rel:Relationship", NS_REL):
#             if rel.get("Id") == rId:
#                 drawing_target = f"xl/{rel.get('Target').lstrip('/')}"
#                 break

#         if not drawing_target or drawing_target not in zf.namelist():
#             return []

#         # فعلاً فقط path را نگه می‌داریم (مختصات در پارت پیشرفته‌تر)
#         return [Image(path=drawing_target)]

#     # ----------------------------------------------------------------------
#     # PART 6-D: Charts (Basic Parsing)
#     # ----------------------------------------------------------------------

#     def _parse_charts(self, zf, drawing_path):
#         from engines.document.models.base.esdm_models import Chart

#         if drawing_path not in zf.namelist():
#             return []

#         root = ET.fromstring(zf.read(drawing_path))
#         charts = []

#         for chart_el in root.findall(".//c:chart", NS_CHART):
#             title_el = chart_el.find(".//c:title//a:t", NS_DRAWING)
#             title = title_el.text if title_el is not None else None
#             charts.append(Chart(title=title))

#         return charts


#     def _parse_worksheet_content(
#         self,
#         zf: zipfile.ZipFile,
#         sheet_path: str,
#         ws_model,            # Worksheet مدل مقصد (همان شیء شیتی که باید پر شود)
#         sheet_root: ET.Element,  # روت XML برای xl/worksheets/sheetX.xml
#     ):
#         """
#         محتوای اصلی یک شیت اکسل را پارس می‌کند:
#         - sheetPr (ویژگی‌ها)
#         - dimension (ابعاد)
#         - cols (تعاریف ستون‌ها)
#         - sheetData (ردیف‌ها و سلول‌ها، شامل فرمول)
#         - mergeCells (بازه‌های ادغام)
#         خروجی را در ws_model قرار می‌دهد.
#         """

#         # وارد کردن مدل‌ها (اگر در سطح ماژول import شده‌اند می‌توانید حذف کنید)
#         from engines.document.models.base.esdm_models import (
#             WorksheetProperties,
#             Column,
#             Row,
#             Cell,
#             MergedCellRange,
#             SharedStrings,
#         )

#         # 1) Sheet Properties
#         sheet_pr_el = sheet_root.find("wb:sheetPr", NS)
#         props = WorksheetProperties()
#         if sheet_pr_el is not None:
#             code_name = sheet_pr_el.get("codeName")
#             if code_name:
#                 props.code_name = code_name
#             # در صورت نیاز می‌توانید سایر ویژگی‌ها را اینجا استخراج کنید
#             # مثل outlinePr، pageSetUpPr، tabColor و ...
#         ws_model.properties = props

#         # 2) Dimensions
#         dim_el = sheet_root.find("wb:dimension", NS)
#         ws_model.dimensions = dim_el.get("ref") if dim_el is not None else None

#         # 3) Columns
#         cols_el = sheet_root.find("wb:cols", NS)
#         columns: list[Column] = []
#         if cols_el is not None:
#             for col_el in cols_el.findall("wb:col", NS):
#                 try:
#                     min_c = int(col_el.get("min", "1"))
#                 except ValueError:
#                     min_c = 1
#                 try:
#                     max_c = int(col_el.get("max", "1"))
#                 except ValueError:
#                     max_c = min_c
#                 width_attr = col_el.get("width")
#                 width_val = None
#                 if width_attr is not None:
#                     try:
#                         width_val = float(width_attr)
#                     except ValueError:
#                         width_val = None
#                 hidden = (col_el.get("hidden") == "1")
#                 best_fit = (col_el.get("bestFit") == "1")
#                 custom_width = (col_el.get("customWidth") == "1")

#                 columns.append(
#                     Column(
#                         start=min_c,
#                         end=max_c,
#                         width=width_val,
#                         hidden=hidden,
#                         best_fit=best_fit if hasattr(Column, "best_fit") else None,
#                         custom_width=custom_width if hasattr(Column, "custom_width") else None,
#                     )
#                 )
#         ws_model.columns = columns

#         # 4) Rows & Cells
#         rows_map: dict[int, Row] = {}
#         sheet_data_el = sheet_root.find("wb:sheetData", NS)
#         shared_strings: SharedStrings | None = getattr(ws_model, "shared_strings", None)
#         # اگر shared_strings روی ws_model نبود، از workbook بگیرید:
#         if not shared_strings and hasattr(ws_model, "workbook") and ws_model.workbook:
#             shared_strings = getattr(ws_model.workbook, "shared_strings", None)

#         if sheet_data_el is not None:
#             for row_el in sheet_data_el.findall("wb:row", NS):
#                 # ایندکس ردیف
#                 r_str = row_el.get("r")
#                 if not r_str:
#                     # در عمل، معمولاً اکسل r دارد. اگر نداشت، می‌توان از شمارنده استفاده کرد.
#                     continue
#                 try:
#                     r_idx = int(r_str)
#                 except ValueError:
#                     continue

#                 # ویژگی‌های اختیاری ردیف
#                 ht = row_el.get("ht")
#                 height = None
#                 if ht is not None:
#                     try:
#                         height = float(ht)
#                     except ValueError:
#                         height = None
#                 hidden = (row_el.get("hidden") == "1")
#                 custom_height = (row_el.get("customHeight") == "1")

#                 row_obj = Row(
#                     index=r_idx,
#                     height=height if hasattr(Row, "height") else None,
#                     hidden=hidden if hasattr(Row, "hidden") else None,
#                     custom_height=custom_height if hasattr(Row, "custom_height") else None,
#                     cells={},  # دیکشنری سلول‌ها در این ردیف
#                 )

#                 # سلول‌ها
#                 for c_el in row_el.findall("wb:c", NS):
#                     coord = c_el.get("r")  # مثل "B3"
#                     if not coord:
#                         continue

#                     # نوع داده
#                     cell_type = c_el.get("t")  # s، b، n، str، inlineStr
#                     # استایل
#                     xf_idx = c_el.get("s")
#                     style_index = None
#                     if xf_idx is not None:
#                         try:
#                             style_index = int(xf_idx)
#                         except ValueError:
#                             style_index = None

#                     # مقدار سلول
#                     value = self._read_cell_value(c_el, shared_strings)

#                     # فرمول (اگر وجود دارد)
#                     f_el = c_el.find("wb:f", NS)
#                     formula = f_el.text if f_el is not None else None

#                     # مقدار فرمول (result cache) ممکن است در <v> باشد که همان value خواهد شد
#                     # اگر لازم دارید جدا نگه‌دارید، می‌توانید فیلد دیگری اضافه کنید.

#                     # ایجاد شیء Cell
#                     cell = Cell(
#                         coordinate=coord,
#                         value=value,
#                         type=cell_type if hasattr(Cell, "type") else None,
#                         style_index=style_index,
#                         formula=formula if hasattr(Cell, "formula") else None,
#                     )

#                     # قرار دادن سلول در ردیف
#                     row_obj.cells[coord] = cell

#                 rows_map[r_idx] = row_obj

#         ws_model.rows = rows_map

#         # 5) Merge Cells
#         merges_el = sheet_root.find("wb:mergeCells", NS)
#         merges: list[MergedCellRange] = []
#         if merges_el is not None:
#             for mc_el in merges_el.findall("wb:mergeCell", NS):
#                 ref = mc_el.get("ref")
#                 if ref:
#                     merges.append(MergedCellRange(range=ref))
#         ws_model.merged_cells = merges

#     def _read_cell_value(self, c_el: ET.Element, shared_strings):
#         """
#         خواندن مقدار یک سلول با توجه به نوع آن:
#         - t="s": Shared String
#         - t="b": Boolean
#         - t="str": نتیجه‌ی فرمول به صورت رشته
#         - t="inlineStr": متن درون <is><t>
#         - t=None یا t="n": عددی/متنی به صورت پیش‌فرض
#         """
#         t = c_el.get("t")
#         v_el = c_el.find("wb:v", NS)
#         v_text = v_el.text if v_el is not None else None

#         # inlineStr
#         if t == "inlineStr":
#             is_el = c_el.find("wb:is", NS)
#             if is_el is not None:
#                 t_el = is_el.find("wb:t", NS)
#                 return t_el.text if t_el is not None else None
#             return None

#         # Shared String
#         if t == "s":
#             if v_text is None:
#                 return None
#             try:
#                 idx = int(v_text)
#             except ValueError:
#                 return None
#             if shared_strings and getattr(shared_strings, "strings", None):
#                 if 0 <= idx < len(shared_strings.strings):
#                     return shared_strings.strings[idx]
#             return None

#         # Boolean
#         if t == "b":
#             return v_text == "1"

#         # Formula string result
#         if t == "str":
#             return v_text

#         # Default: عدد یا متن
#         if v_text is None:
#             return None
#         # تلاش برای تبدیل عددی
#         try:
#             # برخی مقادیر علمی یا اعشاری
#             if any(ch in v_text for ch in (".", "e", "E")):
#                 return float(v_text)
#             return int(v_text)
#         except ValueError:
#             return v_text
