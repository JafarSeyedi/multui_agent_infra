# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import os
import re
from datetime import datetime
from io import BytesIO
from typing import Any
from typing import BinaryIO
from typing import cast
from typing import Literal
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from zipfile import BadZipFile

from ....models.base import BinaryEncoding
from .docx_chart_extractor import parse_docx_chart
from .docx_diagram_extractor import parse_diagram
from .docx_image_extractor import DOCXImageExtractor
from .docx_math_parser import OMMLParser
from .docx_models import (
    DOCXBreak, DOCXChartData, DOCXColumns, DOCXComment, DOCXComplexField,
    DOCXCoreProperties, DOCXCustomProperties, DOCXDocument, DOCXDrawing,
    DOCXExtendedProperties, DOCXField, DOCXFootnoteEndnote, DOCXHeaderFooter,
    DOCXNumberingDefinition, DOCXNumberingInstance, DOCXNumberingLevel,
    DOCXPageMargins, DOCXPageSize, DOCXParagraph, DOCXParagraphProperties,
    DOCXRTLProperties, DOCXRunContent, DOCXRunProperties, DOCXSection,
    DOCXStyle, DOCXSymbol, DOCXTab, DOCXTable, DOCXTableCell,
    DOCXTableCellProperties, DOCXTableGrid, DOCXTableProperties, DOCXTableRow,
    DOCXTextRun, DOCXTOCField, DOCXWatermark, NumberingLevelSuffix,
    ParagraphAlignment, SectionType, TextDirection, VerticalAlignment,
)
from .docx_style_parser import DocxStyleParser
from .docx_table_parser import DocxTableParser
from .docx_utils import get_element_text, NS, parse_border_element
from .docx_utils import parse_dxa_to_points, parse_shading_element
from .docx_utils import safe_find, safe_findall


