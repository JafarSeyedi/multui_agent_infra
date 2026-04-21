# # engines/document/parsers/csv_parser.py
# import csv
# import io
# from typing import Optional, Dict, Any, List, Union, cast
# from pathlib import Path
# import hashlib

# from ..models.media_detection import detect_by_extension
# from ..models.base import BaseDocument
# from ..models.dsdm_models import (
#     DataDocument, DataNode, DataNodeKind, DataValue, 
#     ScalarType, DataDocumentCapabilities, DataSchemaReference
# )
# from .base import BaseDocumentParser, ParseOptions


# class CSVDocumentParser(BaseDocumentParser):
#     """
#     Parser for CSV documents using DSDM model.
#     Supports various CSV dialects, quoted fields, and data type inference.
#     """
    
#     def __init__(self):
#         self._supported_media_types = [
#             "text/csv",
#             "application/csv"
#         ]
#         self._supported_extensions = [".csv", ".tsv", ".txt"]
        
#     async def parse_bytes(
#         self, 
#         data: bytes, 
#         document_id: str, 
#         source_name: str, 
#         metadata: Optional[Dict[str, Any]] = None,
#         options: Optional[ParseOptions] = None
#     ) -> BaseDocument:
#         """
#         Parse CSV from bytes.
        
#         Args:
#             data: CSV data as bytes
#             document_id: Unique identifier for the document
#             source_name: Name of the source
#             metadata: Additional metadata
#             options: Parsing options:
#                 - encoding: CSV encoding (default: 'utf-8')
#                 - delimiter: Field delimiter (default: ',')
#                 - quotechar: Quote character (default: '"')
#                 - doublequote: Handle doubled quotes (default: True)
#                 - escapechar: Escape character (default: None)
#                 - lineterminator: Line terminator (default: '\\r\\n')
#                 - skipinitialspace: Skip spaces after delimiter (default: False)
#                 - strict: Raise exception on bad CSV (default: False)
#                 - has_header: First row is header (bool, default: True)
#                 - dialect: CSV dialect name (e.g., 'excel', 'excel-tab', 'unix')
#                 - infer_types: Infer data types (bool, default: True)
#                 - null_values: List of strings to treat as null (list[str])
#                 - true_values: List of strings to treat as True (list[str])
#                 - false_values: List of strings to treat as False (list[str])
#                 - max_rows: Maximum rows to parse (int, default: None)
#                 - skip_rows: Number of rows to skip (int, default: 0)
                
#         Returns:
#             DataDocument with CSV structure
#         """
#         # Default options
#         default_options: Dict[str, Any] = {
#             'encoding': 'utf-8',
#             'delimiter': ',',
#             'quotechar': '"',
#             'doublequote': True,
#             'escapechar': None,
#             'lineterminator': '\r\n',
#             'skipinitialspace': False,
#             'strict': False,
#             'has_header': True,
#             'dialect': None,
#             'infer_types': True,
#             'null_values': ['', 'null', 'NULL', 'None', 'NA', 'N/A'],
#             'true_values': ['true', 'True', 'TRUE', 'yes', 'Yes', 'YES', '1'],
#             'false_values': ['false', 'False', 'FALSE', 'no', 'No', 'NO', '0'],
#             'max_rows': None,
#             'skip_rows': 0
#         }
        
#         # Merge with provided options
#         if options and options.additional_options:
#             default_options.update(options.additional_options)
        
#         # Decode bytes to string
#         encoding = str(default_options['encoding'])
#         try:
#             csv_text = data.decode(encoding)
#         except UnicodeDecodeError:
#             # Try common encodings
#             for enc in ['utf-8', 'utf-16', 'iso-8859-1', 'cp1256', 'latin-1']:
#                 try:
#                     csv_text = data.decode(enc)
#                     encoding = enc
#                     break
#                 except UnicodeDecodeError:
#                     continue
#             else:
#                 raise ValueError(f"Cannot decode CSV data with encoding {encoding}")
        
#         # Create CSV reader
#         try:
#             csv_data, headers, dialect_info = self._parse_csv_text(
#                 csv_text, 
#                 default_options
#             )
#         except Exception as e:
#             raise ValueError(f"Failed to parse CSV: {e}")
        
