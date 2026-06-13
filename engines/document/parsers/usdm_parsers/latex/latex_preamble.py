# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import re

from .latex_text import _parse_keyval, _parse_length


class LatexPreamble:
    """Mixin providing LaTeX preamble parsing methods."""

    _current_language: str | None

    def _parse_preamble(self, text: str) -> None:
        doc_start = text.find(r"\begin{document}")
        preamble = text[:doc_start] if doc_start >= 0 else text

        dc_m = re.search(r"\documentclass\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", preamble)
        if dc_m:
            self._document_class = dc_m.group(2).strip()
            if dc_m.group(1):
                self._document_options = _parse_keyval(dc_m.group(1))

        for pkg_m in re.finditer(r"\usepackage\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", preamble):
            opts = _parse_keyval(pkg_m.group(1)) if pkg_m.group(1) else {}
            for p in pkg_m.group(2).strip().split(","):
                p = p.strip()
                if p:
                    self._loaded_packages.append(p)
                    if opts.get("main"):
                        self._current_language = opts["main"]

        fe_m = re.search(r"\usepackage\s*\[([^\]]*)\]\s*\{fontenc\}", preamble)
        if fe_m:
            self._font_encoding = fe_m.group(1).strip()

        ie_m = re.search(r"\usepackage\s*\[([^\]]*)\]\s*\{inputenc\}", preamble)
        if ie_m:
            self._input_encoding = ie_m.group(1).strip()

        main_m = re.search(r"\setmainfont\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if main_m:
            self._base_font = main_m.group(1)
        sans_m = re.search(r"\setsansfont\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if sans_m:
            self._sans_font = sans_m.group(1)
        mono_m = re.search(r"\setmonofont\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if mono_m:
            self._mono_font = mono_m.group(1)

        layout_keys = [
            "textwidth", "textheight", "topmargin", "headheight", "headsep",
            "footskip", "oddsidemargin", "evensidemargin", "marginparwidth",
            "marginparsep", "paperwidth", "paperheight", "hoffset", "voffset",
            "columnsep", "columnseprule", "linewidth", "parindent", "parskip",
        ]
        for key in layout_keys:
            m = re.search(r"\\setlength\s*\{\\" + key + r"\}\s*\{([^}]*)\}", preamble)
            if m:
                setattr(self, "_" + key, _parse_length(m.group(1)))

        geo_m = re.search(r"\geometry\s*\{([^}]*)\}", preamble)
        if geo_m:
            self._document_options.update(_parse_keyval(geo_m.group(1)))

        for m in re.finditer(r"\definecolor\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{([^}]*)\}", preamble):
            self._color_definitions[m.group(1)] = {
                "model": m.group(2).strip(), "spec": m.group(3).strip(),
            }

        gp_m = re.search(r"\graphicspath\s*\{(?:\s*\{[^}]*\}\s*)+\}", preamble)
        if gp_m:
            self._graphicspath = re.findall(r"\{([^}]*)\}", gp_m.group(0))

        ge_m = re.search(r"\DeclareGraphicsExtensions\s*\{([^}]*)\}", preamble)
        if ge_m:
            self._graphics_extensions = [e.strip() for e in ge_m.group(1).split(",")]

        title_m = re.search(r"\title\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if title_m:
            self._title = title_m.group(1)
        author_m = re.search(r"\author\s*\{([^}]*)\}", preamble)
        if author_m:
            self._author = author_m.group(1)
        date_m = re.search(r"\date\s*\{([^}]*)\}", preamble)
        if date_m:
            self._date = date_m.group(1)
        thanks_m = re.search(r"\thanks\s*\{([^}]*)\}", preamble)
        if thanks_m:
            self._thanks_notes.append(thanks_m.group(1))

    def _extract_title_from_preamble(self, text: str) -> str | None:
        return self._title
