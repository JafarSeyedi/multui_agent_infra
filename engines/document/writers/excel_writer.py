# # ============================================================
# # excel_writer.py
# # Phase 1 — Writer Base Framework
# # ============================================================

# import zipfile
# from io import BytesIO
# from dataclasses import dataclass, field


# # ------------------------------------------------------------
# # FileBuffer: an in-memory file representation
# # ------------------------------------------------------------

# @dataclass
# class FileBuffer:
#     path: str
#     content: bytes


# # ------------------------------------------------------------
# # XMLBuilder — A small, deterministic XML generator
# # ------------------------------------------------------------

# class XMLBuilder:
#     def __init__(self, indent="  "):
#         self.indent = indent
#         self.lines = []
#         self.level = 0

#     def start(self, tag, **attrs):
#         a = "".join(f' {k}="{v}"' for k, v in attrs.items() if v is not None)
#         self._write(f"<{tag}{a}>")
#         self.level += 1

#     def end(self, tag):
#         self.level -= 1
#         self._write(f"</{tag}>")

#     def empty(self, tag, **attrs):
#         a = "".join(f' {k}="{v}"' for k, v in attrs.items() if v is not None)
#         self._write(f"<{tag}{a}/>")

#     def text(self, tag, text, **attrs):
#         a = "".join(f' {k}="{v}"' for k, v in attrs.items() if v is not None)
#         if text is None:
#             text = ""
#         self._write(f"<{tag}{a}>{self._escape(text)}</{tag}>")

#     def raw(self, xml_line: str):
#         self._write(xml_line)

#     def _write(self, line):
#         self.lines.append(self.indent * self.level + line)

#     def _escape(self, s: str):
#         return (
#             s.replace("&", "&amp;")
#              .replace("<", "&lt;")
#              .replace(">", "&gt;")
#              .replace('"', "&quot;")
#         )

#     def build(self):
#         header = '<?xml version="1.0" encoding="UTF-8"?>'
#         return (header + "\n" + "\n".join(self.lines)).encode("utf-8")


# # ------------------------------------------------------------
# # ZipWriter — Produces final XLSX structure
# # ------------------------------------------------------------

# class ZipWriter:
#     def __init__(self):
#         self.files: list[FileBuffer] = []

#     def add(self, path: str, content: bytes):
#         self.files.append(FileBuffer(path, content))

#     def save(self, filename: str):
#         with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as z:
#             for fb in self.files:
#                 z.writestr(fb.path, fb.content)

# # ============================================================
# # excel_writer.py (Continued)
# # Phase 2 — Core Writers
# # ============================================================

# # ... (FileBuffer, XMLBuilder, ZipWriter from Phase 1) ...

# # ------------------------------------------------------------
# # XML Namespaces
# # ------------------------------------------------------------
# XSI = "http://www.w3.org/2001/XMLSchema-instance"
# PKG = "http://schemas.openxmlformats.org/package/2006/content-types"
# REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
# WB = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
# TF = "http://schemas.microsoft.com/office/spreadsheetml/2011/derivedFormulas"
# MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"


# # ------------------------------------------------------------
# # Content Types Writer
# # ------------------------------------------------------------

# def write_content_types(zip_writer: ZipWriter):
#     builder = XMLBuilder()
#     builder.start("Types", xmlns=PKG, **{"xsi:schemaLocation": f" {PKG} http://schemas.openxmlformats.org/package/2006/content-types/ContentTypesCore.xsd"})
#     builder.empty("Default", Extension="rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")
#     builder.empty("Default", Extension="xml", ContentType="application/xml")
#     builder.empty("Override", PartName="/xl/workbook.xml", ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml")
#     builder.empty("Override", PartName="/xl/sharedStrings.xml", ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml")
#     builder.empty("Override", PartName="/xl/styles.xml", ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml")
#     builder.empty("Override", PartName="/xl/theme/theme1.xml", ContentType="application/vnd.openxmlformats-officedocument.theme+xml")
#     # Add overrides for each sheet
#     # Add override for worksheet relationships
#     builder.empty("Override", PartName="/xl/_rels/workbook.xml.rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")
#     # Add overrides for worksheet relationships (will be added dynamically)
#     # Add override for calcChain.xml
#     # Add override for chartsheets
#     # Add override for pivotTable
#     builder.end("Types")
#     zip_writer.add("[Content_Types].xml", builder.build())


# # ------------------------------------------------------------
# # Workbook Relationships Writer
# # ------------------------------------------------------------

# def write_workbook_rels(zip_writer: ZipWriter):
#     builder = XMLBuilder()
#     builder.start("Relationships", xmlns=REL)
#     builder.empty("Relationship", Id="rId1", Type=REL + "/spreadsheetml/workbook", Target="workbook.xml")
#     # Add relationships for sheets, calcChain, externalLinks, definedNames etc.
#     builder.end("Relationships")
#     zip_writer.add("xl/_rels/workbook.xml.rels", builder.build())


# # ------------------------------------------------------------
# # Workbook Writer
# # ------------------------------------------------------------

# def write_workbook(zip_writer: ZipWriter, sheets_data: list[dict], defined_names: list[dict], calc_chain_id: Optional[int] = None):
#     builder = XMLBuilder()
#     builder.start("workbook", xmlns=WB, **{"mc:Ignorable": "x14ac", "xmlns:mc": MC, "xmlns:x14ac": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac"})

#     # File Version
#     builder.start("fileVersion", {"appName": "xl", "lastEdited": "7700", "lastPrinted": "4300", "version": "16.04", "buildVersion": "16.0.23401", "universalVersion": "1.174035"})
#     builder.end("fileVersion")

#     # Workbook Protection (optional)
#     # builder.start("workbookPr", ...)
#     # builder.end("workbookPr")

#     # Defined Names
#     if defined_names:
#         builder.start("definedNames")
#         for dn in defined_names:
#             builder.text("definedName", dn.get("name"), localSheetId=dn.get("localSheetId"), hidden=dn.get("hidden"), xlm=dn.get("xlm"), **{"r:id": dn.get("rId")})
#         builder.end("definedNames")

#     # Book Views (optional, usually just one active sheet)
#     builder.start("bookViews")
#     builder.start("workbookView", {"activeTab": "0", "yWindow1": "14700", "xWindow1": "11550", "windowWidth": "27150", "windowHeight": "21210"})
#     builder.end("workbookView")
#     builder.end("bookViews")

#     # Sheets
#     builder.start("sheets")
#     for i, sheet in enumerate(sheets_data):
#         sheet_id = str(i)
#         builder.empty("sheet", name=sheet["name"], sheetId=sheet_id, **{"r:id": f"rId{sheet['rId']}"})
#     builder.end("sheets")

#     # Calc Chain (optional)
#     if calc_chain_id:
#         builder.empty("calcChain", **{"r:id": f"rId{calc_chain_id}"})

#     # External Links (optional)
#     # builder.start("externalReferences")
#     # builder.start("externalBook", id="rIdExternal")
#     # ...
#     # builder.end("externalBook")
#     # builder.end("externalReferences")

#     builder.end("workbook")
#     zip_writer.add("xl/workbook.xml", builder.build())


# # ------------------------------------------------------------
# # Shared Strings Writer
# # ------------------------------------------------------------

