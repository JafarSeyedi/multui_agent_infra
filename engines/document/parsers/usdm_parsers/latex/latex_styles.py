# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any

from ....models.usdm_models import (
    CharacterStyle, ListStyle, ParagraphStyle, StyleSheet, TableStyle,
)


class LatexStyles:
    """Mixin providing LaTeX stylesheet and metadata building methods."""

    def _build_stylesheet(self) -> StyleSheet:
        char_styles: dict[str, CharacterStyle] = {}
        para_styles: dict[str, ParagraphStyle] = {}

        char_styles['textbf'] = CharacterStyle(name='textbf', bold=True)
        char_styles['textit'] = CharacterStyle(name='textit', italic=True)
        char_styles['texttt'] = CharacterStyle(name='texttt', font='monospace')
        char_styles['underline'] = CharacterStyle(name='underline', underline=True)
        char_styles['emph'] = CharacterStyle(name='emph', italic=True)
        char_styles['textsl'] = CharacterStyle(name='textsl', italic=True)
        char_styles['textsc'] = CharacterStyle(name='textsc', small_caps=True)
        char_styles['textsuperscript'] = CharacterStyle(name='textsuperscript', superscript=True)
        char_styles['textsubscript'] = CharacterStyle(name='textsubscript', subscript=True)

        if self._font_encoding:
            char_styles[f'fontenc_{self._font_encoding}'] = CharacterStyle(
                name=f'fontenc_{self._font_encoding}',
                font_charset=self._font_encoding,
            )

        for color_name, color_def in self._color_definitions.items():
            char_styles[f'color_{color_name}'] = CharacterStyle(
                name=f'color_{color_name}',
                color=color_def.get('spec'),
                _meta={'model': color_def.get('model'), 'spec': color_def.get('spec')},
            )
        char_styles['textcolor_default'] = CharacterStyle(name='textcolor')

        size_map = {
            'tiny': 5.0, 'scriptsize': 7.0, 'footnotesize': 8.0,
            'small': 9.0, 'normalsize': 10.0, 'large': 12.0,
            'Large': 14.4, 'LARGE': 17.28, 'huge': 20.74, 'Huge': 24.88,
        }
        for sz_name, sz_val in size_map.items():
            char_styles[f'size_{sz_name}'] = CharacterStyle(name=f'size_{sz_name}', size=sz_val)

        char_styles['rmfamily'] = CharacterStyle(name='rmfamily', font_family='roman')
        char_styles['sffamily'] = CharacterStyle(name='sffamily', font_family='sans')
        char_styles['ttfamily'] = CharacterStyle(name='ttfamily', font_family='mono')

        if self._base_font:
            char_styles['setmainfont'] = CharacterStyle(
                name='setmainfont', font=self._base_font,
            )
        if self._sans_font:
            char_styles['setsansfont'] = CharacterStyle(
                name='setsansfont', font=self._sans_font,
            )
        if self._mono_font:
            char_styles['setmonofont'] = CharacterStyle(
                name='setmonofont', font=self._mono_font,
            )

        para_styles['normal'] = ParagraphStyle(name='normal')
        para_styles['chapter'] = ParagraphStyle(name='chapter', spacing_after=24.0)
        para_styles['section'] = ParagraphStyle(name='section', spacing_after=18.0)
        para_styles['subsection'] = ParagraphStyle(name='subsection', spacing_after=14.0)
        para_styles['subsubsection'] = ParagraphStyle(name='subsubsection', spacing_after=12.0)
        para_styles['paragraph'] = ParagraphStyle(name='paragraph', spacing_after=10.0)
        para_styles['subparagraph'] = ParagraphStyle(name='subparagraph', spacing_after=8.0)
        para_styles['center'] = ParagraphStyle(name='center', alignment='center')
        para_styles['flushleft'] = ParagraphStyle(name='flushleft', alignment='left')
        para_styles['flushright'] = ParagraphStyle(name='flushright', alignment='right')

        if self._indentation is not None:
            para_styles['indented'] = ParagraphStyle(name='indented', indent_left=self._indentation)
        if self._parskip is not None:
            para_styles['parskip'] = ParagraphStyle(name='parskip', spacing_after=self._parskip)
        if self._line_spacing is not None:
            para_styles['line_spacing'] = ParagraphStyle(
                name='line_spacing',
                line_spacing=self._line_spacing,
                line_spacing_rule=self._line_spacing_rule,
            )

        list_styles: dict[str, ListStyle] = {}
        list_styles['enumerate'] = ListStyle(name='enumerate', level_styles={
            i: {'format': 'decimal'} for i in range(1, 7)
        })
        list_styles['itemize'] = ListStyle(name='itemize', level_styles={
            i: {'symbol': chr(8226 if i == 1 else 9702 if i == 2 else 9642 if i == 3 else 8226)}
            for i in range(1, 7)
        })
        list_styles['description'] = ListStyle(name='description')

        table_styles: dict[str, Any] = {
            'tabular': TableStyle(name='tabular'),
            'longtable': TableStyle(name='longtable'),
        }

        return StyleSheet(
            character_styles=char_styles,
            paragraph_styles=para_styles,
            list_styles=list_styles,
            table_styles=table_styles,
        )

    def _build_pages(self) -> list:
        return []

    def _build_doc_metadata(self) -> dict[str, Any]:
        fs: dict[str, Any] = {}

        fs['document_class'] = self._document_class
        fs['document_options'] = self._document_options.copy()

        fs['loaded_packages'] = list(self._loaded_packages)

        if self._font_encoding:
            fs['font_encoding'] = self._font_encoding
        if self._input_encoding:
            fs['input_encoding'] = self._input_encoding
        if self._base_font:
            fs['base_font'] = self._base_font
        if self._sans_font:
            fs['sans_font'] = self._sans_font
        if self._mono_font:
            fs['mono_font'] = self._mono_font

        for key in ['textwidth', 'textheight', 'topmargin', 'headheight', 'headsep',
                     'footskip', 'oddsidemargin', 'evensidemargin', 'marginparwidth',
                     'marginparsep', 'paperwidth', 'paperheight', 'hoffset', 'voffset',
                     'columnsep', 'columnseprule', 'linewidth', 'parindent', 'parskip']:
            val = getattr(self, '_' + key, None)
            if val is not None:
                fs[key] = val

        fs['color_definitions'] = dict(self._color_definitions)

        if self._current_language:
            fs['language'] = self._current_language
        if self._languages:
            fs['languages'] = list(self._languages)

        if self._graphicspath:
            fs['graphicspath'] = list(self._graphicspath)
        if self._graphics_extensions:
            fs['graphics_extensions'] = list(self._graphics_extensions)

        fs['footnote_count'] = len(self._footnotes)
        fs['endnote_count'] = len(self._endnotes)
        fs['cross_reference_count'] = len(self._cross_references)
        fs['index_entry_count'] = len(self._index_entries)
        fs['toc_entry_count'] = len(self._toc_entries)
        fs['caption_count'] = len(self._captions)
        fs['label_count'] = len(self._labels)
        fs['is_appendix'] = self._is_appendix

        if self._title:
            fs['title'] = self._title
        if self._author:
            fs['author'] = self._author
        if self._date:
            fs['date'] = self._date

        return fs
