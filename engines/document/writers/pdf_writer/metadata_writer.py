"""
نویسنده Metadataی PDF
"""
import hashlib
import uuid
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from ...models.usdm_models import USDMDocument
from .pdf_objects import PDFInfo
from .pdf_objects import PDFStream


@dataclass
class XMPMetadata:
    """Metadataی XMP"""
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = field(default_factory=list)
    creator: str | None = None
    producer: str | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None
    metadata_date: datetime | None = None
    identifier: str | None = None
    language: str | None = None
    rights: str | None = None
    format: str = "application/pdf"
    pdf_version: str = "1.7"

    # Dublin Core
    dc_contributor: list[str] = field(default_factory=list)
    dc_coverage: str | None = None
    dc_description: str | None = None
    dc_publisher: str | None = None
    dc_relation: list[str] = field(default_factory=list)
    dc_source: str | None = None
    dc_type: str | None = None

    # PDF Schema
    pdf_keywords: str | None = None
    pdf_pdfversion: str | None = None
    pdf_producer: str | None = None

    # XMP Rights Management
    xmp_rights_usage_terms: str | None = None
    xmp_rights_web_statement: str | None = None
    xmp_rights_marked: bool = False

    # Adobe PDF Schema
    pdfa_pdfaid_part: int | None = None
    pdfa_pdfaid_conformance: str | None = None
    pdfa_pdfaid_version: str | None = None