# def write_shared_strings(zip_writer: ZipWriter, shared_strings: list[str]):
#     builder = XMLBuilder()
#     builder.start("sst", xmlns=WB, count=str(len(shared_strings)), uniqueCount=str(len(shared_strings)))
#     for s in shared_strings:
#         builder.text("si", s)
#     builder.end("sst")
#     zip_writer.add("xl/sharedStrings.xml", builder.build())


# # ------------------------------------------------------------
# # Styles Writer
# # ------------------------------------------------------------

# def write_styles(zip_writer: ZipWriter):
#     builder = XMLBuilder()
#     builder.start("styleSheet", xmlns=WB, **{"mc:Ignorable": "x14ac", "xmlns:mc": MC, "xmlns:x14ac": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac"})

#     # Number Formats (Empty for now)
#     builder.start("numFmts", count="0")
#     builder.end("numFmts")

#     # Fonts (Default)
#     builder.start("fonts", count="1")
#     builder.start("font")
#     builder.empty("sz", val="11")
#     builder.empty("color", rgb="FF000000")
#     builder.empty("name", val="Calibri")
#     builder.empty("family", val="2")
#     builder.empty("pitchFamily", val="2")
#     builder.empty("charset", val="1")
#     builder.end("font")
#     builder.end("fonts")

#     # Fills (Default)
#     builder.start("fills", count="2")
#     builder.start("fill") # Default fill
#     builder.start("patternFill", patternType="none")
#     builder.end("patternFill")
#     builder.end("fill")
#     builder.start("fill") # Default gray fill
#     builder.start("patternFill", patternType="gray125")
#     builder.end("patternFill")
#     builder.end("fill")
#     builder.end("fills")

#     # Borders (Default)
#     builder.start("borders", count="1")
#     builder.start("border")
#     builder.empty("left", style="none")
#     builder.empty("right", style="none")
#     builder.empty("top", style="none")
#     builder.empty("bottom", style="none")
#     builder.empty("diagonal", style="none")
#     builder.end("border")
#     builder.end("borders")

#     # Cell Style Xfs (Default)
#     builder.start("CellStyleXfs", count="1")
#     builder.empty("xf", numFmtId="0", fontId="0", fillId="0", borderId="0", xfId="0")
#     builder.end("CellStyleXfs")

#     # Cell Xfs (Default)
#     builder.start("cellXfs", count="1")
#     builder.empty("xf", numFmtId="0", fontId="0", fillId="0", borderId="0", xfId="0")
#     builder.end("cellXfs")

#     # Cell Styles (Default)
#     builder.start("cellStyles")
#     builder.start("cellStyle", name="Normal", builtinId="0")
#     builder.empty("xfId", val="0")
#     builder.end("cellStyle")
#     builder.end("cellStyles")

#     # Table Styles (optional)
#     # builder.start("tableStyles", defaultPivotStyle="PivotStyleLight1", defaultTableStyle="TableStyleMedium9")
#     # ...
#     # builder.end("tableStyles")

#     builder.end("styleSheet")
#     zip_writer.add("xl/styles.xml", builder.build())


# # ------------------------------------------------------------
# # Theme Writer
# # ------------------------------------------------------------

# def write_theme(zip_writer: ZipWriter):
#     # This is a very basic theme, often generated by Excel itself.
#     # A full implementation would involve complex XML for colors, fonts, etc.
#     theme_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
# <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
#   <a:themeElements>
#     <a:clrScheme name="Office">
#       <a:dk1>
#         <a:sysClr val="windowText" lastClr="000000"/>
#       </a:dk1>
#       <a:lt1>
#         <a:sysClr val="window" lastClr="FFFFFF"/>
#       </a:lt1>
#       <a:dk2>
#         <a:srgbClr val="44546A"/>
#       </a:dk2>
#       <a:lt2>
#         <a:srgbClr val="E7E6E6"/>
#       </a:lt2>
#       <a:accent1>
#         <a:srgbClr val="4472C4"/>
#       </a:accent1>
#       <a:accent2>
#         <a:srgbClr val="ED7D31"/>
#       </a:accent2>
#       <a:accent3>
#         <a:srgbClr val="A5A5A5"/>
#       </a:accent3>
#       <a:accent4>
#         <a:srgbClr val="FFC000"/>
#       </a:accent4>
#       <a:accent5>
#         <a:srgbClr val="44546A"/>
#       </a:accent5>
#       <a:accent6>
#         <a:srgbClr val="7030A0"/>
#       </a:accent6>
#       <a:hyperlink>
#         <a:srgbClr val="0563C1"/>
#       </a:hyperlink>
#       <a:visitedHyperlink>
#         <a:srgbClr val="954f76"/>
#       </a:visitedHyperlink>
#     </a:clrScheme>
#     <a:fontScheme name="Office">
#       <a:majorFont>
#         <a:latin typeface="Calibri"/>
#         <a:eaTypeface=""/>
#         <a:cs typeface=""/>
#       </a:majorFont>
#       <a:minorFont>
#         <a:latin typeface=""/>
#         <a:eaTypeface=""/>
#         <a:cs typeface=""/>
#       </a:minorFont>
#     </a:fontScheme>
#     <a:fmtScheme name="Office">
#       <a:fillStyleLst>
#         <a:solidFill>
#           <a:schemeClr val="phClr"/>
#         </a:solidFill>
#         <a:gradFill>
#           <a:gsLst>
#             <a:gs pos="0">
#               <a:schemeClr val="phClr"/>
#             </a:gs>
#             <a:gs pos="1">
#               <a:schemeClr val="phClr"/>
#             </a:gs>
#           </a:gsLst>
#           <a:lin val="1800000"/>
#         </a:gradFill>
#         <a:blipFill>
#           <a:srcRect/>
#           <a:stretch>
#             <a:fillRect/>
#           </a:stretch>
#         </a:blipFill>
#       </a:fillStyleLst>
#       <a:lnRefLst>
#         <a:lnRef idx="1">
#           <a:schemeClr val="accent1"/>
#         </a:lnRef>
#         <a:lnRef idx="2">
#           <a:schemeClr val="accent2"/>
#         </a:lnRef>
#         <a:lnRef idx="3">
#           <a:schemeClr val="accent3"/>
#         </a:lnRef>
#         <a:lnRef idx="4">
#           <a:schemeClr val="accent4"/>
#         </a:lnRef>
#         <a:lnRef idx="5">
#           <a:schemeClr val="accent5"/>
#         </a:lnRef>
#         <a:lnRef idx="6">
#           <a:schemeClr val="accent6"/>
#         </a:lnRef>
#       </a:lnRefLst>
#       <a:spAutoFit val="0"/>
#     </a:fmtScheme>
#   </a:themeElements>
#   <a:objectDefaults/>
#   <a:extraClrSchemeLst/>
# </a:theme>
# """
#     zip_writer.add("xl/theme/theme1.xml", theme_xml.encode("utf-8"))


# # ------------------------------------------------------------
# # Root Relationships Writer (_rels/.rels)
# # ------------------------------------------------------------