#         # Create document metadata
#         doc_metadata = {
#             document_id: document_id,
#             source_name: source_name,
#             size_bytes: len(data),
#             encoding: encoding,
#             media_type: "text/csv",
#             row_count: len(csv_data),
#             column_count: len(headers) if headers else 0,
#             has_header: default_options['has_header']
#         }
#         doc_metadata.update(dialect_info)
        
#         # Add additional metadata if provided
#         if metadata:
#             doc_metadata.update(metadata)
        
#         # Create root node
#         root_node = self._create_csv_root_node(
#             csv_data, 
#             headers, 
#             default_options
#         )
        
#         # Create capabilities
#         capabilities = DataDocumentCapabilities(
#             supports_comments=False,
#             supports_namespaces=False,
#             supports_attributes=False,
#             supports_tags=False,
#             supports_binary_payloads=False,
#             ordered_mappings=True,
#             supports_schema=True
#         )
        
#         # Add schema reference if headers exist
#         schema_refs = []
#         if headers:
#             schema_ref = DataSchemaReference(
#                 schema_type="csv_header",
#                 location="inline",
#                 content={
#                     "columns": headers,
#                     "dialect": dialect_info
#                 }
#             )
#             schema_refs.append(schema_ref)
        
#         mt = detect_by_extension("csv")
#         return DataDocument(
#             id=document_id,
#             media_type=mt,
#             metadata=doc_metadata,
#             root=root_node,
#             capabilities=capabilities,
#             schemas=schema_refs if schema_refs else None
#         )
    
#     async def parse_path(
#         self, 
#         path: Union[str, Path], 
#         document_id: str, 
#         metadata: Optional[Dict[str, Any]] = None,
#         options: Optional[ParseOptions] = None
#     ) -> BaseDocument:
#         """
#         Parse CSV from file path.
        
#         Args:
#             path: Path to CSV file (str or Path)
#             document_id: Unique identifier for the document
#             metadata: Additional metadata
#             options: Same as parse_bytes
            
#         Returns:
#             DataDocument with CSV structure
#         """
#         source_path = Path(path)
#         if not source_path.exists():
#             raise FileNotFoundError(f"CSV file not found: {source_path}")
        
#         # Detect dialect from extension
#         if options is None:
#             options = ParseOptions()
#         if options.additional_options is None:
#             options.additional_options = {}
        
#         # Set delimiter based on extension
#         if source_path.suffix.lower() == '.tsv':
#             options.additional_options['delimiter'] = '\t'
#             options.additional_options['dialect'] = 'excel-tab'
        
#         try:
#             with open(source_path, 'rb') as f:
#                 data = f.read()
#         except IOError as e:
#             raise ValueError(f"Cannot read CSV file {source_path}: {e}")
        
#         # Use parse_bytes with file-specific metadata
#         file_metadata = metadata or {}
#         file_metadata["source_path"] = str(source_path)
#         file_metadata["file_name"] = source_path.name
#         file_metadata["file_stem"] = source_path.stem
        
#         return await self.parse_bytes(
#             data, 
#             document_id, 
#             source_path.name,
#             file_metadata,
#             options
#         )
    
#     def _parse_csv_text(
#         self, 
#         csv_text: str, 
#         options: Dict[str, Any]
#     ) -> tuple[List[List[str]], List[str], Dict[str, Any]]:
#         """
#         Parse CSV text and return data, headers, and dialect info.
#         """
#         # Configure CSV dialect
#         dialect_params = {
#             'delimiter': str(options['delimiter']),
#             'quotechar': str(options['quotechar']) if options['quotechar'] else '"',
#             'doublequote': bool(options['doublequote']),
#             'escapechar': str(options['escapechar']) if options['escapechar'] else None,
#             'lineterminator': str(options['lineterminator']),
#             'skipinitialspace': bool(options['skipinitialspace']),
#             'strict': bool(options['strict'])
#         }
        
#         # Remove None values
#         dialect_params = {k: v for k, v in dialect_params.items() if v is not None}
        
#         # Create CSV reader
#         csv_file = io.StringIO(csv_text)
        
#         # Skip rows if specified
#         skip_rows = int(options['skip_rows'])
#         for _ in range(skip_rows):
#             csv_file.readline()
        