class DOCXExtractorProperties:
    """Mixin providing DOCX extractor properties methods."""

    def _extract_core_properties(self) -> DOCXCoreProperties:
        """Extract core properties from docProps/core.xml."""
        props = DOCXCoreProperties()

        core_xml = self._get_xml_document('docProps/core.xml')
        if core_xml is None:
            return props

        # Map Dublin Core elements
        ns_map = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        }

        props.title = get_element_text(core_xml, './/dc:title', ns_map)
        props.subject = get_element_text(core_xml, './/dc:subject', ns_map)
        props.creator = get_element_text(core_xml, './/dc:creator', ns_map)
        props.description = get_element_text(core_xml, './/dc:description', ns_map)
        props.last_modified_by = get_element_text(core_xml, './/cp:lastModifiedBy', ns_map)
        props.revision = self._parse_int(get_element_text(core_xml, './/cp:revision', ns_map))
        props.category = get_element_text(core_xml, './/cp:category', ns_map)
        props.content_status = get_element_text(core_xml, './/cp:contentStatus', ns_map)

        # Keywords (can be multiple)
        keywords_elem = safe_find(core_xml, './/cp:keywords', ns_map)
        if keywords_elem is not None and keywords_elem.text:
            props.keywords = [k.strip() for k in keywords_elem.text.split(',') if k.strip()]

        # Dates
        created_str = get_element_text(core_xml, './/dcterms:created', ns_map)
        if created_str:
            props.created = self._parse_w3c_datetime(created_str)

        modified_str = get_element_text(core_xml, './/dcterms:modified', ns_map)
        if modified_str:
            props.modified = self._parse_w3c_datetime(modified_str)

        return props


    def _extract_extended_properties(self) -> DOCXExtendedProperties:
        """Extract extended properties from docProps/app.xml."""
        props = DOCXExtendedProperties()

        app_xml = self._get_xml_document('docProps/app.xml')
        if app_xml is None:
            return props

        ns_map = {
            'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
            'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        }

        props.template = get_element_text(app_xml, './/ep:Template', ns_map)
        props.manager = get_element_text(app_xml, './/ep:Manager', ns_map)
        props.company = get_element_text(app_xml, './/ep:Company', ns_map)
        props.presentation_format = get_element_text(app_xml, './/ep:PresentationFormat', ns_map)
        props.application = get_element_text(app_xml, './/ep:Application', ns_map)
        props.app_version = get_element_text(app_xml, './/ep:AppVersion', ns_map)

        # Numeric properties
        props.pages = self._parse_int(get_element_text(app_xml, './/ep:Pages', ns_map))
        props.words = self._parse_int(get_element_text(app_xml, './/ep:Words', ns_map))
        props.characters = self._parse_int(get_element_text(app_xml, './/ep:Characters', ns_map))
        props.characters_with_spaces = self._parse_int(get_element_text(app_xml, './/ep:CharactersWithSpaces', ns_map))
        props.lines = self._parse_int(get_element_text(app_xml, './/ep:Lines', ns_map))
        props.paragraphs = self._parse_int(get_element_text(app_xml, './/ep:Paragraphs', ns_map))
        props.total_time = self._parse_int(get_element_text(app_xml, './/ep:TotalTime', ns_map))

        # Boolean properties
        props.scale_crop = self._parse_bool(get_element_text(app_xml, './/ep:ScaleCrop', ns_map))
        props.links_up_to_date = self._parse_bool(get_element_text(app_xml, './/ep:LinksUpToDate', ns_map))
        props.shared_doc = self._parse_bool(get_element_text(app_xml, './/ep:SharedDoc', ns_map))
        props.hyperlinks_changed = self._parse_bool(get_element_text(app_xml, './/ep:HyperlinksChanged', ns_map))

        return props


    def _extract_custom_properties(self) -> DOCXCustomProperties:
        """Extract custom properties from docProps/custom.xml."""
        props = DOCXCustomProperties()

        custom_xml = self._get_xml_document('docProps/custom.xml')
        if custom_xml is None:
            return props

        ns_map = {
            'cp': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
            'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
        }

        for prop_elem in safe_findall(custom_xml, './/cp:property', ns_map):
            name = prop_elem.get('name')
            if not name:
                continue

            # Determine value type
            value_elem = None
            for vt_type in ['vt:lpwstr', 'vt:lpstr', 'vt:i4', 'vt:r8', 'vt:bool', 'vt:filetime', 'vt:date']:
                value_elem = safe_find(prop_elem, f'.//{vt_type}', ns_map)
                if value_elem is not None:
                    break

            if value_elem is not None:
                value = self._parse_vt_value(value_elem)
                props.properties[name] = value

        return props


    def _parse_vt_value(self, elem: ET.Element) -> Any:
        """Parse a VT (Variant Type) value element."""
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag in ('lpwstr', 'lpstr'):
            return elem.text or ''
        elif tag == 'i4':
            return self._parse_int(elem.text)
        elif tag == 'r8':
            return self._parse_float(elem.text)
        elif tag == 'bool':
            text = (elem.text or '').lower()
            return text == 'true' or text == '1'
        elif tag in ('filetime', 'date'):
            return elem.text
        else:
            return elem.text


    def _extract_settings(self) -> dict[str, Any]:
        """Extract document settings from settings.xml."""
        settings: dict[str, Any] = {}

        settings_xml = self._get_xml_document('word/settings.xml')
        if settings_xml is None:
            return settings

        # Zoom
        zoom_elem = safe_find(settings_xml, './/w:zoom')
        if zoom_elem is not None:
            settings['zoom'] = {
                'percent': self._parse_int(zoom_elem.get(f'{{{NS["w"]}}}percent')),
                'type': zoom_elem.get(f'{{{NS["w"]}}}val')
            }

        # Default tab stop
        tab_elem = safe_find(settings_xml, './/w:defaultTabStop')
        if tab_elem is not None:
            settings['default_tab_stop'] = parse_dxa_to_points(tab_elem.get(f'{{{NS["w"]}}}val'))

        # Display background shape
        bg_shape_elem = safe_find(settings_xml, './/w:displayBackgroundShape')
        if bg_shape_elem is not None:
            settings['display_background_shape'] = True

        # Even and odd headers/footers
        even_odd_elem = safe_find(settings_xml, './/w:evenAndOddHeaders')
        if even_odd_elem is not None:
            settings['even_and_odd_headers'] = True

        # Track revisions
        track_rev_elem = safe_find(settings_xml, './/w:trackRevisions')
        if track_rev_elem is not None:
            settings['track_revisions'] = True

        # Proofing state
        proof_elem = safe_find(settings_xml, './/w:proofState')
        if proof_elem is not None:
            settings['proof_state'] = proof_elem.get(f'{{{NS["w"]}}}val')

        # Document protection
        protect_elem = safe_find(settings_xml, './/w:documentProtection')
        if protect_elem is not None:
            settings['document_protection'] = {
                'edit': protect_elem.get(f'{{{NS["w"]}}}edit'),
                'enforcement': protect_elem.get(f'{{{NS["w"]}}}enforcement') == '1'
            }

        # Compatibility settings
        compat_elem = safe_find(settings_xml, './/w:compat')
        if compat_elem is not None:
            compat_settings = {}
            for setting in compat_elem:
                tag = setting.tag.split('}')[-1] if '}' in setting.tag else setting.tag
                compat_settings[tag] = True
            settings['compatibility'] = compat_settings

        return settings


    def _extract_theme(self) -> dict[str, Any] | None:
        """Extract theme from theme1.xml."""
        theme: dict[str, Any] = {}

        theme_xml = self._get_xml_document('word/theme/theme1.xml')
        if theme_xml is None:
            return None

        # Theme name
        name_elem = safe_find(theme_xml, './/a:themeName', {'a': NS.get('a', '')})
        if name_elem is not None:
            theme['name'] = name_elem.get('name')

        # Theme colors
        theme_colors_elem = safe_find(theme_xml, './/a:themeElements/a:clrScheme', {'a': NS.get('a', '')})
        if theme_colors_elem is not None:
            colors = {}
            color_mappings = {
                'dk1': 'dark1',
                'lt1': 'light1',
                'dk2': 'dark2',
                'lt2': 'light2',
                'accent1': 'accent1',
                'accent2': 'accent2',
                'accent3': 'accent3',
                'accent4': 'accent4',
                'accent5': 'accent5',
                'accent6': 'accent6',
                'hlink': 'hyperlink',
                'folHlink': 'followed_hyperlink'
            }

            for elem_name, key_name in color_mappings.items():
                color_elem = safe_find(theme_colors_elem, f'.//a:{elem_name}', {'a': NS.get('a', '')})
                if color_elem is not None:
                    sys_clr = safe_find(color_elem, './/a:sysClr', {'a': NS.get('a', '')})
                    srgb_clr = safe_find(color_elem, './/a:srgbClr', {'a': NS.get('a', '')})

                    if sys_clr is not None:
                        colors[key_name] = {
                            'type': 'system',
                            'value': sys_clr.get('val')
                        }
                    elif srgb_clr is not None:
                        colors[key_name] = {
                            'type': 'srgb',
                            'value': srgb_clr.get('val')
                        }

            theme['colors'] = colors

        # Theme fonts
        font_scheme_elem = safe_find(theme_xml, './/a:themeElements/a:fontScheme', {'a': NS.get('a', '')})
        if font_scheme_elem is not None:
            fonts = {}

            major_font_elem = safe_find(font_scheme_elem, './/a:majorFont', {'a': NS.get('a', '')})
            if major_font_elem is not None:
                fonts['major'] = self._parse_theme_fonts(major_font_elem)

            minor_font_elem = safe_find(font_scheme_elem, './/a:minorFont', {'a': NS.get('a', '')})
            if minor_font_elem is not None:
                fonts['minor'] = self._parse_theme_fonts(minor_font_elem)

            theme['fonts'] = fonts

        # Theme format scheme
        fmt_scheme_elem = safe_find(theme_xml, './/a:themeElements/a:fmtScheme', {'a': NS.get('a', '')})
        if fmt_scheme_elem is not None:
            fmt_scheme = {}

            # Fill style list
            fill_list_elem = safe_find(fmt_scheme_elem, './/a:fillStyleLst', {'a': NS.get('a', '')})
            if fill_list_elem is not None:
                fmt_scheme['fill_styles'] = self._parse_theme_fill_styles(fill_list_elem)

            # Line style list
            ln_list_elem = safe_find(fmt_scheme_elem, './/a:lnStyleLst', {'a': NS.get('a', '')})
            if ln_list_elem is not None:
                fmt_scheme['line_styles'] = self._parse_theme_line_styles(ln_list_elem)

            # Effect style list
            effect_list_elem = safe_find(fmt_scheme_elem, './/a:effectStyleLst', {'a': NS.get('a', '')})
            if effect_list_elem is not None:
                fmt_scheme['effect_styles'] = self._parse_theme_effect_styles(effect_list_elem)

            # Background fill style list
            bg_fill_list_elem = safe_find(fmt_scheme_elem, './/a:bgFillStyleLst', {'a': NS.get('a', '')})
            if bg_fill_list_elem is not None:
                fmt_scheme['background_fill_styles'] = self._parse_theme_fill_styles(bg_fill_list_elem)

            theme['format_scheme'] = fmt_scheme

        return theme


    def _parse_theme_fonts(self, elem: ET.Element) -> dict[str, str]:
        """Parse theme font definitions."""
        fonts: dict[str, str] = {}
        ns_map = {'a': NS.get('a', '')}

        for script in ['latin', 'ea', 'cs']:
            font_elem = safe_find(elem, f'.//a:{script}', ns_map)
            if font_elem is not None:
                fonts[script] = font_elem.get('typeface', '')

        return fonts


    def _parse_theme_fill_styles(self, elem: ET.Element) -> list[dict[str, Any]]:
        """Parse theme fill styles."""
        styles: list[dict[str, Any]] = []
        ns_map = {'a': NS.get('a', '')}

        for fill_elem in elem:
            style: dict[str, Any] = {}
            tag = fill_elem.tag.split('}')[-1] if '}' in fill_elem.tag else fill_elem.tag

            if tag == 'solidFill':
                style['type'] = 'solid'
                srgb_clr = safe_find(fill_elem, './/a:srgbClr', ns_map)
                if srgb_clr is not None:
                    style['color'] = srgb_clr.get('val')
                scheme_clr = safe_find(fill_elem, './/a:schemeClr', ns_map)
                if scheme_clr is not None:
                    style['scheme_color'] = scheme_clr.get('val')
            elif tag == 'gradFill':
                style['type'] = 'gradient'
            elif tag == 'pattFill':
                style['type'] = 'pattern'
            elif tag == 'noFill':
                style['type'] = 'none'

            styles.append(style)

        return styles


    def _parse_theme_line_styles(self, elem: ET.Element) -> list[dict[str, Any]]:
        """Parse theme line styles."""
        styles: list[dict[str, Any]] = []
        ns_map = {'a': NS.get('a', '')}

        for ln_elem in elem:
            style: dict[str, Any] = {}
            tag = ln_elem.tag.split('}')[-1] if '}' in ln_elem.tag else ln_elem.tag

            if tag == 'ln':
                width = self._parse_int(ln_elem.get('w'))
                if width:
                    style['width'] = width / 12700  # EMU to points

                cap = ln_elem.get('cap')
                if cap:
                    style['cap'] = cap

                cmpd = ln_elem.get('cmpd')
                if cmpd:
                    style['compound'] = cmpd

                algn = ln_elem.get('algn')
                if algn:
                    style['alignment'] = algn

                # Fill
                solid_fill = safe_find(ln_elem, './/a:solidFill', ns_map)
                if solid_fill is not None:
                    style['fill_type'] = 'solid'
                    srgb_clr = safe_find(solid_fill, './/a:srgbClr', ns_map)
                    if srgb_clr is not None:
                        style['color'] = srgb_clr.get('val')

                # Dash
                prst_dash = safe_find(ln_elem, './/a:prstDash', ns_map)
                if prst_dash is not None:
                    style['dash'] = prst_dash.get('val')

            styles.append(style)

        return styles


    def _parse_theme_effect_styles(self, elem: ET.Element) -> list[dict[str, Any]]:
        """Parse theme effect styles."""
        styles: list[dict[str, Any]] = []
        ns_map = {'a': NS.get('a', '')}

        for effect_elem in elem:
            style: dict[str, Any] = {}
            tag = effect_elem.tag.split('}')[-1] if '}' in effect_elem.tag else effect_elem.tag

            if tag == 'effectStyle':
                effect_list = safe_find(effect_elem, './/a:effectLst', ns_map)
                if effect_list is not None:
                    # Shadow
                    shadow = safe_find(effect_list, './/a:outerShdw', ns_map)
                    if shadow is not None:
                        style['shadow'] = {
                            'blur_rad': self._parse_int(shadow.get('blurRad')),
                            'dist': self._parse_int(shadow.get('dist')),
                            'dir': self._parse_int(shadow.get('dir')),
                            'algn': shadow.get('algn')
                        }

                    # Reflection
                    reflection = safe_find(effect_list, './/a:reflection', ns_map)
                    if reflection is not None:
                        style['reflection'] = {
                            'blur_rad': self._parse_int(reflection.get('blurRad')),
                            'st_a': self._parse_int(reflection.get('stA')),
                            'st_pos': self._parse_int(reflection.get('stPos')),
                            'end_a': self._parse_int(reflection.get('endA')),
                            'end_pos': self._parse_int(reflection.get('endPos')),
                            'dist': self._parse_int(reflection.get('dist')),
                            'dir': self._parse_int(reflection.get('dir'))
                        }

                    # Glow
                    glow = safe_find(effect_list, './/a:glow', ns_map)
                    if glow is not None:
                        style['glow'] = {
                            'rad': self._parse_int(glow.get('rad'))
                        }

            styles.append(style)

        return styles


    def _extract_font_table(self) -> dict[str, dict[str, Any]]:
        """Extract font table from fontTable.xml."""
        font_table: dict[str, dict[str, Any]] = {}

        fonts_xml = self._get_xml_document('word/fontTable.xml')
        if fonts_xml is None:
            return font_table

        for font_elem in safe_findall(fonts_xml, './/w:font'):
            font_name = font_elem.get(f'{{{NS["w"]}}}name', '')
            if font_name:
                # Get alternative names
                alt_name_elem = safe_find(font_elem, './/w:altName')
                alt_name = alt_name_elem.get(f'{{{NS["w"]}}}val') if alt_name_elem is not None else None

                # Get font family
                family_elem = safe_find(font_elem, './/w:family')
                family = family_elem.get(f'{{{NS["w"]}}}val') if family_elem is not None else None

                # Get pitch
                pitch_elem = safe_find(font_elem, './/w:pitch')
                pitch = pitch_elem.get(f'{{{NS["w"]}}}val') if pitch_elem is not None else None

                # Get charset
                charset_elem = safe_find(font_elem, './/w:charset')
                charset = charset_elem.get(f'{{{NS["w"]}}}val') if charset_elem is not None else None

                # Store font info
                font_info = {
                    'name': font_name,
                    'alt_name': alt_name,
                    'family': family,
                    'pitch': pitch,
                    'charset': charset
                }

                # Remove None values
                font_info = {k: v for k, v in font_info.items() if v is not None}

                if font_info:
                    font_table[font_name] = font_info

        return font_table


    def _extract_web_settings(self) -> dict[str, Any]:
        """Extract web settings from webSettings.xml."""
        web_settings: dict[str, Any] = {}

        web_xml = self._get_xml_document('word/webSettings.xml')
        if web_xml is None:
            return web_settings

        # Browser optimization
        optimize_elem = safe_find(web_xml, './/w:optimizeForBrowser')
        if optimize_elem is not None:
            web_settings['optimize_for_browser'] = optimize_elem.get(f'{{{NS["w"]}}}val') == 'true'

        # Target browser
        target_elem = safe_find(web_xml, './/w:targetScreenSz')
        if target_elem is not None:
            web_settings['target_screen_size'] = target_elem.get(f'{{{NS["w"]}}}val')

        # Save smart tags as XML
        smart_tags_elem = safe_find(web_xml, './/w:saveSmartTagsAsXml')
        if smart_tags_elem is not None:
            web_settings['save_smart_tags_as_xml'] = smart_tags_elem.get(f'{{{NS["w"]}}}val') == 'true'

        # PNG or JPEG for images
        png_elem = safe_find(web_xml, './/w:allowPNG')
        if png_elem is not None:
            web_settings['allow_png'] = png_elem.get(f'{{{NS["w"]}}}val') == 'true'

        # Rely on CSS for font formatting
        css_elem = safe_find(web_xml, './/w:relyOnCSS')
        if css_elem is not None:
            web_settings['rely_on_css'] = css_elem.get(f'{{{NS["w"]}}}val') == 'true'

        # Encoding
        encoding_elem = safe_find(web_xml, './/w:encoding')
        if encoding_elem is not None:
            web_settings['encoding'] = encoding_elem.get(f'{{{NS["w"]}}}val')

        return web_settings


    def _parse_int(self, value: str | None) -> int | None:
        """Parse string to integer."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


    def _parse_float(self, value: str | None) -> float | None:
        """Parse string to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


    def _parse_bool(self, value: str | None) -> bool:
        """Parse string to boolean."""
        if value is None:
            return False
        return value.lower() in ('true', '1', 'yes', 'on')


    def _parse_w3c_datetime(self, datetime_str: str) -> str | None:
        """Parse W3C datetime format to ISO 8601 string."""
        if not datetime_str:
            return None

        # Already in ISO format
        if 'T' in datetime_str:
            return datetime_str.replace('Z', '+00:00')

        # Try to parse and reformat
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except (ValueError, TypeError):
            return datetime_str