# def write_root_rels(zip_writer: ZipWriter):
#     builder = XMLBuilder()
#     builder.start("Relationships", xmlns=REL)
#     builder.empty("Relationship", Id="rId1", Type=REL + "/officeDocument", Target="xl/workbook.xml")
#     builder.empty("Relationship", Id="rId2", Type=PKG + "/relationships/.xml", Target="xl/_rels/workbook.xml.rels")
#     # Add relationships for other root level files if needed (e.g., presentation.xml for PPTX)
#     builder.end("Relationships")
#     zip_writer.add("_rels/.rels", builder.build())

# # ============================================================
# # Phase 3 — Worksheet Writers (sheetN.xml + rels)
# # ============================================================

# import re
# from typing import Optional

# # ------------------------------------------------------------
# # Utility: Excel Reference Encoder (A1 notation)
# # ------------------------------------------------------------

# def to_excel_address(row: int, col: int) -> str:
#     # Convert col number to letters
#     letters = ""
#     c = col
#     while c > 0:
#         c, remainder = divmod(c - 1, 26)
#         letters = chr(65 + remainder) + letters
#     return f"{letters}{row}"

# def range_to_excel(start_row, start_col, end_row, end_col):
#     return f"{to_excel_address(start_row, start_col)}:{to_excel_address(end_row, end_col)}"


# # ------------------------------------------------------------
# # Worksheet XML Writer
# # ------------------------------------------------------------

# def write_worksheet(zip_writer: ZipWriter, sheet_id: int, sheet_obj, shared_strings: list[str]):
#     builder = XMLBuilder()

#     builder.start(
#         "worksheet",
#         xmlns=WB,
#         **{
#             "xmlns:r": REL,
#             "xmlns:mc": MC,
#             "mc:Ignorable": "x14ac",
#             "xmlns:x14ac": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac"
#         }
#     )

#     # --- Sheet Properties ---
#     if sheet_obj.properties:
#         builder.start("sheetPr")
#         if sheet_obj.properties.tabColor:
#             builder.empty("tabColor", rgb=sheet_obj.properties.tabColor)
#         builder.end("sheetPr")

#     # --- Dimensions ---
#     if sheet_obj.dimensions:
#         dims = sheet_obj.dimensions
#         dim_ref = range_to_excel(dims.min_row, dims.min_col, dims.max_row, dims.max_col)
#         builder.empty("dimension", ref=dim_ref)

#     # --- Sheet Views (default simple view) ---
#     builder.start("sheetViews")
#     builder.empty("sheetView", workbookViewId="0")
#     builder.end("sheetViews")

#     # --- Sheet Format Properties ---
#     builder.empty("sheetFormatPr", defaultRowHeight="15", baseColWidth="10")

#     # --------------------------------------------------------
#     # Columns (widths, hidden state, styles)
#     # --------------------------------------------------------
#     if sheet_obj.columns:
#         builder.start("cols")
#         for col in sheet_obj.columns:
#             builder.empty(
#                 "col",
#                 min=str(col.index),
#                 max=str(col.index),
#                 width=str(col.width or 8.43),
#                 hidden="1" if col.hidden else None,
#                 style=str(col.style_id) if col.style_id is not None else None,
#                 customWidth="1" if col.width else None
#             )
#         builder.end("cols")

#     # --------------------------------------------------------
#     # Rows + Cells
#     # --------------------------------------------------------
#     builder.start("sheetData")

#     for row in sheet_obj.rows:
#         builder.start(
#             "row",
#             r=str(row.index),
#             hidden="1" if row.hidden else None,
#             ht=str(row.height) if row.height else None,
#             customHeight="1" if row.height else None
#         )
#         for cell in row.cells:
#             write_cell_xml(builder, cell, shared_strings)
#         builder.end("row")

#     builder.end("sheetData")

#     # --------------------------------------------------------
#     # Merge Cells
#     # --------------------------------------------------------
#     if sheet_obj.merged_cells:
#         builder.start("mergeCells", count=str(len(sheet_obj.merged_cells)))
#         for mc in sheet_obj.merged_cells:
#             builder.empty("mergeCell", ref=range_to_excel(mc.start_row, mc.start_col, mc.end_row, mc.end_col))
#         builder.end("mergeCells")

#     # --------------------------------------------------------
#     # Hyperlinks
#     # --------------------------------------------------------
#     if sheet_obj.hyperlinks:
#         builder.start("hyperlinks")
#         for link in sheet_obj.hyperlinks:
#             builder.empty(
#                 "hyperlink",
#                 ref=to_excel_address(link.row, link.col),
#                 rId=f"rId{link.rId}"
#             )
#         builder.end("hyperlinks")

#     # --------------------------------------------------------
#     # Data Validations
#     # --------------------------------------------------------
#     if sheet_obj.data_validations:
#         builder.start("dataValidations", count=str(len(sheet_obj.data_validations)))
#         for dv in sheet_obj.data_validations:
#             builder.start(
#                 "dataValidation",
#                 type=dv.type,
#                 allowBlank="1" if dv.allow_blank else "0",
#                 showInputMessage="1" if dv.show_input else "0",
#                 showErrorMessage="1" if dv.show_error else "0",
#                 sqref=" ".join([range_to_excel(*r) for r in dv.ranges])
#             )
#             if dv.formula1:
#                 builder.text("formula1", dv.formula1)
#             if dv.formula2:
#                 builder.text("formula2", dv.formula2)
#             builder.end("dataValidation")
#         builder.end("dataValidations")

#     # --------------------------------------------------------
#     # Conditional Formatting
#     # --------------------------------------------------------
#     if sheet_obj.conditional_formatting:
#         for cf in sheet_obj.conditional_formatting:
#             builder.start("conditionalFormatting", sqref=cf.sqref)
#             for rule in cf.rules:
#                 builder.start(
#                     "cfRule",
#                     type=rule.type,
#                     dxfId=str(rule.dxfId) if rule.dxfId is not None else None,
#                     priority=str(rule.priority),
#                     operator=rule.operator,
#                     stopIfTrue="1" if rule.stop_if_true else None
#                 )

#                 # Color scale
#                 if rule.color_scale:
#                     builder.start("colorScale")
#                     for v in rule.color_scale.values:
#                         builder.empty("cfvo", type=v.type, val=v.val)
#                     for c in rule.color_scale.colors:
#                         builder.empty("color", rgb=c.rgb)
#                     builder.end("colorScale")

#                 # Data bar
#                 if rule.data_bar:
#                     builder.start("dataBar")
#                     builder.empty("cfvo", type="min")
#                     builder.empty("cfvo", type="max")
#                     builder.empty("color", rgb=rule.data_bar.color)
#                     builder.end("dataBar")

#                 # Icon set
#                 if rule.icon_set:
#                     builder.start("iconSet", iconSet=rule.icon_set.iconSet)
#                     for t in rule.icon_set.thresholds:
#                         builder.empty("cfvo", type=t.type, val=t.val)
#                     builder.end("iconSet")

#                 # Standard formulas
#                 if rule.formula:
#                     builder.text("formula", rule.formula)

#                 builder.end("cfRule")
#             builder.end("conditionalFormatting")

#     # --------------------------------------------------------
#     # AutoFilter
#     # --------------------------------------------------------
#     if sheet_obj.auto_filter:
#         r = sheet_obj.auto_filter.range
#         ref = range_to_excel(r[0], r[1], r[2], r[3])
#         builder.start("autoFilter", ref=ref)
#         builder.end("autoFilter")

