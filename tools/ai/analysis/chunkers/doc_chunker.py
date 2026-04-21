#!/usr/bin/env python3
"""
Documentation Chunker - AI Development Framework
Splits documentation files into semantic chunks for embedding and analysis.

Part of the Level 2 Analysis tools (chunkers/doc_chunker.py)

This doc_chunker.py provides:

1. Multi-Format Support - Markdown, RST, plain text, with extensible architecture
2. Heading-Based Chunking - Splits on configurable heading levels
3. Section Detection - Automatically classifies sections (overview, api, examples, etc.)
4. Code Block Extraction - Identifies and preserves code blocks with language detection
5. Frontmatter Parsing - Extracts YAML frontmatter from Markdown files
6. TOC Generation - Builds table of contents from headings
7. Reference Extraction - Finds links and code references
8. Docstring Support - Specialized parser for Python docstrings (Google style)
9. Hierarchy Preservation - Maintains parent-child relationships
10. Embedding-Ready Export - Formats chunks for vector embedding

The doc chunker complements the code_chunker.py for comprehensive project indexing.
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Iterator, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.file_utils import FileUtils

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DocChunkType(str, Enum):
    """Type of documentation chunk."""
    HEADING = "heading"             # Section heading
    PARAGRAPH = "paragraph"         # Text paragraph
    CODE_BLOCK = "code_block"       # Code snippet
    LIST_ITEM = "list_item"         # List entry
    TABLE = "table"                 # Table content
    TABLE_ROW = "table_row"         # Table row
    QUOTE = "quote"                 # Blockquote
    CALL_OUT = "call_out"           # Note/warning/tip
    LINK = "link"                   # Hyperlink
    IMAGE = "image"                 # Image reference
    METADATA = "metadata"           # Frontmatter
    TOC = "toc"                     # Table of contents
    API_DOC = "api_doc"             # API documentation
    EXAMPLE = "example"             # Usage example
    PARAMETER = "parameter"         # Function parameter
    RETURN = "return"               # Return value description
    EXCEPTION = "exception"         # Exception documentation
    ATTRIBUTE = "attribute"         # Class attribute
    METHOD_DOC = "method_doc"       # Method documentation
    CLASS_DOC = "class_doc"         # Class documentation
    MODULE_DOC = "module_doc"       # Module documentation


class DocFormat(str, Enum):
    """Documentation format."""
    MARKDOWN = "markdown"
    RST = "rst"
    DOCSTRING = "docstring"
    PLAIN = "plain"
    HTML = "html"
    JSON = "json"
    YAML = "yaml"
    UNKNOWN = "unknown"


class DocSection(str, Enum):
    """Documentation section types."""
    OVERVIEW = "overview"
    INSTALLATION = "installation"
    QUICKSTART = "quickstart"
    TUTORIAL = "tutorial"
    HOWTO = "howto"
    REFERENCE = "reference"
    API = "api"
    EXAMPLES = "examples"
    FAQ = "faq"
    CONTRIBUTING = "contributing"
    CHANGELOG = "changelog"
    LICENSE = "license"
    ARCHITECTURE = "architecture"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class DocChunk:
    """A semantic chunk of documentation."""
    id: str
    chunk_type: DocChunkType
    format: DocFormat
    content: str
    file_path: str
    start_line: int
    end_line: int
    heading: Optional[str] = None
    heading_level: int = 0
    section: DocSection = DocSection.UNKNOWN
    parent_heading: Optional[str] = None
    language: Optional[str] = None  # For code blocks
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)  # Links to other docs
    code_refs: List[str] = field(default_factory=list)  # References to code symbols
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    order_index: int = 0
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        if not self.id:
            self.id = f"{self.chunk_type.value}_{self.content_hash[:16]}"


@dataclass
class DocStructure:
    """Document structure information."""
    title: Optional[str] = None
    headings: List[Tuple[int, str, int]] = field(default_factory=list)  # (level, text, line)
    sections: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # heading -> (start, end)
    toc: List[Dict[str, Any]] = field(default_factory=list)
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    total_lines: int = 0


@dataclass
class DocChunkingResult:
    """Result of document chunking."""
    chunks: List[DocChunk]
    structure: DocStructure
    total_chunks: int
    total_lines: int
    avg_chunk_size: float
    chunk_types_distribution: Dict[DocChunkType, int]
    file_path: str
    format: DocFormat
    chunked_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocChunkingConfig:
    """Configuration for document chunking."""
    min_chunk_lines: int = 5
    max_chunk_lines: int = 500
    split_on_headings: bool = True
    split_on_code_blocks: bool = False
    merge_small_chunks: bool = True
    extract_code_refs: bool = True
    extract_links: bool = True
    detect_sections: bool = True
    preserve_hierarchy: bool = True
    include_line_numbers: bool = True
    heading_levels_to_split: Set[int] = field(default_factory=lambda: {1, 2, 3})
    code_block_languages: Set[str] = field(default_factory=lambda: {
        'python', 'py', 'javascript', 'js', 'typescript', 'ts',
        'java', 'go', 'rust', 'cpp', 'c', 'bash', 'sh', 'sql',
        'json', 'yaml', 'xml', 'html', 'css'
    })


# ============================================================
# PARSERS
# ============================================================

class MarkdownParser:
    """Parser for Markdown documents."""
    
    def __init__(self, config: DocChunkingConfig):
        self.config = config
        self.lines: List[str] = []
        self.current_heading: Optional[str] = None
        self.current_heading_level: int = 0
        self.heading_stack: List[Tuple[str, int]] = []
        self.in_code_block: bool = False
        self.code_block_language: Optional[str] = None
        self.code_block_lines: List[str] = []
        self.in_list: bool = False
        self.in_table: bool = False
        self.table_rows: List[List[str]] = []
        self.frontmatter: Dict[str, Any] = {}
        
    def parse(self, content: str, file_path: str) -> Tuple[List[DocChunk], DocStructure]:
        """Parse Markdown content into chunks."""
        self.lines = content.split('\n')
        chunks = []
        structure = DocStructure(total_lines=len(self.lines))
        
        # Parse frontmatter
        line_idx = self._parse_frontmatter(structure)
        
        # Parse content
        current_chunk_lines = []
        current_chunk_start = line_idx + 1
        current_heading = None
        
        while line_idx < len(self.lines):
            line = self.lines[line_idx]
            
            # Handle code blocks
            if line.strip().startswith('```'):
                if not self.in_code_block:
                    # Start code block
                    if current_chunk_lines:
                        chunks.append(self._create_chunk(
                            lines=current_chunk_lines,
                            start_line=current_chunk_start,
                            end_line=line_idx,
                            chunk_type=DocChunkType.PARAGRAPH,
                            file_path=file_path,
                            current_heading=current_heading
                        ))
                        current_chunk_lines = []
                    
                    self.in_code_block = True
                    self.code_block_language = line.strip()[3:].strip() or None
                    self.code_block_lines = [line]
                    current_chunk_start = line_idx + 1
                    
                else:
                    # End code block
                    self.code_block_lines.append(line)
                    self.in_code_block = False
                    
                    chunks.append(self._create_chunk(
                        lines=self.code_block_lines,
                        start_line=current_chunk_start,
                        end_line=line_idx + 1,
                        chunk_type=DocChunkType.CODE_BLOCK,
                        file_path=file_path,
                        current_heading=current_heading,
                        language=self.code_block_language
                    ))
                    
                    self.code_block_lines = []
                    self.code_block_language = None
                    current_chunk_lines = []
                    current_chunk_start = line_idx + 1
                    
                line_idx += 1
                continue
            
            if self.in_code_block:
                self.code_block_lines.append(line)
                line_idx += 1
                continue
            
            # Handle headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match and self.config.split_on_headings:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                # Save previous chunk
                if current_chunk_lines:
                    chunks.append(self._create_chunk(
                        lines=current_chunk_lines,
                        start_line=current_chunk_start,
                        end_line=line_idx,
                        chunk_type=DocChunkType.PARAGRAPH,
                        file_path=file_path,
                        current_heading=current_heading
                    ))
                    current_chunk_lines = []
                
                # Add heading as its own chunk if configured
                if level in self.config.heading_levels_to_split:
                    chunks.append(self._create_chunk(
                        lines=[line],
                        start_line=line_idx + 1,
                        end_line=line_idx + 1,
                        chunk_type=DocChunkType.HEADING,
                        file_path=file_path,
                        current_heading=heading_text,
                        heading_level=level
                    ))
                
                # Update heading stack
                while self.heading_stack and self.heading_stack[-1][1] >= level:
                    self.heading_stack.pop()
                self.heading_stack.append((heading_text, level))
                
                current_heading = heading_text
                self.current_heading = heading_text
                self.current_heading_level = level
                
                # Record in structure
                structure.headings.append((level, heading_text, line_idx + 1))
                
                current_chunk_start = line_idx + 1
                line_idx += 1
                continue
            
            # Handle horizontal rules (chunk boundaries)
            if re.match(r'^[-*_]{3,}\s*$', line):
                if current_chunk_lines:
                    chunks.append(self._create_chunk(
                        lines=current_chunk_lines,
                        start_line=current_chunk_start,
                        end_line=line_idx,
                        chunk_type=DocChunkType.PARAGRAPH,
                        file_path=file_path,
                        current_heading=current_heading
                    ))
                    current_chunk_lines = []
                    current_chunk_start = line_idx + 1
                line_idx += 1
                continue
            
            # Handle tables
            if '|' in line and line.strip().startswith('|'):
                if not self.in_table:
                    if current_chunk_lines:
                        chunks.append(self._create_chunk(
                            lines=current_chunk_lines,
                            start_line=current_chunk_start,
                            end_line=line_idx,
                            chunk_type=DocChunkType.PARAGRAPH,
                            file_path=file_path,
                            current_heading=current_heading
                        ))
                        current_chunk_lines = []
                    self.in_table = True
                    self.table_rows = []
                    current_chunk_start = line_idx + 1
                
                self.table_rows.append(self._parse_table_row(line))
                line_idx += 1
                continue
            
            if self.in_table:
                # End of table
                table_content = '\n'.join(str(row) for row in self.table_rows)
                chunks.append(self._create_chunk(
                    lines=[table_content],
                    start_line=current_chunk_start,
                    end_line=line_idx,
                    chunk_type=DocChunkType.TABLE,
                    file_path=file_path,
                    current_heading=current_heading,
                    metadata={'rows': len(self.table_rows)}
                ))
                self.in_table = False
                self.table_rows = []
                current_chunk_lines = []
                current_chunk_start = line_idx + 1
            
            # Handle empty lines (potential chunk boundaries)
            if not line.strip() and len(current_chunk_lines) > self.config.max_chunk_lines:
                chunks.append(self._create_chunk(
                    lines=current_chunk_lines,
                    start_line=current_chunk_start,
                    end_line=line_idx,
                    chunk_type=DocChunkType.PARAGRAPH,
                    file_path=file_path,
                    current_heading=current_heading
                ))
                current_chunk_lines = []
                current_chunk_start = line_idx + 1
            
            current_chunk_lines.append(line)
            line_idx += 1
        
        # Handle final chunk
        if self.in_table:
            table_content = '\n'.join(str(row) for row in self.table_rows)
            chunks.append(self._create_chunk(
                lines=[table_content],
                start_line=current_chunk_start,
                end_line=len(self.lines),
                chunk_type=DocChunkType.TABLE,
                file_path=file_path,
                current_heading=current_heading
            ))
        elif current_chunk_lines:
            chunks.append(self._create_chunk(
                lines=current_chunk_lines,
                start_line=current_chunk_start,
                end_line=len(self.lines),
                chunk_type=DocChunkType.PARAGRAPH,
                file_path=file_path,
                current_heading=current_heading
            ))
        
        # Detect sections
        if self.config.detect_sections:
            structure.sections = self._detect_sections(chunks)
            for chunk in chunks:
                chunk.section = self._classify_section(chunk)
        
        # Build TOC
        structure.toc = self._build_toc(structure.headings)
        
        # Extract references
        if self.config.extract_links:
            chunks = self._extract_references(chunks)
        
        return chunks, structure
    
    def _parse_frontmatter(self, structure: DocStructure) -> int:
        """Parse YAML frontmatter."""
        if not self.lines or self.lines[0].strip() != '---':
            return 0
        
        line_idx = 1
        frontmatter_lines = []
        
        while line_idx < len(self.lines):
            line = self.lines[line_idx]
            if line.strip() == '---':
                break
            frontmatter_lines.append(line)
            line_idx += 1
        
        if frontmatter_lines:
            try:
                import yaml
                structure.frontmatter = yaml.safe_load('\n'.join(frontmatter_lines))
            except:
                # Simple key-value parsing
                for line in frontmatter_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        structure.frontmatter[key.strip()] = value.strip()
        
        return line_idx + 1 if line_idx < len(self.lines) else 0
    
    def _parse_table_row(self, line: str) -> List[str]:
        """Parse a markdown table row."""
        if re.match(r'^[\|\s\-:]+$', line):  # Separator row
            return ['---']
        
        cells = line.strip('|').split('|')
        return [cell.strip() for cell in cells]
    
    def _create_chunk(self,
                      lines: List[str],
                      start_line: int,
                      end_line: int,
                      chunk_type: DocChunkType,
                      file_path: str,
                      current_heading: Optional[str] = None,
                      heading_level: int = 0,
                      language: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> DocChunk:
        """Create a documentation chunk."""
        content = '\n'.join(lines).strip()
        
        if not content and chunk_type != DocChunkType.HEADING:
            return None
        
        parent_heading = self.heading_stack[-2][0] if len(self.heading_stack) > 1 else None
        
        return DocChunk(
            chunk_type=chunk_type,
            format=DocFormat.MARKDOWN,
            content=content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            heading=current_heading,
            heading_level=heading_level or (self.current_heading_level if chunk_type != DocChunkType.HEADING else 0),
            parent_heading=parent_heading,
            language=language,
            metadata=metadata or {}
        )
    
    def _detect_sections(self, chunks: List[DocChunk]) -> Dict[str, Tuple[int, int]]:
        """Detect document sections."""
        sections = {}
        
        for i, chunk in enumerate(chunks):
            if chunk.chunk_type == DocChunkType.HEADING and chunk.heading:
                # Find section end
                end_idx = len(chunks)
                for j in range(i + 1, len(chunks)):
                    if (chunks[j].chunk_type == DocChunkType.HEADING and 
                        chunks[j].heading_level <= chunk.heading_level):
                        end_idx = j
                        break
                
                sections[chunk.heading] = (i, end_idx)
        
        return sections
    
    def _classify_section(self, chunk: DocChunk) -> DocSection:
        """Classify a chunk's section type."""
        if not chunk.heading:
            return DocSection.UNKNOWN
        
        heading_lower = chunk.heading.lower()
        
        classification_patterns = {
            DocSection.OVERVIEW: ['overview', 'introduction', 'about'],
            DocSection.INSTALLATION: ['install', 'setup', 'requirements', 'dependencies'],
            DocSection.QUICKSTART: ['quickstart', 'quick start', 'getting started'],
            DocSection.TUTORIAL: ['tutorial', 'guide', 'walkthrough'],
            DocSection.HOWTO: ['how to', 'how-to', 'usage', 'using'],
            DocSection.REFERENCE: ['reference', 'api', 'configuration', 'options'],
            DocSection.API: ['api', 'endpoint', 'method', 'function', 'class'],
            DocSection.EXAMPLES: ['example', 'sample', 'demo'],
            DocSection.FAQ: ['faq', 'frequently asked', 'questions'],
            DocSection.CONTRIBUTING: ['contributing', 'development', 'developing'],
            DocSection.CHANGELOG: ['changelog', 'changes', 'history', 'releases'],
            DocSection.LICENSE: ['license', 'licence'],
            DocSection.ARCHITECTURE: ['architecture', 'design', 'structure'],
        }
        
        for section, patterns in classification_patterns.items():
            if any(pattern in heading_lower for pattern in patterns):
                return section
        
        return DocSection.UNKNOWN
    
    def _build_toc(self, headings: List[Tuple[int, str, int]]) -> List[Dict[str, Any]]:
        """Build table of contents."""
        toc = []
        stack = []
        
        for level, text, line in headings:
            item = {
                'level': level,
                'text': text,
                'line': line,
                'anchor': self._heading_to_anchor(text),
                'children': []
            }
            
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            if stack:
                stack[-1]['children'].append(item)
            else:
                toc.append(item)
            
            stack.append(item)
        
        return toc
    
    def _heading_to_anchor(self, heading: str) -> str:
        """Convert heading to anchor ID."""
        anchor = heading.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        return anchor
    
    def _extract_references(self, chunks: List[DocChunk]) -> List[DocChunk]:
        """Extract links and references from chunks."""
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        code_ref_pattern = re.compile(r'`([^`]+)`')
        
        for chunk in chunks:
            # Extract markdown links
            for match in link_pattern.finditer(chunk.content):
                link_text = match.group(1)
                link_url = match.group(2)
                chunk.references.append(link_url)
                chunk.metadata.setdefault('links', []).append({
                    'text': link_text,
                    'url': link_url
                })
            
            # Extract potential code references
            if self.config.extract_code_refs:
                for match in code_ref_pattern.finditer(chunk.content):
                    code_text = match.group(1)
                    if self._is_code_reference(code_text):
                        chunk.code_refs.append(code_text)
        
        return chunks
    
    def _is_code_reference(self, text: str) -> bool:
        """Check if text looks like a code reference."""
        # Function call: function_name()
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)$', text):
            return True
        
        # Class name: CamelCase
        if re.match(r'^[A-Z][a-zA-Z0-9_]*$', text):
            return True
        
        # Module import: module.Class or module.function
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*\.[a-zA-Z_][a-zA-Z0-9_]*$', text):
            return True
        
        return False


