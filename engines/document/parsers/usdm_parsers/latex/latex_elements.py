# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any

from ....models.base import ElementType
from ....models.usdm_models import (
    CodeContent, CommentContent, DocumentElement, FootnoteContent, HeadingContent,
    ListContent, ListItemContent, LogicalElement, MathContent, ParagraphContent,
    QuoteContent, RichTextContent, RichTextSpan, Section,
)


class LatexElements:
    """Mixin providing LaTeX element creation methods."""

    def _create_paragraph(self, text: str, alignment: str | None = None) -> None:
        if not text.strip():
            return
        elem_id = self._generate_id('paragraph')
        span = RichTextSpan(text=text)
        para_content = ParagraphContent(
            text=RichTextContent(spans=[span]),
            style=None,
        )
        meta: dict[str, Any] = {}
        if alignment:
            meta['alignment'] = alignment
        if self._line_spacing is not None:
            meta['line_spacing'] = self._line_spacing
        if self._line_spacing_rule:
            meta['line_spacing_rule'] = self._line_spacing_rule
        if self._font_size is not None:
            meta['font_size'] = self._font_size
        if self._current_language:
            meta['language'] = self._current_language
        if self._indentation is not None:
            meta['indentation'] = self._indentation

        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH,
            content=para_content,
            metadata=meta,
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH,
            metadata=meta,
        )
        self._add_element(doc_elem)

    def _create_math_element(self, math_str: str, display: bool = False, env_name: str = '') -> None:
        elem_id = self._generate_id('math')
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.MATH,
            content=MathContent(latex=math_str, display=display),
            metadata={'display': display, 'env': env_name},
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.MATH,
            metadata={'display': display, 'env': env_name},
        )
        self._add_element(doc_elem)

    def _create_list_item(self, content: str, label: str | None = None) -> None:
        elem_id = self._generate_id('list_item')
        meta: dict[str, Any] = {}
        if label:
            meta['label'] = label
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.LIST_ITEM,
            content=ListItemContent(elements=[
                LogicalElement(
                    element_id=self._generate_id('para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=content)])
                    ),
                )
            ]),
            metadata=meta,
        )
        self._add_logical(logical_elem)
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.LIST_ITEM,
            metadata=meta,
        )
        self._add_element(doc_elem)

    def _create_float_section(self, env_name: str, placement: str, float_type: str) -> None:
        elem_id = self._generate_id('float')
        section = Section(
            section_id=elem_id,
            section_type=float_type,
            metadata={
                'float_type': float_type,
                'placement': placement,
                'env_name': env_name,
            },
        )
        self._push_section(section)

    def _finalize_list(self, list_info: dict[str, Any]) -> None:
        elem_id = self._generate_id('list')
        items: list[ListItemContent] = []
        for item_data in list_info.get('items', []):
            items.append(ListItemContent(elements=[
                LogicalElement(
                    element_id=self._generate_id('para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=item_data['content'])])
                    ),
                )
            ]))
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.LIST,
            content=ListContent(
                ordered=list_info.get('ordered', False),
                items=items,
            ),
            metadata={
                'latex_environment': list_info.get('type', ''),
                'depth': list_info.get('depth', 1),
            },
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.LIST,
        )
        self._add_element(doc_elem)

    def _start_quote_env(self, env_name: str) -> None:
        self._quote_lines: list[str] = []

    def _finalize_quote_env(self, env_name: str) -> None:
        elem_id = self._generate_id('quote')
        quote_texts: list[str] = []
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.QUOTE,
            content=QuoteContent(elements=[
                LogicalElement(
                    element_id=self._generate_id('q_para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=' '.join(quote_texts))])
                    ),
                )
            ]),
            metadata={'latex_environment': env_name},
        ))
        doc_elem = DocumentElement(element_id=elem_id, element_type=ElementType.QUOTE)
        self._add_element(doc_elem)

    def _finalize_verbatim(self, lines: list[str]) -> None:
        if not lines:
            return
        code_content = '\n'.join(lines)
        elem_id = self._generate_id('code')
        language = None
        if self._verbatim_env in ('lstlisting', 'minted'):
            language = self._verbatim_env
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.CODE,
            content=CodeContent(code=code_content, language=language),
            metadata={'latex_environment': self._verbatim_env or 'verbatim'},
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.CODE,
        )
        self._add_element(doc_elem)

    def _finalize_titlepage(self) -> None:
        elem_id = self._generate_id('titlepage')
        elements: list[LogicalElement] = []
        if self._title:
            elements.append(LogicalElement(
                element_id=self._generate_id('tp_title'),
                element_type=ElementType.HEADING,
                content=HeadingContent(
                    level=0,
                    text=RichTextContent(spans=[RichTextSpan(text=self._title)]),
                ),
                metadata={'titlepage_element': 'title'},
            ))
        if self._author:
            elements.append(LogicalElement(
                element_id=self._generate_id('tp_author'),
                element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(
                    text=RichTextContent(spans=[RichTextSpan(text=self._author)])
                ),
                metadata={'titlepage_element': 'author'},
            ))
        if self._date:
            elements.append(LogicalElement(
                element_id=self._generate_id('tp_date'),
                element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(
                    text=RichTextContent(spans=[RichTextSpan(text=self._date)])
                ),
                metadata={'titlepage_element': 'date'},
            ))
        for thanks_text in self._thanks_notes:
            fn_id = self._generate_id('thanks')
            fn = FootnoteContent(note_id=fn_id, elements=[
                LogicalElement(
                    element_id=self._generate_id('fn_para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=thanks_text)])
                    ),
                )
            ], reference_text=thanks_text)
            elements.append(LogicalElement(
                element_id=fn_id,
                element_type=ElementType.FOOTNOTE,
                content=fn,
                metadata={'titlepage_element': 'thanks'},
            ))
            self._footnotes.append(fn)

        section = Section(
            section_id=elem_id,
            section_type='titlepage',
            metadata={'raw_latex': '\\maketitle'},
        )
        self._push_section(section)

        for elem in elements:
            self._add_logical(elem)
