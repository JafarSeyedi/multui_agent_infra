#!/usr/bin/env python3
"""
File Utilities - File system operations and utilities.

Part of the Shared module (shared/file_utils.py)


This file_utils.py provides:

Path Utilities - Normalize, check subpaths, relative paths, common parent, sanitize filenames

File Information - Comprehensive file metadata, size formatting, MIME type detection

Text/Binary Detection - Automatic detection of text vs binary files

Encoding Detection - Automatic encoding detection using chardet

Checksum Computation - SHA256, MD5, and other hash algorithms

Safe File Operations - Atomic writes with backup, safe copy/move/delete

Directory Operations - Ensure directories, clean old files, find files by pattern

Temporary Files - Context managers for temp files and directories

Working Directory - Context manager to temporarily change directory

File Watching - Simple file watcher for change detection

Archive Operations - Create and extract ZIP, TAR archives

JSON Utilities - Read/write JSON and JSONL files

File Locking - Simple cross-platform file lock

Line Counting - Fast line counting for text files

CLI Interface - Command-line access to utilities

The file utilities provide a robust foundation for all file system operations throughout the framework.
"""

import os
import re
import sys
import json
import shutil
import hashlib
import tempfile
import fnmatch
import mimetypes
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator, BinaryIO, TextIO
from datetime import datetime
from contextlib import contextmanager
import chardet

from .logger import get_logger

logger = get_logger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

# File size constants
KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB

# Common text file extensions
TEXT_EXTENSIONS = {
    '.py', '.txt', '.md', '.rst', '.json', '.yaml', '.yml', '.toml',
    '.xml', '.html', '.htm', '.css', '.js', '.ts', '.jsx', '.tsx',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    '.c', '.h', '.cpp', '.hpp', '.cc', '.hh', '.java', '.go', '.rs',
    '.swift', '.kt', '.scala', '.rb', '.php', '.pl', '.pm', '.lua',
    '.sql', '.graphql', '.proto', '.csv', '.tsv', '.ini', '.cfg', '.conf',
    '.gitignore', '.dockerignore', '.env', '.editorconfig'
}

# Binary file extensions
BINARY_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.dll', '.dylib', '.exe', '.bin',
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
    '.db', '.sqlite', '.sqlite3',
    '.woff', '.woff2', '.ttf', '.eot', '.otf'
}

# Files to ignore by default
DEFAULT_IGNORE_PATTERNS = [
    '__pycache__', '*.pyc', '*.pyo', '.git', '.svn', '.hg',
    '.venv', 'venv', 'env', '.env', 'virtualenv',
    '.idea', '.vscode', '.DS_Store', 'Thumbs.db',
    'dist', 'build', '*.egg-info', '*.egg',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox',
    'node_modules', 'bower_components',
    'coverage', 'htmlcov', '.coverage',
    '*.log', '*.tmp', '*.temp', '*.swp', '*.swo'
]


# ============================================================
# PATH UTILITIES
# ============================================================

def normalize_path(path: Union[str, Path]) -> Path:
    """Convert to Path and resolve."""
    return Path(path).expanduser().resolve()


def is_subpath(path: Union[str, Path], parent: Union[str, Path]) -> bool:
    """Check if path is under parent directory."""
    try:
        path = normalize_path(path)
        parent = normalize_path(parent)
        return parent in path.parents or path == parent
    except ValueError:
        return False


def relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """Get relative path from base."""
    path = normalize_path(path)
    base = normalize_path(base)
    
    try:
        return path.relative_to(base)
    except ValueError:
        return path


