from __future__ import annotations

import io
import zipfile
from typing import Any


def package_docx(parts: dict[str, bytes]) -> bytes:
    """
    Package OOXML parts into a valid .docx ZIP archive.

    Creates an in-memory ZIP with DEFLATE compression.
    [Content_Types].xml is written first (uncompressed per spec).
    All other parts are written with DEFLATE compression.
    Returns the ZIP file as bytes.
    """
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED)

    ct_key = "[Content_Types].xml"
    if ct_key in parts:
        info = zipfile.ZipInfo(filename=ct_key)
        info.compress_type = zipfile.ZIP_STORED
        zf.writestr(info, parts[ct_key])

    for name, data in parts.items():
        if name == ct_key:
            continue
        zf.writestr(name, data)

    zf.close()
    return buf.getvalue()


def content_types_xml(parts: dict[str, Any] | None = None) -> str:
    """
    Generate [Content_Types].xml for the DOCX package.

    Declares default extensions and overrides for all parts
    included in the document.
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '  <Default Extension="xml" ContentType="application/xml"/>',
        '  <Default Extension="png" ContentType="image/png"/>',
        '  <Default Extension="jpg" ContentType="image/jpeg"/>',
        '  <Default Extension="jpeg" ContentType="image/jpeg"/>',
        '  <Default Extension="gif" ContentType="image/gif"/>',
        '  <Default Extension="bmp" ContentType="image/bmp"/>',
        '  <Default Extension="tiff" ContentType="image/tiff"/>',
        '  <Default Extension="svg" ContentType="image/svg+xml"/>',
        '  <Default Extension="emf" ContentType="image/x-emf"/>',
        '  <Default Extension="wmf" ContentType="image/x-wmf"/>',
        '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>',
        '  <Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>',
        '  <Override PartName="/word/endnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml"/>',
        '  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>',
        '  <Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]

    if parts and "/docProps/custom.xml" in parts:
        lines.append(
            '  <Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>'
        )

    lines.append("</Types>")
    return "\n".join(lines)


def rels_xml() -> str:
    """
    Generate _rels/.rels — package-level relationships.

    Links the core document, core properties, and extended properties.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def document_rels_xml(rels: list[dict[str, str]]) -> str:
    """
    Generate word/_rels/document.xml.rels — document-level relationships.

    Args:
        rels: List of dicts with keys 'id', 'type', 'target', and optionally 'mode'.
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]

    type_map = {
        "styles": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
        "numbering": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering",
        "footnotes": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes",
        "endnotes": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes",
        "comments": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
        "theme": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme",
        "image": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
        "hyperlink": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        "fontTable": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable",
        "settings": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings",
        "webSettings": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/webSettings",
    }

    for i, rel in enumerate(rels, start=1):
        r_id = rel.get("id", f"rId{i}")
        rel_type = rel.get("type", "")
        target = rel.get("target", "")
        mode = rel.get("mode", "")
        resolved_type = type_map.get(rel_type, rel_type)
        mode_attr = f' TargetMode="{mode}"' if mode else ""
        lines.append(
            f'<Relationship Id="{r_id}" Type="{resolved_type}" Target="{target}"{mode_attr}/>'
        )

    lines.append("</Relationships>")
    return "\n".join(lines)


def core_properties_xml(document: Any) -> str:
    """
    Generate docProps/core.xml — Dublin Core metadata.

    Extracts title, creator, subject, description, keywords,
    dates from the USDMDocument.
    """
    title = _esc_xml(getattr(document, "title", "") or "")
    metadata = getattr(document, "metadata", {}) or {}
    creator = _esc_xml(metadata.get("author", "USDM"))
    subject = _esc_xml(metadata.get("subject", ""))
    description = _esc_xml(metadata.get("description", ""))
    keywords = _esc_xml(metadata.get("keywords", ""))

    created_at = getattr(document, "created_at", None)
    modified_at = getattr(document, "modified_at", None)
    created_str = created_at.isoformat() if created_at else ""
    modified_str = modified_at.isoformat() if modified_at else ""

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
    ]
    if title:
        lines.append(f"  <dc:title>{title}</dc:title>")
    if subject:
        lines.append(f"  <dc:subject>{subject}</dc:subject>")
    lines.append(f"  <dc:creator>{creator}</dc:creator>")
    if keywords:
        lines.append(f"  <cp:keywords>{keywords}</cp:keywords>")
    if description:
        lines.append(f"  <dc:description>{description}</dc:description>")
    lines.append(f"  <cp:lastModifiedBy>{creator}</cp:lastModifiedBy>")
    if created_str:
        lines.append(f'  <dcterms:created xsi:type="dcterms:W3CDTF">{created_str}</dcterms:created>')
    if modified_str:
        lines.append(f'  <dcterms:modified xsi:type="dcterms:W3CDTF">{modified_str}</dcterms:modified>')
    lines.append("</cp:coreProperties>")
    return "\n".join(lines)


def app_properties_xml(document: Any) -> str:
    """
    Generate docProps/app.xml — extended document properties.

    Includes application name, company, manager, page/word/character counts.
    """
    metadata = getattr(document, "metadata", {}) or {}
    company = _esc_xml(metadata.get("company", ""))
    manager = _esc_xml(metadata.get("manager", ""))
    page_count = metadata.get("page_count", "0")
    word_count = metadata.get("word_count", "0")
    char_count = metadata.get("character_count", "0")
    para_count = metadata.get("paragraph_count", "0")

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">',
        "  <Application>USDM Document Engine</Application>",
        "  <DocSecurity>0</DocSecurity>",
        "  <ScaleCrop>false</ScaleCrop>",
        "  <LinksUpToDate>false</LinksUpToDate>",
        "  <SharedDoc>false</SharedDoc>",
        "  <HyperlinksChanged>false</HyperlinksChanged>",
    ]
    if company:
        lines.append(f"  <Company>{company}</Company>")
    if manager:
        lines.append(f"  <Manager>{manager}</Manager>")
    lines.append(f"  <Pages>{page_count}</Pages>")
    lines.append(f"  <Words>{word_count}</Words>")
    lines.append(f"  <Characters>{char_count}</Characters>")
    lines.append(f"  <Paragraphs>{para_count}</Paragraphs>")
    lines.append("</Properties>")
    return "\n".join(lines)


def custom_properties_xml(custom_props: dict[str, Any]) -> str:
    """
    Generate docProps/custom.xml — user-defined custom properties.

    Args:
        custom_props: Dictionary mapping property names to values.
    """
    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">',
    ]
    for i, (name, value) in enumerate(custom_props.items(), start=1):
        lines.append(
            f'  <property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{i}" name="{_esc_xml(name)}">'
            f'<vt:lpwstr>{_esc_xml(str(value))}</vt:lpwstr></property>'
        )
    lines.append("</Properties>")
    return "\n".join(lines)


def minimal_theme_xml() -> str:
    """
    Generate a minimal word/theme/theme1.xml.

    Provides a basic Office theme with a two-font scheme
    and minimal formatting scheme.
    """
    t = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<a:theme xmlns:a="{t}" name="Office Theme">'
        '<a:themeElements>'
        '<a:clrScheme name="Office">'
        '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
        '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
        '<a:dk2><a:srgbClr val="44546A"/></a:dk2>'
        '<a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>'
        '<a:accent1><a:srgbClr val="4472C4"/></a:accent1>'
        '<a:accent2><a:srgbClr val="ED7D31"/></a:accent2>'
        '<a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>'
        '<a:accent4><a:srgbClr val="FFC000"/></a:accent4>'
        '<a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>'
        '<a:accent6><a:srgbClr val="70AD47"/></a:accent6>'
        '<a:hlink><a:srgbClr val="0563C1"/></a:hlink>'
        '<a:folHlink><a:srgbClr val="954F72"/></a:folHlink>'
        '</a:clrScheme>'
        '<a:fontScheme name="Office">'
        '<a:majorFont>'
        '<a:latin typeface="Calibri Light" panose="020F0302020204030204"/>'
        '<a:ea typeface=""/>'
        '<a:cs typeface=""/>'
        '<a:font script="Jpan" typeface="Yu Gothic Light"/>'
        '<a:font script="Hang" typeface="맑은 고딕"/>'
        '<a:font script="Hans" typeface="DengXian Light"/>'
        '<a:font script="Hant" typeface="新細明體"/>'
        '<a:font script="Arab" typeface="Times New Roman"/>'
        '<a:font script="Hebr" typeface="Times New Roman"/>'
        '<a:font script="Thai" typeface="Angsana New"/>'
        '<a:font script="Ethi" typeface="Nyala"/>'
        '<a:font script="Beng" typeface="Vrinda"/>'
        '<a:font script="Gujr" typeface="Shruti"/>'
        '<a:font script="Khmr" typeface="MoolBoran"/>'
        '<a:font script="Knda" typeface="Tunga"/>'
        '<a:font script="Guru" typeface="Raavi"/>'
        '<a:font script="Cans" typeface="Euphemia"/>'
        '<a:font script="Cher" typeface="Plantagenet Cherokee"/>'
        '<a:font script="Yiii" typeface="Microsoft Yi Baiti"/>'
        '<a:font script="Tibt" typeface="Microsoft Himalaya"/>'
        '<a:font script="Thaa" typeface="MV Boli"/>'
        '<a:font script="Deva" typeface="Mangal"/>'
        '<a:font script="Telu" typeface="Gautami"/>'
        '<a:font script="Taml" typeface="Latha"/>'
        '<a:font script="Syrc" typeface="Estrangelo Edessa"/>'
        '<a:font script="Orya" typeface="Kalinga"/>'
        '<a:font script="Mlym" typeface="Kartika"/>'
        '<a:font script="Laoo" typeface="DokChampa"/>'
        '<a:font script="Sinh" typeface="Iskoola Pota"/>'
        '<a:font script="Mong" typeface="Mongolian Baiti"/>'
        '<a:font script="Viet" typeface="Times New Roman"/>'
        '<a:font script="Uigh" typeface="Microsoft Uighur"/>'
        '<a:font script="Geor" typeface="Sylfaen"/>'
        '</a:majorFont>'
        '<a:minorFont>'
        '<a:latin typeface="Calibri" panose="020F0502020204030204"/>'
        '<a:ea typeface=""/>'
        '<a:cs typeface=""/>'
        '<a:font script="Jpan" typeface="Yu Gothic"/>'
        '<a:font script="Hang" typeface="맑은 고딕"/>'
        '<a:font script="Hans" typeface="DengXian"/>'
        '<a:font script="Hant" typeface="新細明體"/>'
        '<a:font script="Arab" typeface="Arial"/>'
        '<a:font script="Hebr" typeface="Arial"/>'
        '<a:font script="Thai" typeface="Cordia New"/>'
        '<a:font script="Ethi" typeface="Nyala"/>'
        '<a:font script="Beng" typeface="Vrinda"/>'
        '<a:font script="Gujr" typeface="Shruti"/>'
        '<a:font script="Khmr" typeface="DaunPenh"/>'
        '<a:font script="Knda" typeface="Tunga"/>'
        '<a:font script="Guru" typeface="Raavi"/>'
        '<a:font script="Cans" typeface="Euphemia"/>'
        '<a:font script="Cher" typeface="Plantagenet Cherokee"/>'
        '<a:font script="Yiii" typeface="Microsoft Yi Baiti"/>'
        '<a:font script="Tibt" typeface="Microsoft Himalaya"/>'
        '<a:font script="Thaa" typeface="MV Boli"/>'
        '<a:font script="Deva" typeface="Mangal"/>'
        '<a:font script="Telu" typeface="Gautami"/>'
        '<a:font script="Taml" typeface="Latha"/>'
        '<a:font script="Syrc" typeface="Estrangelo Edessa"/>'
        '<a:font script="Orya" typeface="Kalinga"/>'
        '<a:font script="Mlym" typeface="Kartika"/>'
        '<a:font script="Laoo" typeface="DokChampa"/>'
        '<a:font script="Sinh" typeface="Iskoola Pota"/>'
        '<a:font script="Mong" typeface="Mongolian Baiti"/>'
        '<a:font script="Viet" typeface="Arial"/>'
        '<a:font script="Uigh" typeface="Microsoft Uighur"/>'
        '<a:font script="Geor" typeface="Sylfaen"/>'
        '</a:minorFont>'
        '</a:fontScheme>'
        '<a:fmtScheme name="Office">'
        '<a:fillStyleLst>'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:gradFill rotWithShape="1">'
        '<a:gsLst>'
        '<a:gs pos="0"><a:schemeClr val="phClr"><a:lumMod val="110000"/><a:satMod val="105000"/><a:tint val="67000"/></a:schemeClr></a:gs>'
        '<a:gs pos="50000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="103000"/><a:tint val="73000"/></a:schemeClr></a:gs>'
        '<a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="105000"/><a:satMod val="109000"/><a:tint val="81000"/></a:schemeClr></a:gs>'
        '</a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/>'
        '</a:gradFill>'
        '<a:gradFill rotWithShape="1">'
        '<a:gsLst>'
        '<a:gs pos="0"><a:schemeClr val="phClr"><a:satMod val="103000"/><a:lumMod val="102000"/><a:tint val="94000"/></a:schemeClr></a:gs>'
        '<a:gs pos="50000"><a:schemeClr val="phClr"><a:satMod val="110000"/><a:lumMod val="100000"/><a:shade val="100000"/></a:schemeClr></a:gs>'
        '<a:gs pos="100000"><a:schemeClr val="phClr"><a:lumMod val="99000"/><a:satMod val="120000"/><a:shade val="78000"/></a:schemeClr></a:gs>'
        '</a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/>'
        '</a:gradFill>'
        '</a:fillStyleLst>'
        '<a:lnStyleLst>'
        '<a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="8000000"/></a:ln>'
        '<a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="8000000"/></a:ln>'
        '<a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="8000000"/></a:ln>'
        '</a:lnStyleLst>'
        '<a:effectStyleLst>'
        '<a:effectStyle><a:effectLst/></a:effectStyle>'
        '<a:effectStyle><a:effectLst/></a:effectStyle>'
        '<a:effectStyle><a:effectLst/></a:effectStyle>'
        '</a:effectStyleLst>'
        '<a:bgFillStyleLst>'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:solidFill><a:schemeClr val="phClr"><a:tint val="95000"/><a:satMod val="170000"/></a:schemeClr></a:solidFill>'
        '<a:gradFill rotWithShape="1">'
        '<a:gsLst>'
        '<a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="93000"/><a:satMod val="150000"/><a:lumMod val="102000"/></a:schemeClr></a:gs>'
        '<a:gs pos="50000"><a:schemeClr val="phClr"><a:tint val="98000"/><a:satMod val="130000"/><a:lumMod val="103000"/></a:schemeClr></a:gs>'
        '<a:gs pos="100000"><a:schemeClr val="phClr"><a:shade val="99000"/><a:satMod val="120000"/></a:schemeClr></a:gs>'
        '</a:gsLst>'
        '<a:lin ang="5400000" scaled="0"/>'
        '</a:gradFill>'
        '</a:bgFillStyleLst>'
        '</a:fmtScheme>'
        '</a:themeElements>'
        '<a:objectDefaults/>'
        '<a:extraClrSchemeLst/>'
        '</a:theme>'
    )


def _esc_xml(val: str) -> str:
    """Escape XML special characters."""
    s = str(val)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s
