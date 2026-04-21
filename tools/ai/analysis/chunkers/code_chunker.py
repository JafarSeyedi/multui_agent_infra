#!/usr/bin/env python3
"""
Code Chunker - AI Development Framework
Splits source code into semantic chunks for embedding and analysis.

Part of the Level 2 Analysis tools (chunkers/code_chunker.py)

This code_chunker.py provides:

1. AST-Based Semantic Chunking - Uses Python's AST for intelligent code splitting
2. Multiple Granularity Levels - Fine (functions), medium (classes), coarse (modules)
3. Multi-Language Support - Python, Markdown, JSON, with extensible architecture
4. Hierarchy Preservation - Maintains parent-child relationships between chunks
5. Complexity Calculation - Computes cyclomatic complexity for functions
6. Dependency Extraction - Identifies imports and symbol dependencies
7. Configurable Chunk Sizes - Min/max lines with merge/split options
8. Change Detection - Only rechunks modified files
9. Embedding-Ready Export - Formats chunks for direct embedding
10. Rich Metadata - Captures signatures, docstrings, decorators, and more

The chunker integrates with the ProjectScanner for symbol-based chunking and produces output ready for the OllamaEncoder.
"""

import ast
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Iterator, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.file_utils import FileUtils
from ...level_2_analysis.scanners.project_scanner import ProjectScanner, CodeSymbol

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ChunkType(str, Enum):
    """Type of code chunk."""
    MODULE = "module"               # Entire module/file
    CLASS = "class"                 # Class definition
    METHOD = "method"               # Method definition
    FUNCTION = "function"           # Function definition
    IMPORT_BLOCK = "import_block"   # Import statements
    DECORATOR = "decorator"         # Decorator definition
    CONSTANT = "constant"           # Constant/variable definition
    DOCSTRING = "docstring"         # Module/class docstring
    COMMENT_BLOCK = "comment_block" # Block of related comments
    NESTED_CLASS = "nested_class"   # Class inside another class
    PROPERTY = "property"           # Property getter/setter
    ASYNC_FUNCTION = "async_function" # Async function
    LAMBDA = "lambda"               # Lambda expression
    TYPE_ALIAS = "type_alias"       # Type alias definition
    ENUM = "enum"                   # Enum definition
    DATACLASS = "dataclass"         # Dataclass definition


class ChunkGranularity(str, Enum):
    """Granularity level for chunking."""
    FINE = "fine"           # Individual functions/methods
    MEDIUM = "medium"       # Classes with their methods
    COARSE = "coarse"       # Entire modules
    ADAPTIVE = "adaptive"   # Based on complexity


class Language(str, Enum):
    """Programming language."""
    PYTHON = "python"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class CodeChunk:
    """A semantic chunk of code."""
    id: str
    chunk_type: ChunkType
    language: Language
    content: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: Optional[str] = None
    parent_symbol: Optional[str] = None
    docstring: Optional[str] = None
    signature: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity: int = 0
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)  # Child chunk IDs
    parent_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        if not self.id:
            self.id = f"{self.chunk_type.value}_{self.content_hash[:16]}"


@dataclass
class ChunkingResult:
    """Result of chunking operation."""
    chunks: List[CodeChunk]
    total_chunks: int
    total_lines: int
    avg_chunk_size: float
    chunk_types_distribution: Dict[ChunkType, int]
    file_path: str
    chunked_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkingConfig:
    """Configuration for chunking."""
    granularity: ChunkGranularity = ChunkGranularity.MEDIUM
    min_chunk_lines: int = 3
    max_chunk_lines: int = 200
    include_imports: bool = True
    include_docstrings: bool = True
    include_comments: bool = False
    include_decorators: bool = True
    merge_small_chunks: bool = True
    split_large_chunks: bool = True
    preserve_hierarchy: bool = True
    compute_complexity: bool = True
    extract_dependencies: bool = True


# ============================================================
# AST VISITORS
# ============================================================