def common_path(paths: List[Union[str, Path]]) -> Optional[Path]:
    """Find common parent path of multiple paths."""
    if not paths:
        return None
    
    paths = [normalize_path(p) for p in paths]
    common = paths[0]
    
    for path in paths[1:]:
        while not path.is_relative_to(common):
            common = common.parent
            if common == Path(common.root):
                return common
    
    return common


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize filename by removing invalid characters."""
    # Remove characters not allowed in filenames
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure non-empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def unique_path(path: Path) -> Path:
    """Generate unique path if file already exists."""
    if not path.exists():
        return path
    
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


# ============================================================
# FILE INFORMATION
# ============================================================

def get_file_info(path: Union[str, Path]) -> Dict[str, Any]:
    """Get comprehensive file information."""
    path = Path(path)
    
    if not path.exists():
        return {'exists': False}
    
    stat = path.stat()
    
    info = {
        'exists': True,
        'path': str(path),
        'name': path.name,
        'stem': path.stem,
        'suffix': path.suffix,
        'parent': str(path.parent),
        'is_file': path.is_file(),
        'is_dir': path.is_dir(),
        'is_symlink': path.is_symlink(),
        'size': stat.st_size,
        'size_human': format_size(stat.st_size),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'accessed': datetime.fromtimestamp(stat.st_atime),
        'permissions': stat.st_mode & 0o777,
        'owner': stat.st_uid if hasattr(stat, 'st_uid') else None,
        'group': stat.st_gid if hasattr(stat, 'st_gid') else None,
    }
    
    # MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    info['mime_type'] = mime_type
    
    # Checksum for files
    if path.is_file():
        info['checksum'] = compute_checksum(path)
        info['is_text'] = is_text_file(path)
        info['is_binary'] = is_binary_file(path)
        info['encoding'] = detect_encoding(path) if info['is_text'] else None
    
    # Line count for text files
    if info.get('is_text') and path.is_file():
        info['line_count'] = count_lines(path)
    
    return info


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    if size < KB:
        return f"{size} B"
    elif size < MB:
        return f"{size / KB:.1f} KB"
    elif size < GB:
        return f"{size / MB:.1f} MB"
    elif size < TB:
        return f"{size / GB:.1f} GB"
    else:
        return f"{size / TB:.1f} TB"


def is_text_file(path: Union[str, Path]) -> bool:
    """Check if file is a text file."""
    path = Path(path)
    
    # Check by extension first
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False
    
    # Try to read as text
    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False


def is_binary_file(path: Union[str, Path]) -> bool:
    """Check if file is a binary file."""
    return not is_text_file(path)


def detect_encoding(path: Union[str, Path]) -> str:
    """Detect file encoding."""
    with open(path, 'rb') as f:
        raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        return result.get('encoding', 'utf-8')


def count_lines(path: Union[str, Path]) -> int:
    """Count lines in a text file."""
    count = 0
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for _ in f:
            count += 1
    return count


def compute_checksum(path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Compute file checksum."""
    hash_func = hashlib.new(algorithm)
    
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


# ============================================================
# FILE OPERATIONS
# ============================================================

