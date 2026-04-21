# # engines/document/writers/csv_writer.py
# import csv
# import io
# from typing import Optional, Dict, Any, List, Union, cast
# from pathlib import Path

# from ..models.base import BaseDocument
# from ..models.dsdm_models import DataDocument, DataNode, DataNodeKind, DataValue
# from .base import BaseDocumentWriter, WriteOptions


# class CSVDocumentWriter(BaseDocumentWriter):
#     """
#     Writer for CSV documents from DSDM model.
#     Converts DSDM DataNodes to CSV format.
#     """
    
#     def __init__(self):
#         self._supported_media_types = [
#             "text/csv",
#             "application/csv"
#         ]
#         self._supported_extensions = [".csv", ".tsv", ".txt"]
        
#     async def write(
#         self, 
#         document: BaseDocument, 
#         target: Union[str, Path, bytes],
#         options: Optional[WriteOptions] = None
#     ) -> None:
#         """
#         Write CSV from DSDM document.
        
#         Args:
#             document: DSDM DataDocument containing table structure
#             target: Target path or bytes buffer
#             options: Writing options:
#                 - encoding: CSV encoding (default: 'utf-8')
#                 - delimiter: Field delimiter (default: ',')
#                 - quotechar: Quote character (default: '"')
#                 - quoting: Quoting style (0-3, default: csv.QUOTE_MINIMAL)
#                 - doublequote: Handle doubled quotes (default: True)
#                 - escapechar: Escape character (default: None)
#                 - lineterminator: Line terminator (default: '\\n')
#                 - skipinitialspace: Skip spaces after delimiter (default: False)
#                 - strict: Raise exception on bad CSV (default: False)
#                 - include_header: Include header row (bool, default: True)
#                 - na_rep: String representation of NaN/None (default: '')
#                 - columns: List of columns to include (list[str], default: all)
#                 - column_order: Custom column order (list[str])
#                 - write_index: Write row indices (bool, default: False)
#                 - index_label: Column label for index (str, default: 'index')
#                 - dialect: CSV dialect name (e.g., 'excel', 'excel-tab', 'unix')
#         """
#         if not isinstance(document, DataDocument):
#             raise TypeError(f"Expected DataDocument, got {type(document)}")
        
#         # Default options
#         default_options: Dict[str, Any] = {
#             'encoding': 'utf-8',
#             'delimiter': ',',
#             'quotechar': '"',
#             'quoting': csv.QUOTE_MINIMAL,
#             'doublequote': True,
#             'escapechar': None,
#             'lineterminator': '\n',
#             'skipinitialspace': False,
#             'strict': False,
#             'include_header': True,
#             'na_rep': '',
#             'columns': None,
#             'column_order': None,
#             'write_index': False,
#             'index_label': 'index',
#             'dialect': None
#         }
        
#         # Merge with provided options
#         if options and options.additional_options:
#             default_options.update(options.additional_options)
        
#         # Extract CSV data from DSDM document
#         try:
#             headers, rows = self._extract_csv_data(document.root, default_options)
#         except ValueError as e:
#             raise ValueError(f"Failed to extract CSV data from DSDM: {e}")
        
#         # Generate CSV content
#         csv_content = self._generate_csv_content(
#             headers, 
#             rows, 
#             default_options
#         )
        
#         # Encode to bytes
#         encoding = str(default_options['encoding'])
#         csv_bytes = csv_content.encode(encoding, errors='replace')
        
#         # Write to target
#         if isinstance(target, (str, Path)):
#             target_path = Path(target)
#             target_path.parent.mkdir(parents=True, exist_ok=True)
#             target_path.write_bytes(csv_bytes)
#         elif isinstance(target, bytes):
#             # Assume it's a buffer - copy bytes into it
#             # Note: This is simplified - in reality you'd need a writable buffer
#             target_buf = target
#             # For demonstration, we'll just return
#             # In production, you'd write to the buffer
#             pass
#         else:
#             raise TypeError(f"Unsupported target type: {type(target)}")
    
#     def _extract_csv_data(
#         self, 
#         root_node: DataNode, 
#         options: Dict[str, Any]
#     ) -> tuple[List[str], List[List[Any]]]:
#         """
#         Extract headers and rows from DSDM table structure.
#         """
#         # Find columns and rows nodes
#         columns_node = None
#         rows_node = None
        
#         for child in root_node.children:
#             if child.kind == DataNodeKind.TABLE_COLUMNS:
#                 columns_node = child
#             elif child.kind == DataNodeKind.TABLE_ROWS:
#                 rows_node = child
        
#         if not rows_node:
#             raise ValueError("No rows found in DSDM table structure")
        
#         # Extract headers
#         headers = []
#         if columns_node and options.get('include_header', True):
#             for column in columns_node.children:
#                 if column.kind == DataNodeKind.TABLE_COLUMN:
#                     headers.append(column.name)
        