class MetadataWriter:
    """کلاس نوشتن Metadataی PDF"""

    def __init__(self):
        self._next_obj_id = 1
        self.xmp_namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'pdf': 'http://ns.adobe.com/pdf/1.3/',
            'xmpRights': 'http://ns.adobe.com/xap/1.0/rights/',
            'pdfaid': 'http://www.aiim.org/pdfa/ns/id/'
        }

    def create_pdf_metadata(self, document: USDMDocument,
                           options: Any) -> PDFInfo:
        """ایجاد Metadataی PDF از سند USDM"""

        # استخراج Metadata از سند
        metadata = document.metadata if hasattr(document, 'metadata') else None

        # ایجاد شیء PDFInfo
        pdf_info = PDFInfo(
            obj_id=self._next_obj_id,
            title=self._get_title(document, metadata),
            author=self._get_author(metadata),
            subject=self._get_subject(metadata),
            keywords=self._get_keywords(metadata),
            creator=self._get_creator(metadata),
            producer=options.producer if hasattr(options, 'producer') else "USDM PDF Writer",
            creation_date=self._get_creation_date(metadata),
            mod_date=datetime.now()
        )
        self._next_obj_id += 1

        return pdf_info

    def create_xmp_metadata(self, document: USDMDocument,
                           options: Any) -> PDFStream | None:
        """ایجاد Metadataی XMP"""

        # استخراج Metadata
        metadata = document.metadata if hasattr(document, 'metadata') else None

        # ایجاد XMPMetadata
        xmp_metadata = XMPMetadata(
            title=self._get_title(document, metadata),
            author=self._get_author(metadata),
            subject=self._get_subject(metadata),
            keywords=self._get_keywords_list(metadata),
            creator=self._get_creator(metadata),
            producer=options.producer if hasattr(options, 'producer') else "USDM PDF Writer",
            creation_date=self._get_creation_date(metadata),
            modification_date=datetime.now(),
            metadata_date=datetime.now(),
            identifier=self._generate_document_id(document),
            language=self._get_language(document),
            rights=self._get_rights(metadata),
            pdf_version="1.7",
            pdf_keywords=self._get_keywords(metadata),
            pdf_producer=options.producer if hasattr(options, 'producer') else "USDM PDF Writer",
            xmp_rights_marked=self._is_rights_marked(metadata)
        )

        # تولید XML XMP
        xmp_xml = self._generate_xmp_xml(xmp_metadata)

        # ایجاد استریم XMP
        if xmp_xml:
            return PDFStream(
                obj_id=self._next_obj_id,
                data=xmp_xml.encode('utf-8'),
                filters=[]
            )
        self._next_obj_id += 1
        return None

    def _get_title(self, document: USDMDocument, metadata: dict[str, Any] | None) -> str | None:
        """دریافت عنوان"""
        if metadata and metadata.get('title'):
            return metadata['title']
        elif hasattr(document, 'title') and document.title:
            return document.title
        return None

    def _get_author(self, metadata: dict[str, Any] | None) -> str | None:
        """دریافت نویسنده"""
        if metadata:
            author = metadata.get('author')
            authors = metadata.get('authors')
            if author:
                return author
            if authors and len(authors) > 0:
                return ', '.join(authors)
        return None

    def _get_subject(self, metadata: dict[str, Any] | None) -> str | None:
        if metadata and metadata.get('subject'):
            return metadata['subject']
        return None

    def _get_keywords(self, metadata: dict[str, Any] | None) -> str | None:
        if metadata:
            keywords = metadata.get('keywords')
            tags = metadata.get('tags')
            if keywords:
                if isinstance(keywords, list):
                    return ', '.join(keywords)
                return str(keywords)
            if tags and len(tags) > 0:
                return ', '.join(tags)
        return None

    def _get_keywords_list(self, metadata: dict[str, Any] | None) -> list[str]:
        keywords: list[str] = []
        if metadata:
            kw = metadata.get('keywords')
            if kw:
                if isinstance(kw, list):
                    keywords.extend(kw)
                else:
                    keywords.append(str(kw))
            tags = metadata.get('tags')
            if tags:
                keywords.extend(tags)
        return list(set(keywords))

    def _get_creator(self, metadata: dict[str, Any] | None) -> str | None:
        if metadata and metadata.get('creator'):
            return metadata['creator']
        return "USDM Document Processor"

    def _get_creation_date(self, metadata: dict[str, Any] | None) -> datetime | None:
        if metadata and metadata.get('creation_date'):
            creation_date = metadata['creation_date']
            if isinstance(creation_date, datetime):
                return creation_date
            elif isinstance(creation_date, str):
                try:
                    return datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                except Exception:
                    pass
        return datetime.now()

    def _get_rights(self, metadata: dict[str, Any] | None) -> str | None:
        if metadata:
            rights = metadata.get('rights')
            license_val = metadata.get('license')
            if rights:
                return rights
            if license_val:
                return f"Licensed under {license_val}"
        return None

    def _is_rights_marked(self, metadata: dict[str, Any] | None) -> bool:
        if metadata:
            if metadata.get('copyright'):
                return True
            if metadata.get('rights'):
                return True
            if metadata.get('license'):
                return True
        return False

    def _generate_document_id(self, document: USDMDocument) -> str:
        """تولید شناسه منحصر به فرد سند"""
        # ترکیب timestamp و hash سند
        import time

        timestamp = int(time.time() * 1000)
        doc_hash = hashlib.md5(str(document.document_id).encode()).hexdigest()[:16]

        return f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, f'{timestamp}-{doc_hash}')}"

    def _get_language(self, document: USDMDocument) -> str | None:
        """دریافت زبان سند"""
        # بررسی از metadata
        if hasattr(document, 'metadata') and document.metadata:
            if hasattr(document.metadata, 'language') and document.metadata.language:
                return document.metadata.language

        # بررسی از محتوا
        if hasattr(document, 'logical_elements') and document.logical_elements:
            for element in document.logical_elements:
                if hasattr(element, 'language') and element.language:
                    return element.language
                if hasattr(element, 'text_runs') and element.text_runs:
                    for text_run in element.text_runs:
                        if hasattr(text_run, 'language') and text_run.language:
                            return text_run.language

        return "en-US"  # پیش‌فرض

    def _generate_xmp_xml(self, xmp: XMPMetadata) -> str:
        """تولید XML Metadataی XMP"""

        xml_parts = []

        # شروع XMP
        xml_parts.append('<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>')
        xml_parts.append('<x:xmpmeta xmlns:x="adobe:ns:meta/">')
        xml_parts.append('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">')

        # Dublin Core
        xml_parts.append('<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">')
        if xmp.title:
            xml_parts.append(f'  <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{self._escape_xml(xmp.title)}</rdf:li></rdf:Alt></dc:title>')
        if xmp.author:
            xml_parts.append(f'  <dc:creator><rdf:Seq><rdf:li>{self._escape_xml(xmp.author)}</rdf:li></rdf:Seq></dc:creator>')
        if xmp.subject:
            xml_parts.append(f'  <dc:description><rdf:Alt><rdf:li xml:lang="x-default">{self._escape_xml(xmp.subject)}</rdf:li></rdf:Alt></dc:description>')
        if xmp.keywords:
            xml_parts.append('  <dc:subject><rdf:Bag>')
            for keyword in xmp.keywords:
                xml_parts.append(f'    <rdf:li>{self._escape_xml(keyword)}</rdf:li>')
            xml_parts.append('  </rdf:Bag></dc:subject>')
        if xmp.language:
            xml_parts.append(f'  <dc:language><rdf:Bag><rdf:li>{xmp.language}</rdf:li></rdf:Bag></dc:language>')
        if xmp.rights:
            xml_parts.append(f'  <dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{self._escape_xml(xmp.rights)}</rdf:li></rdf:Alt></dc:rights>')
        xml_parts.append('</rdf:Description>')

        # XMP Basic
        xml_parts.append('<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">')
        if xmp.creator:
            xml_parts.append(f'  <xmp:CreatorTool>{self._escape_xml(xmp.creator)}</xmp:CreatorTool>')
        if xmp.creation_date:
            xml_parts.append(f'  <xmp:CreateDate>{xmp.creation_date.isoformat()}</xmp:CreateDate>')
        if xmp.modification_date:
            xml_parts.append(f'  <xmp:ModifyDate>{xmp.modification_date.isoformat()}</xmp:ModifyDate>')
        if xmp.metadata_date:
            xml_parts.append(f'  <xmp:MetadataDate>{xmp.metadata_date.isoformat()}</xmp:MetadataDate>')
        xml_parts.append('</rdf:Description>')

        # PDF Schema
        xml_parts.append('<rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">')
        if xmp.producer:
            xml_parts.append(f'  <pdf:Producer>{self._escape_xml(xmp.producer)}</pdf:Producer>')
        if xmp.pdf_keywords:
            xml_parts.append(f'  <pdf:Keywords>{self._escape_xml(xmp.pdf_keywords)}</pdf:Keywords>')
        if xmp.pdf_version:
            xml_parts.append(f'  <pdf:PDFVersion>{xmp.pdf_version}</pdf:PDFVersion>')
        xml_parts.append('</rdf:Description>')

        # PDF/A Identification
        if xmp.pdfa_pdfaid_part:
            xml_parts.append('<rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">')
            xml_parts.append(f'  <pdfaid:part>{xmp.pdfa_pdfaid_part}</pdfaid:part>')
            if xmp.pdfa_pdfaid_conformance:
                xml_parts.append(f'  <pdfaid:conformance>{xmp.pdfa_pdfaid_conformance}</pdfaid:conformance>')
            xml_parts.append('</rdf:Description>')

        # XMP Rights Management
        if xmp.xmp_rights_marked:
            xml_parts.append('<rdf:Description rdf:about="" xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">')
            xml_parts.append('  <xmpRights:Marked>True</xmpRights:Marked>')
            if xmp.xmp_rights_usage_terms:
                xml_parts.append(f'  <xmpRights:UsageTerms><rdf:Alt><rdf:li xml:lang="x-default">{self._escape_xml(xmp.xmp_rights_usage_terms)}</rdf:li></rdf:Alt></xmpRights:UsageTerms>')
            if xmp.xmp_rights_web_statement:
                xml_parts.append(f'  <xmpRights:WebStatement>{self._escape_xml(xmp.xmp_rights_web_statement)}</xmpRights:WebStatement>')
            xml_parts.append('</rdf:Description>')

        # پایان XMP
        xml_parts.append('</rdf:RDF>')
        xml_parts.append('</x:xmpmeta>')
        xml_parts.append('<?xpacket end="r"?>')

        return '\n'.join(xml_parts)

    def _escape_xml(self, text: str) -> str:
        """فرار کردن کاراکترهای خاص XML"""
        if not text:
            return ""

        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;'
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def create_custom_metadata(self, document: USDMDocument,
                              custom_fields: dict[str, Any]) -> dict[str, Any]:
        """ایجاد Metadataی سفارشی"""
        metadata_dict = {}

        # Metadataی استاندارد
        if hasattr(document, 'metadata') and document.metadata:
            metadata = document.metadata

            # فیلدهای استاندارد
            standard_fields = [
                ('title', 'title'),
                ('author', 'author'),
                ('subject', 'subject'),
                ('keywords', 'keywords'),
                ('creator', 'creator'),
                ('producer', 'producer'),
                ('creation_date', 'creation_date'),
                ('modification_date', 'modification_date'),
                ('language', 'language'),
                ('rights', 'rights'),
                ('license', 'license'),
                ('copyright', 'copyright'),
                ('version', 'version'),
                ('identifier', 'document_id')
            ]

            for pdf_field, usdm_field in standard_fields:
                if hasattr(metadata, usdm_field):
                    value = getattr(metadata, usdm_field)
                    if value:
                        metadata_dict[pdf_field.capitalize()] = value

        # فیلدهای سفارشی
        metadata_dict.update(custom_fields)

        return metadata_dict

    def validate_metadata(self, metadata_dict: dict[str, Any]) -> list[str]:
        """Validation Metadata"""
        warnings = []

        # بررسی فیلدهای اجباری
        required_fields = ['Title', 'Author', 'Creator', 'Producer']
        for required_field in required_fields:
            if required_field not in metadata_dict or not metadata_dict[required_field]:
                warnings.append(f"فیلد {required_field} خالی است")

        # بررسی تاریخ‌ها
        date_fields = ['CreationDate', 'ModDate']
        for date_field in date_fields:
            if date_field in metadata_dict:
                value = metadata_dict[date_field]
                if isinstance(value, str):
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        warnings.append(f"فرمت تاریخ {date_field} نامعتبر است: {value}")

        # بررسی طول رشته‌ها
        string_fields = ['Title', 'Author', 'Subject', 'Keywords']
        for string_field in string_fields:
            if string_field in metadata_dict and metadata_dict[string_field]:
                value = str(metadata_dict[string_field])
                if len(value) > 255:
                    warnings.append(f"فیلد {string_field} بیش از حد طولانی است ({len(value)} کاراکتر)")

        return warnings
