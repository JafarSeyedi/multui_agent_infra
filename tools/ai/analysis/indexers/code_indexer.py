#!/usr/bin/env python3
"""
Code Indexer - AI Development Framework
Indexes code chunks into vector store for semantic code search.

Part of the Level 2 Analysis tools (indexers/code_indexer.py)

This code_indexer.py provides:

Full and Incremental Indexing - Index entire codebase or only changed files
1. Chunk and Symbol Indexing - Both granular chunks and high-level symbols
2. Git Integration - Track changes via git commits, auto-update on watched branches
3. Semantic Code Search - Natural language queries over code
4. Symbol-Aware Search - Search by symbol name with type filtering
5. Dependency Graph - Track and query code dependencies
6. Duplicate Detection - Find duplicate code chunks
7. Code Metrics - Complexity analysis, most-used symbols, etc.
8. State Persistence - Incremental updates with content hashing
9. Watch Mode - Continuous monitoring and auto-indexing
10. Export Capabilities - Export index data for backup/analysis
11. Rich Metadata - Store and query by complexity, dependencies, docstrings

The code indexer provides the foundation for intelligent code search and analysis across your entire codebase.
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
from ..scanners.project_scanner import ProjectScanner, CodeSymbol, ModuleInfo
from ..chunkers.code_chunker import CodeChunker, CodeChunk, ChunkingResult, ChunkType
from ..encoders.embedding_store import EmbeddingStore, CollectionType, SearchResult, StoredDocument
from ..encoders.batch_encoder import BatchEncoder, BatchJob, BatchPriority

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class IndexStatus(str, Enum):
    """Status of indexing operation."""
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    UP_TO_DATE = "up_to_date"


class SymbolType(str, Enum):
    """Type of code symbol for indexing."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    DECORATOR = "decorator"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TYPE_ALIAS = "type_alias"
    ENUM = "enum"
    DATACLASS = "dataclass"
    IMPORT = "import"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class IndexingConfig:
    """Configuration for code indexing."""
    project_root: Path
    vector_store_path: Optional[Path] = None
    include_patterns: List[str] = field(default_factory=lambda: ["*.py"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__/*", "*.pyc", ".git/*", ".venv/*", "venv/*",
        "dist/*", "build/*", "*.egg-info/*", ".pytest_cache/*",
        ".mypy_cache/*", ".ruff_cache/*", ".ai_state/*"
    ])
    chunk_granularity: str = "medium"  # fine, medium, coarse
    min_chunk_lines: int = 5
    max_chunk_lines: int = 200
    batch_size: int = 50
    incremental: bool = True
    track_changes: bool = True
    index_imports: bool = True
    index_docstrings: bool = True
    compute_complexity: bool = True
    extract_dependencies: bool = True
    auto_update_on_commit: bool = False
    watch_branches: List[str] = field(default_factory=lambda: ["main", "master", "develop"])


@dataclass
class IndexingResult:
    """Result of indexing operation."""
    status: IndexStatus
    total_files: int
    indexed_files: int
    skipped_files: int
    failed_files: int
    total_chunks: int
    total_symbols: int
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
class FileIndexState:
    """State of an indexed file."""
    file_path: str
    content_hash: str
    indexed_at: datetime
    chunk_count: int
    symbol_count: int
    chunk_ids: List[str] = field(default_factory=list)
    symbol_ids: List[str] = field(default_factory=list)
    git_commit: Optional[str] = None


@dataclass
class CodeSearchResult:
    """Enhanced search result for code."""
    chunk: CodeChunk
    symbol: Optional[CodeSymbol] = None
    similarity: float = 0.0
    matched_terms: List[str] = field(default_factory=list)
    source_file: str = ""
    line_range: Tuple[int, int] = (0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk.id,
            'chunk_type': self.chunk.chunk_type.value,
            'content': self.chunk.content,
            'symbol_name': self.symbol.name if self.symbol else None,
            'symbol_type': self.symbol.symbol_type if self.symbol else None,
            'similarity': self.similarity,
            'matched_terms': self.matched_terms,
            'source_file': self.source_file,
            'line_start': self.line_range[0],
            'line_end': self.line_range[1],
            'signature': self.chunk.signature,
            'docstring': self.chunk.docstring,
            'complexity': self.chunk.complexity
        }


# ============================================================
# MAIN CODE INDEXER CLASS
# ============================================================

class CodeIndexer:
    """
    Indexes code into vector store for semantic search and analysis.
    
    Features:
    - Full and incremental indexing of codebase
    - Chunk-based indexing with configurable granularity
    - Symbol-level indexing for precise code search
    - Git integration for change tracking
    - Automatic updates on commits
    - Cross-referencing between chunks and symbols
    - Dependency graph indexing
    - Semantic code search with filters
    - Code-aware similarity scoring
    - Export and backup capabilities
    """
    
    def __init__(self, 
                 config: IndexingConfig,
                 store: Optional[EmbeddingStore] = None,
                 scanner: Optional[ProjectScanner] = None,
                 chunker: Optional[CodeChunker] = None,
                 batch_encoder: Optional[BatchEncoder] = None):
        self.config = config
        
        # Initialize components
        self.store = store or EmbeddingStore()
        self.scanner = scanner or ProjectScanner(config.project_root)
        self.chunker = chunker or CodeChunker()
        self.batch_encoder = batch_encoder
        
        # Git integration
        self.git = GitUtils(config.project_root) if config.track_changes else None
        
        # State management
        self.state = StateManager(config.project_root / ".ai_state" / "code_indexer.json")
        self.file_states: Dict[str, FileIndexState] = {}
        
        # Caches
        self._chunk_cache: Dict[str, CodeChunk] = {}
        self._symbol_cache: Dict[str, CodeSymbol] = {}
        self._dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self._reverse_dependency_graph: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing state
        self._load_state()
        
        logger.info(f"CodeIndexer initialized for {config.project_root}")
    
    def _load_state(self):
        """Load persisted indexing state."""
        saved_states = self.state.get('file_states', {})
        for file_path, state_data in saved_states.items():
            self.file_states[file_path] = FileIndexState(
                file_path=state_data['file_path'],
                content_hash=state_data['content_hash'],
                indexed_at=datetime.fromisoformat(state_data['indexed_at']),
                chunk_count=state_data.get('chunk_count', 0),
                symbol_count=state_data.get('symbol_count', 0),
                chunk_ids=state_data.get('chunk_ids', []),
                symbol_ids=state_data.get('symbol_ids', []),
                git_commit=state_data.get('git_commit')
            )
        
        # Load dependency graph
        saved_graph = self.state.get('dependency_graph', {})
        for source, targets in saved_graph.items():
            self._dependency_graph[source] = targets
        
        saved_reverse = self.state.get('reverse_dependency_graph', {})
        for target, sources in saved_reverse.items():
            self._reverse_dependency_graph[target] = sources
        
        logger.info(f"Loaded state for {len(self.file_states)} files")
    
    def _save_state(self):
        """Persist indexing state."""
        state_data = {}
        for file_path, state in self.file_states.items():
            state_data[file_path] = {
                'file_path': state.file_path,
                'content_hash': state.content_hash,
                'indexed_at': state.indexed_at.isoformat(),
                'chunk_count': state.chunk_count,
                'symbol_count': state.symbol_count,
                'chunk_ids': state.chunk_ids,
                'symbol_ids': state.symbol_ids,
                'git_commit': state.git_commit
            }
        
        self.state.set('file_states', state_data)
        self.state.set('dependency_graph', dict(self._dependency_graph))
        self.state.set('reverse_dependency_graph', dict(self._reverse_dependency_graph))
        self.state.set('last_indexed', datetime.now().isoformat())
        self.state.save()
    
    # ============================================================
    # INDEXING
    # ============================================================
    
    def index(self, 
              full: bool = False,
              files: Optional[List[Path]] = None,
              symbols_only: bool = False) -> IndexingResult:
        """
        Index the codebase.
        
        Args:
            full: Force full reindexing
            files: Specific files to index
            symbols_only: Only index symbols, skip chunks
        """
        start_time = datetime.now()
        logger.info(f"Starting indexing (full={full}, symbols_only={symbols_only})")
        
        result = IndexingResult(
            status=IndexStatus.INDEXING,
            total_files=0,
            indexed_files=0,
            skipped_files=0,
            failed_files=0,
            total_chunks=0,
            total_symbols=0,
            new_chunks=0,
            updated_chunks=0,
            unchanged_chunks=0,
            duration_seconds=0
        )
        
        # Get current git commit
        if self.git:
            result.git_commit = self.git.get_current_commit()
        
        # Scan project
        if files:
            python_files = [f for f in files if f.suffix == '.py']
        else:
            python_files = list(self.config.project_root.rglob("*.py"))
        
        # Filter excluded patterns
        python_files = self._filter_files(python_files)
        result.total_files = len(python_files)
        
        # Process files
        for file_path in python_files:
            try:
                file_result = self._index_file(file_path, full, symbols_only)
                
                if file_result['indexed']:
                    result.indexed_files += 1
                    result.total_chunks += file_result.get('chunks', 0)
                    result.total_symbols += file_result.get('symbols', 0)
                    result.new_chunks += file_result.get('new_chunks', 0)
                    result.updated_chunks += file_result.get('updated_chunks', 0)
                    result.unchanged_chunks += file_result.get('unchanged_chunks', 0)
                else:
                    result.skipped_files += 1
                    
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                result.failed_files += 1
                result.errors.append(f"{file_path}: {str(e)}")
        
        # Build dependency graph
        if self.config.extract_dependencies and not symbols_only:
            self._build_dependency_graph()
        
        # Update status
        result.status = IndexStatus.COMPLETED if result.failed_files == 0 else IndexStatus.PARTIAL
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        
        # Save state
        self._save_state()
        
        logger.info(f"Indexing completed: {result.indexed_files} files, {result.total_chunks} chunks, {result.total_symbols} symbols in {result.duration_seconds:.1f}s")
        
        return result
    
    def _filter_files(self, files: List[Path]) -> List[Path]:
        """Filter files based on include/exclude patterns."""
        import fnmatch
        
        filtered = []
        
        for file_path in files:
            rel_path = str(file_path.relative_to(self.config.project_root))
            
            # Check include patterns
            included = any(fnmatch.fnmatch(rel_path, p) for p in self.config.include_patterns)
            if not included:
                continue
            
            # Check exclude patterns
            excluded = any(fnmatch.fnmatch(rel_path, p) for p in self.config.exclude_patterns)
            if excluded:
                continue
            
            filtered.append(file_path)
        
        return filtered
    
    def _index_file(self, 
                    file_path: Path,
                    force: bool = False,
                    symbols_only: bool = False) -> Dict[str, Any]:
        """Index a single file."""
        rel_path = str(file_path.relative_to(self.config.project_root))
        
        # Check if file needs indexing
        content_hash = self._compute_file_hash(file_path)
        existing_state = self.file_states.get(rel_path)
        
        if not force and existing_state and existing_state.content_hash == content_hash:
            logger.debug(f"Skipping unchanged file: {rel_path}")
            return {
                'indexed': False,
                'reason': 'unchanged'
            }
        
        logger.info(f"Indexing file: {rel_path}")
        
        # Scan file for symbols
        module_info = self.scanner._analyze_module(file_path)
        
        if not module_info:
            return {
                'indexed': False,
                'reason': 'scan_failed'
            }
        
        result = {
            'indexed': True,
            'chunks': 0,
            'symbols': len(module_info.symbols),
            'new_chunks': 0,
            'updated_chunks': 0,
            'unchanged_chunks': 0
        }
        
        # Index symbols
        symbol_ids = []
        for symbol in module_info.symbols:
            symbol_id = self._index_symbol(symbol, rel_path)
            if symbol_id:
                symbol_ids.append(symbol_id)
                self._symbol_cache[symbol_id] = symbol
        
        # Index chunks (if not symbols_only)
        if not symbols_only:
            chunking_result = self.chunker.chunk_file(file_path)
            
            # Batch encode chunks
            chunk_ids = self._index_chunks(chunking_result.chunks, rel_path)
            result['chunks'] = len(chunk_ids)
            
            # Determine new/updated/unchanged
            if existing_state:
                old_chunk_ids = set(existing_state.chunk_ids)
                new_chunk_ids = set(chunk_ids)
                
                result['new_chunks'] = len(new_chunk_ids - old_chunk_ids)
                result['updated_chunks'] = 0  # Would need content comparison
                result['unchanged_chunks'] = len(new_chunk_ids & old_chunk_ids)
            else:
                result['new_chunks'] = len(chunk_ids)
                result['unchanged_chunks'] = 0
            
            # Delete old chunks
            if existing_state:
                for old_id in existing_state.chunk_ids:
                    if old_id not in chunk_ids:
                        self.store.delete(old_id, CollectionType.CODE)
        else:
            chunk_ids = []
        
        # Update file state
        git_commit = self.git.get_current_commit() if self.git else None
        
        self.file_states[rel_path] = FileIndexState(
            file_path=rel_path,
            content_hash=content_hash,
            indexed_at=datetime.now(),
            chunk_count=len(chunk_ids),
            symbol_count=len(symbol_ids),
            chunk_ids=chunk_ids,
            symbol_ids=symbol_ids,
            git_commit=git_commit
        )
        
        return result
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _index_chunks(self, chunks: List[CodeChunk], source_file: str) -> List[str]:
        """Index code chunks into vector store."""
        chunk_ids = []
        
        for chunk in chunks:
            # Prepare metadata
            metadata = {
                'source_file': source_file,
                'chunk_type': chunk.chunk_type.value,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'symbol_name': chunk.symbol_name,
                'parent_symbol': chunk.parent_symbol,
                'complexity': chunk.complexity,
                'has_docstring': chunk.docstring is not None,
                'language': chunk.language.value,
                **chunk.metadata
            }
            
            if chunk.decorators:
                metadata['decorators'] = chunk.decorators
            
            if chunk.dependencies:
                metadata['dependencies'] = chunk.dependencies
            
            # Add to store
            doc_id = chunk.id
            stored_id = self.store.add(
                content=chunk.content,
                collection_type=CollectionType.CODE,
                metadata=metadata,
                doc_id=doc_id
            )
            
            if stored_id:
                chunk_ids.append(stored_id)
                self._chunk_cache[stored_id] = chunk
                
                # Index dependencies
                for dep in chunk.dependencies:
                    self._dependency_graph[chunk.symbol_name or chunk.id].append(dep)
                    self._reverse_dependency_graph[dep].append(chunk.symbol_name or chunk.id)
        
        return chunk_ids
    
    def _index_symbol(self, symbol: CodeSymbol, source_file: str) -> Optional[str]:
        """Index a code symbol."""
        # Prepare content for embedding
        content_parts = []
        content_parts.append(f"Symbol: {symbol.name}")
        content_parts.append(f"Type: {symbol.symbol_type}")
        
        if symbol.signature:
            content_parts.append(f"Signature: {symbol.signature}")
        
        if symbol.docstring:
            content_parts.append(f"Documentation: {symbol.docstring}")
        
        if symbol.decorators:
            content_parts.append(f"Decorators: {', '.join(symbol.decorators)}")
        
        content = '\n'.join(content_parts)
        
        # Prepare metadata
        metadata = {
            'source_file': source_file,
            'symbol_name': symbol.name,
            'symbol_type': symbol.symbol_type,
            'line_start': symbol.line_start,
            'line_end': symbol.line_end,
            'complexity': symbol.complexity,
            'has_docstring': symbol.docstring is not None,
            'dependencies': symbol.dependencies,
            'used_by': symbol.used_by
        }
        
        if symbol.decorators:
            metadata['decorators'] = symbol.decorators
        
        # Add to store
        doc_id = f"symbol_{hashlib.sha256(symbol.name.encode()).hexdigest()[:16]}"
        stored_id = self.store.add(
            content=content,
            collection_type=CollectionType.SYMBOLS,
            metadata=metadata,
            doc_id=doc_id
        )
        
        return stored_id
    
    def _build_dependency_graph(self):
        """Build full dependency graph from indexed symbols."""
        # Query all symbols
        symbols = self.store.get_by_metadata({}, CollectionType.SYMBOLS)
        
        for symbol in symbols:
            symbol_name = symbol.metadata.get('symbol_name')
            dependencies = symbol.metadata.get('dependencies', [])
            
            if symbol_name:
                self._dependency_graph[symbol_name] = dependencies
                for dep in dependencies:
                    self._reverse_dependency_graph[dep].append(symbol_name)
        
        logger.info(f"Built dependency graph with {len(self._dependency_graph)} nodes")
    
    # ============================================================
    # INCREMENTAL INDEXING
    # ============================================================
    
    def index_changed_files(self) -> IndexingResult:
        """Index only files that have changed since last index."""
        if not self.git:
            logger.warning("Git integration not available for incremental indexing")
            return self.index(full=True)
        
        # Get changed files
        changed_files = self.git.get_changed_files()
        
        if not changed_files:
            logger.info("No changed files detected")
            return IndexingResult(
                status=IndexStatus.UP_TO_DATE,
                total_files=0,
                indexed_files=0,
                skipped_files=0,
                failed_files=0,
                total_chunks=0,
                total_symbols=0,
                new_chunks=0,
                updated_chunks=0,
                unchanged_chunks=0,
                duration_seconds=0
            )
        
        # Filter Python files
        python_files = [f for f in changed_files if f.suffix == '.py']
        python_files = self._filter_files(python_files)
        
        logger.info(f"Indexing {len(python_files)} changed files")
        
        return self.index(files=python_files)
    
    def watch_and_index(self, interval_seconds: int = 60):
        """Watch for changes and automatically index."""
        import time
        
        logger.info(f"Starting watch mode (interval={interval_seconds}s)")
        
        try:
            while True:
                if self.config.auto_update_on_commit:
                    # Check if on watched branch
                    current_branch = self.git.get_current_branch()
                    if current_branch in self.config.watch_branches:
                        result = self.index_changed_files()
                        if result.indexed_files > 0:
                            logger.info(f"Auto-indexed {result.indexed_files} files")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Watch mode stopped")
    
    # ============================================================
    # SEARCH
    # ============================================================
    
    def search(self,
               query: str,
               n_results: int = 10,
               min_similarity: float = 0.3,
               symbol_types: Optional[List[str]] = None,
               file_pattern: Optional[str] = None,
               include_dependencies: bool = False) -> List[CodeSearchResult]:
        """
        Search code semantically.
        
        Args:
            query: Search query
            n_results: Number of results
            min_similarity: Minimum similarity threshold
            symbol_types: Filter by symbol types
            file_pattern: Filter by file pattern
            include_dependencies: Include dependent code
        """
        # Build metadata filter
        where = {}
        
        if symbol_types:
            where['symbol_type'] = {'$in': symbol_types}
        
        # Search in store
        store_results = self.store.search(
            query=query,
            collection_type=CollectionType.CODE,
            n_results=n_results * 2,  # Get more for filtering
            where=where if where else None,
            min_similarity=min_similarity
        )
        
        # Also search symbols collection
        symbol_results = self.store.search(
            query=query,
            collection_type=CollectionType.SYMBOLS,
            n_results=n_results,
            where=where if where else None,
            min_similarity=min_similarity
        )
        
        # Combine and convert results
        combined_results = []
        
        for sr in store_results + symbol_results:
            # Apply file pattern filter
            if file_pattern:
                source_file = sr.metadata.get('source_file', '')
                if not self._match_pattern(source_file, file_pattern):
                    continue
            
            # Convert to CodeSearchResult
            chunk = self._chunk_cache.get(sr.id)
            if not chunk:
                # Try to reconstruct chunk from stored data
                chunk = CodeChunk(
                    id=sr.id,
                    chunk_type=ChunkType(sr.metadata.get('chunk_type', 'function')),
                    language=Language.PYTHON,
                    content=sr.content,
                    file_path=sr.metadata.get('source_file', ''),
                    start_line=sr.metadata.get('start_line', 0),
                    end_line=sr.metadata.get('end_line', 0),
                    symbol_name=sr.metadata.get('symbol_name'),
                    docstring=None,  # Not stored separately
                    complexity=sr.metadata.get('complexity', 0)
                )
            
            # Find associated symbol
            symbol_name = sr.metadata.get('symbol_name')
            symbol = None
            if symbol_name:
                for sym_id, sym in self._symbol_cache.items():
                    if sym.name == symbol_name:
                        symbol = sym
                        break
            
            # Extract matched terms (simple keyword matching)
            query_terms = set(query.lower().split())
            content_terms = set(sr.content.lower().split())
            matched_terms = list(query_terms & content_terms)[:5]
            
            result = CodeSearchResult(
                chunk=chunk,
                symbol=symbol,
                similarity=sr.similarity,
                matched_terms=matched_terms,
                source_file=sr.metadata.get('source_file', ''),
                line_range=(sr.metadata.get('start_line', 0), sr.metadata.get('end_line', 0))
            )
            
            combined_results.append(result)
        
        # Sort by similarity
        combined_results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Limit results
        results = combined_results[:n_results]
        
        # Include dependencies if requested
        if include_dependencies:
            results = self._expand_with_dependencies(results)
        
        return results
    
    def search_by_symbol(self,
                         symbol_name: str,
                         include_related: bool = True) -> List[CodeSearchResult]:
        """Search for a specific symbol by name."""
        # Direct lookup in symbol cache
        for sym_id, symbol in self._symbol_cache.items():
            if symbol.name == symbol_name:
                # Find associated chunks
                chunks = []
                for chunk_id, chunk in self._chunk_cache.items():
                    if chunk.symbol_name == symbol_name:
                        result = CodeSearchResult(
                            chunk=chunk,
                            symbol=symbol,
                            similarity=1.0,
                            matched_terms=[symbol_name],
                            source_file=symbol.file_path,
                            line_range=(symbol.line_start, symbol.line_end)
                        )
                        chunks.append(result)
                
                if chunks:
                    return chunks
        
        # Fallback to store search
        results = self.store.get_by_metadata(
            {'symbol_name': symbol_name},
            CollectionType.CODE
        )
        
        search_results = []
        for doc in results:
            chunk = self._chunk_cache.get(doc.id)
            if chunk:
                search_results.append(CodeSearchResult(
                    chunk=chunk,
                    similarity=1.0,
                    matched_terms=[symbol_name],
                    source_file=doc.metadata.get('source_file', ''),
                    line_range=(doc.metadata.get('start_line', 0), doc.metadata.get('end_line', 0))
                ))
        
        # Include related symbols
        if include_related and symbol_name in self._dependency_graph:
            deps = self._dependency_graph[symbol_name]
            for dep in deps[:5]:
                dep_results = self.search_by_symbol(dep, include_related=False)
                search_results.extend(dep_results)
        
        return search_results
    
    def search_dependencies(self, symbol_name: str, direction: str = 'both') -> Dict[str, List[str]]:
        """Get dependencies for a symbol."""
        result = {
            'symbol': symbol_name,
            'dependencies': self._dependency_graph.get(symbol_name, []),
            'dependents': self._reverse_dependency_graph.get(symbol_name, [])
        }
        
        if direction == 'up':
            result.pop('dependents', None)
        elif direction == 'down':
            result.pop('dependencies', None)
        
        return result
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match text against glob pattern."""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def _expand_with_dependencies(self, results: List[CodeSearchResult]) -> List[CodeSearchResult]:
        """Expand search results with dependencies."""
        expanded = list(results)
        seen_symbols = set()
        
        for result in results:
            if result.symbol:
                seen_symbols.add(result.symbol.name)
        
        for result in results:
            if result.symbol and result.symbol.name in self._dependency_graph:
                for dep in self._dependency_graph[result.symbol.name][:3]:
                    if dep not in seen_symbols:
                        dep_results = self.search_by_symbol(dep, include_related=False)
                        expanded.extend(dep_results)
                        seen_symbols.add(dep)
        
        return expanded
    
    # ============================================================
    # QUERY AND ANALYSIS
    # ============================================================
    
    def find_similar_code(self, code_snippet: str, n_results: int = 5) -> List[CodeSearchResult]:
        """Find code similar to a given snippet."""
        return self.search(query=code_snippet, n_results=n_results, min_similarity=0.5)
    
    def find_duplicate_code(self, min_similarity: float = 0.9) -> List[Tuple[CodeSearchResult, CodeSearchResult]]:
        """Find potentially duplicate code chunks."""
        duplicates = []
        seen_hashes = {}
        
        # Get all chunks
        all_docs = self.store.get_by_metadata({}, CollectionType.CODE)
        
        for doc in all_docs:
            content_hash = hashlib.sha256(doc.content.encode()).hexdigest()
            
            if content_hash in seen_hashes:
                # Found duplicate
                chunk1 = self._chunk_cache.get(seen_hashes[content_hash])
                chunk2 = self._chunk_cache.get(doc.id)
                
                if chunk1 and chunk2:
                    result1 = CodeSearchResult(
                        chunk=chunk1,
                        similarity=1.0,
                        source_file=chunk1.file_path,
                        line_range=(chunk1.start_line, chunk1.end_line)
                    )
                    result2 = CodeSearchResult(
                        chunk=chunk2,
                        similarity=1.0,
                        source_file=chunk2.file_path,
                        line_range=(chunk2.start_line, chunk2.end_line)
                    )
                    duplicates.append((result1, result2))
            else:
                seen_hashes[content_hash] = doc.id
        
        return duplicates
    
    def get_code_metrics(self) -> Dict[str, Any]:
        """Get code metrics from indexed data."""
        metrics = {
            'total_files': len(self.file_states),
            'total_chunks': sum(s.chunk_count for s in self.file_states.values()),
            'total_symbols': sum(s.symbol_count for s in self.file_states.values()),
            'by_symbol_type': defaultdict(int),
            'by_complexity': {
                'low': 0,
                'medium': 0,
                'high': 0,
                'very_high': 0
            },
            'most_complex': [],
            'most_depended_upon': []
        }
        
        # Analyze symbols
        for symbol in self._symbol_cache.values():
            metrics['by_symbol_type'][symbol.symbol_type] += 1
            
            if symbol.complexity <= 5:
                metrics['by_complexity']['low'] += 1
            elif symbol.complexity <= 10:
                metrics['by_complexity']['medium'] += 1
            elif symbol.complexity <= 20:
                metrics['by_complexity']['high'] += 1
            else:
                metrics['by_complexity']['very_high'] += 1
        
        # Most complex symbols
        complex_symbols = sorted(
            self._symbol_cache.values(),
            key=lambda s: s.complexity,
            reverse=True
        )[:10]
        metrics['most_complex'] = [
            {'name': s.name, 'type': s.symbol_type, 'complexity': s.complexity, 'file': s.file_path}
            for s in complex_symbols
        ]
        
        # Most depended upon
        dep_counts = {name: len(deps) for name, deps in self._reverse_dependency_graph.items()}
        most_depended = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        metrics['most_depended_upon'] = [
            {'name': name, 'dependents': count}
            for name, count in most_depended
        ]
        
        return dict(metrics)
    
    # ============================================================
    # EXPORT AND MAINTENANCE
    # ============================================================
    
    def export_index(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Export index data."""
        data = {
            'exported_at': datetime.now().isoformat(),
            'config': {
                'project_root': str(self.config.project_root),
                'chunk_granularity': self.config.chunk_granularity
            },
            'statistics': self.get_code_metrics(),
            'file_states': {
                path: {
                    'content_hash': state.content_hash,
                    'indexed_at': state.indexed_at.isoformat(),
                    'chunk_count': state.chunk_count,
                    'symbol_count': state.symbol_count,
                    'git_commit': state.git_commit
                }
                for path, state in self.file_states.items()
            },
            'dependency_graph': dict(self._dependency_graph),
            'reverse_dependency_graph': dict(self._reverse_dependency_graph)
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported index to {output_path}")
        
        return data
    
    def clear_index(self, confirm: bool = False):
        """Clear all indexed data."""
        if not confirm:
            logger.warning("Use confirm=True to clear index")
            return
        
        # Clear vector store collections
        self.store.clear_collection(CollectionType.CODE)
        self.store.clear_collection(CollectionType.SYMBOLS)
        
        # Clear state
        self.file_states.clear()
        self._chunk_cache.clear()
        self._symbol_cache.clear()
        self._dependency_graph.clear()
        self._reverse_dependency_graph.clear()
        
        self._save_state()
        
        logger.info("Index cleared")
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get current index status."""
        return {
            'total_files_indexed': len(self.file_states),
            'total_chunks_cached': len(self._chunk_cache),
            'total_symbols_cached': len(self._symbol_cache),
            'dependency_graph_nodes': len(self._dependency_graph),
            'last_indexed': self.state.get('last_indexed'),
            'git_commit': self.git.get_current_commit() if self.git else None,
            'collection_stats': self.store.get_collection_stats()
        }
    
    def close(self):
        """Clean up resources."""
        self._save_state()
        self.store.close()
        logger.info("CodeIndexer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for code indexer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index code for semantic search")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--index", action="store_true", help="Index the codebase")
    parser.add_argument("--full", action="store_true", help="Force full reindexing")
    parser.add_argument("--incremental", action="store_true", help="Index only changed files")
    parser.add_argument("--search", type=str, help="Search query")
    parser.add_argument("--symbol", type=str, help="Search for specific symbol")
    parser.add_argument("--n-results", type=int, default=10, help="Number of search results")
    parser.add_argument("--metrics", action="store_true", help="Show code metrics")
    parser.add_argument("--duplicates", action="store_true", help="Find duplicate code")
    parser.add_argument("--dependencies", type=str, help="Show dependencies for symbol")
    parser.add_argument("--export", type=Path, help="Export index to file")
    parser.add_argument("--status", action="store_true", help="Show index status")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--clear", action="store_true", help="Clear index")
    
    args = parser.parse_args()
    
    config = IndexingConfig(project_root=args.project_root)
    indexer = CodeIndexer(config)
    
    if args.clear:
        indexer.clear_index(confirm=True)
        print("Index cleared")
        return
    
    if args.status:
        status = indexer.get_index_status()
        print(json.dumps(status, indent=2, default=str))
        return
    
    if args.index or args.full or args.incremental:
        if args.incremental:
            result = indexer.index_changed_files()
        else:
            result = indexer.index(full=args.full)
        
        print(f"\nIndexing completed:")
        print(f"  Status: {result.status.value}")
        print(f"  Files: {result.indexed_files} indexed, {result.skipped_files} skipped, {result.failed_files} failed")
        print(f"  Chunks: {result.total_chunks} total ({result.new_chunks} new, {result.updated_chunks} updated)")
        print(f"  Symbols: {result.total_symbols}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors[:5]:
                print(f"  - {error}")
        return
    
    if args.metrics:
        metrics = indexer.get_code_metrics()
        print(json.dumps(metrics, indent=2, default=str))
        return
    
    if args.duplicates:
        duplicates = indexer.find_duplicate_code()
        print(f"\nFound {len(duplicates)} duplicate pairs:\n")
        for i, (r1, r2) in enumerate(duplicates[:10], 1):
            print(f"{i}. {r1.source_file}:{r1.line_range[0]}-{r1.line_range[1]}")
            print(f"   {r2.source_file}:{r2.line_range[0]}-{r2.line_range[1]}")
            print()
        return
    
    if args.dependencies:
        deps = indexer.search_dependencies(args.dependencies)
        print(f"\nDependencies for '{args.dependencies}':")
        print(f"  Depends on ({len(deps['dependencies'])}): {', '.join(deps['dependencies'][:10])}")
        print(f"  Depended upon by ({len(deps['dependents'])}): {', '.join(deps['dependents'][:10])}")
        return
    
    if args.symbol:
        results = indexer.search_by_symbol(args.symbol)
        print(f"\nSearch results for symbol '{args.symbol}':\n")
        for i, r in enumerate(results[:args.n_results], 1):
            print(f"{i}. {r.source_file}:{r.line_range[0]}-{r.line_range[1]}")
            print(f"   Type: {r.chunk.chunk_type.value}")
            if r.symbol and r.symbol.signature:
                print(f"   Signature: {r.symbol.signature}")
            if r.chunk.docstring:
                print(f"   Docstring: {r.chunk.docstring[:100]}...")
            print()
        return
    
    if args.search:
        results = indexer.search(args.search, n_results=args.n_results)
        print(f"\nSearch results for '{args.search}':\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r.similarity:.3f}] {r.source_file}:{r.line_range[0]}-{r.line_range[1]}")
            print(f"   Type: {r.chunk.chunk_type.value}")
            if r.symbol:
                print(f"   Symbol: {r.symbol.name}")
            if r.matched_terms:
                print(f"   Matched: {', '.join(r.matched_terms)}")
            print(f"   Content: {r.chunk.content[:200]}...")
            print()
        return
    
    if args.export:
        indexer.export_index(args.export)
        print(f"Index exported to {args.export}")
        return
    
    if args.watch:
        # Ensure index exists
        if indexer.get_index_status()['total_files_indexed'] == 0:
            print("Building initial index...")
            indexer.index()
        
        print("Watching for changes (Ctrl+C to stop)...")
        indexer.watch_and_index()
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()