#     # --------------------------------------------------------
#     # Page Margins / Page Setup
#     # --------------------------------------------------------
#     if sheet_obj.page_margins:
#         pm = sheet_obj.page_margins
#         builder.empty(
#             "pageMargins",
#             left=str(pm.left), right=str(pm.right),
#             top=str(pm.top), bottom=str(pm.bottom),
#             header=str(pm.header), footer=str(pm.footer)
#         )

#     if sheet_obj.page_setup:
#         ps = sheet_obj.page_setup
#         builder.empty(
#             "pageSetup",
#             paperSize=str(ps.paper_size),
#             orientation=ps.orientation,
#             scale=str(ps.scale) if ps.scale else None,
#             fitToWidth=str(ps.fit_to_width) if ps.fit_to_width else None,
#             fitToHeight=str(ps.fit_to_height) if ps.fit_to_height else None,
#             horizontalDpi=str(ps.hdpi) if ps.hdpi else None,
#             verticalDpi=str(ps.vdpi) if ps.vdpi else None
#         )

#     # --------------------------------------------------------
#     # Finish worksheet
#     # --------------------------------------------------------
#     builder.end("worksheet")

#     zip_writer.add(f"xl/worksheets/sheet{sheet_id}.xml", builder.build())


# # ------------------------------------------------------------
# # Cell Writer
# # ------------------------------------------------------------

# def write_cell_xml(builder: XMLBuilder, cell, shared_strings: list[str]):
#     addr = to_excel_address(cell.row, cell.col)

#     attrs = {"r": addr}

#     if cell.style_id is not None:
#         attrs["s"] = str(cell.style_id)

#     if cell.data_type == "s":  # shared string
#         idx = shared_strings.index(cell.value)
#         attrs["t"] = "s"
#         builder.start("c", **attrs)
#         builder.text("v", str(idx))
#         builder.end("c")

#     elif cell.data_type == "n":  # number
#         builder.start("c", **attrs)
#         builder.text("v", str(cell.value))
#         builder.end("c")

#     elif cell.data_type == "b":  # boolean
#         builder.start("c", t="b", **attrs)
#         builder.text("v", "1" if cell.value else "0")
#         builder.end("c")

#     elif cell.data_type == "str":  # plain inline string
#         builder.start("c", t="inlineStr", **attrs)
#         builder.text("is", cell.value)
#         builder.end("c")

#     elif cell.data_type == "f":  # formula
#         builder.start("c", **attrs)
#         if cell.shared_formula_ref is not None:
#             builder.start("f", t="shared", ref=cell.shared_formula_ref, si=str(cell.shared_formula_id))
#         else:
#             builder.start("f")
#         builder.raw(cell.formula)
#         builder.end("f")
#         if cell.value is not None:
#             builder.text("v", str(cell.value))
#         builder.end("c")

#     else:
#         # Blank cell
#         builder.empty("c", **attrs)


# # ------------------------------------------------------------
# # Worksheet Relationships Writer
# # (sheetN.xml.rels)
# # ------------------------------------------------------------

# def write_worksheet_rels(zip_writer: ZipWriter, sheet_id: int, sheet_obj):
#     builder = XMLBuilder()
#     builder.start("Relationships", xmlns=REL)

#     # Hyperlinks
#     for link in sheet_obj.hyperlinks:
#         builder.empty(
#             "Relationship",
#             Id=f"rId{link.rId}",
#             Type=REL + "/hyperlink",
#             Target=link.target,
#             TargetMode="External"
#         )

#     # Comments (Phase 6)
#     # Tables (Phase 4)
#     # Drawings (charts, shapes) (Phase 5)

#     builder.end("Relationships")

#     zip_writer.add(f"xl/worksheets/_rels/sheet{sheet_id}.xml.rels", builder.build())


# # ============================================================
# # Phase 4 — Table Writers (tableN.xml + sheet rels integration)
# # ============================================================

# def write_table(zip_writer: ZipWriter, table_obj, table_id: int):
#     """
#     Writes xl/tables/tableN.xml
#     """
#     builder = XMLBuilder()

#     ref = range_to_excel(
#         table_obj.range.start_row,
#         table_obj.range.start_col,
#         table_obj.range.end_row,
#         table_obj.range.end_col
#     )

#     builder.start(
#         "table",
#         xmlns=TAB_NS,
#         id=str(table_id),
#         name=table_obj.name,
#         displayName=table_obj.display_name or table_obj.name,
#         ref=ref,
#         totalsRowShown="1" if table_obj.totals_row_shown else "0"
#     )

#     # --------------------------------------------------------
#     # Table Columns
#     # --------------------------------------------------------
#     builder.start("tableColumns", count=str(len(table_obj.columns)))
#     for col in table_obj.columns:
#         builder.start(
#             "tableColumn",
#             id=str(col.id),
#             name=col.name
#         )

#         if col.totals_row_function:
#             builder.empty("totalsRowFunction", **{"": col.totals_row_function})

#         if col.totals_row_label:
#             builder.empty("totalsRowLabel", val=col.totals_row_label)

#         if col.calculated_formula:   # Table formula like: =[Column1] * 2
#             builder.text("calculatedColumnFormula", col.calculated_formula)

#         builder.end("tableColumn")
#     builder.end("tableColumns")

#     # --------------------------------------------------------
#     # AutoFilter
#     # --------------------------------------------------------
#     if table_obj.auto_filter:
#         af = table_obj.auto_filter
#         af_ref = range_to_excel(
#             af.range.start_row, af.range.start_col,
#             af.range.end_row, af.range.end_col
#         )
#         builder.start("autoFilter", ref=af_ref)

#         for fcol in af.filter_columns:
#             builder.start("filterColumn", colId=str(fcol.col_id))

#             if fcol.filters:
#                 builder.start("filters", "blank=\"1\"" if fcol.filters.allow_blank else None)
#                 for f in fcol.filters.values:
#                     builder.empty("filter", val=f)
#                 builder.end("filters")

#             if fcol.custom_filters:
#                 builder.start("customFilters", "and=\"1\"" if fcol.custom_filters.and_mode else "0")
#                 for cf in fcol.custom_filters.filters:
#                     builder.empty(
#                         "customFilter",
#                         operator=cf.operator,
#                         val=cf.val
#                     )
#                 builder.end("customFilters")

#             if fcol.dynamic_filter:
#                 builder.empty(
#                     "dynamicFilter",
#                     type=fcol.dynamic_filter.type
#                 )

#             builder.end("filterColumn")

#         builder.end("autoFilter")

#     # --------------------------------------------------------
#     # Table Style
#     # --------------------------------------------------------
#     if table_obj.style:
#         s = table_obj.style
#         builder.empty(
#             "tableStyleInfo",
#             name=s.name,
#             showFirstColumn="1" if s.show_first_column else "0",
#             showLastColumn="1" if s.show_last_column else "0",
#             showRowStripes="1" if s.show_row_stripes else "0",
#             showColumnStripes="1" if s.show_column_stripes else "0"
#         )

#     builder.end("table")

#     # Save file
#     zip_writer.add(f"xl/tables/table{table_id}.xml", builder.build())


# # ============================================================
# # Worksheet integration for tables
# # ============================================================

