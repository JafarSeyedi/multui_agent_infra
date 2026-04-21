#!/usr/bin/env python3
"""
Git Utilities - Git operations and repository management.

Part of the Shared module (shared/git_utils.py)

This git_utils.py provides:

Repository Information - Check if repo, get config, user info
Status and Diff - Porcelain status parsing, file diffs
Commit Management - History, details, statistics, conventional commits
Branch Management - List, create, delete, checkout, merge, rebase
Remote Operations - Fetch, pull, push, remote management
Tag Management - Create, list, delete annotated and lightweight tags
Stash Management - Push, pop, apply, drop, list stashes
File Operations - Stage, unstage, commit, reset, clean
Change Detection - Get changed files, file history
Context Managers - Temporary branches and commits
Conventional Commits - Support for conventional commit format
CLI Interface - Command-line access to git operations

The git utilities provide seamless integration with Git for version control operations throughout the framework.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager

from .logger import get_logger
from .file_utils import safe_read, safe_write, working_directory

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class GitStatus(str, Enum):
    """Git file status."""
    UNMODIFIED = "unmodified"
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    UNTRACKED = "untracked"
    IGNORED = "ignored"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class ChangeType(str, Enum):
    """Type of change."""
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "?"
    IGNORED = "!"
    CONFLICT = "U"


class MergeStrategy(str, Enum):
    """Merge strategy."""
    MERGE = "merge"
    REBASE = "rebase"
    SQUASH = "squash"
    FAST_FORWARD = "fast-forward"


class CommitType(str, Enum):
    """Conventional commit type."""
    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    BUILD = "build"
    CI = "ci"
    CHORE = "chore"
    REVERT = "revert"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class GitFileStatus:
    """Status of a single file."""
    file_path: str
    status: GitStatus
    change_type: ChangeType
    staged: bool = False
    old_path: Optional[str] = None  # For renamed files
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitCommit:
    """Git commit information."""
    hash: str
    short_hash: str
    author: str
    author_email: str
    committer: str
    committer_email: str
    message: str
    date: datetime
    parents: List[str] = field(default_factory=list)
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitBranch:
    """Git branch information."""
    name: str
    is_current: bool = False
    is_remote: bool = False
    remote_name: Optional[str] = None
    upstream: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    last_commit: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitTag:
    """Git tag information."""
    name: str
    commit_hash: str
    message: Optional[str] = None
    tagger: Optional[str] = None
    date: Optional[datetime] = None
    is_annotated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitRemote:
    """Git remote information."""
    name: str
    url: str
    fetch_url: Optional[str] = None
    push_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitDiff:
    """Git diff information."""
    file_path: str
    old_path: Optional[str] = None
    change_type: ChangeType = ChangeType.MODIFIED
    diff_content: str = ""
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    insertions: int = 0
    deletions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitStash:
    """Git stash information."""
    index: int
    branch: str
    message: str
    date: datetime
    commit_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# GIT UTILITIES
# ============================================================

class GitUtils:
    """
    Git operations and repository management.
    
    Features:
    - Repository status and information
    - Commit history and details
    - Branch management
    - Tag management
    - Remote operations
    - Stash management
    - Diff generation
    - File staging and committing
    - Merge and rebase operations
    - Conventional commits
    - Git hooks support
    """
    
    def __init__(self, repo_path: Union[str, Path] = Path.cwd()):
        """Initialize Git utilities."""
        self.repo_path = Path(repo_path)
        self._git_dir: Optional[Path] = None
        self._is_repo: Optional[bool] = None
        
        logger.debug(f"GitUtils initialized for {self.repo_path}")
    
    # ============================================================
    # REPOSITORY INFORMATION
    # ============================================================
    
    @property
    def is_repo(self) -> bool:
        """Check if directory is a git repository."""
        if self._is_repo is None:
            try:
                self._run_git("rev-parse", "--git-dir", check=True)
                self._is_repo = True
            except subprocess.CalledProcessError:
                self._is_repo = False
        return self._is_repo
    
    @property
    def git_dir(self) -> Optional[Path]:
        """Get .git directory path."""
        if not self.is_repo:
            return None
        
        if self._git_dir is None:
            result = self._run_git("rev-parse", "--git-dir", check=True)
            git_dir = Path(result.strip())
            if not git_dir.is_absolute():
                git_dir = self.repo_path / git_dir
            self._git_dir = git_dir.resolve()
        
        return self._git_dir
    
    def init(self, bare: bool = False, initial_branch: str = "main") -> bool:
        """Initialize a new git repository."""
        try:
            cmd = ["init"]
            if bare:
                cmd.append("--bare")
            if initial_branch:
                cmd.extend(["--initial-branch", initial_branch])
            
            self._run_git(*cmd, check=True)
            self._is_repo = True
            self._git_dir = None
            logger.info(f"Initialized git repository at {self.repo_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to init repository: {e}")
            return False
    
    def get_config(self, key: str, scope: str = "local") -> Optional[str]:
        """Get git configuration value."""
        try:
            result = self._run_git("config", f"--{scope}", key, check=True)
            return result.strip() or None
        except subprocess.CalledProcessError:
            return None
    
    def set_config(self, key: str, value: str, scope: str = "local") -> bool:
        """Set git configuration value."""
        try:
            self._run_git("config", f"--{scope}", key, value, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    def get_user_name(self) -> Optional[str]:
        """Get configured user name."""
        return self.get_config("user.name") or self.get_config("user.name", "global")
    
    def get_user_email(self) -> Optional[str]:
        """Get configured user email."""
        return self.get_config("user.email") or self.get_config("user.email", "global")
    
    # ============================================================
    # STATUS AND DIFF
    # ============================================================
    
    def get_status(self, include_untracked: bool = True) -> List[GitFileStatus]:
        """Get repository status."""
        if not self.is_repo:
            return []
        
        try:
            cmd = ["status", "--porcelain=v1", "--branch"]
            if not include_untracked:
                cmd.append("--untracked-files=no")
            
            result = self._run_git(*cmd, check=True)
            statuses = []
            
            for line in result.split('\n'):
                if not line.strip() or line.startswith('#'):
                    continue
                
                # Parse porcelain status
                if len(line) >= 2:
                    staged_code = line[0]
                    unstaged_code = line[1] if len(line) > 2 else ' '
                    file_path = line[3:].strip()
                    
                    status = self._parse_status_codes(staged_code, unstaged_code)
                    
                    if status:
                        file_status = GitFileStatus(
                            file_path=file_path,
                            status=status,
                            change_type=self._code_to_change_type(staged_code or unstaged_code),
                            staged=staged_code != ' '
                        )
                        
                        # Handle renamed files
                        if status == GitStatus.RENAMED and ' -> ' in file_path:
                            old, new = file_path.split(' -> ', 1)
                            file_status.old_path = old
                            file_status.file_path = new
                        
                        statuses.append(file_status)
            
            return statuses
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get status: {e}")
            return []
    
    def _parse_status_codes(self, staged: str, unstaged: str) -> Optional[GitStatus]:
        """Parse porcelain status codes."""
        # Combined status
        code = staged + unstaged
        
        status_map = {
            'M': GitStatus.MODIFIED,
            'A': GitStatus.ADDED,
            'D': GitStatus.DELETED,
            'R': GitStatus.RENAMED,
            'C': GitStatus.COPIED,
            '??': GitStatus.UNTRACKED,
            '!!': GitStatus.IGNORED,
            'UU': GitStatus.CONFLICT,
            'AA': GitStatus.CONFLICT,
            'DD': GitStatus.CONFLICT,
        }
        
        return status_map.get(code.strip())
    
    def _code_to_change_type(self, code: str) -> ChangeType:
        """Convert status code to ChangeType."""
        type_map = {
            'M': ChangeType.MODIFIED,
            'A': ChangeType.ADDED,
            'D': ChangeType.DELETED,
            'R': ChangeType.RENAMED,
            'C': ChangeType.COPIED,
            '?': ChangeType.UNTRACKED,
            '!': ChangeType.IGNORED,
            'U': ChangeType.CONFLICT,
        }
        return type_map.get(code.strip(), ChangeType.MODIFIED)
    
    def get_diff(self, staged: bool = False, file_path: Optional[str] = None,
                  commit: Optional[str] = None, compare_with: Optional[str] = None) -> List[GitDiff]:
        """Get diff information."""
        if not self.is_repo:
            return []
        
        try:
            cmd = ["diff"]
            
            if staged:
                cmd.append("--staged")
            if file_path:
                cmd.append("--")
                cmd.append(file_path)
            if commit:
                cmd.append(commit)
            if compare_with:
                cmd.append(compare_with)
            
            result = self._run_git(*cmd, check=False)
            
            # Parse diff output
            diffs = []
            current_diff = None
            current_content = []
            
            for line in result.split('\n'):
                if line.startswith('diff --git'):
                    if current_diff:
                        current_diff.diff_content = '\n'.join(current_content)
                        diffs.append(current_diff)
                    
                    # Parse new diff header
                    parts = line.split(' ')
                    old_path = parts[2][2:] if len(parts) > 2 else None
                    new_path = parts[3][2:] if len(parts) > 3 else None
                    
                    current_diff = GitDiff(
                        file_path=new_path or old_path or "",
                        old_path=old_path if old_path != new_path else None
                    )
                    current_content = [line]
                    
                elif current_diff is not None:
                    current_content.append(line)
                    
                    if line.startswith('+++'):
                        pass
                    elif line.startswith('---'):
                        pass
                    elif line.startswith('+') and not line.startswith('+++'):
                        current_diff.insertions += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        current_diff.deletions += 1
            
            if current_diff:
                current_diff.diff_content = '\n'.join(current_content)
                diffs.append(current_diff)
            
            return diffs
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get diff: {e}")
            return []
    
    def get_file_content(self, file_path: str, revision: str = "HEAD") -> Optional[str]:
        """Get file content at a specific revision."""
        try:
            return self._run_git("show", f"{revision}:{file_path}", check=True)
        except subprocess.CalledProcessError:
            return None
    
    # ============================================================
    # COMMITS
    # ============================================================
    
    def get_commits(self, max_count: int = 100, branch: Optional[str] = None,
                     author: Optional[str] = None, since: Optional[str] = None,
                     until: Optional[str] = None, file_path: Optional[str] = None) -> List[GitCommit]:
        """Get commit history."""
        if not self.is_repo:
            return []
        
        try:
            cmd = ["log", f"--max-count={max_count}", "--format=%H|%h|%an|%ae|%cn|%ce|%s|%ct|%P"]
            
            if branch:
                cmd.append(branch)
            if author:
                cmd.extend(["--author", author])
            if since:
                cmd.extend(["--since", since])
            if until:
                cmd.extend(["--until", until])
            if file_path:
                cmd.append("--")
                cmd.append(file_path)
            
            result = self._run_git(*cmd, check=True)
            commits = []
            
            for line in result.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 9:
                    commit = GitCommit(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        author_email=parts[3],
                        committer=parts[4],
                        committer_email=parts[5],
                        message=parts[6],
                        date=datetime.fromtimestamp(int(parts[7])),
                        parents=parts[8].split() if parts[8] else []
                    )
                    commits.append(commit)
            
            # Get stats for each commit
            for commit in commits:
                stats = self.get_commit_stats(commit.hash)
                if stats:
                    commit.files_changed = stats['files']
                    commit.insertions = stats['insertions']
                    commit.deletions = stats['deletions']
            
            return commits
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get commits: {e}")
            return []
    
    def get_commit(self, revision: str = "HEAD") -> Optional[GitCommit]:
        """Get a single commit by revision."""
        commits = self.get_commits(max_count=1, branch=revision)
        return commits[0] if commits else None
    
    def get_commit_stats(self, revision: str = "HEAD") -> Optional[Dict[str, int]]:
        """Get commit statistics."""
        try:
            result = self._run_git("show", "--stat", "--format=", revision, check=True)
            lines = result.strip().split('\n')
            
            if lines:
                last_line = lines[-1].strip()
                match = re.search(r'(\d+)\s+files?\s+changed(?:,\s+(\d+)\s+insertions?)?(?:,\s+(\d+)\s+deletions?)?', last_line)
                if match:
                    return {
                        'files': int(match.group(1) or 0),
                        'insertions': int(match.group(2) or 0),
                        'deletions': int(match.group(3) or 0)
                    }
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def get_current_commit(self) -> Optional[str]:
        """Get current commit hash."""
        try:
            return self._run_git("rev-parse", "HEAD", check=True).strip()
        except subprocess.CalledProcessError:
            return None
    
    def get_last_commit_date(self) -> Optional[datetime]:
        """Get last commit date."""
        try:
            timestamp = self._run_git("log", "-1", "--format=%ct", check=True).strip()
            return datetime.fromtimestamp(int(timestamp))
        except subprocess.CalledProcessError:
            return None
    
    def get_last_author(self) -> Optional[str]:
        """Get last commit author."""
        try:
            return self._run_git("log", "-1", "--format=%an", check=True).strip()
        except subprocess.CalledProcessError:
            return None
    
    # ============================================================
    # BRANCHES
    # ============================================================
    
    def get_branches(self, include_remote: bool = True) -> List[GitBranch]:
        """Get all branches."""
        if not self.is_repo:
            return []
        
        try:
            cmd = ["branch", "-a", "--format=%(refname:short)|%(objectname)|%(upstream:short)|%(upstream:track)"]
            if include_remote:
                cmd.append("-a")
            
            result = self._run_git(*cmd, check=True)
            branches = []
            current_branch = self.get_current_branch()
            
            for line in result.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|')
                name = parts[0].strip()
                
                # Skip HEAD pointer
                if name == 'HEAD' or '->' in name:
                    continue
                
                is_remote = name.startswith('remotes/')
                remote_name = None
                if is_remote:
                    remote_name = name.split('/')[1]
                    display_name = '/'.join(name.split('/')[2:])
                else:
                    display_name = name
                
                branch = GitBranch(
                    name=display_name,
                    is_current=(display_name == current_branch),
                    is_remote=is_remote,
                    remote_name=remote_name,
                    upstream=parts[2].strip() if len(parts) > 2 and parts[2] else None,
                    last_commit=parts[1].strip() if len(parts) > 1 else None
                )
                
                # Parse ahead/behind
                if len(parts) > 3 and parts[3]:
                    track = parts[3].strip()
                    ahead_match = re.search(r'ahead\s+(\d+)', track)
                    behind_match = re.search(r'behind\s+(\d+)', track)
                    if ahead_match:
                        branch.ahead = int(ahead_match.group(1))
                    if behind_match:
                        branch.behind = int(behind_match.group(1))
                
                branches.append(branch)
            
            return branches
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get branches: {e}")
            return []
    
    def get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        try:
            return self._run_git("branch", "--show-current", check=True).strip()
        except subprocess.CalledProcessError:
            return None
    
    def create_branch(self, name: str, start_point: Optional[str] = None,
                       checkout: bool = False) -> bool:
        """Create a new branch."""
        try:
            cmd = ["branch", name]
            if start_point:
                cmd.append(start_point)
            
            self._run_git(*cmd, check=True)
            
            if checkout:
                self.checkout(name)
            
            logger.info(f"Created branch: {name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e}")
            return False
    
    def delete_branch(self, name: str, force: bool = False,
                       remote: bool = False) -> bool:
        """Delete a branch."""
        try:
            cmd = ["branch"]
            if force:
                cmd.append("-D")
            else:
                cmd.append("-d")
            if remote:
                cmd.append("-r")
            cmd.append(name)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Deleted branch: {name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete branch: {e}")
            return False
    
    def checkout(self, target: str, create_branch: bool = False) -> bool:
        """Checkout a branch or commit."""
        try:
            cmd = ["checkout"]
            if create_branch:
                cmd.append("-b")
            cmd.append(target)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Checked out: {target}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to checkout: {e}")
            return False
    
    def merge(self, branch: str, strategy: MergeStrategy = MergeStrategy.MERGE,
               message: Optional[str] = None, squash: bool = False,
               no_commit: bool = False) -> bool:
        """Merge a branch."""
        try:
            cmd = ["merge"]
            
            if strategy == MergeStrategy.SQUASH or squash:
                cmd.append("--squash")
            elif strategy == MergeStrategy.FAST_FORWARD:
                cmd.append("--ff-only")
            else:
                cmd.append("--no-ff")
            
            if message:
                cmd.extend(["-m", message])
            if no_commit:
                cmd.append("--no-commit")
            
            cmd.append(branch)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Merged branch: {branch}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to merge: {e}")
            return False
    
    def rebase(self, upstream: str, interactive: bool = False,
                onto: Optional[str] = None) -> bool:
        """Rebase current branch."""
        try:
            cmd = ["rebase"]
            if interactive:
                cmd.append("-i")
            if onto:
                cmd.extend(["--onto", onto])
            cmd.append(upstream)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Rebased onto {upstream}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to rebase: {e}")
            return False
    
    # ============================================================
    # REMOTES
    # ============================================================
    
    def get_remotes(self) -> List[GitRemote]:
        """Get all remotes."""
        try:
            result = self._run_git("remote", "-v", check=True)
            remotes = {}
            
            for line in result.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    url = parts[1]
                    remote_type = parts[2].strip('()')
                    
                    if name not in remotes:
                        remotes[name] = GitRemote(name=name, url="")
                    
                    if remote_type == 'fetch':
                        remotes[name].url = url
                    elif remote_type == 'push':
                        remotes[name].push_url = url
            
            return list(remotes.values())
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get remotes: {e}")
            return []
    
    def add_remote(self, name: str, url: str) -> bool:
        """Add a remote."""
        try:
            self._run_git("remote", "add", name, url, check=True)
            logger.info(f"Added remote: {name} -> {url}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add remote: {e}")
            return False
    
    def remove_remote(self, name: str) -> bool:
        """Remove a remote."""
        try:
            self._run_git("remote", "remove", name, check=True)
            logger.info(f"Removed remote: {name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove remote: {e}")
            return False
    
    def fetch(self, remote: str = "origin", prune: bool = False,
               tags: bool = False) -> bool:
        """Fetch from remote."""
        try:
            cmd = ["fetch", remote]
            if prune:
                cmd.append("--prune")
            if tags:
                cmd.append("--tags")
            
            self._run_git(*cmd, check=True)
            logger.info(f"Fetched from {remote}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to fetch: {e}")
            return False
    
    def pull(self, remote: str = "origin", branch: Optional[str] = None,
              rebase: bool = False) -> bool:
        """Pull from remote."""
        try:
            cmd = ["pull"]
            if rebase:
                cmd.append("--rebase")
            cmd.append(remote)
            if branch:
                cmd.append(branch)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Pulled from {remote}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull: {e}")
            return False
    
    def push(self, remote: str = "origin", branch: Optional[str] = None,
              set_upstream: bool = False, force: bool = False,
              tags: bool = False) -> bool:
        """Push to remote."""
        try:
            cmd = ["push"]
            if set_upstream:
                cmd.append("-u")
            if force:
                cmd.append("--force")
            if tags:
                cmd.append("--tags")
            cmd.append(remote)
            if branch:
                cmd.append(branch)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Pushed to {remote}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push: {e}")
            return False
    
    # ============================================================
    # TAGS
    # ============================================================
    
    def get_tags(self) -> List[GitTag]:
        """Get all tags."""
        try:
            result = self._run_git("tag", "-l", "--format=%(refname:short)|%(objectname)|%(subject)|%(taggername)|%(taggerdate:unix)", check=True)
            tags = []
            
            for line in result.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|')
                tag = GitTag(
                    name=parts[0],
                    commit_hash=parts[1],
                    message=parts[2] if len(parts) > 2 and parts[2] else None,
                    tagger=parts[3] if len(parts) > 3 and parts[3] else None,
                    date=datetime.fromtimestamp(int(parts[4])) if len(parts) > 4 and parts[4] else None,
                    is_annotated=bool(parts[3] if len(parts) > 3 else False)
                )
                tags.append(tag)
            
            return tags
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get tags: {e}")
            return []
    
    def create_tag(self, name: str, message: Optional[str] = None,
                    commit: Optional[str] = None) -> bool:
        """Create a tag."""
        try:
            cmd = ["tag"]
            if message:
                cmd.extend(["-a", name, "-m", message])
            else:
                cmd.append(name)
            if commit:
                cmd.append(commit)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Created tag: {name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create tag: {e}")
            return False
    
    def delete_tag(self, name: str) -> bool:
        """Delete a tag."""
        try:
            self._run_git("tag", "-d", name, check=True)
            logger.info(f"Deleted tag: {name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete tag: {e}")
            return False
    
    # ============================================================
    # STASH
    # ============================================================
    
    def get_stashes(self) -> List[GitStash]:
        """Get all stashes."""
        try:
            result = self._run_git("stash", "list", "--format=%gd|%gs|%H|%ct", check=True)
            stashes = []
            
            for line in result.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 4:
                    # Parse stash index
                    index_match = re.search(r'stash@{(\d+)}', parts[0])
                    index = int(index_match.group(1)) if index_match else 0
                    
                    # Parse branch from message
                    branch = "unknown"
                    message = parts[1]
                    branch_match = re.search(r'On\s+(\S+):', message)
                    if branch_match:
                        branch = branch_match.group(1)
                    
                    stash = GitStash(
                        index=index,
                        branch=branch,
                        message=message,
                        date=datetime.fromtimestamp(int(parts[3])),
                        commit_hash=parts[2]
                    )
                    stashes.append(stash)
            
            return stashes
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get stashes: {e}")
            return []
    
    def stash(self, message: Optional[str] = None, include_untracked: bool = False) -> bool:
        """Stash current changes."""
        try:
            cmd = ["stash", "push"]
            if message:
                cmd.extend(["-m", message])
            if include_untracked:
                cmd.append("--include-untracked")
            
            self._run_git(*cmd, check=True)
            logger.info("Stashed changes")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stash: {e}")
            return False
    
    def stash_pop(self, index: int = 0) -> bool:
        """Pop a stash."""
        try:
            self._run_git("stash", "pop", f"stash@{{{index}}}", check=True)
            logger.info(f"Popped stash@{index}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pop stash: {e}")
            return False
    
    def stash_apply(self, index: int = 0) -> bool:
        """Apply a stash without dropping."""
        try:
            self._run_git("stash", "apply", f"stash@{{{index}}}", check=True)
            logger.info(f"Applied stash@{index}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply stash: {e}")
            return False
    
    def stash_drop(self, index: int = 0) -> bool:
        """Drop a stash."""
        try:
            self._run_git("stash", "drop", f"stash@{{{index}}}", check=True)
            logger.info(f"Dropped stash@{index}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to drop stash: {e}")
            return False
    
    def stash_clear(self) -> bool:
        """Clear all stashes."""
        try:
            self._run_git("stash", "clear", check=True)
            logger.info("Cleared all stashes")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clear stashes: {e}")
            return False
    
    # ============================================================
    # FILE OPERATIONS
    # ============================================================
    
    def add(self, paths: Union[str, List[str]]) -> bool:
        """Stage files."""
        if isinstance(paths, str):
            paths = [paths]
        
        try:
            self._run_git("add", *paths, check=True)
            logger.info(f"Staged: {', '.join(paths)}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stage: {e}")
            return False
    
    def add_all(self) -> bool:
        """Stage all changes."""
        return self.add(".")
    
    def unstage(self, paths: Union[str, List[str]]) -> bool:
        """Unstage files."""
        if isinstance(paths, str):
            paths = [paths]
        
        try:
            self._run_git("reset", "HEAD", "--", *paths, check=True)
            logger.info(f"Unstaged: {', '.join(paths)}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unstage: {e}")
            return False
    
    def commit(self, message: str, allow_empty: bool = False) -> bool:
        """Create a commit."""
        try:
            cmd = ["commit", "-m", message]
            if allow_empty:
                cmd.append("--allow-empty")
            
            self._run_git(*cmd, check=True)
            logger.info(f"Committed: {message[:50]}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e}")
            return False
    
    def commit_conventional(self, commit_type: CommitType, scope: Optional[str],
                            description: str, body: Optional[str] = None,
                            breaking: bool = False) -> bool:
        """Create a conventional commit."""
        # Build commit message
        message = f"{commit_type.value}"
        if scope:
            message += f"({scope})"
        if breaking:
            message += "!"
        message += f": {description}"
        
        if body:
            message += f"\n\n{body}"
        
        if breaking:
            message += "\n\nBREAKING CHANGE: See description above."
        
        return self.commit(message)
    
    def reset(self, target: str = "HEAD", hard: bool = False) -> bool:
        """Reset to a target."""
        try:
            cmd = ["reset"]
            if hard:
                cmd.append("--hard")
            cmd.append(target)
            
            self._run_git(*cmd, check=True)
            logger.info(f"Reset to {target}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reset: {e}")
            return False
    
    def clean(self, force: bool = False, directories: bool = False) -> bool:
        """Clean working directory."""
        try:
            cmd = ["clean"]
            if force:
                cmd.append("-f")
            if directories:
                cmd.append("-d")
            
            self._run_git(*cmd, check=True)
            logger.info("Cleaned working directory")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clean: {e}")
            return False
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def get_changed_files(self, compare_with: str = "HEAD~1") -> List[Path]:
        """Get list of changed files."""
        try:
            result = self._run_git("diff", "--name-only", compare_with, check=True)
            return [Path(f) for f in result.strip().split('\n') if f]
        except subprocess.CalledProcessError:
            return []
    
    def get_file_history(self, file_path: str, max_count: int = 50) -> List[GitCommit]:
        """Get file change history."""
        return self.get_commits(max_count=max_count, file_path=file_path)
    
    def get_last_commit_for_file(self, file_path: str) -> Optional[str]:
        """Get last commit hash for a file."""
        commits = self.get_commits(max_count=1, file_path=file_path)
        return commits[0].hash if commits else None
    
    def get_last_author_for_file(self, file_path: str) -> Optional[str]:
        """Get last author for a file."""
        commits = self.get_commits(max_count=1, file_path=file_path)
        return commits[0].author if commits else None
    
    def is_ignored(self, file_path: str) -> bool:
        """Check if file is ignored by git."""
        try:
            self._run_git("check-ignore", file_path, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_ignored_files(self) -> List[str]:
        """Get list of ignored files."""
        try:
            result = self._run_git("ls-files", "--others", "--ignored", "--exclude-standard", check=True)
            return result.strip().split('\n') if result.strip() else []
        except subprocess.CalledProcessError:
            return []
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        statuses = self.get_status()
        return any(s.staged or s.status in (GitStatus.MODIFIED, GitStatus.ADDED, GitStatus.DELETED) 
                   for s in statuses)
    
    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if one commit is ancestor of another."""
        try:
            self._run_git("merge-base", "--is-ancestor", ancestor, descendant, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_merge_base(self, commit1: str, commit2: str) -> Optional[str]:
        """Get merge base of two commits."""
        try:
            return self._run_git("merge-base", commit1, commit2, check=True).strip()
        except subprocess.CalledProcessError:
            return None
    
    # ============================================================
    # INTERNAL METHODS
    # ============================================================
    
    def _run_git(self, *args: str, check: bool = False, 
                  capture_output: bool = True, timeout: int = 60) -> str:
        """Run git command."""
        cmd = ["git"] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return e.stdout or ""
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {' '.join(cmd)}")
            return ""
    
    @contextmanager
    def temporary_branch(self, name: str, start_point: Optional[str] = None):
        """Context manager for temporary branch."""
        original_branch = self.get_current_branch()
        created = False
        
        try:
            # Create and checkout temporary branch
            self.create_branch(name, start_point, checkout=True)
            created = True
            yield name
        finally:
            # Return to original branch
            if original_branch:
                self.checkout(original_branch)
            # Delete temporary branch
            if created:
                self.delete_branch(name, force=True)
    
    @contextmanager
    def temporary_commit(self, message: str = "WIP: temporary commit"):
        """Context manager for temporary commit."""
        has_changes = self.has_uncommitted_changes()
        commit_hash = None
        
        try:
            if has_changes:
                self.add_all()
                self.commit(message)
                commit_hash = self.get_current_commit()
            yield commit_hash
        finally:
            if commit_hash:
                self.reset("HEAD~1", hard=True)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for git utilities."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Git utilities")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository path")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    subparsers.add_parser('status', help='Show repository status')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Show commit history')
    log_parser.add_argument('--max-count', type=int, default=20, help='Maximum commits')
    log_parser.add_argument('--branch', help='Branch to show')
    
    # Branch command
    branch_parser = subparsers.add_parser('branch', help='Branch operations')
    branch_parser.add_argument('--list', action='store_true', help='List branches')
    branch_parser.add_argument('--create', help='Create branch')
    branch_parser.add_argument('--delete', help='Delete branch')
    branch_parser.add_argument('--checkout', help='Checkout branch')
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Create commit')
    commit_parser.add_argument('--message', '-m', required=True, help='Commit message')
    commit_parser.add_argument('--type', choices=[t.value for t in CommitType], help='Conventional commit type')
    commit_parser.add_argument('--scope', help='Commit scope')
    
    # Changed files command
    changed_parser = subparsers.add_parser('changed', help='Show changed files')
    changed_parser.add_argument('--compare', default='HEAD~1', help='Compare with')
    
    args = parser.parse_args()
    
    git = GitUtils(args.repo)
    
    if not git.is_repo:
        print(f"Not a git repository: {args.repo}")
        sys.exit(1)
    
    if args.command == 'status':
        statuses = git.get_status()
        for s in statuses:
            staged = '+' if s.staged else ' '
            print(f"{staged}{s.change_type.value} {s.file_path}")
    
    elif args.command == 'log':
        commits = git.get_commits(max_count=args.max_count, branch=args.branch)
        for c in commits:
            print(f"{c.short_hash} {c.date.strftime('%Y-%m-%d %H:%M')} {c.author}")
            print(f"    {c.message[:80]}")
            print()
    
    elif args.command == 'branch':
        if args.list:
            branches = git.get_branches()
            for b in branches:
                marker = '*' if b.is_current else ' '
                remote = ' (remote)' if b.is_remote else ''
                print(f"{marker} {b.name}{remote}")
        elif args.create:
            git.create_branch(args.create, checkout=True)
        elif args.delete:
            git.delete_branch(args.delete)
        elif args.checkout:
            git.checkout(args.checkout)
    
    elif args.command == 'commit':
        if args.type:
            git.commit_conventional(
                CommitType(args.type),
                args.scope,
                args.message
            )
        else:
            git.commit(args.message)
    
    elif args.command == 'changed':
        files = git.get_changed_files(args.compare)
        for f in files:
            print(f)


if __name__ == "__main__":
    main()