class DocstringParser:
    """Parser for Python docstrings."""
    
    def __init__(self, config: DocChunkingConfig):
        self.config = config
    
    def parse_docstring(self, 
                        docstring: str,
                        symbol_name: str,
                        symbol_type: str,
                        file_path: str) -> List[DocChunk]:
        """Parse a docstring into chunks."""
        chunks = []
        
        if not docstring:
            return chunks
        
        lines = docstring.split('\n')
        
        # Determine chunk type
        if symbol_type == 'module':
            chunk_type = DocChunkType.MODULE_DOC
        elif symbol_type == 'class':
            chunk_type = DocChunkType.CLASS_DOC
        elif symbol_type in ('function', 'method'):
            chunk_type = DocChunkType.METHOD_DOC
        else:
            chunk_type = DocChunkType.PARAGRAPH
        
        # Parse Google-style docstring sections
        sections = self._parse_google_style(lines)
        
        if sections:
            for section_name, section_lines in sections.items():
                content = '\n'.join(section_lines).strip()
                if content:
                    chunk = DocChunk(
                        chunk_type=self._section_to_chunk_type(section_name),
                        format=DocFormat.DOCSTRING,
                        content=content,
                        file_path=file_path,
                        start_line=0,
                        end_line=0,
                        heading=section_name if section_name != 'description' else symbol_name,
                        metadata={
                            'symbol_name': symbol_name,
                            'symbol_type': symbol_type,
                            'section': section_name
                        }
                    )
                    chunks.append(chunk)
        else:
            # Single chunk for entire docstring
            chunk = DocChunk(
                chunk_type=chunk_type,
                format=DocFormat.DOCSTRING,
                content=docstring,
                file_path=file_path,
                start_line=0,
                end_line=0,
                heading=symbol_name,
                metadata={
                    'symbol_name': symbol_name,
                    'symbol_type': symbol_type
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _parse_google_style(self, lines: List[str]) -> Dict[str, List[str]]:
        """Parse Google-style docstring sections."""
        sections = {'description': []}
        current_section = 'description'
        
        section_headers = {
            'args:', 'arguments:', 'parameters:', 'params:',
            'returns:', 'return:',
            'raises:', 'exceptions:',
            'yields:', 'yield:',
            'examples:', 'example:',
            'notes:', 'note:',
            'attributes:', 'attrs:',
            'methods:',
            'see also:', 'see_also:',
            'todo:',
            'deprecated:'
        }
        
        for line in lines:
            stripped = line.strip().lower()
            
            # Check for section header
            if stripped in section_headers or any(stripped.startswith(h) for h in section_headers):
                current_section = stripped.rstrip(':')
                sections[current_section] = []
            else:
                sections[current_section].append(line)
        
        return sections
    
    def _section_to_chunk_type(self, section: str) -> DocChunkType:
        """Convert docstring section to chunk type."""
        mapping = {
            'description': DocChunkType.PARAGRAPH,
            'args': DocChunkType.PARAMETER,
            'arguments': DocChunkType.PARAMETER,
            'parameters': DocChunkType.PARAMETER,
            'params': DocChunkType.PARAMETER,
            'returns': DocChunkType.RETURN,
            'return': DocChunkType.RETURN,
            'raises': DocChunkType.EXCEPTION,
            'exceptions': DocChunkType.EXCEPTION,
            'yields': DocChunkType.RETURN,
            'examples': DocChunkType.EXAMPLE,
            'attributes': DocChunkType.ATTRIBUTE,
        }
        return mapping.get(section, DocChunkType.PARAGRAPH)


# ============================================================
# MAIN CHUNKER CLASS
# ============================================================

class DocChunker:
    """
    Documentation chunker for embedding and analysis.
    
    Features:
    - Multi-format support (Markdown, RST, docstrings)
    - Heading-based chunking
    - Section detection and classification
    - Code block extraction
    - Link and reference extraction
    - Frontmatter parsing
    - TOC generation
    - Hierarchy preservation
    - Change detection
    """
    
    def __init__(self, config: Optional[DocChunkingConfig] = None):
        self.config = config or DocChunkingConfig()
        self.file_hashes: Dict[str, str] = {}
        self.markdown_parser = MarkdownParser(self.config)
        self.docstring_parser = DocstringParser(self.config)
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def chunk_file(self, file_path: Path) -> DocChunkingResult:
        """Chunk a single documentation file."""
        logger.info(f"Chunking document: {file_path}")
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return self._empty_result(str(file_path))
        
        # Detect format
        doc_format = self._detect_format(file_path)
        
        # Chunk based on format
        if doc_format == DocFormat.MARKDOWN:
            chunks, structure = self.markdown_parser.parse(content, str(file_path))
        elif doc_format == DocFormat.RST:
            chunks, structure = self._chunk_rst(content, str(file_path))
        elif doc_format == DocFormat.PLAIN:
            chunks, structure = self._chunk_plain(content, str(file_path))
        else:
            chunks, structure = self._chunk_generic(content, str(file_path))
        
        # Post-process chunks
        chunks = self._post_process_chunks(chunks)
        
        # Calculate statistics
        total_lines = len(content.split('\n'))
        avg_chunk_size = sum(len(c.content.split('\n')) for c in chunks) / max(len(chunks), 1)
        
        type_distribution = defaultdict(int)
        for chunk in chunks:
            type_distribution[chunk.chunk_type] += 1
        
        result = DocChunkingResult(
            chunks=chunks,
            structure=structure,
            total_chunks=len(chunks),
            total_lines=total_lines,
            avg_chunk_size=avg_chunk_size,
            chunk_types_distribution=dict(type_distribution),
            file_path=str(file_path),
            format=doc_format
        )
        
        logger.info(f"Created {len(chunks)} chunks from {file_path}")
        return result
    
    def chunk_docstring(self,
                        docstring: str,
                        symbol_name: str,
                        symbol_type: str,
                        file_path: str) -> List[DocChunk]:
        """Chunk a Python docstring."""
        return self.docstring_parser.parse_docstring(
            docstring, symbol_name, symbol_type, file_path
        )
    
    def chunk_directory(self,
                        directory: Path,
                        recursive: bool = True,
                        patterns: List[str] = None) -> List[DocChunkingResult]:
        """Chunk all documentation files in a directory."""
        results = []
        patterns = patterns or ["*.md", "*.markdown", "*.rst", "*.txt"]
        
        for pattern in patterns:
            glob_func = directory.rglob if recursive else directory.glob
            for file_path in glob_func(pattern):
                if self._should_skip(file_path):
                    continue
                
                if not self._has_changed(file_path):
                    logger.debug(f"Skipping unchanged file: {file_path}")
                    continue
                
                result = self.chunk_file(file_path)
                results.append(result)
        
        logger.info(f"Chunked {len(results)} documentation files")
        return results
    
    def merge_chunks(self, chunks: List[DocChunk]) -> List[DocChunk]:
        """Merge small chunks together."""
        if not self.config.merge_small_chunks:
            return chunks
        
        merged = []
        current_group = []
        
        for chunk in sorted(chunks, key=lambda c: c.start_line):
            chunk_size = len(chunk.content.split('\n'))
            
            if (chunk_size < self.config.min_chunk_lines and 
                chunk.chunk_type == DocChunkType.PARAGRAPH):
                current_group.append(chunk)
            else:
                if current_group:
                    merged.append(self._merge_chunk_group(current_group))
                    current_group = []
                merged.append(chunk)
        
        if current_group:
            merged.append(self._merge_chunk_group(current_group))
        
        return merged
    
    # ============================================================
    # FORMAT-SPECIFIC CHUNKING
    # ============================================================
    
    def _chunk_rst(self, content: str, file_path: str) -> Tuple[List[DocChunk], DocStructure]:
        """Chunk reStructuredText document."""
        # Basic RST parsing - could be expanded
        lines = content.split('\n')
        chunks = []
        structure = DocStructure(total_lines=len(lines))
        
        current_chunk_lines = []
        current_chunk_start = 1
        current_heading = None
        
        for i, line in enumerate(lines, 1):
            # Check for RST headings
            if i < len(lines) and self._is_rst_heading(line, lines[i] if i < len(lines) else ''):
                if current_chunk_lines:
                    chunks.append(self._create_rst_chunk(
                        current_chunk_lines, current_chunk_start, i - 1,
                        file_path, current_heading
                    ))
                    current_chunk_lines = []
                
                heading_level = self._get_rst_heading_level(line, lines[i])
                heading_text = line.strip()
                structure.headings.append((heading_level, heading_text, i))
                current_heading = heading_text
                current_chunk_start = i
                
                chunks.append(self._create_rst_chunk(
                    [line], i, i, file_path, heading_text,
                    chunk_type=DocChunkType.HEADING
                ))
                
                current_chunk_start = i + 1
            
            current_chunk_lines.append(line)
        
        if current_chunk_lines:
            chunks.append(self._create_rst_chunk(
                current_chunk_lines, current_chunk_start, len(lines),
                file_path, current_heading
            ))
        
        return chunks, structure
    
    def _is_rst_heading(self, line: str, next_line: str) -> bool:
        """Check if line is an RST heading."""
        if not line.strip():
            return False
        
        heading_chars = set('=-~^"\'`*+#')
        next_line_stripped = next_line.strip()
        
        if not next_line_stripped:
            return False
        
        char = next_line_stripped[0]
        return (char in heading_chars and 
                len(next_line_stripped) >= len(line.strip()) and
                all(c == char for c in next_line_stripped))
    
    def _get_rst_heading_level(self, line: str, next_line: str) -> int:
        """Get RST heading level based on character used."""
        char = next_line.strip()[0]
        level_map = {'=': 1, '-': 2, '~': 3, '^': 4, '"': 5, "'": 6}
        return level_map.get(char, 3)
    
    def _create_rst_chunk(self,
                          lines: List[str],
                          start_line: int,
                          end_line: int,
                          file_path: str,
                          heading: Optional[str] = None,
                          chunk_type: DocChunkType = DocChunkType.PARAGRAPH) -> DocChunk:
        """Create an RST chunk."""
        return DocChunk(
            chunk_type=chunk_type,
            format=DocFormat.RST,
            content='\n'.join(lines).strip(),
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            heading=heading
        )
    
    def _chunk_plain(self, content: str, file_path: str) -> Tuple[List[DocChunk], DocStructure]:
        """Chunk plain text document."""
        lines = content.split('\n')
        chunks = []
        structure = DocStructure(total_lines=len(lines))
        
        # Simple paragraph-based chunking
        current_para = []
        current_start = 1
        
        for i, line in enumerate(lines, 1):
            if not line.strip():
                if current_para:
                    chunks.append(DocChunk(
                        chunk_type=DocChunkType.PARAGRAPH,
                        format=DocFormat.PLAIN,
                        content='\n'.join(current_para).strip(),
                        file_path=file_path,
                        start_line=current_start,
                        end_line=i - 1
                    ))
                    current_para = []
                    current_start = i + 1
            else:
                current_para.append(line)
        
        if current_para:
            chunks.append(DocChunk(
                chunk_type=DocChunkType.PARAGRAPH,
                format=DocFormat.PLAIN,
                content='\n'.join(current_para).strip(),
                file_path=file_path,
                start_line=current_start,
                end_line=len(lines)
            ))
        
        return chunks, structure
    
    def _chunk_generic(self, content: str, file_path: str) -> Tuple[List[DocChunk], DocStructure]:
        """Generic chunking for unknown formats."""
        lines = content.split('\n')
        chunks = []
        structure = DocStructure(total_lines=len(lines))
        
        chunk_size = self.config.max_chunk_lines
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk = DocChunk(
                chunk_type=DocChunkType.PARAGRAPH,
                format=DocFormat.UNKNOWN,
                content='\n'.join(chunk_lines),
                file_path=file_path,
                start_line=i + 1,
                end_line=min(i + chunk_size, len(lines))
            )
            chunks.append(chunk)
        
        return chunks, structure
    
    # ============================================================
    # POST-PROCESSING
    # ============================================================
    
    def _post_process_chunks(self, chunks: List[DocChunk]) -> List[DocChunk]:
        """Apply post-processing to chunks."""
        # Filter out empty chunks
        chunks = [c for c in chunks if c and c.content.strip()]
        
        # Merge small chunks
        chunks = self.merge_chunks(chunks)
        
        # Add order indices
        for i, chunk in enumerate(chunks):
            chunk.order_index = i
        
        # Build hierarchy
        if self.config.preserve_hierarchy:
            chunks = self._build_hierarchy(chunks)
        
        # Add tags based on content
        chunks = self._add_content_tags(chunks)
        
        return chunks
    
    def _build_hierarchy(self, chunks: List[DocChunk]) -> List[DocChunk]:
        """Build parent-child relationships."""
        heading_map = {}
        
        for chunk in chunks:
            if chunk.chunk_type == DocChunkType.HEADING and chunk.heading:
                heading_map[chunk.heading] = chunk.id
        
        for chunk in chunks:
            if chunk.parent_heading and chunk.parent_heading in heading_map:
                parent_id = heading_map[chunk.parent_heading]
                chunk.parent_id = parent_id
                
                # Add to parent's children
                for c in chunks:
                    if c.id == parent_id:
                        if chunk.id not in c.children:
                            c.children.append(chunk.id)
                        break
        
        return chunks
    
    def _add_content_tags(self, chunks: List[DocChunk]) -> List[DocChunk]:
        """Add tags based on content analysis."""
        for chunk in chunks:
            content_lower = chunk.content.lower()
            
            # Check for code-related content
            if any(word in content_lower for word in ['function', 'class', 'method', 'module']):
                chunk.tags.append('api')
            
            if any(word in content_lower for word in ['example', 'sample', 'usage']):
                chunk.tags.append('example')
            
            if any(word in content_lower for word in ['install', 'setup', 'configure']):
                chunk.tags.append('setup')
            
            if any(word in content_lower for word in ['error', 'exception', 'warning']):
                chunk.tags.append('error-handling')
            
            if chunk.chunk_type == DocChunkType.CODE_BLOCK:
                chunk.tags.append('code')
                if chunk.language:
                    chunk.tags.append(f'lang-{chunk.language}')
        
        return chunks
    
    def _merge_chunk_group(self, chunks: List[DocChunk]) -> DocChunk:
        """Merge a group of chunks."""
        if not chunks:
            raise ValueError("Cannot merge empty chunk group")
        
        first = chunks[0]
        last = chunks[-1]
        
        content_parts = [c.content for c in chunks]
        merged_content = '\n\n'.join(content_parts)
        
        return DocChunk(
            chunk_type=DocChunkType.PARAGRAPH,
            format=first.format,
            content=merged_content,
            file_path=first.file_path,
            start_line=first.start_line,
            end_line=last.end_line,
            heading=first.heading,
            parent_heading=first.parent_heading,
            tags=list(set().union(*[c.tags for c in chunks])),
            references=list(set().union(*[c.references for c in chunks])),
            code_refs=list(set().union(*[c.code_refs for c in chunks])),
            metadata={'merged_from': [c.id for c in chunks]}
        )
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _detect_format(self, file_path: Path) -> DocFormat:
        """Detect document format from extension."""
        ext = file_path.suffix.lower()
        
        if ext in ('.md', '.markdown'):
            return DocFormat.MARKDOWN
        elif ext in ('.rst', '.rest'):
            return DocFormat.RST
        elif ext == '.txt':
            return DocFormat.PLAIN
        elif ext == '.html':
            return DocFormat.HTML
        elif ext == '.json':
            return DocFormat.JSON
        elif ext in ('.yaml', '.yml'):
            return DocFormat.YAML
        else:
            return DocFormat.UNKNOWN
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', 'dist', 'build', '.pytest_cache',
            '.mypy_cache', '.ruff_cache', '.ai_state'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _has_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last chunking."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_hash = hashlib.sha256(content.encode()).hexdigest()
            
            if file_path in self.file_hashes:
                if self.file_hashes[file_path] == current_hash:
                    return False
            
            self.file_hashes[str(file_path)] = current_hash
            return True
            
        except Exception:
            return True
    
    def _empty_result(self, file_path: str) -> DocChunkingResult:
        """Create empty chunking result."""
        return DocChunkingResult(
            chunks=[],
            structure=DocStructure(),
            total_chunks=0,
            total_lines=0,
            avg_chunk_size=0,
            chunk_types_distribution={},
            file_path=file_path,
            format=DocFormat.UNKNOWN
        )
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_chunks_json(self, result: DocChunkingResult, output_path: Optional[Path] = None) -> str:
        """Export chunks as JSON."""
        data = {
            'file_path': result.file_path,
            'format': result.format.value,
            'chunked_at': result.chunked_at.isoformat(),
            'total_chunks': result.total_chunks,
            'total_lines': result.total_lines,
            'avg_chunk_size': result.avg_chunk_size,
            'chunk_types_distribution': {k.value: v for k, v in result.chunk_types_distribution.items()},
            'structure': {
                'title': result.structure.title,
                'headings': [
                    {'level': h[0], 'text': h[1], 'line': h[2]}
                    for h in result.structure.headings
                ],
                'toc': result.structure.toc,
                'frontmatter': result.structure.frontmatter
            },
            'chunks': [
                {
                    'id': c.id,
                    'type': c.chunk_type.value,
                    'format': c.format.value,
                    'content': c.content,
                    'start_line': c.start_line,
                    'end_line': c.end_line,
                    'heading': c.heading,
                    'heading_level': c.heading_level,
                    'section': c.section.value,
                    'parent_heading': c.parent_heading,
                    'language': c.language,
                    'tags': c.tags,
                    'references': c.references,
                    'code_refs': c.code_refs,
                    'content_hash': c.content_hash,
                    'children': c.children,
                    'parent_id': c.parent_id,
                    'order_index': c.order_index,
                    'metadata': c.metadata
                }
                for c in result.chunks
            ]
        }
        
        json_str = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(json_str)
        
        return json_str
    
    def export_chunks_for_embedding(self, chunks: List[DocChunk]) -> List[Dict[str, Any]]:
        """Export chunks in format ready for embedding."""
        return [
            {
                'id': c.id,
                'text': self._format_chunk_for_embedding(c),
                'metadata': {
                    'type': c.chunk_type.value,
                    'format': c.format.value,
                    'file_path': c.file_path,
                    'heading': c.heading,
                    'section': c.section.value,
                    'tags': c.tags,
                    'code_refs': c.code_refs,
                    **c.metadata
                }
            }
            for c in chunks
        ]
    
    def _format_chunk_for_embedding(self, chunk: DocChunk) -> str:
        """Format chunk content for optimal embedding."""
        parts = []
        
        if chunk.heading:
            parts.append(f"# {chunk.heading}")
        
        if chunk.section != DocSection.UNKNOWN:
            parts.append(f"Section: {chunk.section.value}")
        
        if chunk.chunk_type == DocChunkType.CODE_BLOCK and chunk.language:
            parts.append(f"Language: {chunk.language}")
        
        parts.append(chunk.content)
        
        return '\n'.join(parts)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for doc chunker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chunk documentation files for embedding and analysis")
    parser.add_argument("path", type=Path, help="File or directory to chunk")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--min-lines", type=int, default=5, help="Minimum chunk size in lines")
    parser.add_argument("--max-lines", type=int, default=500, help="Maximum chunk size in lines")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process directories recursively")
    parser.add_argument("--embedding-format", action="store_true", help="Output in embedding-ready format")
    parser.add_argument("--no-merge", action="store_true", help="Disable merging small chunks")
    parser.add_argument("--no-hierarchy", action="store_true", help="Disable hierarchy preservation")
    
    args = parser.parse_args()
    
    config = DocChunkingConfig(
        min_chunk_lines=args.min_lines,
        max_chunk_lines=args.max_lines,
        merge_small_chunks=not args.no_merge,
        preserve_hierarchy=not args.no_hierarchy
    )
    
    chunker = DocChunker(config)
    
    if args.path.is_file():
        result = chunker.chunk_file(args.path)
        results = [result]
    else:
        results = chunker.chunk_directory(args.path, recursive=args.recursive)
    
    # Prepare output
    if args.embedding_format:
        all_chunks = []
        for r in results:
            all_chunks.extend(r.chunks)
        output_data = chunker.export_chunks_for_embedding(all_chunks)
        output_str = json.dumps(output_data, indent=2)
    else:
        output_data = {
            'results': [
                {
                    'file_path': r.file_path,
                    'format': r.format.value,
                    'total_chunks': r.total_chunks,
                    'total_lines': r.total_lines,
                    'avg_chunk_size': r.avg_chunk_size,
                    'chunk_types': {k.value: v for k, v in r.chunk_types_distribution.items()},
                    'title': r.structure.title,
                    'headings_count': len(r.structure.headings)
                }
                for r in results
            ],
            'summary': {
                'total_files': len(results),
                'total_chunks': sum(r.total_chunks for r in results),
                'total_lines': sum(r.total_lines for r in results)
            }
        }
        output_str = json.dumps(output_data, indent=2)
    
    if args.output:
        args.output.write_text(output_str)
        print(f"Output saved to {args.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()