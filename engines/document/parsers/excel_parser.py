# from __future__ import annotations

# import io
# from typing import Any, Dict, Optional

# from engines.document.models.base.esdm_models import (
#     Workbook,
#     WorkbookProperties,
#     Worksheet,
#     WorksheetProperties,
#     SheetDimensions,
#     Column,
#     MergedCellRange,
#     NamedRange,
#     Relationship,
#     RelationshipCollection,
#     SharedStrings,
#     HyperlinkCollection,
#     Hyperlink,
#     CommentCollection,
#     CommentText,
#     Table,
#     TableColumn,
#     ExcelTableRow,
#     TableStyleInfo,
#     DefinedNameCollection,
#     DefinedName,
#     DataValidationCollection,
#     DataValidation,
#     DataValidationRule,
#     DataValidationType,
#     DataValidationOperator,
# )
# from engines.document.models.base import DocumentFormat, BaseDocument, DocumentElement, ElementType, DocumentMetadata

# from .base import BaseDocumentParser
# from .models import ParseOptions


# class ExcelParser(BaseDocumentParser):
#     """Excel parser that maps workbook structure into the ESDM workbook model."""

#     name = "excel"
#     supported_extensions = (".xlsx", ".xlsm", ".xltx")

#     async def parse_bytes(
#         self,
#         data: bytes,
#         document_id: str,
#         source_name: str,
#         metadata: Dict[str, Any] | None = None,
#         options: ParseOptions | None = None,
#     ) -> BaseDocument:
#         try:
#             from openpyxl import load_workbook  # type: ignore[import-untyped]
#             from openpyxl.cell.cell import Cell as OpenPyxlCell  # type: ignore[import-untyped]
#             from openpyxl.utils import column_index_from_string  # type: ignore[import-untyped]
#             from openpyxl.utils.cell import range_boundaries  # type: ignore[import-untyped]
#             from openpyxl.worksheet.table import Table as OpenPyxlTable  # type: ignore[import-untyped]
#         except ImportError as exc:
#             raise RuntimeError("openpyxl is required for ExcelParser.") from exc

#         workbook_file = load_workbook(io.BytesIO(data), data_only=False)
#         esdm_workbook = Workbook(
#             properties=WorkbookProperties(
#                 date_1904=getattr(workbook_file, "excel_base_date", "") == "1904",
#                 active_tab=getattr(getattr(workbook_file, "active", None), "_index", 0) or 0,
#             ),
#             shared_strings=SharedStrings(),
#             relationships=RelationshipCollection(),
#         )

#         defined_names = DefinedNameCollection()
#         for defined_name in getattr(workbook_file.defined_names, "definedName", []):
#             defined_names.add(
#                 DefinedName(
#                     name=getattr(defined_name, "name", ""),
#                     formula=getattr(defined_name, "attr_text", ""),
#                     local_sheet_id=getattr(defined_name, "localSheetId", None),
#                     hidden=bool(getattr(defined_name, "hidden", False)),
#                     comment=getattr(defined_name, "comment", None),
#                 )
#             )
#             if getattr(defined_name, "localSheetId", None) is None:
#                 esdm_workbook.named_ranges.append(
#                     NamedRange(name=getattr(defined_name, "name", ""), range=self._reference_to_cell_range(getattr(defined_name, "attr_text", "")))
#                 )

#         for sheet_index, ws in enumerate(workbook_file.worksheets):
#             sheet = Worksheet(
#                 name=ws.title,
#                 properties=WorksheetProperties(
#                     show_gridlines=bool(getattr(getattr(ws, "sheet_view", None), "showGridLines", True)),
#                     show_headings=bool(getattr(getattr(ws, "sheet_view", None), "showRowColHeaders", True)),
#                     tab_color=self._extract_tab_color(ws),
#                 ),
#                 dimensions=SheetDimensions(
#                     min_row=1,
#                     max_row=max(1, ws.max_row),
#                     min_col=1,
#                     max_col=max(1, ws.max_column),
#                 ),
#             )
#             hyperlinks = HyperlinkCollection()
#             comments = CommentCollection()
#             data_validations = DataValidationCollection()
#             tables: list[Table] = []

#             for rel_id, rel in getattr(ws, "_rels", {}).items():
#                 esdm_workbook.relationships.add(
#                     Relationship(
#                         id=str(rel_id),
#                         type=str(getattr(rel, "Type", "worksheet")),
#                         target=str(getattr(rel, "Target", "")),
#                         mode=str(getattr(rel, "TargetMode", "Internal") or "Internal"),
#                     )
#                 )