#         # Determine dialect
#         if options['dialect']:
#             try:
#                 dialect = csv.get_dialect(options['dialect'])
#             except csv.Error:
#                 # Create custom dialect
#                 class CustomDialect(csv.Dialect):
#                     delimiter = dialect_params['delimiter']
#                     quotechar = dialect_params['quotechar']
#                     doublequote = dialect_params['doublequote']
#                     escapechar = dialect_params.get('escapechar')
#                     lineterminator = dialect_params['lineterminator']
#                     skipinitialspace = dialect_params['skipinitialspace']
#                     strict = dialect_params['strict']
#                     quoting = csv.QUOTE_MINIMAL
                
#                 dialect = CustomDialect()
#         else:
#             # Use custom parameters
#             class CustomDialect(csv.Dialect):
#                 delimiter = dialect_params['delimiter']
#                 quotechar = dialect_params['quotechar']
#                 doublequote = dialect_params['doublequote']
#                 escapechar = dialect_params.get('escapechar')
#                 lineterminator = dialect_params['lineterminator']
#                 skipinitialspace = dialect_params['skipinitialspace']
#                 strict = dialect_params['strict']
#                 quoting = csv.QUOTE_MINIMAL
            
#             dialect = CustomDialect()
        
#         # Create reader
#         reader = csv.reader(csv_file, dialect)
        
#         # Read data
#         data = []
#         headers = []
#         max_rows = options['max_rows']
#         row_count = 0
        
#         for row in reader:
#             if max_rows and row_count >= max_rows:
#                 break
            
#             data.append(row)
#             row_count += 1
        
#         # Extract headers if specified
#         if data and options['has_header']:
#             headers = data[0]
#             data = data[1:]
        
#         # Collect dialect information
#         dialect_info = {
#             "dialect_name": getattr(dialect, '__class__.__name__', 'custom'),
#             "delimiter": dialect.delimiter,
#             "quotechar": dialect.quotechar,
#             "doublequote": dialect.doublequote,
#             "escapechar": dialect.escapechar,
#             "lineterminator": repr(dialect.lineterminator),
#             "skipinitialspace": dialect.skipinitialspace,
#             "strict": dialect.strict,
#             "quoting": getattr(dialect, 'quoting', csv.QUOTE_MINIMAL)
#         }
        
#         return data, headers, dialect_info
    
#     def _create_csv_root_node(
#         self, 
#         data: List[List[str]], 
#         headers: List[str],
#         options: Dict[str, Any]
#     ) -> DataNode:
#         """
#         Create DSDM root node for CSV data.
#         """
#         root_node = DataNode(
#             node_id="csv_root",
#             kind=DataNodeKind.TABLE,
#             path="$",
#             name="csv_data",
#             metadata={
#                 "row_count": len(data),
#                 "column_count": len(headers) if headers else (len(data[0]) if data else 0),
#                 "has_headers": bool(headers)
#             }
#         )
        
#         # Create column nodes if headers exist
#         column_nodes = []
#         if headers:
#             for i, header in enumerate(headers):
#                 column_node = DataNode(
#                     node_id=f"column_{i}",
#                     kind=DataNodeKind.TABLE_COLUMN,
#                     path=f"$.columns.{header}",
#                     name=header,
#                     metadata={
#                         "index": i,
#                         "header": header
#                     }
#                 )
#                 column_nodes.append(column_node)
#         else:
#             # Create generic column nodes
#             if data:
#                 num_cols = len(data[0])
#                 for i in range(num_cols):
#                     column_node = DataNode(
#                         node_id=f"column_{i}",
#                         kind=DataNodeKind.TABLE_COLUMN,
#                         path=f"$.columns.column_{i}",
#                         name=f"column_{i}",
#                         metadata={
#                             "index": i,
#                             "header": None
#                         }
#                     )
#                     column_nodes.append(column_node)
        
#         # Add column nodes to root
#         if column_nodes:
#             columns_node = DataNode(
#                 node_id="columns",
#                 kind=DataNodeKind.TABLE_COLUMNS,
#                 path="$.columns",
#                 name="columns"
#             )
#             columns_node.children.extend(column_nodes)
#             root_node.children.append(columns_node)
        
#         # Create row nodes
#         rows_node = DataNode(
#             node_id="rows",
#             kind=DataNodeKind.TABLE_ROWS,
#             path="$.rows",
#             name="rows"
#         )
        