def safe_read(path: Union[str, Path], encoding: Optional[str] = None) -> Optional[str]:
    """Safely read file content."""
    path = Path(path)
    
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    
    try:
        if encoding is None and is_text_file(path):
            encoding = detect_encoding(path)
        
        with open(path, 'r', encoding=encoding or 'utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return None


def safe_read_lines(path: Union[str, Path], encoding: Optional[str] = None) -> List[str]:
    """Safely read file lines."""
    content = safe_read(path, encoding)
    if content is None:
        return []
    return content.splitlines()


def safe_write(path: Union[str, Path], content: str, encoding: str = 'utf-8',
               create_dirs: bool = True, backup: bool = False) -> bool:
    """Safely write content to file."""
    path = Path(path)
    
    try:
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        if backup and path.exists():
            backup_path = path.with_suffix(path.suffix + '.bak')
            shutil.copy2(path, backup_path)
        
        # Write to temp file first
        with tempfile.NamedTemporaryFile(
            mode='w', encoding=encoding, dir=path.parent, delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        # Atomic rename
        tmp_path.replace(path)
        return True
        
    except Exception as e:
        logger.error(f"Failed to write {path}: {e}")
        return False


def safe_write_lines(path: Union[str, Path], lines: List[str],
                     encoding: str = 'utf-8', **kwargs) -> bool:
    """Safely write lines to file."""
    return safe_write(path, '\n'.join(lines), encoding, **kwargs)


def safe_copy(src: Union[str, Path], dst: Union[str, Path],
              overwrite: bool = False) -> bool:
    """Safely copy file or directory."""
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        logger.warning(f"Source not found: {src}")
        return False
    
    try:
        if dst.exists():
            if not overwrite:
                dst = unique_path(dst)
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=overwrite)
        else:
            shutil.copy2(src, dst)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        return False


def safe_move(src: Union[str, Path], dst: Union[str, Path],
              overwrite: bool = False) -> bool:
    """Safely move file or directory."""
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        logger.warning(f"Source not found: {src}")
        return False
    
    try:
        if dst.exists() and overwrite:
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True
        
    except Exception as e:
        logger.error(f"Failed to move {src} to {dst}: {e}")
        return False


def safe_delete(path: Union[str, Path], missing_ok: bool = True) -> bool:
    """Safely delete file or directory."""
    path = Path(path)
    
    if not path.exists():
        if missing_ok:
            return True
        logger.warning(f"Path not found: {path}")
        return False
    
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        return False


# ============================================================
# DIRECTORY OPERATIONS
# ============================================================

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_dir(path: Union[str, Path], keep: int = 0) -> bool:
    """Clean directory contents."""
    path = Path(path)
    
    if not path.exists() or not path.is_dir():
        return False
    
    try:
        items = sorted(path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        
        for item in items[keep:]:
            safe_delete(item)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to clean directory {path}: {e}")
        return False


def find_files(directory: Union[str, Path], pattern: str = "*",
               recursive: bool = True, include_dirs: bool = False,
               exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """Find files matching pattern."""
    directory = Path(directory)
    exclude_patterns = exclude_patterns or []
    
    if not directory.exists():
        return []
    
    files = []
    
    if recursive:
        iterator = directory.rglob(pattern)
    else:
        iterator = directory.glob(pattern)
    
    for path in iterator:
        if not include_dirs and path.is_dir():
            continue
        
        # Check exclude patterns
        excluded = False
        for excl in exclude_patterns:
            if fnmatch.fnmatch(str(path), excl) or fnmatch.fnmatch(path.name, excl):
                excluded = True
                break
        
        if not excluded:
            files.append(path)
    
    return sorted(files)


def find_python_files(directory: Union[str, Path], recursive: bool = True,
                      exclude_tests: bool = False) -> List[Path]:
    """Find Python files in directory."""
    exclude_patterns = DEFAULT_IGNORE_PATTERNS.copy()
    
    if exclude_tests:
        exclude_patterns.extend(['test_*.py', '*_test.py', 'tests', 'test'])
    
    return find_files(directory, "*.py", recursive, exclude_patterns=exclude_patterns)


def get_directory_size(directory: Union[str, Path]) -> int:
    """Calculate total size of directory."""
    directory = Path(directory)
    total = 0
    
    if directory.exists():
        for path in directory.rglob('*'):
            if path.is_file():
                total += path.stat().st_size
    
    return total


def copy_directory_structure(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """Copy directory structure without files."""
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists() or not src.is_dir():
        return False
    
    try:
        for item in src.rglob('*'):
            if item.is_dir():
                target = dst / item.relative_to(src)
                target.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to copy directory structure: {e}")
        return False


# ============================================================
# TEMPORARY FILES
# ============================================================

@contextmanager
def temp_file(suffix: Optional[str] = None, prefix: Optional[str] = None,
              directory: Optional[Path] = None, delete: bool = True) -> Iterator[Path]:
    """Context manager for temporary file."""
    if directory:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
    
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=str(directory) if directory else None)
    path = Path(path)
    
    try:
        os.close(fd)
        yield path
    finally:
        if delete and path.exists():
            path.unlink()


@contextmanager
def temp_dir(suffix: Optional[str] = None, prefix: Optional[str] = None,
             directory: Optional[Path] = None, delete: bool = True) -> Iterator[Path]:
    """Context manager for temporary directory."""
    path = Path(tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(directory) if directory else None))
    
    try:
        yield path
    finally:
        if delete and path.exists():
            shutil.rmtree(path, ignore_errors=True)


@contextmanager
def working_directory(path: Union[str, Path]) -> Iterator[Path]:
    """Context manager to temporarily change working directory."""
    path = Path(path)
    old_cwd = Path.cwd()
    
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(old_cwd)


# ============================================================
# FILE WATCHING
# ============================================================

class FileWatcher:
    """Simple file watcher for detecting changes."""
    
    def __init__(self, paths: List[Union[str, Path]], recursive: bool = True):
        self.paths = [Path(p) for p in paths]
        self.recursive = recursive
        self._snapshots: Dict[Path, Dict[str, float]] = {}
        self.take_snapshot()
    
    def take_snapshot(self) -> Dict[Path, Dict[str, float]]:
        """Take snapshot of current file states."""
        snapshot = {}
        
        for path in self.paths:
            if path.is_file():
                snapshot[path] = {'mtime': path.stat().st_mtime}
            elif path.is_dir():
                for file_path in path.rglob('*') if self.recursive else path.glob('*'):
                    if file_path.is_file():
                        snapshot[file_path] = {'mtime': file_path.stat().st_mtime}
        
        self._snapshots = snapshot
        return snapshot
    
    def get_changes(self) -> Tuple[List[Path], List[Path], List[Path]]:
        """Get changed, added, and deleted files."""
        old_snapshot = self._snapshots
        new_snapshot = self.take_snapshot()
        
        old_files = set(old_snapshot.keys())
        new_files = set(new_snapshot.keys())
        
        added = list(new_files - old_files)
        deleted = list(old_files - new_files)
        changed = []
        
        for file_path in old_files & new_files:
            if old_snapshot[file_path]['mtime'] != new_snapshot[file_path]['mtime']:
                changed.append(file_path)
        
        return changed, added, deleted


# ============================================================
# ARCHIVE OPERATIONS
# ============================================================

def create_archive(source: Union[str, Path], destination: Union[str, Path],
                   format: str = 'zip') -> Optional[Path]:
    """Create archive from file or directory."""
    source = Path(source)
    destination = Path(destination)
    
    if not source.exists():
        logger.warning(f"Source not found: {source}")
        return None
    
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove extension if present
        base_name = str(destination).rsplit('.', 1)[0]
        root_dir = source.parent if source.is_file() else source
        base_dir = source.name if source.is_dir() else None
        
        archive_path = shutil.make_archive(
            base_name=base_name,
            format=format,
            root_dir=root_dir,
            base_dir=base_dir
        )
        
        return Path(archive_path)
        
    except Exception as e:
        logger.error(f"Failed to create archive: {e}")
        return None


def extract_archive(archive_path: Union[str, Path], destination: Union[str, Path]) -> bool:
    """Extract archive to destination."""
    archive_path = Path(archive_path)
    destination = Path(destination)
    
    if not archive_path.exists():
        logger.warning(f"Archive not found: {archive_path}")
        return False
    
    try:
        destination.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(archive_path), str(destination))
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract archive: {e}")
        return False


# ============================================================
# JSON UTILITIES
# ============================================================

def read_json(path: Union[str, Path], default: Any = None) -> Any:
    """Read and parse JSON file."""
    content = safe_read(path)
    if content is None:
        return default
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON {path}: {e}")
        return default


def write_json(path: Union[str, Path], data: Any, indent: int = 2,
               ensure_ascii: bool = False, **kwargs) -> bool:
    """Write data as JSON file."""
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, 
                            default=str, **kwargs)
        return safe_write(path, content)
    except Exception as e:
        logger.error(f"Failed to write JSON {path}: {e}")
        return False


