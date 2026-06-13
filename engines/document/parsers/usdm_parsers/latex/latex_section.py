# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import re

from ....models.base import ElementType
from ....models.usdm_models import (
    DocumentElement, HeadingContent, LogicalElement, RichTextContent, RichTextSpan, Section,
)


class LatexSection:
    """Mixin providing LaTeX section handling methods."""

    def _match_section_command(self, line: str) -> tuple[str, str | None, bool] | None:
        section_patterns = [
            (r'\\part\s*\*?\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}', 0),
            (r'\\chapter\s*\*?\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}', 1),
            (r'\\section\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 2),
            (r'\\subsection\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 3),
            (r'\\subsubsection\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 4),
            (r'\\paragraph\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 5),
            (r'\\subparagraph\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 6),
        ]
        for pattern, _ in section_patterns:
            m = re.search(pattern, line)
            if m:
                groups = m.groups()
                open_brace = line.index('{')
                starred = '*' in line[:open_brace]
                if len(groups) == 1:
                    return groups[0], None, starred
                else:
                    short = groups[0] if groups[0] else None
                    title = groups[1] if len(groups) > 1 else groups[0]
                    return title, short, starred

        minisec_m = re.search(r'\\minisec\s*\{([^}]*)\}', line)
        if minisec_m:
            return minisec_m.group(1), None, True

        add_m = re.search(r'\\addcontentsline\s*\{[^}]*\}\s*\{([^}]*)\}\s*\{([^}]*)\}', line)
        if add_m:
            return add_m.group(2), None, True

        return None

    def _get_section_cmd_index(self, line: str) -> int:
        cmds = ['part', 'chapter', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
        for idx, cmd in enumerate(cmds):
            if re.search(r'\\' + cmd + r'\s*[\*\[{]', line):
                return idx
        return 2

    def _get_section_raw_cmd(self, line: str) -> str:
        m = re.search(r'\\([a-zA-Z]+)', line)
        return '\\' + m.group(1) if m else '\\section'

    def _create_section(self, title: str, level: int, raw_cmd: str = '\\section',
                        section_type: str = 'section') -> None:
        elem_id = self._generate_id(f'section_{level}')
        section = Section(
            title=HeadingContent(
                level=level,
                text=RichTextContent(spans=[RichTextSpan(text=title)])
            ),
            section_type=section_type,
            metadata={'raw_latex': raw_cmd, 'append': self._is_appendix},
        )
        self._push_section(section)

        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.HEADING,
            content=HeadingContent(
                level=level,
                text=RichTextContent(spans=[RichTextSpan(text=title)])
            ),
            metadata={'level': level, 'raw_latex': raw_cmd, 'section_type': section_type},
        )
        self._add_logical(logical_elem)

        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.HEADING,
            metadata={'level': level, 'section_type': section_type},
        )
        self._add_element(doc_elem)
