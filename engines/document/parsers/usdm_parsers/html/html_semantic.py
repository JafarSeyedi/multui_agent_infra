# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from ....models.base import ElementType
from ....models.usdm_models import Section


class HTMLSemanticParser:
    """Mixin providing HTML semantic and legacy element parsing methods."""

    def _handle_semantic_section_start(self, section_type: str, attrs: dict[str, str]) -> None:
        section = Section(
            section_id=f"section_{section_type}_{len(self.sections) + 1}",
            title=None,
            elements=[],
            section_type=section_type,
            metadata={"html_tag": section_type, **attrs},
        )
        self._push_section(section)

    def _handle_semantic_section_end(self, section_type: str) -> None:
        pass

    def _handle_header_start(self, attrs: dict[str, str]) -> None:
        section = Section(
            section_id=f"section_header_{len(self.sections) + 1}",
            title=None,
            elements=[],
            section_type="header",
            metadata={"html_tag": "header", **attrs},
        )
        self._push_section(section)

    def _handle_header_end(self) -> None:
        pass

    def _handle_footer_start(self, attrs: dict[str, str]) -> None:
        section = Section(
            section_id=f"section_footer_{len(self.sections) + 1}",
            title=None,
            elements=[],
            section_type="footer",
            metadata={"html_tag": "footer", **attrs},
        )
        self._push_section(section)

    def _handle_footer_end(self) -> None:
        pass

    def _handle_address_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_address_end(self) -> None:
        para = self._flush_text_as_paragraph()
        if para:
            element = self._create_logical_element(ElementType.PARAGRAPH, para)
            self._add_element(element)

    def _handle_legacy_font(self, attrs: dict[str, str]) -> None:
        color = attrs.get("color")
        face = attrs.get("face")
        size = attrs.get("size")
        if color:
            self._set_style_attr("font_color", color)
        if face:
            self._set_style_attr("font_face", face)
        if size:
            self._set_style_attr("font_size", size)

    def _handle_legacy_center(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("center", True)
