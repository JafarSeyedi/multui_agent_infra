# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from ....models.base import ElementType
from ....models.usdm_models import AudioContent, ImageContent, VideoContent
from .html_parser_utils import safe_float, safe_int


class HTMLMediaParser:
    """Mixin providing media element parsing methods for HTML."""

    def _handle_image(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        if src:
            content = ImageContent(
                src=src,
                alt=alt,
                width=safe_float(attrs.get("width")),
                height=safe_float(attrs.get("height")),
                metadata={
                    "html_attrs": dict(attrs),
                    "title": attrs.get("title"),
                    "loading": attrs.get("loading"),
                    "srcset": attrs.get("srcset"),
                    "sizes": attrs.get("sizes"),
                },
            )
            element = self._create_logical_element(ElementType.IMAGE, content, attrs)
            self._add_element(element)

    def _handle_audio(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        content = AudioContent(
            src=src,
            autoplay=attrs.get("autoplay") is not None,
            controls=attrs.get("controls") is not None,
            loop=attrs.get("loop") is not None,
        )
        element = self._create_logical_element(ElementType.AUDIO, content, attrs)
        self._add_element(element)

    def _handle_video(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        content = VideoContent(
            src=src,
            width=safe_int(attrs.get("width")) if attrs.get("width") else None,
            height=safe_int(attrs.get("height")) if attrs.get("height") else None,
            poster=attrs.get("poster"),
            autoplay=attrs.get("autoplay") is not None,
            controls=attrs.get("controls") is not None,
        )
        element = self._create_logical_element(ElementType.VIDEO, content, attrs)
        self._add_element(element)

    def _handle_iframe(self, attrs: dict[str, str]) -> None:
        meta = {
            "src": attrs.get("src", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
            "sandbox": attrs.get("sandbox"),
            "allow": attrs.get("allow"),
            "loading": attrs.get("loading"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_embed(self, attrs: dict[str, str]) -> None:
        meta = {
            "src": attrs.get("src", ""),
            "type": attrs.get("type", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_object(self, attrs: dict[str, str]) -> None:
        meta = {
            "data": attrs.get("data", ""),
            "type": attrs.get("type", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_canvas(self, attrs: dict[str, str]) -> None:
        meta = {
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.DRAWING, meta, attrs)
        self._add_element(element)

    def _handle_legacy_applet(self, attrs: dict[str, str]) -> None:
        meta = {
            "code": attrs.get("code", ""),
            "archive": attrs.get("archive", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_legacy_frame(self, attrs: dict[str, str]) -> None:
        meta = {
            "src": attrs.get("src", ""),
            "name": attrs.get("name", ""),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)
