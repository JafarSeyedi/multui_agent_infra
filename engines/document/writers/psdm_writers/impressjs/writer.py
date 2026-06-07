# engines/document/writers/psdm_writers/impressjs/writer.py
"""
Impress.js writer – converts a PSDMDocument into an impress.js HTML presentation.
"""
from __future__ import annotations

import html
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from ....models.psdm_models import PSDMDocument, Slide, TransitionType
from ....models.base import BaseDocument
from ...base import BaseDocumentWriter, WriteOptions


class ImpressJSWriter(BaseDocumentWriter):
    """Writer that converts PSDMDocument to impress.js HTML presentation."""

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        psdm = cast(PSDMDocument, document)
        data = await self.write(psdm)
        yield data

    async def write(self, document: BaseDocument) -> bytes:
        psdm = cast(PSDMDocument, document)
        html_content = self._generate_html(psdm)
        return html_content.encode(self.options.encoding)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        psdm = cast(PSDMDocument, document)
        data = await self.write(psdm)
        target.write_bytes(data)

    def get_supported_media_types(self) -> list[str]:
        return ["text/html"]

    def get_supported_extensions(self) -> list[str]:
        return [".html"]

    def _get_step_data_attrs(self, idx: int, slide: Slide) -> str:
        """Generate impress.js step data attributes (data-x, data-y, data-scale, etc.)."""
        x = idx * 1000
        y = 0
        scale = 1
        rotate = 0

        transition = slide.transition
        if transition.type == TransitionType.ZOOM:
            scale = 2
        elif transition.type == TransitionType.PUSH:
            x = idx * 1500

        return f'data-x="{x}" data-y="{y}" data-scale="{scale}" data-rotate="{rotate}"'

    def _render_element(self, element_data: dict) -> str:
        """Render a single logical element to HTML."""
        elem_type = element_data.get("element_type", "")
        content = element_data.get("content", {})

        if elem_type == "paragraph":
            text = content.get("text", {})
            spans = text.get("spans", [])
            text_content = "".join(
                html.escape(span.get("text", "")) for span in spans
            )
            return f"<p>{text_content}</p>"

        if elem_type == "heading":
            text = content.get("text", {})
            spans = text.get("spans", [])
            text_content = "".join(
                html.escape(span.get("text", "")) for span in spans
            )
            level = content.get("level", 1)
            tag = f"h{min(level + 1, 6)}"
            return f"<{tag}>{text_content}</{tag}>"

        if elem_type == "image":
            src = content.get("src", "")
            alt = content.get("alt", "")
            return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" />'

        if elem_type == "code":
            code = content.get("code", "")
            content.get("language", "")
            return f'<pre><code>{html.escape(code)}</code></pre>'

        if elem_type == "table":
            rows = content.get("rows", [])
            html_rows = []
            for row in rows:
                cells = row.get("cells", [])
                html_cells = []
                for cell in cells:
                    cell_html = "".join(
                        self._render_element(e) for e in cell.get("content", [])
                    )
                    html_cells.append(f"<td>{cell_html}</td>")
                html_rows.append(f"<tr>{''.join(html_cells)}</tr>")
            return f"<table>{''.join(html_rows)}</table>"

        if elem_type == "list":
            items = content.get("items", [])
            list_items = []
            for item in items:
                elements = item.get("elements", [])
                item_html = "".join(self._render_element(e) for e in elements)
                list_items.append(f"<li>{item_html}</li>")
            return "<ul>" + "".join(list_items) + "</ul>"

        return ""

    def _generate_html(self, psdm: PSDMDocument) -> str:
        """Generate impress.js HTML from PSDMDocument."""
        slides_html = []
        for idx, slide in enumerate(psdm.slides):
            step_attrs = self._get_step_data_attrs(idx, slide)

            slide_content = []
            for elem in slide.elements:
                element_dict = {
                    "element_type": elem.element_type.value if hasattr(elem.element_type, 'value') else str(elem.element_type),
                    "content": elem.content.__dict__ if hasattr(elem.content, '__dict__') else {},
                }
                rendered = self._render_element(element_dict)
                if rendered:
                    slide_content.append(rendered)

            notes_html = ""
            if slide.notes and slide.notes.plain_text:
                notes_html = f'<div class="notes">{html.escape(slide.notes.plain_text)}</div>'

            slides_html.append(
                f'        <div class="step" {step_attrs}>\n' +
                ''.join(f"            {line}\n" for line in slide_content) +
                f"            {notes_html}\n" +
                "        </div>"
            )

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{html.escape(psdm.title)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .step {{
            width: 900px;
            height: 700px;
            padding: 40px;
            box-sizing: border-box;
        }}
        .step h1, .step h2, .step h3, .step h4, .step h5, .step h6 {{
            font-size: 2.5em;
            margin-bottom: 0.5em;
        }}
        .step p {{
            font-size: 1.5em;
            line-height: 1.5;
        }}
        .hint {{
            display: none;
        }}
    </style>
</head>
<body>
    <div id="impress">
{''.join(slides_html)}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/impress.js@1.0.0/js/impress.min.js"></script>
    <script>
        impress().init();
    </script>
</body>
</html>"""