# def write_worksheet_tables(builder: XMLBuilder, sheet_obj):
#     """Injects <tableParts> into sheetN.xml"""
#     if not sheet_obj.tables:
#         return

#     builder.start("tableParts", count=str(len(sheet_obj.tables)))
#     for t in sheet_obj.tables:
#         builder.empty("tablePart", rId=f"rId{t.rId}")
#     builder.end("tableParts")


# # ============================================================
# # Add table relationships to sheetN.xml.rels
# # ============================================================

# def write_table_rels(builder: XMLBuilder, sheet_obj):
#     for t in sheet_obj.tables:
#         builder.empty(
#             "Relationship",
#             Id=f"rId{t.rId}",
#             Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table",
#             Target=f"../tables/table{t.internal_id}.xml"
#         )

# # ============================================================
# # Phase 5 — Formula Writer + Calculation Chain + ExternalLinks
# # ============================================================

# # -----------------------------------------
# # Write formula tag <f> for a cell
# # -----------------------------------------
# def write_formula(builder: XMLBuilder, cell):
#     """
#     Writes <f> tag inside <c>.
#     Supports:
#       - shared formulas
#       - normal formulas
#       - array formulas
#     """

#     # Shared formula
#     if cell.shared_formula_id is not None:
#         attrs = {"t": "shared", "si": str(cell.shared_formula_id)}
#         if cell.shared_formula_ref:
#             attrs["ref"] = cell.shared_formula_ref

#         builder.start("f", **attrs)
#         builder.raw(cell.formula)
#         builder.end("f")
#         return

#     # Array formula
#     if cell.is_array_formula:
#         builder.start("f", t="array", ref=cell.array_range)
#         builder.raw(cell.formula)
#         builder.end("f")
#         return

#     # Normal formula
#     builder.start("f")
#     builder.raw(cell.formula)
#     builder.end("f")


# # -----------------------------------------
# # Replace in Phase 3 Cell Writer
# # -----------------------------------------

# def write_cell_xml(builder: XMLBuilder, cell, shared_strings):
#     address = to_excel_address(cell.row, cell.col)
#     attrs = {"r": address}

#     if cell.style_id is not None:
#         attrs["s"] = str(cell.style_id)

#     # Formula cell
#     if cell.data_type == "f":
#         builder.start("c", **attrs)
#         write_formula(builder, cell)
#         if cell.value is not None:
#             builder.text("v", str(cell.value))
#         builder.end("c")
#         return

#     # Shared string
#     if cell.data_type == "s":
#         idx = shared_strings.index(cell.value)
#         attrs["t"] = "s"
#         builder.start("c", **attrs)
#         builder.text("v", str(idx))
#         builder.end("c")
#         return

#     # Number
#     if cell.data_type == "n":
#         builder.start("c", **attrs)
#         builder.text("v", str(cell.value))
#         builder.end("c")
#         return

#     # Boolean
#     if cell.data_type == "b":
#         builder.start("c", t="b", **attrs)
#         builder.text("v", "1" if cell.value else "0")
#         builder.end("c")
#         return

#     # Inline string
#     if cell.data_type == "str":
#         builder.start("c", t="inlineStr", **attrs)
#         builder.text("is", cell.value)
#         builder.end("c")
#         return

#     # Blank
#     builder.empty("c", **attrs)


# # ============================================================
# # Calculation Chain (calcChain.xml)
# # ============================================================

# def write_calc_chain(zip_writer: ZipWriter, workbook):
#     """
#     Build calcChain.xml based on the order of formula cells in sheets.
#     """
#     builder = XMLBuilder()
#     builder.start("calcChain", xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main")

#     chain_index = 1

#     for sheet_index, sheet in enumerate(workbook.sheets, start=1):
#         for row in sheet.rows:
#             for cell in row.cells:
#                 if cell.data_type == "f":
#                     addr = to_excel_address(cell.row, cell.col)

#                     attrs = {"r": addr, "i": str(sheet_index)}

#                     # Shared formula master gets "s"
#                     if cell.shared_formula_id is not None and cell.shared_formula_ref:
#                         attrs["s"] = "1"

#                     builder.empty("c", **attrs)

#     builder.end("calcChain")

#     # Only add calcChain if there are formulas
#     zip_writer.add("xl/calcChain.xml", builder.build())


# # ============================================================
# # External Links Writer
# # ============================================================

# def write_external_links(zip_writer: ZipWriter, workbook):
#     """
#     Writes externalLinkN.xml files for references to external workbooks.
#     """
#     counter = 1

#     for link in workbook.external_links:
#         builder = XMLBuilder()
#         builder.start("externalLink", xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main")
#         builder.start("externalBook", id=str(counter))

#         for sheet in link.sheets:
#             builder.empty("sheetName", val=sheet)

#         builder.end("externalBook")
#         builder.end("externalLink")

#         zip_writer.add(f"xl/externalLinks/externalLink{counter}.xml", builder.build())
#         counter += 1


# # ============================================================
# # Workbook.rels modification for external links
# # ============================================================

# def write_external_links_rels(builder: XMLBuilder, workbook):
#     counter = 1
#     for _link in workbook.external_links:
#         builder.empty(
#             "Relationship",
#             Id=f"rId_ext_{counter}",
#             Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink",
#             Target=f"externalLinks/externalLink{counter}.xml"
#         )
#         counter += 1


# # ============================================================
# # Phase 6 — Comments (Legacy & Threaded) + Drawings + Images
# # ============================================================

# # ------------------------------------------------------------
# # 6.1 — Legacy Comments (The classic yellow notes)
# # ------------------------------------------------------------
# def write_comments(zip_writer: ZipWriter, sheet_obj, sheet_id: int):
#     """Writes xl/commentsN.xml"""
#     if not sheet_obj.comments:
#         return

#     builder = XMLBuilder()
#     builder.start("comments", xmlns=MAIN_NS)
    
#     # 1. Authors
#     authors = list(set(c.author for c in sheet_obj.comments))
#     builder.start("authors")
#     for author in authors:
#         builder.text("author", author)
#     builder.end("authors")

#     # 2. Comment List
#     builder.start("commentList")
#     for comment in sheet_obj.comments:
#         ref = to_excel_address(comment.row, comment.col)
#         author_id = authors.index(comment.author)
        
#         builder.start("comment", ref=ref, authorId=str(author_id))
#         builder.start("text")
#         builder.start("r")
#         builder.text("t", comment.text)
#         builder.end("r")
#         builder.end("text")
#         builder.end("comment")
#     builder.end("commentList")
    
#     builder.end("comments")
#     zip_writer.add(f"xl/comments{sheet_id}.xml", builder.build())

# def write_vml_drawing(zip_writer: ZipWriter, sheet_obj, sheet_id: int):
#     """
#     Writes xl/drawings/vmlDrawingN.vml (Legacy format for comments)
#     This is a non-standard XML format.
#     """
#     if not sheet_obj.comments:
#         return

#     # VML namespaces are unique
#     vml = [
#         '<xml xmlns:v="urn:schemas-microsoft-com:vml" ',
#         'xmlns:o="urn:schemas-microsoft-com:office:office" ',
#         'xmlns:x="urn:schemas-microsoft-com:office:excel">'
#     ]
    
#     # Shape Layout
#     vml.append('<o:shapelayout v:ext="edit"><o:idmap v:ext="edit" data="1"/></o:shapelayout>')
    
