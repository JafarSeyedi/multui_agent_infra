#!/usr/bin/env python3
"""
Documentation Indexer - AI Development Framework
Indexes documentation chunks into vector store for semantic search.

Part of the Level 2 Analysis tools (indexers/doc_indexer.py)

This doc_indexer.py provides:

1. Multi-Format Support - Indexes Markdown, RST, plain text, and more
2. Section-Aware Indexing - Preserves document structure and hierarchy
3. Full and Incremental Indexing - Index entire docs or only changed files
4. Git Integration - Track changes and auto-update on commits
5. Cross-References - Link between docs and code, internal links
6. Breadcrumb Navigation - Preserves document navigation context
7. Collections Management - Group related documents logically
8. Semantic Search - Natural language queries with metadata filtering
9. TOC Generation - Extract and cache tables of contents
10. Frontmatter Support - Index YAML frontmatter metadata
11. Code Reference Tracking - Find docs that reference specific code
12. Rich Metadata - Filter by doc type, section, format, and more

The doc indexer works alongside the code indexer to provide comprehensive semantic search across your entire project documentation.

"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from ...shared.git_utils import GitUtils
from ..chunkers.doc_chunker import (
    DocChunker, 
    DocChunk, 
    DocChunkingResult, 
    DocChunkType, 
    DocFormat, 
    DocSection,
    DocStructure
)
from ..encoders.embedding_store import EmbeddingStore, CollectionType, SearchResult, StoredDocument
from ..encoders.batch_encoder import BatchEncoder, BatchJob, BatchPriority

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DocIndexStatus(str, Enum):
    """Status of documentation indexing operation."""
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    UP_TO_DATE = "up_to_date"


class DocType(str, Enum):
    """Type of documentation."""
    README = "readme"
    API_DOCS = "api_docs"
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    HOWTO = "howto"
    REFERENCE = "reference"
    CHANGELOG = "changelog"
    CONTRIBUTING = "contributing"
    LICENSE = "license"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class DocIndexingConfig:
    """Configuration for documentation indexing."""
    project_root: Path
    docs_paths: List[Path] = field(default_factory=lambda: [
        Path("docs"),
        Path("documentation"),
        Path("README.md"),
        Path("CONTRIBUTING.md"),
        Path("CHANGELOG.md"),
        Path("LICENSE")
    ])
    vector_store_path: Optional[Path] = None
    include_patterns: List[str] = field(default_factory=lambda: [
        "*.md", "*.markdown", "*.rst", "*.txt", "*.adoc"
    ])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__/*", ".git/*", ".venv/*", "venv/*",
        "dist/*", "build/*", "*.egg-info/*", ".ai_state/*",
        "node_modules/*", "*.lock", "package-lock.json"
    ])
    min_chunk_lines: int = 5
    max_chunk_lines: int = 500
    split_on_headings: bool = True
    heading_levels_to_split: Set[int] = field(default_factory=lambda: {1, 2, 3})
    batch_size: int = 50
    incremental: bool = True
    track_changes: bool = True
    extract_code_refs: bool = True
    extract_links: bool = True
    detect_sections: bool = True
    preserve_hierarchy: bool = True
    index_frontmatter: bool = True
    index_toc: bool = True
    auto_update_on_commit: bool = False
    watch_branches: List[str] = field(default_factory=lambda: ["main", "master", "develop"])


@dataclass
class DocIndexingResult:
    """Result of documentation indexing operation."""
    status: DocIndexStatus
    total_files: int
    indexed_files: int
    skipped_files: int
    failed_files: int
    total_chunks: int
    total_sections: int
    total_headings: int
    new_chunks: int
    updated_chunks: int
    unchanged_chunks: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    indexed_at: datetime = field(default_factory=datetime.now)
    git_commit: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocFileState:
    """State of an indexed documentation file."""
    file_path: str
    content_hash: str
    indexed_at: datetime
    chunk_count: int
    section_count: int
    heading_count: int
    chunk_ids: List[str] = field(default_factory=list)
    doc_type: DocType = DocType.UNKNOWN
    title: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    git_commit: Optional[str] = None


@dataclass
class DocSearchResult:
    """Enhanced search result for documentation."""
    chunk: DocChunk
    similarity: float = 0.0
    matched_terms: List[str] = field(default_factory=list)
    source_file: str = ""
    heading: Optional[str] = None
    section: DocSection = DocSection.UNKNOWN
    breadcrumb: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk.id,
            'chunk_type': self.chunk.chunk_type.value,
            'content': self.chunk.content,
            'similarity': self.similarity,
            'matched_terms': self.matched_terms,
            'source_file': self.source_file,
            'heading': self.heading,
            'section': self.section.value,
            'breadcrumb': self.breadcrumb,
            'line_start': self.chunk.start_line,
            'line_end': self.chunk.end_line,
            'language': self.chunk.language,
            'tags': self.chunk.tags,
            'references': self.chunk.references,
            'code_refs': self.chunk.code_refs
        }


@dataclass
class DocCollection:
    """A logical collection of related documents."""
    name: str
    doc_type: DocType
    files: List[str] = field(default_factory=list)
    chunk_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# MAIN DOCUMENTATION INDEXER CLASS
# ============================================================

class DocIndexer:
    """
    Indexes documentation into vector store for semantic search.
    
    Features:
    - Multi-format documentation support (Markdown, RST, plain text)
    - Section and heading-aware chunking
    - Full and incremental indexing
    - Git integration for change tracking
    - Cross-references between docs and code
    - Breadcrumb navigation preservation
    - Frontmatter metadata extraction
    - Table of contents indexing
    - Semantic search with section filtering
    - Document collections management
    - Auto-update on commits
    """
    
    def __init__(self, 
                 config: DocIndexingConfig,
                 store: Optional[EmbeddingStore] = None,
                 chunker: Optional[DocChunker] = None,
                 batch_encoder: Optional[BatchEncoder] = None):
        self.config = config
        
        # Initialize components
        self.store = store or EmbeddingStore()
        self.chunker = chunker or DocChunker()
        self.batch_encoder = batch_encoder
        
        # Git integration
        self.git = GitUtils(config.project_root) if config.track_changes else None
        
        # State management
        self.state = StateManager(config.project_root / ".ai_state" / "doc_indexer.json")
        self.file_states: Dict[str, DocFileState] = {}
        self.collections: Dict[str, DocCollection] = {}
        
        # Caches
        self._chunk_cache: Dict[str, DocChunk] = {}
        self._structure_cache: Dict[str, DocStructure] = {}
        self._breadcrumb_cache: Dict[str, List[str]] = {}
        self._toc_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Reference mappings
        self._doc_to_code_refs: Dict[str, List[str]] = defaultdict(list)
        self._code_to_doc_refs: Dict[str, List[str]] = defaultdict(list)
        self._internal_links: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing state
        self._load_state()
        self._initialize_collections()
        
        logger.info(f"DocIndexer initialized for {config.project_root}")
    
    def _load_state(self):
        """Load persisted indexing state."""
        saved_states = self.state.get('file_states', {})
        for file_path, state_data in saved_states.items():
            self.file_states[file_path] = DocFileState(
                file_path=state_data['file_path'],
                content_hash=state_data['content_hash'],
                indexed_at=datetime.fromisoformat(state_data['indexed_at']),
                chunk_count=state_data.get('chunk_count', 0),
                section_count=state_data.get('section_count', 0),
                heading_count=state_data.get('heading_count', 0),
                chunk_ids=state_data.get('chunk_ids', []),
                doc_type=DocType(state_data.get('doc_type', 'unknown')),
                title=state_data.get('title'),
                structure=state_data.get('structure'),
                git_commit=state_data.get('git_commit')
            )
        
        # Load collections
        saved_collections = self.state.get('collections', {})
        for name, coll_data in saved_collections.items():
            self.collections[name] = DocCollection(
                name=coll_data['name'],
                doc_type=DocType(coll_data['doc_type']),
                files=coll_data.get('files', []),
                chunk_ids=coll_data.get('chunk_ids', []),
                metadata=coll_data.get('metadata', {})
            )
        
        # Load reference mappings
        self._doc_to_code_refs.update(self.state.get('doc_to_code_refs', {}))
        self._code_to_doc_refs.update(self.state.get('code_to_doc_refs', {}))
        self._internal_links.update(self.state.get('internal_links', {}))
        
        logger.info(f"Loaded state for {len(self.file_states)} documentation files")
    
    def _save_state(self):
        """Persist indexing state."""
        state_data = {}
        for file_path, state in self.file_states.items():
            state_data[file_path] = {
                'file_path': state.file_path,
                'content_hash': state.content_hash,
                'indexed_at': state.indexed_at.isoformat(),
                'chunk_count': state.chunk_count,
                'section_count': state.section_count,
                'heading_count': state.heading_count,
                'chunk_ids': state.chunk_ids,
                'doc_type': state.doc_type.value,
                'title': state.title,
                'structure': state.structure,
                'git_commit': state.git_commit
            }
        
        collections_data = {}
        for name, coll in self.collections.items():
            collections_data[name] = {
                'name': coll.name,
                'doc_type': coll.doc_type.value,
                'files': coll.files,
                'chunk_ids': coll.chunk_ids,
                'metadata': coll.metadata
            }
        
        self.state.set('file_states', state_data)
        self.state.set('collections', collections_data)
        self.state.set('doc_to_code_refs', dict(self._doc_to_code_refs))
        self.state.set('code_to_doc_refs', dict(self._code_to_doc_refs))
        self.state.set('internal_links', dict(self._internal_links))
        self.state.set('last_indexed', datetime.now().isoformat())
        self.state.save()
    
    def _initialize_collections(self):
        """Initialize default document collections."""
        default_collections = {
            'readme': DocType.README,
            'api_docs': DocType.API_DOCS,
            'architecture': DocType.ARCHITECTURE,
            'tutorials': DocType.TUTORIAL,
            'howtos': DocType.HOWTO,
            'reference': DocType.REFERENCE
        }
        
        for name, doc_type in default_collections.items():
            if name not in self.collections:
                self.collections[name] = DocCollection(
                    name=name,
                    doc_type=doc_type
                )
    
    # ============================================================
    # DOCUMENT DETECTION
    # ============================================================
    
    def _find_documentation_files(self) -> List[Path]:
        """Find all documentation files to index."""
        files = []
        
        for docs_path in self.config.docs_paths:
            full_path = self.config.project_root / docs_path
            
            if full_path.is_file():
                if self._should_include_file(full_path):
                    files.append(full_path)
            elif full_path.is_dir():
                for pattern in self.config.include_patterns:
                    for file_path in full_path.rglob(pattern):
                        if self._should_include_file(file_path):
                            files.append(file_path)
        
        return files
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included."""
        import fnmatch
        
        rel_path = str(file_path.relative_to(self.config.project_root))
        
        # Check include patterns
        included = any(fnmatch.fnmatch(rel_path, p) for p in self.config.include_patterns)
        if not included:
            return False
        
        # Check exclude patterns
        excluded = any(fnmatch.fnmatch(rel_path, p) for p in self.config.exclude_patterns)
        if excluded:
            return False
        
        return True
    
    def _detect_doc_type(self, file_path: Path, structure: Optional[DocStructure] = None) -> DocType:
        """Detect document type from file name and content."""
        file_name = file_path.name.lower()
        
        if 'readme' in file_name:
            return DocType.README
        elif 'contributing' in file_name:
            return DocType.CONTRIBUTING
        elif 'changelog' in file_name or 'changes' in file_name:
            return DocType.CHANGELOG
        elif 'license' in file_name or 'licence' in file_name:
            return DocType.LICENSE
        elif 'api' in file_name or file_path.parent.name in ['api', 'reference']:
            return DocType.API_DOCS
        elif 'architecture' in file_name or 'design' in file_name:
            return DocType.ARCHITECTURE
        elif 'tutorial' in file_name or 'guide' in file_name:
            return DocType.TUTORIAL
        elif 'howto' in file_name or 'how-to' in file_name:
            return DocType.HOWTO
        
        # Check structure
        if structure:
            if structure.sections:
                if 'API' in structure.sections or 'Reference' in structure.sections:
                    return DocType.API_DOCS
        
        return DocType.UNKNOWN
    
    # ============================================================
    # INDEXING
    # ============================================================
    
    def index(self, 
              full: bool = False,
              files: Optional[List[Path]] = None,
              collection: Optional[str] = None) -> DocIndexingResult:
        """
        Index documentation.
        
        Args:
            full: Force full reindexing
            files: Specific files to index
            collection: Target collection name
        """
        start_time = datetime.now()
        logger.info(f"Starting documentation indexing (full={full})")
        
        result = DocIndexingResult(
            status=DocIndexStatus.INDEXING,
            total_files=0,
            indexed_files=0,
            skipped_files=0,
            failed_files=0,
            total_chunks=0,
            total_sections=0,
            total_headings=0,
            new_chunks=0,
            updated_chunks=0,
            unchanged_chunks=0,
            duration_seconds=0
        )
        
        # Get current git commit
        if self.git:
            result.git_commit = self.git.get_current_commit()
        
        # Find files to index
        if files:
            doc_files = [f for f in files if self._should_include_file(f)]
        else:
            doc_files = self._find_documentation_files()
        
        result.total_files = len(doc_files)
        
        # Process files
        for file_path in doc_files:
            try:
                file_result = self._index_file(file_path, full, collection)
                
                if file_result['indexed']:
                    result.indexed_files += 1
                    result.total_chunks += file_result.get('chunks', 0)
                    result.total_sections += file_result.get('sections', 0)
                    result.total_headings += file_result.get('headings', 0)
                    result.new_chunks += file_result.get('new_chunks', 0)
                    result.updated_chunks += file_result.get('updated_chunks', 0)
                    result.unchanged_chunks += file_result.get('unchanged_chunks', 0)
                else:
                    result.skipped_files += 1
                    
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                result.failed_files += 1
                result.errors.append(f"{file_path}: {str(e)}")
        
        # Build cross-references
        self._build_cross_references()
        
        # Update status
        result.status = DocIndexStatus.COMPLETED if result.failed_files == 0 else DocIndexStatus.PARTIAL
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        
        # Save state
        self._save_state()
        
        logger.info(f"Documentation indexing completed: {result.indexed_files} files, {result.total_chunks} chunks in {result.duration_seconds:.1f}s")
        
        return result
    
    def _index_file(self, 
                    file_path: Path,
                    force: bool = False,
                    collection: Optional[str] = None) -> Dict[str, Any]:
        """Index a single documentation file."""
        rel_path = str(file_path.relative_to(self.config.project_root))
        
        # Check if file needs indexing
        content_hash = self._compute_file_hash(file_path)
        existing_state = self.file_states.get(rel_path)
        
        if not force and existing_state and existing_state.content_hash == content_hash:
            logger.debug(f"Skipping unchanged documentation: {rel_path}")
            return {
                'indexed': False,
                'reason': 'unchanged'
            }
        
        logger.info(f"Indexing documentation: {rel_path}")
        
        # Chunk the document
        chunking_result = self.chunker.chunk_file(file_path)
        
        if not chunking_result.chunks:
            return {
                'indexed': False,
                'reason': 'no_chunks'
            }
        
        result = {
            'indexed': True,
            'chunks': len(chunking_result.chunks),
            'sections': len(chunking_result.structure.sections),
            'headings': len(chunking_result.structure.headings),
            'new_chunks': 0,
            'updated_chunks': 0,
            'unchanged_chunks': 0
        }
        
        # Detect document type
        doc_type = self._detect_doc_type(file_path, chunking_result.structure)
        
        # Extract title
        title = chunking_result.structure.title
        if not title and chunking_result.structure.headings:
            title = chunking_result.structure.headings[0][1]
        if not title:
            title = file_path.stem
        
        # Index chunks
        chunk_ids = self._index_chunks(chunking_result.chunks, rel_path, doc_type)
        
        # Determine new/updated/unchanged
        if existing_state:
            old_chunk_ids = set(existing_state.chunk_ids)
            new_chunk_ids = set(chunk_ids)
            
            result['new_chunks'] = len(new_chunk_ids - old_chunk_ids)
            result['updated_chunks'] = 0
            result['unchanged_chunks'] = len(new_chunk_ids & old_chunk_ids)
            
            # Delete old chunks
            for old_id in existing_state.chunk_ids:
                if old_id not in chunk_ids:
                    self.store.delete(old_id, CollectionType.DOCUMENTATION)
        else:
            result['new_chunks'] = len(chunk_ids)
            result['unchanged_chunks'] = 0
        
        # Update file state
        git_commit = self.git.get_current_commit() if self.git else None
        
        self.file_states[rel_path] = DocFileState(
            file_path=rel_path,
            content_hash=content_hash,
            indexed_at=datetime.now(),
            chunk_count=len(chunk_ids),
            section_count=len(chunking_result.structure.sections),
            heading_count=len(chunking_result.structure.headings),
            chunk_ids=chunk_ids,
            doc_type=doc_type,
            title=title,
            structure={
                'headings': [
                    {'level': h[0], 'text': h[1], 'line': h[2]}
                    for h in chunking_result.structure.headings
                ],
                'sections': chunking_result.structure.sections,
                'toc': chunking_result.structure.toc,
                'frontmatter': chunking_result.structure.frontmatter
            },
            git_commit=git_commit
        )
        
        # Add to collection
        coll_name = collection or self._get_collection_for_doc_type(doc_type)
        if coll_name in self.collections:
            if rel_path not in self.collections[coll_name].files:
                self.collections[coll_name].files.append(rel_path)
            self.collections[coll_name].chunk_ids.extend(chunk_ids)
        
        # Cache structures
        self._structure_cache[rel_path] = chunking_result.structure
        self._toc_cache[rel_path] = chunking_result.structure.toc
        
        # Build breadcrumb cache
        self._build_breadcrumb_cache(rel_path, chunking_result)
        
        return result
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _index_chunks(self, chunks: List[DocChunk], source_file: str, doc_type: DocType) -> List[str]:
        """Index documentation chunks into vector store."""
        chunk_ids = []
        
        for chunk in chunks:
            # Prepare metadata
            metadata = {
                'source_file': source_file,
                'chunk_type': chunk.chunk_type.value,
                'format': chunk.format.value,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'heading': chunk.heading,
                'heading_level': chunk.heading_level,
                'section': chunk.section.value,
                'parent_heading': chunk.parent_heading,
                'doc_type': doc_type.value,
                'tags': chunk.tags,
                'references': chunk.references,
                'code_refs': chunk.code_refs,
                'order_index': chunk.order_index,
                **chunk.metadata
            }
            
            if chunk.language:
                metadata['language'] = chunk.language
            
            if chunk.children:
                metadata['children'] = chunk.children
            
            if chunk.parent_id:
                metadata['parent_id'] = chunk.parent_id
            
            # Add to store
            doc_id = chunk.id
            stored_id = self.store.add(
                content=chunk.content,
                collection_type=CollectionType.DOCUMENTATION,
                metadata=metadata,
                doc_id=doc_id
            )
            
            if stored_id:
                chunk_ids.append(stored_id)
                self._chunk_cache[stored_id] = chunk
                
                # Track references
                for ref in chunk.references:
                    self._internal_links[stored_id].append(ref)
                
                for code_ref in chunk.code_refs:
                    self._doc_to_code_refs[stored_id].append(code_ref)
                    self._code_to_doc_refs[code_ref].append(stored_id)
        
        return chunk_ids
    
    def _build_breadcrumb_cache(self, file_path: str, chunking_result: DocChunkingResult):
        """Build breadcrumb navigation cache."""
        heading_stack = []
        
        for chunk in chunking_result.chunks:
            if chunk.chunk_type == DocChunkType.HEADING and chunk.heading:
                while heading_stack and heading_stack[-1][1] >= chunk.heading_level:
                    heading_stack.pop()
                heading_stack.append((chunk.heading, chunk.heading_level))
            
            breadcrumb = [h[0] for h in heading_stack]
            self._breadcrumb_cache[chunk.id] = breadcrumb
    
    def _get_collection_for_doc_type(self, doc_type: DocType) -> str:
        """Get collection name for document type."""
        mapping = {
            DocType.README: 'readme',
            DocType.API_DOCS: 'api_docs',
            DocType.ARCHITECTURE: 'architecture',
            DocType.TUTORIAL: 'tutorials',
            DocType.HOWTO: 'howtos',
            DocType.REFERENCE: 'reference',
            DocType.CHANGELOG: 'reference',
            DocType.CONTRIBUTING: 'reference',
            DocType.LICENSE: 'reference'
        }
        return mapping.get(doc_type, 'reference')
    
    def _build_cross_references(self):
        """Build cross-reference mappings between documents."""
        # Resolve internal links
        resolved_links = {}
        for source_id, targets in self._internal_links.items():
            resolved = []
            for target in targets:
                # Try to find target chunk
                for chunk_id, chunk in self._chunk_cache.items():
                    if chunk.heading and target in chunk.heading:
                        resolved.append(chunk_id)
                        break
            resolved_links[source_id] = resolved
        
        self._internal_links.update(resolved_links)
    
    # ============================================================
    # INCREMENTAL INDEXING
    # ============================================================
    
    def index_changed_files(self) -> DocIndexingResult:
        """Index only documentation files that have changed."""
        if not self.git:
            logger.warning("Git integration not available for incremental indexing")
            return self.index(full=True)
        
        # Get changed files
        changed_files = self.git.get_changed_files()
        
        if not changed_files:
            logger.info("No changed documentation files detected")
            return DocIndexingResult(
                status=DocIndexStatus.UP_TO_DATE,
                total_files=0,
                indexed_files=0,
                skipped_files=0,
                failed_files=0,
                total_chunks=0,
                total_sections=0,
                total_headings=0,
                new_chunks=0,
                updated_chunks=0,
                unchanged_chunks=0,
                duration_seconds=0
            )
        
        # Filter documentation files
        doc_files = [f for f in changed_files if self._should_include_file(f)]
        
        logger.info(f"Indexing {len(doc_files)} changed documentation files")
        
        return self.index(files=doc_files)
    
    # ============================================================
    # SEARCH
    # ============================================================
    
    def search(self,
               query: str,
               n_results: int = 10,
               min_similarity: float = 0.3,
               doc_type: Optional[DocType] = None,
               section: Optional[DocSection] = None,
               collection: Optional[str] = None,
               file_pattern: Optional[str] = None) -> List[DocSearchResult]:
        """
        Search documentation semantically.
        
        Args:
            query: Search query
            n_results: Number of results
            min_similarity: Minimum similarity threshold
            doc_type: Filter by document type
            section: Filter by section type
            collection: Filter by collection name
            file_pattern: Filter by file pattern
        """
        # Build metadata filter
        where = {}
        
        if doc_type:
            where['doc_type'] = doc_type.value
        
        if section:
            where['section'] = section.value
        
        if collection and collection in self.collections:
            # Filter by collection files
            coll_files = self.collections[collection].files
            if coll_files:
                where['source_file'] = {'$in': coll_files}
        
        # Search in store
        store_results = self.store.search(
            query=query,
            collection_type=CollectionType.DOCUMENTATION,
            n_results=n_results * 2,
            where=where if where else None,
            min_similarity=min_similarity
        )
        
        # Convert results
        results = []
        
        for sr in store_results:
            # Apply file pattern filter
            if file_pattern:
                source_file = sr.metadata.get('source_file', '')
                if not self._match_pattern(source_file, file_pattern):
                    continue
            
            # Get cached chunk
            chunk = self._chunk_cache.get(sr.id)
            if not chunk:
                # Reconstruct chunk
                chunk = DocChunk(
                    id=sr.id,
                    chunk_type=DocChunkType(sr.metadata.get('chunk_type', 'paragraph')),
                    format=DocFormat(sr.metadata.get('format', 'markdown')),
                    content=sr.content,
                    file_path=sr.metadata.get('source_file', ''),
                    start_line=sr.metadata.get('start_line', 0),
                    end_line=sr.metadata.get('end_line', 0),
                    heading=sr.metadata.get('heading'),
                    heading_level=sr.metadata.get('heading_level', 0),
                    section=DocSection(sr.metadata.get('section', 'unknown')),
                    parent_heading=sr.metadata.get('parent_heading'),
                    language=sr.metadata.get('language'),
                    tags=sr.metadata.get('tags', []),
                    references=sr.metadata.get('references', []),
                    code_refs=sr.metadata.get('code_refs', [])
                )
            
            # Extract matched terms
            query_terms = set(query.lower().split())
            content_terms = set(sr.content.lower().split())
            matched_terms = list(query_terms & content_terms)[:5]
            
            # Get breadcrumb
            breadcrumb = self._breadcrumb_cache.get(sr.id, [])
            
            result = DocSearchResult(
                chunk=chunk,
                similarity=sr.similarity,
                matched_terms=matched_terms,
                source_file=sr.metadata.get('source_file', ''),
                heading=chunk.heading,
                section=chunk.section,
                breadcrumb=breadcrumb
            )
            
            results.append(result)
        
        # Sort by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results[:n_results]
    
    def search_by_heading(self, heading: str, doc_type: Optional[DocType] = None) -> List[DocSearchResult]:
        """Search for documentation by heading."""
        where = {'heading': heading}
        if doc_type:
            where['doc_type'] = doc_type.value
        
        docs = self.store.get_by_metadata(where, CollectionType.DOCUMENTATION)
        
        results = []
        for doc in docs:
            chunk = self._chunk_cache.get(doc.id)
            if chunk:
                results.append(DocSearchResult(
                    chunk=chunk,
                    similarity=1.0,
                    matched_terms=[heading],
                    source_file=doc.metadata.get('source_file', ''),
                    heading=chunk.heading,
                    section=chunk.section,
                    breadcrumb=self._breadcrumb_cache.get(doc.id, [])
                ))
        
        return results
    
    def search_code_references(self, code_symbol: str) -> List[DocSearchResult]:
        """Find documentation referencing a specific code symbol."""
        doc_ids = self._code_to_doc_refs.get(code_symbol, [])
        
        results = []
        for doc_id in doc_ids:
            chunk = self._chunk_cache.get(doc_id)
            if chunk:
                results.append(DocSearchResult(
                    chunk=chunk,
                    similarity=1.0,
                    matched_terms=[code_symbol],
                    source_file=chunk.file_path,
                    heading=chunk.heading,
                    section=chunk.section,
                    breadcrumb=self._breadcrumb_cache.get(doc_id, [])
                ))
        
        return results
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match text against glob pattern."""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    # ============================================================
    # NAVIGATION AND TOC
    # ============================================================
    
    def get_document_structure(self, file_path: str) -> Optional[DocStructure]:
        """Get cached document structure."""
        return self._structure_cache.get(file_path)
    
    def get_table_of_contents(self, file_path: str) -> List[Dict[str, Any]]:
        """Get table of contents for a document."""
        return self._toc_cache.get(file_path, [])
    
    def get_breadcrumb(self, chunk_id: str) -> List[str]:
        """Get breadcrumb for a chunk."""
        return self._breadcrumb_cache.get(chunk_id, [])
    
    def get_document_navigation(self, file_path: str) -> Dict[str, Any]:
        """Get complete navigation structure for a document."""
        structure = self._structure_cache.get(file_path)
        if not structure:
            return {}
        
        return {
            'title': structure.title,
            'headings': [
                {'level': h[0], 'text': h[1], 'line': h[2]}
                for h in structure.headings
            ],
            'toc': structure.toc,
            'sections': structure.sections
        }
    
    # ============================================================
    # COLLECTION MANAGEMENT
    # ============================================================
    
    def create_collection(self, name: str, doc_type: DocType, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new document collection."""
        if name in self.collections:
            logger.warning(f"Collection '{name}' already exists")
            return False
        
        self.collections[name] = DocCollection(
            name=name,
            doc_type=doc_type,
            metadata=metadata or {}
        )
        
        self._save_state()
        logger.info(f"Created collection: {name}")
        return True
    
    def add_to_collection(self, collection_name: str, file_path: str) -> bool:
        """Add a document to a collection."""
        if collection_name not in self.collections:
            logger.warning(f"Collection '{collection_name}' not found")
            return False
        
        if file_path not in self.file_states:
            logger.warning(f"File '{file_path}' not indexed")
            return False
        
        collection = self.collections[collection_name]
        
        if file_path not in collection.files:
            collection.files.append(file_path)
            collection.chunk_ids.extend(self.file_states[file_path].chunk_ids)
            self._save_state()
        
        return True
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        return [
            {
                'name': coll.name,
                'doc_type': coll.doc_type.value,
                'file_count': len(coll.files),
                'chunk_count': len(coll.chunk_ids),
                'metadata': coll.metadata
            }
            for coll in self.collections.values()
        ]
    
    # ============================================================
    # METRICS AND STATISTICS
    # ============================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get documentation statistics."""
        stats = {
            'total_files': len(self.file_states),
            'total_chunks': sum(s.chunk_count for s in self.file_states.values()),
            'total_sections': sum(s.section_count for s in self.file_states.values()),
            'total_headings': sum(s.heading_count for s in self.file_states.values()),
            'by_doc_type': defaultdict(int),
            'by_format': defaultdict(int),
            'by_section': defaultdict(int),
            'collections': len(self.collections),
            'code_references': len(self._doc_to_code_refs),
            'internal_links': sum(len(links) for links in self._internal_links.values())
        }
        
        for state in self.file_states.values():
            stats['by_doc_type'][state.doc_type.value] += 1
        
        return dict(stats)
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get current index status."""
        return {
            'total_files_indexed': len(self.file_states),
            'total_chunks_cached': len(self._chunk_cache),
            'collections': len(self.collections),
            'last_indexed': self.state.get('last_indexed'),
            'git_commit': self.git.get_current_commit() if self.git else None,
            'collection_stats': self.store.get_collection_stats(CollectionType.DOCUMENTATION)
        }
    
    # ============================================================
    # EXPORT AND MAINTENANCE
    # ============================================================
    
    def export_index(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Export index data."""
        data = {
            'exported_at': datetime.now().isoformat(),
            'config': {
                'project_root': str(self.config.project_root),
                'docs_paths': [str(p) for p in self.config.docs_paths]
            },
            'statistics': self.get_statistics(),
            'file_states': {
                path: {
                    'content_hash': state.content_hash,
                    'indexed_at': state.indexed_at.isoformat(),
                    'chunk_count': state.chunk_count,
                    'doc_type': state.doc_type.value,
                    'title': state.title,
                    'git_commit': state.git_commit
                }
                for path, state in self.file_states.items()
            },
            'collections': {
                name: {
                    'doc_type': coll.doc_type.value,
                    'files': coll.files,
                    'chunk_count': len(coll.chunk_ids),
                    'metadata': coll.metadata
                }
                for name, coll in self.collections.items()
            }
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported documentation index to {output_path}")
        
        return data
    
    def clear_index(self, confirm: bool = False):
        """Clear all indexed documentation."""
        if not confirm:
            logger.warning("Use confirm=True to clear index")
            return
        
        self.store.clear_collection(CollectionType.DOCUMENTATION)
        
        self.file_states.clear()
        self._chunk_cache.clear()
        self._structure_cache.clear()
        self._breadcrumb_cache.clear()
        self._toc_cache.clear()
        self._doc_to_code_refs.clear()
        self._code_to_doc_refs.clear()
        self._internal_links.clear()
        
        for coll in self.collections.values():
            coll.files.clear()
            coll.chunk_ids.clear()
        
        self._save_state()
        
        logger.info("Documentation index cleared")
    
    def close(self):
        """Clean up resources."""
        self._save_state()
        self.store.close()
        logger.info("DocIndexer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for documentation indexer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index documentation for semantic search")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--index", action="store_true", help="Index documentation")
    parser.add_argument("--full", action="store_true", help="Force full reindexing")
    parser.add_argument("--incremental", action="store_true", help="Index only changed files")
    parser.add_argument("--search", type=str, help="Search query")
    parser.add_argument("--heading", type=str, help="Search by heading")
    parser.add_argument("--doc-type", choices=[t.value for t in DocType], help="Filter by document type")
    parser.add_argument("--collection", type=str, help="Filter by collection")
    parser.add_argument("--n-results", type=int, default=10, help="Number of search results")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--status", action="store_true", help="Show index status")
    parser.add_argument("--toc", type=str, help="Show table of contents for file")
    parser.add_argument("--collections", action="store_true", help="List collections")
    parser.add_argument("--create-collection", type=str, help="Create new collection")
    parser.add_argument("--export", type=Path, help="Export index to file")
    parser.add_argument("--clear", action="store_true", help="Clear index")
    
    args = parser.parse_args()
    
    config = DocIndexingConfig(project_root=args.project_root)
    indexer = DocIndexer(config)
    
    if args.clear:
        indexer.clear_index(confirm=True)
        print("Documentation index cleared")
        return
    
    if args.status:
        status = indexer.get_index_status()
        print(json.dumps(status, indent=2, default=str))
        return
    
    if args.stats:
        stats = indexer.get_statistics()
        print(json.dumps(stats, indent=2, default=str))
        return
    
    if args.collections:
        collections = indexer.list_collections()
        print(f"\nCollections ({len(collections)}):\n")
        for coll in collections:
            print(f"  {coll['name']}: {coll['doc_type']} ({coll['file_count']} files, {coll['chunk_count']} chunks)")
        return
    
    if args.create_collection:
        doc_type = DocType(args.doc_type) if args.doc_type else DocType.REFERENCE
        if indexer.create_collection(args.create_collection, doc_type):
            print(f"Created collection: {args.create_collection}")
        else:
            print(f"Failed to create collection")
        return
    
    if args.toc:
        toc = indexer.get_table_of_contents(args.toc)
        if toc:
            print(f"\nTable of Contents for {args.toc}:\n")
            for item in toc:
                indent = "  " * (item['level'] - 1)
                print(f"{indent}- {item['text']}")
        else:
            print(f"Document not found: {args.toc}")
        return
    
    if args.index or args.full or args.incremental:
        if args.incremental:
            result = indexer.index_changed_files()
        else:
            result = indexer.index(full=args.full)
        
        print(f"\nDocumentation indexing completed:")
        print(f"  Status: {result.status.value}")
        print(f"  Files: {result.indexed_files} indexed, {result.skipped_files} skipped, {result.failed_files} failed")
        print(f"  Chunks: {result.total_chunks} total ({result.new_chunks} new)")
        print(f"  Sections: {result.total_sections}, Headings: {result.total_headings}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors[:5]:
                print(f"  - {error}")
        return
    
    if args.heading:
        doc_type = DocType(args.doc_type) if args.doc_type else None
        results = indexer.search_by_heading(args.heading, doc_type)
        print(f"\nSearch results for heading '{args.heading}':\n")
        for i, r in enumerate(results[:args.n_results], 1):
            print(f"{i}. {r.source_file}")
            print(f"   Heading: {r.heading}")
            print(f"   Section: {r.section.value}")
            print(f"   Content: {r.chunk.content[:200]}...")
            print()
        return
    
    if args.search:
        doc_type = DocType(args.doc_type) if args.doc_type else None
        results = indexer.search(
            args.search,
            n_results=args.n_results,
            doc_type=doc_type,
            collection=args.collection
        )
        
        print(f"\nSearch results for '{args.search}':\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r.similarity:.3f}] {r.source_file}")
            if r.heading:
                print(f"   Heading: {r.heading}")
            if r.breadcrumb:
                print(f"   Breadcrumb: {' > '.join(r.breadcrumb)}")
            if r.matched_terms:
                print(f"   Matched: {', '.join(r.matched_terms)}")
            print(f"   Content: {r.chunk.content[:200]}...")
            print()
        return
    
    if args.export:
        indexer.export_index(args.export)
        print(f"Index exported to {args.export}")
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()