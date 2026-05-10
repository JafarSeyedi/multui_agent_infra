# engines/document/writers/dsdm_writers/csv_tsv_writer.py
"""CSV/TSV writer."""
import csv
import io
from datetime import datetime, date, time
from ...models.dsdm_models import DataDocument, DataNode, DataNodeKind, DataValue
from ...models.msdm_models import Attribute
from .base_dsdm_writer import BaseDSDMWriter, DSDMWriteOptions

class CSVTSVWriter(BaseDSDMWriter):
    name = "csv_tsv"
    supported_extensions = (".csv", ".tsv", ".tab")
    media_type_str = "text/csv"

    def get_supported_media_types(self) -> list[str]:
        return [self.media_type_str]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    async def _serialise_root(self, root_node: DataNode, options: DSDMWriteOptions) -> bytes:
        self._check_required_fields(root_node, options)

        delimiter = options.custom.get("delimiter", ",")
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        # The root should be an ARRAY of OBJECTs (rows)
        if root_node.kind != DataNodeKind.ARRAY:
            raise ValueError("CSV writer expects an ARRAY of rows as root")

        rows = root_node.children
        if not rows:
            return b""

        # Determine header from first row or schema
        first_row = rows[0]
        if first_row.kind != DataNodeKind.OBJECT:
            raise ValueError("CSV writer expects each row to be an OBJECT")

        # Use schema ordering if available
        ordering = self._get_attribute_order(root_node, options)
        if ordering:
            headers = ordering
        else:
            headers = [child.name for child in first_row.children if child.name]

        writer.writerow(headers)

        for row_node in rows:
            row_data = []
            for header in headers:
                # find matching child
                cell = next((c for c in row_node.children if c.name == header), None)
                if cell:
                    if self._should_include_field(header, row_node, options):
                        row_data.append(self._format_cell(cell))
                    else:
                        row_data.append("")  # excluded field
                else:
                    row_data.append("")  # missing field
            writer.writerow(row_data)

        return output.getvalue().encode(options.encoding)

    async def _serialise_node(self, node: DataNode, options: DSDMWriteOptions) -> bytes:
        return await self._serialise_root(node, options)

    def _format_cell(self, node: DataNode) -> str:
        if node.value is None:
            return ""
        val = node.value.value
        st = node.value.scalar_type
        if val is None:
            return ""
        if isinstance(val, datetime):
            return val.isoformat()
        if isinstance(val, date):
            return val.isoformat()
        if isinstance(val, time):
            return val.isoformat()
        if isinstance(val, bool):
            return str(val).lower()
        if isinstance(val, (int, float)):
            return str(val)
        # binary -> base64
        if st.value == "binary" and isinstance(val, bytes):
            import base64
            return base64.b64encode(val).decode()
        return str(val)