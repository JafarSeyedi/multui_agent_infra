# engines/document/writers/psdm_writers/stagecraft/writer.py
"""
Stagecraft writer – converts a PSDMDocument into a modern HTML presentation.
"""
from __future__ import annotations

import html
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from ....models.psdm_models import PSDMDocument, TransitionType
from ....models.base import BaseDocument
from ...base import BaseDocumentWriter, WriteOptions


class StagecraftWriter(BaseDocumentWriter):
    """Writer that converts PSDMDocument to Stagecraft-style HTML presentation."""

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

    def _get_transition_css(self, transition_type: TransitionType) -> str:
        """Get CSS transition for slide."""
        transition_map = {
            TransitionType.FADE: "opacity 0.5s ease-in-out",
            TransitionType.PUSH: "transform 0.5s ease-in-out",
            TransitionType.WIPE: "clip-path 0.5s ease-in-out",
            TransitionType.ZOOM: "transform 0.5s ease-in-out",
        }
        return transition_map.get(transition_type, "opacity 0.3s ease")

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
            return f"<p class='slide-paragraph'>{text_content}</p>"

        if elem_type == "heading":
            text = content.get("text", {})
            spans = text.get("spans", [])
            text_content = "".join(
                html.escape(span.get("text", "")) for span in spans
            )
            level = min(content.get("level", 1), 6)
            return f"<h{level} class='slide-heading'>{text_content}</h{level}>"

        if elem_type == "image":
            src = content.get("src", "")
            alt = content.get("alt", "")
            width = content.get("width", "")
            height = content.get("height", "")
            style = ""
            if width:
                style += f"width:{width}px;"
            if height:
                style += f"height:{height}px;"
            return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" style="{style}" class="slide-image" />'

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
            return f"<table class='slide-table'>{''.join(html_rows)}</table>"

        if elem_type == "list":
            items = content.get("items", [])
            ordered = content.get("ordered", False)
            list_tag = "ol" if ordered else "ul"
            list_items = []
            for item in items:
                elements = item.get("elements", [])
                item_html = "".join(self._render_element(e) for e in elements)
                list_items.append(f"<li>{item_html}</li>")
            return f"<{list_tag} class='slide-list'>{''.join(list_items)}</{list_tag}>"

        return ""

    def _generate_html(self, psdm: PSDMDocument) -> str:
        """Generate Stagecraft-style HTML from PSDMDocument."""
        theme = psdm.theme
        theme_css = ":root { --primary-color: #007acc; --secondary-color: #f5f5f5; }"
        if theme and theme.color_scheme:
            colors = theme.color_scheme
            if colors.get("dk1"):
                theme_css += f"\n    --primary-color: {colors['dk1']};"
            if colors.get("lt1"):
                theme_css += f"\n    --bg-color: {colors['lt1']};"

        slides_html = []
        for idx, slide in enumerate(psdm.slides):
            slide_class = "stage-slide"
            bg_style = ""
            if slide.background_color:
                bg_style = f"background-color: {slide.background_color};"
            if slide.background_image and slide.background_image.src:
                bg_style += f"background-image: url('{slide.background_image.src}');"

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
                notes_html = f'<div class="slide-notes">{html.escape(slide.notes.plain_text)}</div>'

            transition_css = self._get_transition_css(slide.transition.type)
            slides_html.append(
                f'            <section class="{slide_class}"'
                f' style="{bg_style}"'
                f' data-transition="{slide.transition.type.value}"'
                f' data-animation="{transition_css}">\n' +
                ''.join(f"                {line}\n" for line in slide_content) +
                f"                {notes_html}\n" +
                "            </section>"
            )

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{html.escape(psdm.title)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #fff;
            overflow: hidden;
        }}
        .presentation {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        .stage-slide {{
            width: 100%;
            height: 100%;
            padding: 4rem;
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: {theme_css};
        }}
        .stage-slide.active {{
            display: flex;
        }}
        .slide-heading {{
            font-size: 3rem;
            margin-bottom: 2rem;
            text-align: center;
        }}
        .slide-paragraph {{
            font-size: 1.5rem;
            max-width: 80%;
            text-align: center;
        }}
        .slide-image {{
            max-width: 90%;
            max-height: 70%;
            object-fit: contain;
        }}
        .navigation {{
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 1rem;
        }}
        .nav-btn {{
            padding: 0.5rem 1rem;
            background: var(--primary-color, #007acc);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .slide-counter {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="presentation" id="presentation">
{''.join(slides_html)}
    </div>
    <div class="navigation">
        <button class="nav-btn" onclick="prevSlide()">Previous</button>
        <button class="nav-btn" onclick="nextSlide()">Next</button>
    </div>
    <div class="slide-counter">
        <span id="current-slide">1</span> / <span id="total-slides">{len(psdm.slides)}</span>
    </div>
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.stage-slide');
        const totalSlides = slides.length;

        function showSlide(index) {{
            slides.forEach((s, i) => s.classList.toggle('active', i === index));
            document.getElementById('current-slide').textContent = index + 1;
        }}

        function nextSlide() {{
            currentSlide = (currentSlide + 1) % totalSlides;
            showSlide(currentSlide);
        }}

        function prevSlide() {{
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
            showSlide(currentSlide);
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
        }});

        showSlide(0);
    </script>
</body>
</html>"""