def read_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read JSON Lines file."""
    lines = safe_read_lines(path)
    result = []
    
    for line in lines:
        line = line.strip()
        if line:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    return result


def write_jsonl(path: Union[str, Path], data: List[Dict[str, Any]], **kwargs) -> bool:
    """Write data as JSON Lines file."""
    lines = [json.dumps(item, default=str, **kwargs) for item in data]
    return safe_write_lines(path, lines)


# ============================================================
# LOCK FILE
# ============================================================

class FileLock:
    """Simple file-based lock."""
    
    def __init__(self, lock_file: Union[str, Path], timeout: float = 10.0):
        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self._locked = False
    
    def acquire(self) -> bool:
        """Acquire the lock."""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                # Try to create lock file
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                self._locked = True
                return True
            except FileExistsError:
                # Check if lock is stale
                try:
                    lock_time = self.lock_file.stat().st_mtime
                    if time.time() - lock_time > self.timeout:
                        # Stale lock, remove it
                        self.lock_file.unlink()
                        continue
                except FileNotFoundError:
                    continue
            
            time.sleep(0.1)
        
        logger.warning(f"Failed to acquire lock: {self.lock_file}")
        return False
    
    def release(self):
        """Release the lock."""
        if self._locked:
            try:
                self.lock_file.unlink()
            except FileNotFoundError:
                pass
            self._locked = False
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for file utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="File system utilities")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get file information')
    info_parser.add_argument('path', type=Path, help='File path')
    info_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Find command
    find_parser = subparsers.add_parser('find', help='Find files')
    find_parser.add_argument('directory', type=Path, help='Directory to search')
    find_parser.add_argument('--pattern', default='*', help='File pattern')
    find_parser.add_argument('--no-recursive', action='store_true', help='Disable recursive search')
    find_parser.add_argument('--exclude', nargs='*', help='Exclude patterns')
    
    # Checksum command
    checksum_parser = subparsers.add_parser('checksum', help='Compute file checksum')
    checksum_parser.add_argument('path', type=Path, help='File path')
    checksum_parser.add_argument('--algorithm', default='sha256', help='Hash algorithm')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean directory')
    clean_parser.add_argument('directory', type=Path, help='Directory to clean')
    clean_parser.add_argument('--keep', type=int, default=0, help='Number of files to keep')
    
    args = parser.parse_args()
    
    if args.command == 'info':
        info = get_file_info(args.path)
        if args.json:
            print(json.dumps(info, indent=2, default=str))
        else:
            for key, value in info.items():
                print(f"{key}: {value}")
    
    elif args.command == 'find':
        files = find_files(
            args.directory,
            pattern=args.pattern,
            recursive=not args.no_recursive,
            exclude_patterns=args.exclude
        )
        for f in files:
            print(f)
    
    elif args.command == 'checksum':
        checksum = compute_checksum(args.path, args.algorithm)
        print(f"{args.algorithm}: {checksum}")
    
    elif args.command == 'clean':
        if clean_dir(args.directory, args.keep):
            print(f"Cleaned {args.directory}")
        else:
            print(f"Failed to clean {args.directory}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()