#     # Shape Template
#     vml.append('<v:shapetype id="_x0000_t202" coordsize="21600,21600" o:spt="202" path="m,l,21600r21600,l21600,xe">')
#     vml.append('<v:stroke joinstyle="miter"/><v:path gradientshapeok="t" o:connecttype="rect"/></v:shapetype>')

#     for i, comment in enumerate(sheet_obj.comments, start=1):
#         ref = to_excel_address(comment.row, comment.col)
#         # VML needs specific positioning logic
#         vml.append(f'<v:shape id="_x0000_s{i}" type="#_x0000_t202" ')
#         vml.append('style="position:absolute; margin-left:59.25pt;margin-top:1.5pt;width:108pt;height:59.25pt;z-index:1;visibility:hidden" ')
#         vml.append('fillcolor="#ffffe1" o:insetmode="auto">')
#         vml.append('<v:fill color2="#ffffe1"/><v:shadow on="t" color="black" obscured="t"/>')
#         vml.append('<v:path o:connecttype="none"/><v:textbox style="mso-direction-alt:auto">')
#         vml.append('<div style="text-align:left"></div></v:textbox>')
#         vml.append('<x:ClientData ObjectType="Note">')
#         vml.append(f'<x:MoveWithCells/><x:SizeWithCells/><x:Anchor>1, 15, 0, 2, 3, 15, 3, 16</x:Anchor>')
#         vml.append(f'<x:AutoFill>False</x:AutoFill><x:Row>{comment.row - 1}</x:Row><x:Column>{comment.col - 1}</x:Column>')
#         vml.append('</x:ClientData></v:shape>')

#     vml.append('</xml>')
#     zip_writer.add(f"xl/drawings/vmlDrawing{sheet_id}.vml", "".join(vml))


# # ------------------------------------------------------------
# # 6.2 — Threaded Comments (Modern O365 Comments)
# # ------------------------------------------------------------
# def write_threaded_comments(zip_writer: ZipWriter, sheet_obj, sheet_id: int):
#     """Writes xl/threadedComments/threadedCommentN.xml"""
#     if not sheet_obj.threaded_comments:
#         return

#     builder = XMLBuilder()
#     builder.start("ThreadedComments", xmlns=MAIN_NS, xmlns_pg="http://schemas.microsoft.com/office/spreadsheetml/2018/threadedcomments")
    
#     for tc in sheet_obj.threaded_comments:
#         builder.start(
#             "threadedComment", 
#             ref=to_excel_address(tc.row, tc.col),
#             authorId=tc.author_id,
#             id=tc.id,
#             parentId=tc.parent_id if tc.parent_id else None
#         )
#         builder.text("text", tc.text)
#         builder.end("threadedComment")
        
#     builder.end("ThreadedComments")
#     zip_writer.add(f"xl/threadedComments/threadedComment{sheet_id}.xml", builder.build())


# # ------------------------------------------------------------
# # 6.3 — Drawings (Images and Shapes)
# # ------------------------------------------------------------
# def write_drawing_xml(zip_writer: ZipWriter, sheet_obj, drawing_id: int):
#     """Writes xl/drawings/drawingN.xml"""
#     if not sheet_obj.drawings:
#         return

#     builder = XMLBuilder()
#     # Drawings use multiple complex namespaces
#     NS_DRW = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
#     NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    
#     builder.start("xdr:wsDr", xmlns_xdr=NS_DRW, xmlns_a=NS_A)
    
#     for i, drw in enumerate(sheet_obj.drawings, start=1):
#         # Anchor (Positioning)
#         builder.start("xdr:twoCellAnchor")
        
#         # From/To cells
#         for pos in ["from", "to"]:
#             anchor = getattr(drw, pos)
#             builder.start(f"xdr:{pos}")
#             builder.text("xdr:col", str(anchor.col - 1))
#             builder.text("xdr:colOff", str(anchor.col_off))
#             builder.text("xdr:row", str(anchor.row - 1))
#             builder.text("xdr:rowOff", str(anchor.row_off))
#             builder.end(f"xdr:{pos}")
        
#         # Image (Pic) or Shape
#         if drw.type == "picture":
#             builder.start("xdr:pic")
#             builder.start("xdr:nvPicPr")
#             builder.empty("xdr:cNvPr", id=str(i), name=drw.name)
#             builder.empty("xdr:cNvPicPr")
#             builder.end("xdr:nvPicPr")
            
#             builder.start("xdr:blipFill")
#             builder.empty("a:blip", xmlns_r=REL, **{"r:embed": f"rId{drw.rel_id}"})
#             builder.empty("a:stretch")
#             builder.end("xdr:blipFill")
            
#             builder.start("xdr:spPr")
#             builder.start("a:xfrm")
#             builder.empty("a:off", x="0", y="0")
#             builder.empty("a:ext", cx="0", cy="0")
#             builder.end("a:xfrm")
#             builder.empty("a:prstGeom", prst="rect")
#             builder.end("xdr:spPr")
#             builder.end("xdr:pic")
            
#         builder.empty("xdr:clientData")
#         builder.end("xdr:twoCellAnchor")
        
#     builder.end("xdr:wsDr")
#     zip_writer.add(f"xl/drawings/drawing{drawing_id}.xml", builder.build())



# # ============================================================
# # Phase 7 — Final Packaging & Validation (Full Implementation)
# # ExcelWriter inherited from BaseDocumentWriter
# # ============================================================

# from __future__ import annotations
# import datetime
# from .base import BaseDocumentWriter
# from ..models.base import BaseDocument

# # -----------------------------
# # Assumed existing helpers
# # -----------------------------
# # - XMLBuilder()
# # - ZipWriter()
# # - MAIN_NS, REL
# # - Writer functions from Phase 1..6:
# #     * write_shared_strings()
# #     * write_styles()
# #     * write_workbook()
# #     * write_sheet()
# #     * write_sheet_visuals()
# #     * write_sheet_rels()
# #     * write_persons()
# # -----------------------------


# class ExcelWriter(BaseDocumentWriter):
#     name = "xlsx"
#     supported_extensions = ("xlsx",)

#     def __init__(self):
#         self.creator = "Custom Excel Engine"
#         self.timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

#         self.sheets = []
#         self.shared_strings = []
#         self.persons = []

#         self.zip_writer = ZipWriter()
#         self.workbook_data = {"sheets": [], "defined_names": [], "calc_chain_id": None}
#         self.shared_strings = []
#         self.next_sheet_rId = 1
#         self.next_defined_name_rId = None # Will be determined later if needed
#         self.next_calc_chain_rId = None

#     # ------------------------------------------------------------
#     # 1. [Content_Types].xml
#     # ------------------------------------------------------------
#     def write_content_types(self):
#         builder = XMLBuilder()
#         builder.start("Types", xmlns="http://schemas.openxmlformats.org/package/2006/content-types")

#         # defaults
#         builder.empty("Default", Extension="xml", ContentType="application/xml")
#         builder.empty("Default", Extension="rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")

#         # workbook
#         builder.empty(
#             "Override",
#             PartName="/xl/workbook.xml",
#             ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
#         )

#         # docProps
#         builder.empty("Override", PartName="/docProps/core.xml",
#                       ContentType="application/vnd.openxmlformats-package.core-properties+xml")
#         builder.empty("Override", PartName="/docProps/app.xml",
#                       ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml")

