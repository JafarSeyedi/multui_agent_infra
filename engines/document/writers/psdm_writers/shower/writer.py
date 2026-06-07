# engines/document/writers/psdm_writers/shower/writer.py
"""
Shower writer – converts a PSDMDocument into a Shower HTML presentation.
"""
from __future__ import annotations

import html
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from ....models.psdm_models import PSDMDocument
from ....models.base import BaseDocument
from ...base import BaseDocumentWriter, WriteOptions


class ShowerWriter(BaseDocumentWriter):
    """Writer that converts PSDMDocument to Shower HTML presentation."""

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
            return f'<figure><img src="{html.escape(src)}" alt="{html.escape(alt)}" class="cover">\n<figcaption>{html.escape(alt)}</figcaption></figure>'

        if elem_type == "code":
            code = content.get("code", "")
            language = content.get("language", "")
            return f'<pre><code class="language-{html.escape(language)}">{html.escape(code)}</code></pre>'

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
            return f"<table class='striped'>{''.join(html_rows)}</table>"

        if elem_type == "list":
            items = content.get("items", [])
            list_items = []
            for item in items:
                elements = item.get("elements", [])
                item_html = "".join(self._render_element(e) for e in elements)
                list_items.append(f"<li>{item_html}</li>")
            return "<ol>" + "".join(list_items) + "</ol>"

        if elem_type == "quote":
            elements = content.get("elements", [])
            quote_html = "".join(self._render_element(e) for e in elements)
            return f"<blockquote>{quote_html}</blockquote>"

        return ""

    def _generate_html(self, psdm: PSDMDocument) -> str:
        """Generate Shower HTML from PSDMDocument."""
        theme = psdm.theme
        theme_class = "black"
        if theme and theme.name:
            theme_class = theme.name.lower().replace(" ", "-")

        slides_html = []
        for idx, slide in enumerate(psdm.slides):
            slide_class = f"slide slide--{idx + 1}"
            if slide.background_color:
                slide_class += f' style="background-color: {slide.background_color};"'

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
                notes_html = f'<footer class="badge">{html.escape(slide.notes.plain_text)}</footer>'

            slides_html.append(
                f"        <section class='{slide_class}' data-transition='{slide.transition.type.value}'>\n" +
                ''.join(f"            {line}\n" for line in slide_content) +
                f"            {notes_html}\n" +
                "        </section>"
            )

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{html.escape(psdm.title)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://shwr.me/shower/themes/{theme_class}.css">
</head>
<body class="shower">
    <header class="caption">
        <h1>{html.escape(psdm.title)}</h1>
    </header>
    <section class="slides">
{''.join(slides_html)}
    </section>
    <script src="https://shwr.me/shower/shower.js"></script>
</body>
</html>"""