class CodeChunkVisitor(ast.NodeVisitor):
    """AST visitor that extracts code chunks."""
    
    def __init__(self, 
                 source_code: str,
                 file_path: str,
                 config: ChunkingConfig,
                 lines: List[str]):
        self.source_code = source_code
        self.file_path = file_path
        self.config = config
        self.lines = lines
        self.chunks: List[CodeChunk] = []
        self.current_class: Optional[str] = None
        self.imports: List[str] = []
        self.module_docstring: Optional[str] = None
        self._chunk_stack: List[str] = []  # For hierarchy
        
    def visit_Module(self, node: ast.Module) -> None:
        """Visit module node."""
        # Extract module docstring
        self.module_docstring = ast.get_docstring(node)
        
        # Extract imports first
        for child in node.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                self.visit(child)
        
        # Create module-level chunk if coarse granularity
        if self.config.granularity == ChunkGranularity.COARSE:
            chunk = self._create_module_chunk(node)
            self.chunks.append(chunk)
            self._chunk_stack.append(chunk.id)
        
        # Visit children
        for child in node.body:
            if not isinstance(child, (ast.Import, ast.ImportFrom)):
                self.visit(child)
        
        if self._chunk_stack:
            self._chunk_stack.pop()
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import node."""
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import node."""
        if node.module:
            self.imports.append(node.module)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        prev_class = self.current_class
        self.current_class = node.name
        
        # Determine chunk type
        chunk_type = self._get_class_chunk_type(node)
        
        # Create class chunk
        chunk = self._create_chunk_from_node(
            node=node,
            chunk_type=chunk_type,
            symbol_name=node.name,
            docstring=ast.get_docstring(node)
        )
        
        # Add decorators
        chunk.decorators = self._extract_decorators(node)
        
        # Add base classes as dependencies
        for base in node.bases:
            if isinstance(base, ast.Name):
                chunk.dependencies.append(base.id)
            elif isinstance(base, ast.Attribute):
                chunk.dependencies.append(self._get_attribute_name(base))
        
        self.chunks.append(chunk)
        
        # Update hierarchy
        if self._chunk_stack:
            parent_id = self._chunk_stack[-1]
            chunk.parent_id = parent_id
            for c in self.chunks:
                if c.id == parent_id:
                    c.children.append(chunk.id)
                    break
        
        self._chunk_stack.append(chunk.id)
        
        # Visit class body
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.visit(child)
            elif self.config.include_comments:
                # Could extract class-level comments
                pass
        
        self._chunk_stack.pop()
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool) -> None:
        """Common function visitor."""
        # Determine if this is a method
        is_method = self.current_class is not None
        
        # Determine chunk type
        if is_method:
            if node.name.startswith('__') and node.name.endswith('__'):
                chunk_type = ChunkType.METHOD  # Magic method
            elif any(d.id == 'property' or (isinstance(d, ast.Attribute) and d.attr == 'setter') 
                    for d in node.decorator_list):
                chunk_type = ChunkType.PROPERTY
            else:
                chunk_type = ChunkType.METHOD
        else:
            chunk_type = ChunkType.ASYNC_FUNCTION if is_async else ChunkType.FUNCTION
        
        # Create function chunk
        chunk = self._create_chunk_from_node(
            node=node,
            chunk_type=chunk_type,
            symbol_name=f"{self.current_class}.{node.name}" if is_method else node.name,
            docstring=ast.get_docstring(node)
        )
        
        # Add signature
        chunk.signature = self._get_function_signature(node)
        
        # Add decorators
        chunk.decorators = self._extract_decorators(node)
        
        # Add imports
        chunk.imports = self.imports.copy()
        
        # Compute complexity if enabled
        if self.config.compute_complexity:
            chunk.complexity = self._compute_cyclomatic_complexity(node)
        
        self.chunks.append(chunk)
        
        # Update hierarchy
        if self._chunk_stack:
            parent_id = self._chunk_stack[-1]
            chunk.parent_id = parent_id
            for c in self.chunks:
                if c.id == parent_id:
                    c.children.append(chunk.id)
                    break
        
        # Don't visit function body for chunking (keeps chunks focused)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment (for constants)."""
        # Only create constant chunks at module level
        if not self.current_class and not self._chunk_stack:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    chunk = self._create_chunk_from_node(
                        node=node,
                        chunk_type=ChunkType.CONSTANT,
                        symbol_name=target.id
                    )
                    self.chunks.append(chunk)
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment (for type aliases)."""
        if not self.current_class and not self._chunk_stack:
            if isinstance(node.target, ast.Name):
                chunk = self._create_chunk_from_node(
                    node=node,
                    chunk_type=ChunkType.TYPE_ALIAS,
                    symbol_name=node.target.id
                )
                self.chunks.append(chunk)
    
    def _get_class_chunk_type(self, node: ast.ClassDef) -> ChunkType:
        """Determine class chunk type based on decorators."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'dataclass':
                    return ChunkType.DATACLASS
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == 'dataclass':
                    return ChunkType.DATACLASS
        
        # Check if it's an enum
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Enum':
                return ChunkType.ENUM
            elif isinstance(base, ast.Attribute) and base.attr == 'Enum':
                return ChunkType.ENUM
        
        return ChunkType.CLASS
    
    def _create_module_chunk(self, node: ast.Module) -> CodeChunk:
        """Create a module-level chunk."""
        return CodeChunk(
            chunk_type=ChunkType.MODULE,
            language=Language.PYTHON,
            content=self.source_code,
            file_path=self.file_path,
            start_line=1,
            end_line=len(self.lines),
            docstring=self.module_docstring,
            imports=self.imports.copy(),
            complexity=self._compute_module_complexity(node),
            metadata={
                'total_lines': len(self.lines),
                'has_docstring': self.module_docstring is not None
            }
        )
    
    def _create_chunk_from_node(self, 
                                 node: ast.AST,
                                 chunk_type: ChunkType,
                                 symbol_name: str,
                                 docstring: Optional[str] = None) -> CodeChunk:
        """Create a chunk from an AST node."""
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Extract content
        content_lines = self.lines[start_line - 1:end_line]
        content = '\n'.join(content_lines)
        
        # Check size limits
        if self.config.split_large_chunks and len(content_lines) > self.config.max_chunk_lines:
            # Could split further if needed
            pass
        
        return CodeChunk(
            chunk_type=chunk_type,
            language=Language.PYTHON,
            content=content,
            file_path=self.file_path,
            start_line=start_line,
            end_line=end_line,
            symbol_name=symbol_name,
            docstring=docstring,
            imports=self.imports.copy() if self.config.include_imports else [],
            metadata={
                'node_type': type(node).__name__,
                'line_count': end_line - start_line + 1
            }
        )
    
    def _extract_decorators(self, node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extract decorator names."""
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(self._get_attribute_name(dec))
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(self._get_attribute_name(dec.func))
        return decorators
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
    
    def _get_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Get function signature as string."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"
        
        return f"def {node.name}({', '.join(args)}){returns}"
    
    def _compute_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Compute cyclomatic complexity of a function."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.IfExp):
                complexity += 1
        
        return complexity
    
    def _compute_module_complexity(self, node: ast.Module) -> int:
        """Compute overall module complexity."""
        total = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += self._compute_cyclomatic_complexity(child)
        return total


# ============================================================
# MAIN CHUNKER CLASS
# ============================================================

class CodeChunker:
    """
    Intelligent code chunker for embedding and analysis.
    
    Features:
    - AST-based semantic chunking
    - Multiple granularity levels
    - Hierarchy preservation
    - Complexity calculation
    - Dependency extraction
    - Configurable chunk sizes
    - Support for multiple languages
    - Chunk relationship tracking
    - Incremental chunking (only changed files)
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        self.file_hashes: Dict[str, str] = {}
        
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def chunk_file(self, file_path: Path) -> ChunkingResult:
        """Chunk a single file."""
        logger.info(f"Chunking file: {file_path}")
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return self._empty_result(str(file_path))
        
        # Detect language
        language = self._detect_language(file_path)
        
        # Chunk based on language
        if language == Language.PYTHON:
            chunks = self._chunk_python(source_code, str(file_path))
        elif language == Language.MARKDOWN:
            chunks = self._chunk_markdown(source_code, str(file_path))
        elif language == Language.JSON:
            chunks = self._chunk_json(source_code, str(file_path))
        else:
            chunks = self._chunk_generic(source_code, str(file_path))
        
        # Post-process chunks
        chunks = self._post_process_chunks(chunks)
        
        # Calculate statistics
        total_lines = len(source_code.split('\n'))
        avg_chunk_size = sum(c.end_line - c.start_line + 1 for c in chunks) / max(len(chunks), 1)
        
        # Distribution by type
        type_distribution = defaultdict(int)
        for chunk in chunks:
            type_distribution[chunk.chunk_type] += 1
        
        result = ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            total_lines=total_lines,
            avg_chunk_size=avg_chunk_size,
            chunk_types_distribution=dict(type_distribution),
            file_path=str(file_path)
        )
        
        logger.info(f"Created {len(chunks)} chunks from {file_path}")
        return result
    
    def chunk_directory(self, 
                        directory: Path,
                        recursive: bool = True,
                        patterns: List[str] = None) -> List[ChunkingResult]:
        """Chunk all files in a directory."""
        results = []
        patterns = patterns or ["*.py", "*.md", "*.json", "*.yaml"]
        
        for pattern in patterns:
            glob_func = directory.rglob if recursive else directory.glob
            for file_path in glob_func(pattern):
                if self._should_skip(file_path):
                    continue
                
                # Check if file has changed
                if not self._has_changed(file_path):
                    logger.debug(f"Skipping unchanged file: {file_path}")
                    continue
                
                result = self.chunk_file(file_path)
                results.append(result)
        
        logger.info(f"Chunked {len(results)} files")
        return results
    
    def chunk_symbols(self, symbols: List[CodeSymbol]) -> List[CodeChunk]:
        """Create chunks from pre-extracted symbols."""
        chunks = []
        
        for symbol in symbols:
            chunk = CodeChunk(
                chunk_type=self._symbol_to_chunk_type(symbol.symbol_type),
                language=Language.PYTHON,
                content=self._symbol_to_content(symbol),
                file_path=symbol.file_path,
                start_line=symbol.line_start,
                end_line=symbol.line_end,
                symbol_name=symbol.name,
                docstring=symbol.docstring,
                signature=symbol.signature,
                decorators=symbol.decorators,
                dependencies=symbol.dependencies,
                complexity=symbol.complexity,
                metadata={
                    'used_by': symbol.used_by,
                    'symbol_type': symbol.symbol_type
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def merge_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Merge small chunks together."""
        if not self.config.merge_small_chunks:
            return chunks
        
        merged = []
        current_group = []
        
        for chunk in sorted(chunks, key=lambda c: c.start_line):
            chunk_size = chunk.end_line - chunk.start_line + 1
            
            if chunk_size < self.config.min_chunk_lines:
                current_group.append(chunk)
            else:
                if current_group:
                    merged.append(self._merge_chunk_group(current_group))
                    current_group = []
                merged.append(chunk)
        
        if current_group:
            merged.append(self._merge_chunk_group(current_group))
        
        return merged
    
    def split_large_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Split chunks that are too large."""
        if not self.config.split_large_chunks:
            return chunks
        
        result = []
        
        for chunk in chunks:
            chunk_size = chunk.end_line - chunk.start_line + 1
            
            if chunk_size > self.config.max_chunk_lines:
                split = self._split_chunk(chunk)
                result.extend(split)
            else:
                result.append(chunk)
        
        return result
    
    # ============================================================
    # LANGUAGE-SPECIFIC CHUNKING
    # ============================================================
    
    def _chunk_python(self, source_code: str, file_path: str) -> List[CodeChunk]:
        """Chunk Python source code."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return self._chunk_generic(source_code, file_path)
        
        lines = source_code.split('\n')
        visitor = CodeChunkVisitor(source_code, file_path, self.config, lines)
        visitor.visit(tree)
        
        return visitor.chunks
    
    def _chunk_markdown(self, source_code: str, file_path: str) -> List[CodeChunk]:
        """Chunk Markdown document."""
        chunks = []
        lines = source_code.split('\n')
        
        # Parse sections
        current_section = []
        current_heading = ""
        section_start = 1
        
        for i, line in enumerate(lines, 1):
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    chunk = self._create_markdown_chunk(
                        content='\n'.join(current_section),
                        file_path=file_path,
                        start_line=section_start,
                        end_line=i - 1,
                        heading=current_heading
                    )
                    chunks.append(chunk)
                
                # Start new section
                current_heading = line
                current_section = [line]
                section_start = i
            else:
                current_section.append(line)
        
        # Save final section
        if current_section:
            chunk = self._create_markdown_chunk(
                content='\n'.join(current_section),
                file_path=file_path,
                start_line=section_start,
                end_line=len(lines),
                heading=current_heading
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_json(self, source_code: str, file_path: str) -> List[CodeChunk]:
        """Chunk JSON file."""
        try:
            data = json.loads(source_code)
        except json.JSONDecodeError:
            return self._chunk_generic(source_code, file_path)
        
        chunks = []
        
        # Create chunks for top-level keys if it's a dict
        if isinstance(data, dict):
            for key, value in data.items():
                chunk_content = json.dumps({key: value}, indent=2)
                chunk = CodeChunk(
                    chunk_type=ChunkType.CONSTANT,
                    language=Language.JSON,
                    content=chunk_content,
                    file_path=file_path,
                    start_line=0,  # Line numbers not precise for JSON
                    end_line=0,
                    symbol_name=key,
                    metadata={'json_key': key}
                )
                chunks.append(chunk)
        else:
            # Single chunk for array/primitive
            chunk = CodeChunk(
                chunk_type=ChunkType.MODULE,
                language=Language.JSON,
                content=source_code,
                file_path=file_path,
                start_line=1,
                end_line=len(source_code.split('\n'))
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_generic(self, source_code: str, file_path: str) -> List[CodeChunk]:
        """Generic chunking for unknown formats."""
        lines = source_code.split('\n')
        chunks = []
        
        # Simple line-based chunking
        chunk_size = self.config.max_chunk_lines
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk = CodeChunk(
                chunk_type=ChunkType.MODULE,
                language=Language.UNKNOWN,
                content='\n'.join(chunk_lines),
                file_path=file_path,
                start_line=i + 1,
                end_line=min(i + chunk_size, len(lines)),
                metadata={'chunk_index': i // chunk_size}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_markdown_chunk(self, 
                                content: str,
                                file_path: str,
                                start_line: int,
                                end_line: int,
                                heading: str) -> CodeChunk:
        """Create a Markdown chunk."""
        return CodeChunk(
            chunk_type=ChunkType.DOCSTRING,
            language=Language.MARKDOWN,
            content=content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            symbol_name=heading.strip('# ')[:50],
            metadata={
                'heading': heading,
                'heading_level': heading.count('#')
            }
        )
    
    # ============================================================
    # POST-PROCESSING
    # ============================================================
    
    def _post_process_chunks(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Apply post-processing to chunks."""
        # Merge small chunks
        chunks = self.merge_chunks(chunks)
        
        # Split large chunks
        chunks = self.split_large_chunks(chunks)
        
        # Add hierarchy relationships
        if self.config.preserve_hierarchy:
            chunks = self._build_hierarchy(chunks)
        
        # Extract dependencies if enabled
        if self.config.extract_dependencies:
            chunks = self._extract_chunk_dependencies(chunks)
        
        return chunks
    
    def _build_hierarchy(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Build parent-child relationships between chunks."""
        # Sort by start line
        sorted_chunks = sorted(chunks, key=lambda c: (c.start_line, -c.end_line))
        
        # Build hierarchy based on containment
        for i, chunk in enumerate(sorted_chunks):
            for j in range(i + 1, len(sorted_chunks)):
                other = sorted_chunks[j]
                
                # Check if other is contained within chunk
                if (other.start_line >= chunk.start_line and 
                    other.end_line <= chunk.end_line and
                    other.chunk_type != chunk.chunk_type):
                    
                    # Check if not already parented to something more specific
                    if not other.parent_id or (
                        other.parent_id == chunk.parent_id and
                        chunk.end_line - chunk.start_line < 
                        self._get_chunk_by_id(chunks, other.parent_id).end_line - 
                        self._get_chunk_by_id(chunks, other.parent_id).start_line
                    ):
                        other.parent_id = chunk.id
                        if other.id not in chunk.children:
                            chunk.children.append(other.id)
        
        return sorted_chunks
    
    def _get_chunk_by_id(self, chunks: List[CodeChunk], chunk_id: str) -> Optional[CodeChunk]:
        """Get chunk by ID."""
        for chunk in chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def _extract_chunk_dependencies(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Extract dependencies between chunks."""
        symbol_map = {c.symbol_name: c.id for c in chunks if c.symbol_name}
        
        for chunk in chunks:
            # Parse imports for dependencies
            for imp in chunk.imports:
                if imp in symbol_map:
                    if symbol_map[imp] not in chunk.dependencies:
                        chunk.dependencies.append(symbol_map[imp])
        
        return chunks
    
    def _merge_chunk_group(self, chunks: List[CodeChunk]) -> CodeChunk:
        """Merge a group of chunks into one."""
        if not chunks:
            raise ValueError("Cannot merge empty chunk group")
        
        first = chunks[0]
        last = chunks[-1]
        
        # Combine content
        content_parts = []
        for chunk in chunks:
            content_parts.append(chunk.content)
        
        merged_content = '\n\n'.join(content_parts)
        
        # Merge metadata
        merged_metadata = {
            'merged_from': [c.id for c in chunks],
            'original_types': [c.chunk_type.value for c in chunks]
        }
        
        return CodeChunk(
            chunk_type=ChunkType.MODULE,  # Default for merged chunks
            language=first.language,
            content=merged_content,
            file_path=first.file_path,
            start_line=first.start_line,
            end_line=last.end_line,
            imports=list(set().union(*[c.imports for c in chunks])),
            metadata=merged_metadata
        )
    
    def _split_chunk(self, chunk: CodeChunk) -> List[CodeChunk]:
        """Split a large chunk into smaller ones."""
        lines = chunk.content.split('\n')
        splits = []
        
        chunk_size = self.config.max_chunk_lines
        
        for i in range(0, len(lines), chunk_size):
            split_lines = lines[i:i + chunk_size]
            split_content = '\n'.join(split_lines)
            
            split_chunk = CodeChunk(
                chunk_type=chunk.chunk_type,
                language=chunk.language,
                content=split_content,
                file_path=chunk.file_path,
                start_line=chunk.start_line + i,
                end_line=min(chunk.start_line + i + chunk_size - 1, chunk.end_line),
                symbol_name=f"{chunk.symbol_name}_part_{i // chunk_size}" if chunk.symbol_name else None,
                imports=chunk.imports,
                metadata={
                    **chunk.metadata,
                    'split_from': chunk.id,
                    'split_index': i // chunk_size,
                    'total_splits': (len(lines) + chunk_size - 1) // chunk_size
                }
            )
            splits.append(split_chunk)
        
        return splits
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _detect_language(self, file_path: Path) -> Language:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            return Language.PYTHON
        elif ext in ('.md', '.markdown'):
            return Language.MARKDOWN
        elif ext == '.json':
            return Language.JSON
        elif ext in ('.yaml', '.yml'):
            return Language.YAML
        else:
            return Language.UNKNOWN
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', 'dist', 'build', '.pytest_cache',
            '.mypy_cache', '.ruff_cache', '.ai_state',
            '*.pyc', '*.pyo', '*.so', '*.dll'
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
    
    def _symbol_to_chunk_type(self, symbol_type: str) -> ChunkType:
        """Convert symbol type to chunk type."""
        mapping = {
            'class': ChunkType.CLASS,
            'function': ChunkType.FUNCTION,
            'method': ChunkType.METHOD,
            'module': ChunkType.MODULE,
            'variable': ChunkType.CONSTANT,
        }
        return mapping.get(symbol_type, ChunkType.FUNCTION)
    
    def _symbol_to_content(self, symbol: CodeSymbol) -> str:
        """Reconstruct symbol content for chunking."""
        parts = []
        
        if symbol.docstring:
            parts.append(f'"""{symbol.docstring}"""')
        
        if symbol.signature:
            parts.append(symbol.signature)
        
        return '\n'.join(parts)
    
    def _empty_result(self, file_path: str) -> ChunkingResult:
        """Create empty chunking result."""
        return ChunkingResult(
            chunks=[],
            total_chunks=0,
            total_lines=0,
            avg_chunk_size=0,
            chunk_types_distribution={},
            file_path=file_path
        )
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_chunks_json(self, result: ChunkingResult, output_path: Optional[Path] = None) -> str:
        """Export chunks as JSON."""
        data = {
            'file_path': result.file_path,
            'chunked_at': result.chunked_at.isoformat(),
            'total_chunks': result.total_chunks,
            'total_lines': result.total_lines,
            'avg_chunk_size': result.avg_chunk_size,
            'chunk_types_distribution': {k.value: v for k, v in result.chunk_types_distribution.items()},
            'chunks': [
                {
                    'id': c.id,
                    'type': c.chunk_type.value,
                    'language': c.language.value,
                    'content': c.content,
                    'start_line': c.start_line,
                    'end_line': c.end_line,
                    'symbol_name': c.symbol_name,
                    'parent_symbol': c.parent_symbol,
                    'docstring': c.docstring,
                    'signature': c.signature,
                    'decorators': c.decorators,
                    'imports': c.imports,
                    'dependencies': c.dependencies,
                    'complexity': c.complexity,
                    'content_hash': c.content_hash,
                    'children': c.children,
                    'parent_id': c.parent_id,
                    'metadata': c.metadata
                }
                for c in result.chunks
            ]
        }
        
        json_str = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(json_str)
        
        return json_str
    
    def export_chunks_for_embedding(self, chunks: List[CodeChunk]) -> List[Dict[str, Any]]:
        """Export chunks in format ready for embedding."""
        return [
            {
                'id': c.id,
                'text': self._format_chunk_for_embedding(c),
                'metadata': {
                    'type': c.chunk_type.value,
                    'language': c.language.value,
                    'file_path': c.file_path,
                    'symbol_name': c.symbol_name,
                    'complexity': c.complexity,
                    'dependencies': c.dependencies,
                    **c.metadata
                }
            }
            for c in chunks
        ]
    
    def _format_chunk_for_embedding(self, chunk: CodeChunk) -> str:
        """Format chunk content for optimal embedding."""
        parts = []
        
        # Add context
        parts.append(f"Type: {chunk.chunk_type.value}")
        
        if chunk.symbol_name:
            parts.append(f"Name: {chunk.symbol_name}")
        
        if chunk.signature:
            parts.append(f"Signature: {chunk.signature}")
        
        if chunk.docstring:
            parts.append(f"Documentation: {chunk.docstring}")
        
        if chunk.decorators:
            parts.append(f"Decorators: {', '.join(chunk.decorators)}")
        
        if chunk.imports:
            parts.append(f"Imports: {', '.join(chunk.imports[:10])}")
        
        # Add the actual code
        parts.append(f"Code:\n{chunk.content}")
        
        return '\n'.join(parts)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for code chunker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chunk code files for embedding and analysis")
    parser.add_argument("path", type=Path, help="File or directory to chunk")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--granularity", choices=["fine", "medium", "coarse", "adaptive"],
                       default="medium", help="Chunking granularity")
    parser.add_argument("--min-lines", type=int, default=3, help="Minimum chunk size in lines")
    parser.add_argument("--max-lines", type=int, default=200, help="Maximum chunk size in lines")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process directories recursively")
    parser.add_argument("--embedding-format", action="store_true", help="Output in embedding-ready format")
    parser.add_argument("--no-merge", action="store_true", help="Disable merging small chunks")
    parser.add_argument("--no-split", action="store_true", help="Disable splitting large chunks")
    
    args = parser.parse_args()
    
    config = ChunkingConfig(
        granularity=ChunkGranularity(args.granularity),
        min_chunk_lines=args.min_lines,
        max_chunk_lines=args.max_lines,
        merge_small_chunks=not args.no_merge,
        split_large_chunks=not args.no_split
    )
    
    chunker = CodeChunker(config)
    
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
                    'total_chunks': r.total_chunks,
                    'total_lines': r.total_lines,
                    'avg_chunk_size': r.avg_chunk_size,
                    'chunk_types': {k.value: v for k, v in r.chunk_types_distribution.items()}
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