# engines/document/writers/psdm_writers/revealjs/writer.py
"""
Reveal.js writer – converts a PSDMDocument into a reveal.js HTML presentation.
"""
from __future__ import annotations

import html
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from ....models.psdm_models import Animation, AnimationType, PSDMDocument, TransitionType
from ....models.base import BaseDocument
from ...base import BaseDocumentWriter, WriteOptions


class RevealJSWriter(BaseDocumentWriter):
    """Writer that converts PSDMDocument to reveal.js HTML."""

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
        return [
            "text/html",
            "application/x-revealjs+zip",
        ]

    def get_supported_extensions(self) -> list[str]:
        return [".html"]

    def _get_transition_name(self, transition_type: TransitionType) -> str:
        """Map PSDM transition type to reveal.js transition name."""
        transition_map = {
            TransitionType.FADE: "fade",
            TransitionType.PUSH: "slide",
            TransitionType.WIPE: "none",
            TransitionType.SPLIT: "concave",
            TransitionType.COVER: "convex",
            TransitionType.UNCOVER: "convex",
            TransitionType.ZOOM: "zoom",
            TransitionType.RANDOM: "none",
            TransitionType.NO_TRANSITION: "none",
        }
        return transition_map.get(transition_type, "none")

    def _get_animation_style(self, animation: Animation, index: int) -> str:
        """Generate CSS for reveal.js animations."""
        animation_map = {
            AnimationType.APPEAR: "fadeIn",
            AnimationType.FADE_IN: "fadeIn",
            AnimationType.FLY_IN: "fadeIn",
            AnimationType.ZOOM_IN: "zoomIn",
            AnimationType.SPIN: "spin",
            AnimationType.GROW: "grow",
        }
        effect = animation_map.get(animation.type, "fadeIn")
        return f".fragment.{effect}-slide-{index} {{ animation: {effect} {animation.duration_ms}ms; }}"

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
            width = content.get("width")
            height = content.get("height")
            style = ""
            if width:
                style += f"width:{width}px;"
            if height:
                style += f"height:{height}px;"
            return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" style="{style}" />'

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
            return f"<table>{''.join(html_rows)}</table>"

        if elem_type == "list":
            items = content.get("items", [])
            ordered = content.get("ordered", False)
            list_tag = "ol" if ordered else "ul"
            list_items = []
            for item in items:
                elements = item.get("elements", [])
                item_html = "".join(self._render_element(e) for e in elements)
                list_items.append(f"<li>{item_html}</li>")
            return f"<{list_tag}>" + "".join(list_items) + f"</{list_tag}>"

        if elem_type == "rich_text":
            text = content.get("text", {})
            spans = text.get("spans", [])
            parts = []
            for span in spans:
                span_text = html.escape(span.get("text", ""))
                if span.get("bold"):
                    span_text = f"<strong>{span_text}</strong>"
                if span.get("italic"):
                    span_text = f"<em>{span_text}</em>"
                parts.append(span_text)
            return f"<div>{''.join(parts)}</div>"

        return ""

    def _generate_html(self, psdm: PSDMDocument) -> str:
        """Generate reveal.js HTML from PSDMDocument."""
        theme = psdm.theme
        theme_css = ""
        if theme and theme.color_scheme:
            theme_css = "<style>\n"
            for key, value in theme.color_scheme.items():
                theme_css += f"    .theme-{key} {{ color: {value}; }}\n"
            theme_css += "</style>\n"

        slides_html = []
        for idx, slide in enumerate(psdm.slides):
            slide_attrs = ""
            if slide.background_color:
                slide_attrs += f' data-background-color="{slide.background_color}"'
            transition_name = self._get_transition_name(slide.transition.type)
            if transition_name and transition_name != "none":
                slide_attrs += f' data-transition="{transition_name}"'
            if slide.transition.duration_ms:
                slide_attrs += f' data-transition-duration="{slide.transition.duration_ms / 1000}"'

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

            slides_html.append(f"        <section{slide_attrs}>\n" +
                           "".join(f"            {line}\n" for line in slide_content) +
                           f"            {notes_html}\n" +
                           "        </section>")

        auto_advance = "autoSlide: true," if psdm.presentation_properties.auto_advance else ""
        slides_joined = '\n'.join(slides_html)

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{html.escape(psdm.title)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.5/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.5/theme/black.min.css" id="theme">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.5/plugin/highlight/monokai.min.css">
    {theme_css}
</head>
<body>
    <div class="reveal">
        <div class="slides">
{slides_joined}
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.5/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.5/plugin/highlight/highlight.min.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: true,
            history: true,
            {auto_advance}
            highlight: {{
                highlightjs: true
            }}
        }});
    </script>
</body>
</html>"""