#             for row_index, row in enumerate(ws.iter_rows(), start=1):
#                 row_model = sheet.get_row(row_index)
#                 row_dim = ws.row_dimensions.get(row_index)
#                 if row_dim is not None:
#                     row_model.height = row_dim.height
#                     row_model.hidden = bool(row_dim.hidden)
#                 for cell in row:
#                     if not isinstance(cell, OpenPyxlCell):
#                         continue
#                     if self._is_empty_cell(cell):
#                         continue
#                     model_cell = sheet.get_cell(cell.row, cell.column)
#                     model_cell.value = cell.value
#                     model_cell.formula = str(cell.value) if cell.data_type == "f" and cell.value is not None else None
#                     model_cell.style_id = getattr(cell, "style_id", None)
#                     if cell.hyperlink is not None:
#                         target = str(getattr(cell.hyperlink, "target", None) or getattr(cell.hyperlink, "location", ""))
#                         model_cell.hyperlink = target
#                         hyperlinks.add(Hyperlink(ref=cell.coordinate, target=target, tooltip=getattr(cell.hyperlink, "tooltip", None), display=getattr(cell.hyperlink, "display", None)))
#                     if cell.comment is not None:
#                         author_id = comments.add_author(cell.comment.author or "Unknown")
#                         comments.add_comment(cell.coordinate, author_id, CommentText.from_string(cell.comment.text or ""))
#                         model_cell.comment = cell.comment.text
#                     if isinstance(cell.value, str):
#                         esdm_workbook.shared_strings.get_index(cell.value)

#             for key, col_dim in ws.column_dimensions.items():
#                 try:
#                     col_index = column_index_from_string(key)
#                 except ValueError:
#                     continue
#                 sheet.columns[col_index] = Column(index=col_index, width=col_dim.width, hidden=bool(col_dim.hidden))

#             for merged in ws.merged_cells.ranges:
#                 min_col, min_row, max_col, max_row = range_boundaries(str(merged))
#                 sheet.merged_cells.append(
#                     MergedCellRange(
#                         min_row=int(min_row or 1),
#                         max_row=int(max_row or 1),
#                         min_col=int(min_col or 1),
#                         max_col=int(max_col or 1),
#                     )
#                 )

#             for table_name, table_obj in getattr(ws, "tables", {}).items():
#                 if not isinstance(table_obj, OpenPyxlTable):
#                     continue
#                 esdm_table = self._build_table(ws, table_obj, range_boundaries)
#                 tables.append(esdm_table)

#             for validation in getattr(getattr(ws, "data_validations", None), "dataValidation", []):
#                 rule = DataValidationRule(
#                     type=self._map_validation_type(getattr(validation, "type", None)),
#                     operator=self._map_validation_operator(getattr(validation, "operator", None)),
#                     allow_blank=bool(getattr(validation, "allowBlank", False)),
#                     show_input_message=bool(getattr(validation, "showInputMessage", False)),
#                     show_error_message=bool(getattr(validation, "showErrorMessage", True)),
#                     error_title=getattr(validation, "errorTitle", None),
#                     error_message=getattr(validation, "error", None),
#                     prompt_title=getattr(validation, "promptTitle", None),
#                     prompt_message=getattr(validation, "prompt", None),
#                     formula1=getattr(validation, "formula1", None),
#                     formula2=getattr(validation, "formula2", None),
#                 )
#                 sqref = str(getattr(validation, "sqref", ""))
#                 if sqref:
#                     data_validations.add(DataValidation(ref=sqref, rule=rule))

#             sheet._meta["hyperlinks"] = hyperlinks
#             sheet._meta["comments"] = comments
#             sheet._meta["tables"] = tables
#             sheet._meta["data_validations"] = data_validations
#             esdm_workbook.sheets.append(sheet)

#         esdm_workbook._meta["defined_names"] = defined_names

#         summary = self._build_summary(esdm_workbook)
#         return BaseDocument(
#             document_id=document_id,
#             title=source_name.rsplit(".", 1)[0],
#             source_name=source_name,
#             format=DocumentFormat.XLSX,
#             text=summary,
#             content=esdm_workbook,
#             metadata=DocumentMetadata(properties=metadata or {}),
#             elements=[
#                 DocumentElement(
#                     element_id=f"{document_id}:workbook",
#                     element_type=ElementType.SPREADSHEET,
#                     text=summary,
#                     content=esdm_workbook,
#                     metadata={"sheet_count": len(esdm_workbook.sheets)},
#                 )
#             ],
#         )

#     def _build_summary(self, workbook: Workbook) -> str:
#         sheet_names = ", ".join(sheet.name for sheet in workbook.sheets)
#         return f"Workbook with {len(workbook.sheets)} sheet(s): {sheet_names}"