#         # sheets
#         for sheet_id in range(1, len(self.sheets) + 1):
#             builder.empty(
#                 "Override",
#                 PartName=f"/xl/worksheets/sheet{sheet_id}.xml",
#                 ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
#             )

#         # styles
#         builder.empty("Override", PartName="/xl/styles.xml",
#                       ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml")

#         # sharedStrings
#         if self.shared_strings:
#             builder.empty(
#                 "Override",
#                 PartName="/xl/sharedStrings.xml",
#                 ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml",
#             )

#         # visuals: comments, drawings, threaded
#         for sheet_id, s in enumerate(self.sheets, start=1):

#             if s.drawings:
#                 builder.empty(
#                     "Override",
#                     PartName=f"/xl/drawings/drawing{sheet_id}.xml",
#                     ContentType="application/vnd.openxmlformats-officedocument.drawing+xml",
#                 )

#             if s.comments:
#                 builder.empty(
#                     "Override",
#                     PartName=f"/xl/comments{sheet_id}.xml",
#                     ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml",
#                 )
#                 builder.empty(
#                     "Override",
#                     PartName=f"/xl/drawings/vmlDrawing{sheet_id}.vml",
#                     ContentType="application/vnd.openxmlformats-officedocument.vmlDrawing",
#                 )

#             if s.threaded_comments:
#                 builder.empty(
#                     "Override",
#                     PartName=f"/xl/threadedComments/threadedComment{sheet_id}.xml",
#                     ContentType="application/vnd.ms-excel.threadedcomments+xml",
#                 )
#                 builder.empty(
#                     "Override",
#                     PartName="/xl/persons/person.xml",
#                     ContentType="application/vnd.ms-excel.person+xml",
#                 )

#         builder.end("Types")
#         self.zip_writer.add("[Content_Types].xml", builder.build())

#     # ------------------------------------------------------------
#     # 2. _rels/.rels
#     # ------------------------------------------------------------
#     def write_root_rels(self):
#         builder = XMLBuilder()
#         builder.start("Relationships", xmlns=REL)

#         builder.empty(
#             "Relationship",
#             Id="rId1",
#             Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
#             Target="xl/workbook.xml",
#         )
#         builder.empty(
#             "Relationship",
#             Id="rId2",
#             Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
#             Target="docProps/core.xml",
#         )
#         builder.empty(
#             "Relationship",
#             Id="rId3",
#             Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
#             Target="docProps/app.xml",
#         )
#         builder.end("Relationships")
#         self.zip_writer.add("_rels/.rels", builder.build())

#     # ------------------------------------------------------------
#     # 3. xl/_rels/workbook.xml.rels
#     # ------------------------------------------------------------
#     def write_workbook_rels(self):
#         builder = XMLBuilder()
#         builder.start("Relationships", xmlns=REL)

#         # Sheets
#         for i in range(1, len(self.sheets) + 1):
#             builder.empty(
#                 "Relationship",
#                 Id=f"rId{i}",
#                 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
#                 Target=f"worksheets/sheet{i}.xml",
#             )

#         # Styles
#         builder.empty(
#             "Relationship",
#             Id="rId100",
#             Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
#             Target="styles.xml",
#         )

#         # Shared Strings
#         if self.shared_strings:
#             builder.empty(
#                 "Relationship",
#                 Id="rId101",
#                 Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings",
#                 Target="sharedStrings.xml",
#             )

#         # Persons for threaded comments
#         if any(s.threaded_comments for s in self.sheets):
#             builder.empty(
#                 "Relationship",
#                 Id="rId200",
#                 Type="http://schemas.microsoft.com/office/2017/06/relationships/person",
#                 Target="persons/person.xml",
#             )

#         builder.end("Relationships")
#         self.zip_writer.add("xl/_rels/workbook.xml.rels", builder.build())

#     # ------------------------------------------------------------
#     # 4. docProps/core.xml
#     # ------------------------------------------------------------
#     def write_core_props(self):
#         builder = XMLBuilder()
#         builder.start(
#             "cp:coreProperties",
#             xmlns_cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
#             xmlns_dc="http://purl.org/dc/elements/1.1/",
#             xmlns_dcterms="http://purl.org/dc/terms/",
#             xmlns_xsi="http://www.w3.org/2001/XMLSchema-instance",
#         )

#         builder.text("dc:creator", self.creator)
#         builder.text("cp:lastModifiedBy", self.creator)
#         builder.text("dcterms:created", self.timestamp, **{"xsi:type": "dcterms:W3CDTF"})
#         builder.text("dcterms:modified", self.timestamp, **{"xsi:type": "dcterms:W3CDTF"})

#         builder.end("cp:coreProperties")
#         self.zip_writer.add("docProps/core.xml", builder.build())

#     # ------------------------------------------------------------
#     # 5. docProps/app.xml
#     # ------------------------------------------------------------
#     def write_app_props(self):
#         builder = XMLBuilder()
#         builder.start(
#             "Properties",
#             xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
#             xmlns_vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
#         )

#         builder.text("Application", "Custom Excel Engine")
#         builder.text("DocSecurity", "0")
#         builder.text("ScaleCrop", "false")
#         builder.empty("HeadingPairs")
#         builder.empty("TitlesOfParts")

#         builder.end("Properties")
#         self.zip_writer.add("docProps/app.xml", builder.build())

#     # ------------------------------------------------------------
#     # 6. Final Assembly
#     # ------------------------------------------------------------
#     def finalize(self) -> bytes:
#         # Shared Strings
#         self.write_shared_strings()

#         # Styles
#         self.write_styles()

#         # Workbook XML
#         self.write_workbook()
#         self.write_workbook_rels()

#         # Sheets + Visuals + Rels
#         for sheet_id, sheet in enumerate(self.sheets, start=1):
#             self.write_sheet(sheet, sheet_id)
#             self.write_sheet_visuals(sheet, sheet_id)
#             self.write_sheet_rels(sheet, sheet_id)

#         # Threaded comments persons.xml
#         if self.persons:
#             self.write_persons()

#         # Properties
#         self.write_core_props()
#         self.write_app_props()

#         # Root rels & content types
#         self.write_root_rels()
#         self.write_content_types()

#         # Finish ZIP
#         return self.zip_writer.close()

#     # ------------------------------------------------------------
#     # 7. Integration with your system (BaseDocumentWriter)
#     # ------------------------------------------------------------
#     async def write(self, document: BaseDocument) -> bytes:
#         """
#         This is the high-level entry point required by BaseDocumentWriter.
#         Converts BaseDocument -> Sheets -> XLSX binary.
#         """

#         # Convert BaseDocument into our internal sheet model
#         self.sheets = document.sheets
#         self.shared_strings = document.shared_strings
#         self.persons = getattr(document, "persons", [])

#         # Produce XLSX
#         return self.finalize()

#     def write_sheet_visuals(self, sheet, sheet_id):
#         """Main entry for sheet visuals"""
        
#         # 1. Traditional Comments
#         if sheet.comments:
#             write_comments(self.zip_writer, sheet, sheet_id)
#             write_vml_drawing(self.zip_writer, sheet, sheet_id)
            