#         for row_idx, row in enumerate(data):
#             row_node = self._create_row_node(
#                 row, 
#                 row_idx, 
#                 headers, 
#                 column_nodes,
#                 options
#             )
#             if row_node:
#                 rows_node.children.append(row_node)
        
#         root_node.children.append(rows_node)
        
#         return root_node
    
#     def _create_row_node(
#         self, 
#         row: List[str], 
#         row_idx: int, 
#         headers: List[str],
#         column_nodes: List[DataNode],
#         options: Dict[str, Any]
#     ) -> DataNode:
#         """
#         Create DSDM node for a CSV row.
#         """
#         row_node = DataNode(
#             node_id=f"row_{row_idx}",
#             kind=DataNodeKind.TABLE_ROW,
#             path=f"$.rows.row_{row_idx}",
#             name=f"row_{row_idx}",
#             metadata={
#                 "index": row_idx,
#                 "line_number": row_idx + (2 if headers else 1)  # Account for header
#             }
#         )
        
#         # Create cell nodes
#         for col_idx, cell_value in enumerate(row):
#             # Get column name
#             if headers and col_idx < len(headers):
#                 col_name = headers[col_idx]
#             elif col_idx < len(column_nodes):
#                 col_name = column_nodes[col_idx].name
#             else:
#                 col_name = f"column_{col_idx}"
            
#             # Infer data type
#             scalar_type, typed_value = self._infer_cell_type(
#                 cell_value, 
#                 options
#             )
            
#             cell_node = DataNode(
#                 node_id=f"row_{row_idx}_cell_{col_idx}",
#                 kind=DataNodeKind.TABLE_CELL,
#                 path=f"$.rows.row_{row_idx}.{col_name}",
#                 name=col_name,
#                 metadata={
#                     "row_index": row_idx,
#                     "column_index": col_idx,
#                     "column_name": col_name
#                 },
#                 value=DataValue(
#                     scalar_type=scalar_type,
#                     value=typed_value,
#                     lexical_value=cell_value
#                 ) if cell_value != "" else None
#             )
            
#             row_node.children.append(cell_node)
        
#         return row_node
    
#     def _infer_cell_type(
#         self, 
#         cell_value: str, 
#         options: Dict[str, Any]
#     ) -> tuple[ScalarType, Any]:
#         """
#         Infer data type from cell value.
#         """
#         if not options.get('infer_types', True):
#             return ScalarType.STRING, cell_value
        
#         # Check for null values
#         null_values = options.get('null_values', ['', 'null', 'NULL', 'None', 'NA', 'N/A'])
#         if cell_value.strip() in null_values:
#             return ScalarType.NULL, None
        
#         # Check for boolean values
#         true_values = options.get('true_values', ['true', 'True', 'TRUE', 'yes', 'Yes', 'YES', '1'])
#         false_values = options.get('false_values', ['false', 'False', 'FALSE', 'no', 'No', 'NO', '0'])
        
#         if cell_value.strip() in true_values:
#             return ScalarType.BOOLEAN, True
#         elif cell_value.strip() in false_values:
#             return ScalarType.BOOLEAN, False
        
#         # Check for integer
#         try:
#             # Try to parse as int
#             int_value = int(cell_value)
#             return ScalarType.INTEGER, int_value
#         except ValueError:
#             pass
        
#         # Check for float
#         try:
#             # Try to parse as float
#             float_value = float(cell_value)
#             return ScalarType.FLOAT, float_value
#         except ValueError:
#             pass
        
#         # Check for ISO date/time
#         # This is simplified - in production, use dateutil or similar
#         date_patterns = [
#             r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
#             r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',  # ISO with time
#             r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
#             r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
#         ]
        
#         import re
#         for pattern in date_patterns:
#             if re.match(pattern, cell_value.strip()):
#                 return ScalarType.DATETIME, cell_value
        
#         # Default to string
#         return ScalarType.STRING, cell_value
    
#     def get_supported_media_types(self) -> list[str]:
#         """Get list of supported media types."""
#         return self._supported_media_types
    
#     def get_supported_extensions(self) -> list[str]:
#         """Get list of supported file extensions."""
#         return self._supported_extensions