#         # If no headers from columns, use metadata or generate
#         if not headers and rows_node.children:
#             # Try to get headers from first row's cell names
#             first_row = rows_node.children[0]
#             if first_row.kind == DataNodeKind.TABLE_ROW:
#                 headers = [cell.name for cell in first_row.children 
#                           if cell.kind == DataNodeKind.TABLE_CELL]
        
#         # If still no headers, generate generic ones
#         if not headers and rows_node.children:
#             first_row = rows_node.children[0]
#             num_cols = len([c for c in first_row.children 
#                            if c.kind == DataNodeKind.TABLE_CELL])
#             headers = [f"column_{i}" for i in range(num_cols)]
        
#         # Apply column filtering and ordering
#         if options.get('columns'):
#             selected_columns = options['columns']
#             # Reorder headers based on selected columns
#             headers = [h for h in headers if h in selected_columns]
#             # Apply custom order if specified
#             if options.get('column_order'):
#                 # Sort headers according to column_order
#                 header_order = {h: i for i, h in enumerate(options['column_order'])}
#                 headers.sort(key=lambda h: header_order.get(h, len(headers)))
        
#         # Extract rows
#         rows = []
#         for row_node in rows_node.children:
#             if row_node.kind != DataNodeKind.TABLE_ROW:
#                 continue
            
#             row_data = []
            
#             # If write_index is True, add index
#             if options.get('write_index', False):
#                 index = row_node.metadata.get("index", len(rows))
#                 row_data.append(index)
            
#             # Collect cell values
#             cell_dict = {}
#             for cell in row_node.children:
#                 if cell.kind == DataNodeKind.TABLE_CELL:
#                     cell_name = cell.name
#                     cell_value = self._get_cell_value(cell, options)
#                     cell_dict[cell_name] = cell_value
            
#             # Order cells according to headers
#             for header in headers:
#                 if header in cell_dict:
#                     row_data.append(cell_dict[header])
#                 else:
#                     row_data.append(options.get('na_rep', ''))
            
#             rows.append(row_data)
        
#         # Add index header if needed
#         if options.get('write_index', False):
#             headers = [options.get('index_label', 'index')] + headers
        
#         return headers, rows
    
#     def _get_cell_value(
#         self, 
#         cell_node: DataNode, 
#         options: Dict[str, Any]
#     ) -> str:
#         """
#         Get string representation of cell value.
#         """
#         if not cell_node.value:
#             return options.get('na_rep', '')
        
#         value = cell_node.value.value
#         lexical_value = cell_node.value.lexical_value
        
#         # Use lexical value if available
#         if lexical_value is not None:
#             return str(lexical_value)
        
#         # Convert value based on type
#         if value is None:
#             return options.get('na_rep', '')
        
#         # Handle different scalar types
#         scalar_type = cell_node.value.scalar_type
        
#         if scalar_type == ScalarType.BOOLEAN:
#             return str(value).lower()
#         elif scalar_type == ScalarType.INTEGER:
#             return str(int(value))
#         elif scalar_type == ScalarType.FLOAT:
#             # Format float to avoid scientific notation
#             return format(float(value), 'f').rstrip('0').rstrip('.')
#         elif scalar_type == ScalarType.DATETIME:
#             return str(value)
#         else:
#             return str(value)
    
#     def _generate_csv_content(
#         self, 
#         headers: List[str], 
#         rows: List[List[Any]], 
#         options: Dict[str, Any]
#     ) -> str:
#         """
#         Generate CSV string from headers and rows.
#         """
#         # Configure CSV dialect
#         dialect_params = {
#             'delimiter': str(options['delimiter']),
#             'quotechar': str(options['quotechar']),
#             'doublequote': bool(options['doublequote']),
#             'escapechar': str(options['escapechar']) if options['escapechar'] else None,
#             'lineterminator': str(options['lineterminator']),
#             'skipinitialspace': bool(options['skipinitialspace']),
#             'strict': bool(options['strict']),
#             'quoting': int(options['quoting'])
#         }
        
#         # Remove None values
#         dialect_params = {k: v for k, v in dialect_params.items() if v is not None}
        
#         # Create CSV writer
#         output = io.StringIO()
        
#         # Determine dialect
#         if options['dialect']:
#             try:
#                 writer = csv.writer(output, dialect=options['dialect'])
#             except csv.Error:
#                 # Fall back to custom dialect
#                 writer = csv.writer(output, **dialect_params)
#         else:
#             writer = csv.writer(output, **dialect_params)
        
#         # Write header if needed
#         if headers and options.get('include_header', True):
#             writer.writerow(headers)
        
#         # Write rows
#         for row in rows:
#             writer.writerow(row)
        
#         # Get CSV content
#         csv_content = output.getvalue()
#         output.close()
        
#         return csv_content
    
#     def get_supported_media_types(self) -> list[str]:
#         """Get list of supported media types."""
#         return self._supported_media_types
    
#     def get_supported_extensions(self) -> list[str]:
#         """Get list of supported file extensions."""
#         return self._supported_extensions
