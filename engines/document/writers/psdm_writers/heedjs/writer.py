# engines/document/writers/psdm_writers/heedjs/writer.py
"""
HeedJS writer – converts a PSDMDocument into a HeedJS HTML presentation.
"""
from __future__ import annotations

import html
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from ....models.psdm_models import PSDMDocument
from ....models.base import BaseDocument
from ...base import BaseDocumentWriter, WriteOptions


class HeedJSWriter(BaseDocumentWriter):
    """Writer that converts PSDMDocument to HeedJS HTML presentation."""

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
            return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" class="slide-image" />'

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
            return f"<table class='presentation-table'>{''.join(html_rows)}</table>"

        if elem_type == "list":
            items = content.get("items", [])
            list_items = []
            for item in items:
                elements = item.get("elements", [])
                item_html = "".join(self._render_element(e) for e in elements)
                list_items.append(f"<li>{item_html}</li>")
            return "<ul class='presentation-list'>" + "".join(list_items) + "</ul>"

        return ""

    def _generate_html(self, psdm: PSDMDocument) -> str:
        """Generate HeedJS HTML from PSDMDocument."""
        theme = psdm.theme
        bg_color = "#1a1a1a"
        primary_color = "#00bcd4"
        if theme and theme.color_scheme:
            bg_color = theme.color_scheme.get("dk1", bg_color)
            primary_color = theme.color_scheme.get("accent", primary_color)

        slides_html = []
        for idx, slide in enumerate(psdm.slides):
            slide_attrs = f'data-transition="{slide.transition.type.value}"'

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
                notes_html = f'<aside class="notes">{html.escape(slide.notes.plain_text)}</aside>'

            slides_html.append(
                f"        <div class='heed-slide'{slide_attrs}>\n" +
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background: {bg_color};
            color: #fff;
            overflow: hidden;
        }}
        .heed-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        .heed-slide {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            padding: 4rem;
            display: none;
            flex-direction: column;
            justify-content: center;
        }}
        .heed-slide.active {{
            display: flex;
        }}
        .heed-slide h1, .heed-slide h2, .heed-slide h3 {{
            font-size: 3rem;
            margin-bottom: 1.5rem;
            color: {primary_color};
        }}
        .heed-slide p {{
            font-size: 1.5rem;
            line-height: 1.6;
        }}
        .navigation {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}
        .nav-button {{
            padding: 10px 20px;
            background: {primary_color};
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="heed-container" id="heedPresentation">
{''.join(slides_html)}
    </div>
    <div class="navigation">
        <button class="nav-button" onclick="heedPrev()">Prev</button>
        <button class="nav-button" onclick="heedNext()">Next</button>
    </div>
    <script>
        let currentHeed = 0;
        const heedSlides = document.querySelectorAll('.heed-slide');

        function showHeedSlide(index) {{
            heedSlides.forEach((s, i) => s.classList.toggle('active', i === index));
        }}

        function heedNext() {{
            currentHeed = (currentHeed + 1) % heedSlides.length;
            showHeedSlide(currentHeed);
        }}

        function heedPrev() {{
            currentHeed = (currentHeed - 1 + heedSlides.length) % heedSlides.length;
            showHeedSlide(currentHeed);
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === ' ') heedNext();
            if (e.key === 'ArrowLeft') heedPrev();
        }});

        showHeedSlide(0);
    </script>
</body>
</html>"""