#         # 2. Threaded Comments
#         if sheet.threaded_comments:
#             write_threaded_comments(self.zip_writer, sheet, sheet_id)
            
#         # 3. Drawings (Images/Charts)
#         if sheet.drawings:
#             write_drawing_xml(self.zip_writer, sheet, sheet_id)

#     def write_sheet_rels(self, sheet, sheet_id):
#         """Update to include new relationships"""
#         rel_builder = XMLBuilder()
#         rel_builder.start("Relationships", xmlns=REL)
        
#         r_id = 1
#         # Hyperlinks (Phase 3)
#         # Tables (Phase 4)
        
#         # Legacy Comments
#         if sheet.comments:
#             rel_builder.empty("Relationship", Id=f"rId{r_id}", 
#                              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
#                              Target=f"../comments{sheet_id}.xml")
#             sheet.comment_rel_id = r_id
#             r_id += 1
            
#             rel_builder.empty("Relationship", Id=f"rId{r_id}", 
#                              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing",
#                              Target=f"../drawings/vmlDrawing{sheet_id}.vml")
#             sheet.vml_rel_id = r_id
#             r_id += 1

#         # Drawings
#         if sheet.drawings:
#             rel_builder.empty("Relationship", Id=f"rId{r_id}", 
#                              Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing",
#                              Target=f"../drawings/drawing{sheet_id}.xml")
#             sheet.drawing_rel_id = r_id
#             r_id += 1
            
#         rel_builder.end("Relationships")
#         self.zip_writer.add(f"xl/worksheets/_rels/sheet{sheet_id}.xml.rels", rel_builder.build())

#     def write(self, workbook):
#         self.prepare_shared_strings(workbook)
#         self.write_workbook_xml(workbook)
#         self.write_workbook_rels(workbook)
#         self.write_shared_strings()
#         self.write_styles()

#         # Phase 4
#         self.write_all_tables(workbook)

#         # Phase 3
#         self.write_all_worksheets(workbook)

#         # Phase 5
#         write_calc_chain(self.zip_writer, workbook)
#         write_external_links(self.zip_writer, workbook)

#         return self.zip_writer.finalize()

#     def write_workbook_rels(self, workbook):
#         builder = XMLBuilder()
#         builder.start("Relationships", xmlns=REL)

#         # existing parts
#         builder.empty("Relationship", Id="rId1", Type=WB_REL, Target="workbook.xml")

#         # add table, hyperlinks, etc (Phase 3/4)
#         write_external_links_rels(builder, workbook)

#         builder.end("Relationships")
#         self.zip_writer.add("xl/_rels/workbook.xml.rels", builder.build())

#     def write_all_tables(self, workbook):
#         """
#         Generates xl/tables/tableN.xml for each table.
#         Assigns tableId and links them with rId in worksheets.
#         """
#         table_counter = 1

#         for sheet in workbook.sheets:
#             for table in sheet.tables:
#                 table.internal_id = table_counter
#                 table_counter += 1
#                 write_table(self.zip_writer, table, table.internal_id)

#     def write_all_worksheets(self, workbook):
#         """
#         Override from Phase 3 → now also inject tables
#         """
#         for sheet in workbook.sheets:
#             sheet_id = sheet.internal_id

#             # --- Build sheetN.xml ---
#             sheet_builder = XMLBuilder()
#             # (we reuse the previous write_worksheet code, but add tableParts injection)
#             write_worksheet(self.zip_writer, sheet_id, sheet, self.shared_strings)

#             # Now we re-open the built XML (from memory) → inject tableParts before </worksheet>
#             # Simpler approach: modify write_worksheet: call write_worksheet_tables(builder, …)
#             # That version is cleaner. You approve earlier.
#             # So the correct version is modifying write_worksheet() directly.

#             # --- Build sheetN.xml.rels ---
#             rel_builder = XMLBuilder()
#             rel_builder.start("Relationships", xmlns=REL)
#             write_hyperlink_rels(rel_builder, sheet)
#             write_table_rels(rel_builder, sheet)
#             rel_builder.end("Relationships")

#             self.zip_writer.add(f"xl/worksheets/_rels/sheet{sheet_id}.xml.rels", rel_builder.build())

#     def add_worksheet(self, sheet_obj):
#         assigned_id = self.next_sheet_rId
#         self.next_sheet_rId += 1
#         self.workbook_data["sheets"].append({"name": sheet_obj.name, "rId": assigned_id})
#         return assigned_id

#     def write_all_worksheets(self, workbook):
#         for sheet in workbook.sheets:
#             sheet_id = sheet.internal_id
#             write_worksheet(self.zip_writer, sheet_id, sheet, self.shared_strings)
#             write_worksheet_rels(self.zip_writer, sheet_id, sheet)

#     def add_sheet(self, name: str, rId: int):
#         self.workbook_data["sheets"].append({"name": name, "rId": rId})

#     def add_shared_string(self, s: str) -> int:
#         # Add string if not present, return its index
#         if s not in self.shared_strings:
#             self.shared_strings.append(s)
#         return self.shared_strings.index(s)

#     def finalize_workbook_rels(self):
#         # Dynamically build relationships for sheets, etc.
#         builder = XMLBuilder()
#         builder.start("Relationships", xmlns=REL)
#         # Add relationship for workbook itself (already done in root_rels, but convention needs this too)
#         builder.empty("Relationship", Id="rId1", Type=REL + "/spreadsheetml/workbook", Target="workbook.xml")

#         # Add relationships for each sheet
#         for sheet_info in self.workbook_data["sheets"]:
#             builder.empty("Relationship", Id=f"rId{sheet_info['rId']}", Type=REL + "/spreadsheetml/worksheet", Target=f"worksheets/sheet{sheet_info['rId']}.xml")

#         # Add relationship for calcChain if it exists
#         if self.next_calc_chain_rId:
#             builder.empty("Relationship", Id=f"rId{self.next_calc_chain_rId}", Type=REL + "/spreadsheetml/calcChain", Target="calcChain.xml")

#         # Add relationships for definedNames if they have external references (rId)
#         # if self.next_defined_name_rId:
#         #     builder.empty("Relationship", Id=f"rId{self.next_defined_name_rId}", Type=REL + "/spreadsheetml/definedNames", Target="definedNames.xml")

#         builder.end("Relationships")
#         self.zip_writer.add("xl/_rels/workbook.xml.rels", builder.build())


#     def generate_xlsx(self, filename: str):
#         # --- Write Core Files ---
#         write_content_types(self.zip_writer)
#         write_root_rels(self.zip_writer)
#         self.finalize_workbook_rels() # Needs sheet info to build correctly
#         write_shared_strings(self.zip_writer, self.shared_strings)
#         write_styles(self.zip_writer)
#         write_theme(self.zip_writer)
#         write_workbook(self.zip_writer, self.workbook_data["sheets"], self.workbook_data["defined_names"], self.next_calc_chain_rId)
#         # Add calcChain.xml if exists (Phase 6)
#         # Add definedNames.xml if exists (Phase 6)

#         # --- Placeholders for future phases ---
#         # Add sheetN.xml and its rels (Phase 3)
#         # Add tableN.xml etc. (Phase 4)
#         # Add pivot files etc. (Phase 5)

#         # --- Save the ZIP file ---
#         self.zip_writer.save(filename)