#     def _is_empty_cell(self, cell: Any) -> bool:
#         return cell.value is None and getattr(cell, "hyperlink", None) is None and getattr(cell, "comment", None) is None

#     def _extract_tab_color(self, worksheet: Any) -> Optional[str]:
#         color = getattr(getattr(worksheet, "sheet_properties", None), "tabColor", None)
#         rgb = getattr(color, "rgb", None)
#         if isinstance(rgb, str):
#             return rgb
#         return None

#     def _reference_to_cell_range(self, reference: str) -> MergedCellRange:
#         min_row = max_row = min_col = max_col = 1
#         if "!" in reference and ":" in reference:
#             area = reference.split("!", 1)[1].replace("$", "")
#             try:
#                 from openpyxl.utils.cell import range_boundaries  # type: ignore[import-untyped]
#                 bounds = range_boundaries(area)
#                 min_col = int(bounds[0] or 1)
#                 min_row = int(bounds[1] or 1)
#                 max_col = int(bounds[2] or 1)
#                 max_row = int(bounds[3] or 1)
#             except Exception:
#                 pass
#         return MergedCellRange(
#             min_row=int(min_row or 1),
#             max_row=int(max_row or 1),
#             min_col=int(min_col or 1),
#             max_col=int(max_col or 1),
#         )

#     def _build_table(self, worksheet: Any, table_obj: Any, range_boundaries: Any) -> Table:
#         min_col, min_row, max_col, max_row = range_boundaries(str(table_obj.ref))
#         min_col = int(min_col or 1)
#         min_row = int(min_row or 1)
#         max_col = int(max_col or 1)
#         max_row = int(max_row or 1)
#         columns: list[TableColumn] = []
#         header_values = [worksheet.cell(row=min_row, column=col).value for col in range(min_col, max_col + 1)]
#         for index, header in enumerate(header_values, start=1):
#             columns.append(TableColumn(id=index, name=str(header or f"Column{index}")))
#         rows: list[ExcelTableRow] = []
#         for row_number in range(min_row + 1, max_row + 1):
#             table_row = ExcelTableRow(index=row_number)
#             for column_id, col in enumerate(range(min_col, max_col + 1), start=1):
#                 table_row.set_value(column_id, worksheet.cell(row=row_number, column=col).value)
#             rows.append(table_row)
#         style = getattr(table_obj, "tableStyleInfo", None)
#         return Table(
#             id=int(getattr(table_obj, "id", 0) or 0),
#             name=str(getattr(table_obj, "name", "Table")),
#             display_name=getattr(table_obj, "displayName", None),
#             ref=str(getattr(table_obj, "ref", "")),
#             header_row_count=int(getattr(table_obj, "headerRowCount", 1) or 1),
#             totals_row_count=int(getattr(table_obj, "totalsRowCount", 0) or 0),
#             columns=columns,
#             rows=rows,
#             table_style_info=TableStyleInfo(
#                 name=str(getattr(style, "name", "TableStyleMedium9") or "TableStyleMedium9"),
#                 show_first_column=bool(getattr(style, "showFirstColumn", False)) if style is not None else False,
#                 show_last_column=bool(getattr(style, "showLastColumn", False)) if style is not None else False,
#                 show_row_stripes=bool(getattr(style, "showRowStripes", True)) if style is not None else True,
#                 show_column_stripes=bool(getattr(style, "showColumnStripes", False)) if style is not None else False,
#             ),
#         )

#     def _map_validation_type(self, value: Any) -> DataValidationType:
#         mapping = {
#             "whole": DataValidationType.WHOLE,
#             "decimal": DataValidationType.DECIMAL,
#             "list": DataValidationType.LIST,
#             "date": DataValidationType.DATE,
#             "time": DataValidationType.TIME,
#             "textLength": DataValidationType.TEXT_LENGTH,
#             "custom": DataValidationType.CUSTOM,
#         }
#         return mapping.get(str(value), DataValidationType.CUSTOM)

#     def _map_validation_operator(self, value: Any) -> Optional[DataValidationOperator]:
#         if value is None:
#             return None
#         mapping = {
#             "between": DataValidationOperator.BETWEEN,
#             "notBetween": DataValidationOperator.NOT_BETWEEN,
#             "lessThan": DataValidationOperator.LESS_THAN,
#             "greaterThan": DataValidationOperator.GREATER_THAN,
#             "equal": DataValidationOperator.EQUAL,
#             "notEqual": DataValidationOperator.NOT_EQUAL,
#         }
#         return mapping.get(str(value))
