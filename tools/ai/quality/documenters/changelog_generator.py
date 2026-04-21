"""
Changelog Generator

Generates comprehensive changelogs from git history, commit messages, and code changes including:
- Version-based changelog organization
- Semantic versioning support
- Commit message categorization
- Breaking change detection
- Contributor attribution
- Release notes generation
- Multi-format output (Markdown, HTML, JSON)


This changelog_generator.py provides:

Key Features:
1. Git History Analysis
Fetches all commits with metadata
Parses conventional commit messages
Extracts PR numbers and issue references
Identifies co-authors

2. Conventional Commit Support
feat: → New features (MINOR bump)
fix: → Bug fixes (PATCH bump)
breaking: → Breaking changes (MAJOR bump)
security: → Security fixes
perf: → Performance improvements
refactor: → Code refactoring
docs: → Documentation

3. Version Detection
Automatic tag parsing
Semantic version ordering
Version range filtering (since/until)
Pre-release detection

4. Changelog Organization
Group by release version
Categorize by change type
Scope-based grouping
Contributor attribution

5. Breaking Change Detection
Identifies breaking changes from commit messages
Highlights in dedicated section
Shows affected scopes

6. Multi-Format Output
Format	Use Case
Markdown	README, documentation
HTML	Web display, styled
JSON	API consumption, automation

7. Smart Features
Automatic version suggestion
Unreleased changes tracking
PR and issue linking
Co-author attribution

Usage Examples:
python
# Basic usage
from tools.ai.quality.documenters.changelog_generator import generate_changelog

generate_changelog(
    repo_path="/path/to/repo",
    output_path="/path/to/CHANGELOG.md",
    format="markdown"
)

# Generate with version range
generate_changelog(
    repo_path="/path/to/repo",
    since_tag="v1.0.0",
    until_tag="v2.0.0",
    include_unreleased=False
)

# Generate HTML for web display
generate_changelog(
    repo_path="/path/to/repo",
    output_path="/path/to/changelog.html",
    format="html"
)
Output Example (Markdown):
markdown
# Changelog

## [2.0.0] - 2024-01-15

### ⚠️ BREAKING CHANGES

- **api:** Removed deprecated /v1/users endpoint (PR #123)

### ✨ Features

#### Authentication
- Added OAuth2 support (PR #120)
- Implemented JWT refresh tokens (PR #121)

#### API
- New /v2/users endpoint with pagination (PR #122)

### 🐛 Bug Fixes

- Fixed memory leak in WebSocket handler (PR #119)
- Resolved race condition in task queue (PR #118)

### 🔒 Security

- Updated dependencies to fix CVE-2024-1234 (PR #117)

### 👥 Contributors

- John Doe
- Jane Smith

---

## [1.0.0] - 2023-12-01

### ✨ Features

- Initial release
- Basic CRUD operations
- Authentication support
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, Counter

from ...shared.logger import get_logger
from ...shared.state_manager import state_manager
from ...shared.config import config
from ...shared.file_utils import file_utils
from ...shared.git_utils import git_utils

logger = get_logger(__name__)


class ChangeType(Enum):
    """Types of changes for categorization"""
    FEATURE = "feature"           # New features
    FIX = "fix"                   # Bug fixes
    DEPRECATED = "deprecated"     # Deprecated features
    REMOVED = "removed"           # Removed features
    SECURITY = "security"         # Security fixes
    PERFORMANCE = "performance"   # Performance improvements
    REFACTOR = "refactor"         # Code refactoring
    DOCS = "docs"                 # Documentation
    STYLE = "style"               # Code style
    TEST = "test"                 # Testing
    BUILD = "build"               # Build system
    CI = "ci"                     # CI/CD
    BREAKING = "breaking"         # Breaking changes


class VersionBump(Enum):
    """Semantic version bump types"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    NONE = "none"


@dataclass
class Commit:
    """Represents a git commit"""
    hash: str
    short_hash: str
    author: str
    author_email: str
    date: datetime
    message: str
    body: str = ""
    change_type: Optional[ChangeType] = None
    is_breaking: bool = False
    scope: Optional[str] = None
    pr_number: Optional[int] = None
    issue_numbers: List[int] = field(default_factory=list)
    co_authors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.hash,
            "short_hash": self.short_hash,
            "author": self.author,
            "author_email": self.author_email,
            "date": self.date.isoformat(),
            "message": self.message,
            "body": self.body,
            "change_type": self.change_type.value if self.change_type else None,
            "is_breaking": self.is_breaking,
            "scope": self.scope,
            "pr_number": self.pr_number,
            "issue_numbers": self.issue_numbers,
            "co_authors": self.co_authors
        }


@dataclass
class Release:
    """Represents a release version"""
    version: str
    date: datetime
    commits: List[Commit]
    previous_version: Optional[str] = None
    is_prerelease: bool = False
    
    @property
    def changes_by_type(self) -> Dict[ChangeType, List[Commit]]:
        """Group changes by type"""
        changes = defaultdict(list)
        for commit in self.commits:
            if commit.change_type:
                changes[commit.change_type].append(commit)
            else:
                changes[ChangeType.FEATURE].append(commit)
        return dict(changes)
    
    @property
    def has_breaking_changes(self) -> bool:
        """Check if release has breaking changes"""
        return any(c.is_breaking for c in self.commits)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "date": self.date.isoformat(),
            "commits": [c.to_dict() for c in self.commits],
            "previous_version": self.previous_version,
            "is_prerelease": self.is_prerelease,
            "has_breaking_changes": self.has_breaking_changes
        }


@dataclass
class ChangelogConfig:
    """Configuration for changelog generation"""
    version_pattern: str = r"^v?(\d+\.\d+\.\d+)$"
    version_bump_patterns: Dict[str, VersionBump] = field(default_factory=lambda: {
        "breaking": VersionBump.MAJOR,
        "feature": VersionBump.MINOR,
        "fix": VersionBump.PATCH,
        "deprecated": VersionBump.MINOR,
        "security": VersionBump.PATCH,
        "performance": VersionBump.PATCH,
        "refactor": VersionBump.PATCH,
        "docs": VersionBump.PATCH,
        "style": VersionBump.PATCH,
        "test": VersionBump.PATCH,
        "build": VersionBump.PATCH,
        "ci": VersionBump.PATCH
    })
    conventional_commits: bool = True
    group_by_scope: bool = True
    include_unreleased: bool = True
    max_commits_per_release: int = 500
    unreleased_label: str = "Unreleased"
    changelog_filename: str = "CHANGELOG.md"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_pattern": self.version_pattern,
            "conventional_commits": self.conventional_commits,
            "group_by_scope": self.group_by_scope,
            "include_unreleased": self.include_unreleased,
            "max_commits_per_release": self.max_commits_per_release,
            "unreleased_label": self.unreleased_label
        }


class ChangelogGenerator:
    """
    Generates comprehensive changelogs from git history.
    
    Features:
    - Conventional commit parsing
    - Automatic version detection
    - Breaking change detection
    - Contributor attribution
    - Multi-format output
    - Release categorization
    - Semantic version suggestion
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.commits: List[Commit] = []
        self.releases: List[Release] = []
        self.config = ChangelogConfig()
        self.contributors: Counter = Counter()
        self.version_tags: Dict[str, str] = {}  # tag -> commit_hash
        
        logger.info(f"ChangelogGenerator initialized for {self.repo_path}")
    
    def generate(self, repo_path: Optional[str] = None,
                output_path: Optional[str] = None,
                since_tag: Optional[str] = None,
                until_tag: Optional[str] = None,
                include_unreleased: bool = True,
                format: str = "markdown") -> Dict[str, Any]:
        """
        Generate changelog from git history.
        
        Args:
            repo_path: Path to git repository
            output_path: Path to write changelog
            since_tag: Starting tag (exclusive)
            until_tag: Ending tag (inclusive)
            include_unreleased: Include unreleased changes
            format: Output format (markdown, html, json)
            
        Returns:
            Generation metadata
        """
        if repo_path:
            self.repo_path = Path(repo_path)
        
        self.config.include_unreleased = include_unreleased
        
        logger.info(f"Generating changelog for {self.repo_path}")
        
        # Step 1: Fetch git history
        self._fetch_git_history()
        
        # Step 2: Parse conventional commits
        self._parse_conventional_commits()
        
        # Step 3: Detect versions
        self._detect_versions()
        
        # Step 4: Group commits by release
        self._group_commits_by_release(since_tag, until_tag)
        
        # Step 5: Generate changelog
        if format == "markdown":
            changelog = self._generate_markdown()
        elif format == "html":
            changelog = self._generate_html()
        elif format == "json":
            changelog = self._generate_json()
        else:
            changelog = self._generate_markdown()
        
        # Step 6: Write output
        if output_path:
            self._write_output(output_path, changelog, format)
        
        return {
            "changelog_path": output_path,
            "total_commits": len(self.commits),
            "total_releases": len(self.releases),
            "total_contributors": len(self.contributors),
            "since_tag": since_tag,
            "until_tag": until_tag,
            "include_unreleased": include_unreleased,
            "format": format,
            "generated_at": datetime.now().isoformat()
        }
    
    def _fetch_git_history(self) -> None:
        """Fetch commit history from git"""
        try:
            # Get all commits with details
            cmd = [
                'git', 'log', '--pretty=format:%H|%h|%an|%ae|%at|%s|%b', 
                '--all', '--reverse'
            ]
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Git log failed: {result.stderr}")
                return
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 6)
                if len(parts) < 6:
                    continue
                
                commit_hash = parts[0]
                short_hash = parts[1]
                author = parts[2]
                author_email = parts[3]
                timestamp = int(parts[4])
                subject = parts[5]
                body = parts[6] if len(parts) > 6 else ""
                
                commit = Commit(
                    hash=commit_hash,
                    short_hash=short_hash,
                    author=author,
                    author_email=author_email,
                    date=datetime.fromtimestamp(timestamp),
                    message=subject,
                    body=body
                )
                
                self.commits.append(commit)
                self.contributors[author] += 1
            
            # Get tags
            tag_cmd = ['git', 'tag', '-l', '--format=%(refname:strip=2) %(objectname)']
            tag_result = subprocess.run(tag_cmd, cwd=self.repo_path, capture_output=True, text=True)
            
            for line in tag_result.stdout.strip().split('\n'):
                if line and ' ' in line:
                    tag, commit_hash = line.split(' ', 1)
                    self.version_tags[tag] = commit_hash
            
            logger.info(f"Fetched {len(self.commits)} commits and {len(self.version_tags)} tags")
            
        except Exception as e:
            logger.error(f"Failed to fetch git history: {e}")
    
    def _parse_conventional_commits(self) -> None:
        """Parse conventional commit messages"""
        # Conventional commit pattern: <type>(<scope>): <description>
        pattern = r'^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:?\s*(?P<description>.+)$'
        
        for commit in self.commits:
            message = commit.message.strip()
            match = re.match(pattern, message, re.IGNORECASE)
            
            if match and self.config.conventional_commits:
                type_str = match.group('type').lower()
                scope = match.group('scope')
                is_breaking = bool(match.group('breaking'))
                description = match.group('description')
                
                # Map type to ChangeType
                type_mapping = {
                    'feat': ChangeType.FEATURE,
                    'fix': ChangeType.FIX,
                    'deprecate': ChangeType.DEPRECATED,
                    'remove': ChangeType.REMOVED,
                    'security': ChangeType.SECURITY,
                    'perf': ChangeType.PERFORMANCE,
                    'refactor': ChangeType.REFACTOR,
                    'docs': ChangeType.DOCS,
                    'style': ChangeType.STYLE,
                    'test': ChangeType.TEST,
                    'build': ChangeType.BUILD,
                    'ci': ChangeType.CI,
                    'breaking': ChangeType.BREAKING
                }
                
                commit.change_type = type_mapping.get(type_str, ChangeType.FEATURE)
                commit.scope = scope
                commit.is_breaking = is_breaking or type_str == 'breaking'
                commit.message = description
            else:
                # Default to feature if not conventional
                commit.change_type = ChangeType.FEATURE
            
            # Extract PR number
            pr_pattern = r'\(#(\d+)\)$'
            pr_match = re.search(pr_pattern, commit.message)
            if pr_match:
                commit.pr_number = int(pr_match.group(1))
                commit.message = re.sub(pr_pattern, '', commit.message).strip()
            
            # Extract issue numbers
            issue_pattern = r'#(\d+)'
            commit.issue_numbers = [int(m) for m in re.findall(issue_pattern, commit.message)]
            
            # Extract co-authors from body
            co_author_pattern = r'Co-authored-by:\s*([^<]+)'
            commit.co_authors = re.findall(co_author_pattern, commit.body)
        
        logger.info(f"Parsed {len(self.commits)} conventional commits")
    
    def _detect_versions(self) -> None:
        """Detect versions from git tags"""
        versions = []
        
        for tag, commit_hash in self.version_tags.items():
            match = re.match(self.config.version_pattern, tag)
            if match:
                version = match.group(1)
                versions.append((version, commit_hash, tag))
        
        # Sort versions by semver
        versions.sort(key=lambda v: [int(x) for x in v[0].split('.')])
        
        logger.info(f"Detected {len(versions)} versions: {[v[0] for v in versions]}")
    
    def _group_commits_by_release(self, since_tag: Optional[str] = None,
                                  until_tag: Optional[str] = None) -> None:
        """Group commits by release version"""
        self.releases = []
        
        # Get all version tags with their commit positions
        version_commits = []
        for tag, commit_hash in self.version_tags.items():
            if re.match(self.config.version_pattern, tag):
                # Find commit index
                for idx, commit in enumerate(self.commits):
                    if commit.hash.startswith(commit_hash[:7]):
                        version_commits.append((tag, idx))
                        break
        
        # Sort by commit index
        version_commits.sort(key=lambda x: x[1])
        
        # Filter by since/until
        start_idx = 0
        end_idx = len(self.commits)
        
        if since_tag:
            for tag, idx in version_commits:
                if tag == since_tag:
                    start_idx = idx + 1
                    break
        
        if until_tag:
            for tag, idx in version_commits:
                if tag == until_tag:
                    end_idx = idx + 1
                    break
        
        # Group commits
        prev_idx = start_idx
        for i, (tag, idx) in enumerate(version_commits):
            if idx < start_idx or idx > end_idx:
                continue
            
            if idx > prev_idx:
                version_commits_between = self.commits[prev_idx:idx]
                if version_commits_between:
                    version_num = tag.lstrip('v')
                    release = Release(
                        version=version_num,
                        date=self.commits[idx].date if idx < len(self.commits) else datetime.now(),
                        commits=version_commits_between,
                        previous_version=version_commits[i-1][0].lstrip('v') if i > 0 else None
                    )
                    self.releases.append(release)
            
            prev_idx = idx + 1
        
        # Unreleased commits
        if self.config.include_unreleased and prev_idx < end_idx:
            unreleased_commits = self.commits[prev_idx:end_idx]
            if unreleased_commits:
                release = Release(
                    version=self.config.unreleased_label,
                    date=datetime.now(),
                    commits=unreleased_commits,
                    previous_version=self.releases[-1].version if self.releases else None,
                    is_prerelease=True
                )
                self.releases.append(release)
        
        # Limit commits per release
        for release in self.releases:
            if len(release.commits) > self.config.max_commits_per_release:
                release.commits = release.commits[:self.config.max_commits_per_release]
        
        logger.info(f"Grouped commits into {len(self.releases)} releases")
    
    def _generate_markdown(self) -> str:
        """Generate Markdown changelog"""
        lines = []
        
        # Header
        lines.append("# Changelog\n")
        lines.append(f"All notable changes to this project will be documented in this file.\n")
        lines.append(f"The format is based on [Keep a Changelog](https://keepachangelog.com/),")
        lines.append(f"and this project adheres to [Semantic Versioning](https://semver.org/).\n")
        
        # Releases
        for release in self.releases:
            # Version header
            if release.is_prerelease:
                lines.append(f"## [{release.version}]")
            else:
                lines.append(f"## [{release.version}] - {release.date.strftime('%Y-%m-%d')}")
            lines.append("")
            
            # Breaking changes section
            if release.has_breaking_changes:
                lines.append("### ⚠️ BREAKING CHANGES\n")
                for commit in release.commits:
                    if commit.is_breaking:
                        lines.append(f"- **{commit.scope or 'general'}:** {commit.message}")
                        if commit.pr_number:
                            lines[-1] += f" (PR #{commit.pr_number})"
                lines.append("")
            
            # Changes by type
            type_order = [
                (ChangeType.FEATURE, "✨ Features"),
                (ChangeType.FIX, "🐛 Bug Fixes"),
                (ChangeType.SECURITY, "🔒 Security"),
                (ChangeType.PERFORMANCE, "⚡ Performance"),
                (ChangeType.DEPRECATED, "⚠️ Deprecated"),
                (ChangeType.REMOVED, "🗑️ Removed"),
                (ChangeType.REFACTOR, "♻️ Refactoring"),
                (ChangeType.DOCS, "📚 Documentation"),
                (ChangeType.STYLE, "🎨 Style"),
                (ChangeType.TEST, "✅ Testing"),
                (ChangeType.BUILD, "📦 Build"),
                (ChangeType.CI, "🔧 CI/CD")
            ]
            
            for change_type, title in type_order:
                commits = [c for c in release.commits if c.change_type == change_type]
                if commits:
                    lines.append(f"### {title}\n")
                    
                    if self.config.group_by_scope:
                        # Group by scope
                        by_scope = defaultdict(list)
                        for commit in commits:
                            scope = commit.scope or "general"
                            by_scope[scope].append(commit)
                        
                        for scope, scope_commits in sorted(by_scope.items()):
                            lines.append(f"#### {scope.title()}\n")
                            for commit in scope_commits:
                                line = f"- {commit.message}"
                                if commit.pr_number:
                                    line += f" (PR #{commit.pr_number})"
                                if commit.issue_numbers:
                                    issues = ', '.join(f"#{i}" for i in commit.issue_numbers)
                                    line += f" (Issues: {issues})"
                                lines.append(line)
                            lines.append("")
                    else:
                        for commit in commits:
                            line = f"- {commit.message}"
                            if commit.scope:
                                line = f"- **{commit.scope}:** {commit.message}"
                            if commit.pr_number:
                                line += f" (PR #{commit.pr_number})"
                            if commit.issue_numbers:
                                issues = ', '.join(f"#{i}" for i in commit.issue_numbers)
                                line += f" (Issues: {issues})"
                            lines.append(line)
                        lines.append("")
            
            # Contributors section
            contributors = set()
            for commit in release.commits:
                contributors.add(commit.author)
                contributors.update(commit.co_authors)
            
            if contributors:
                lines.append("### 👥 Contributors\n")
                for contributor in sorted(contributors):
                    lines.append(f"- {contributor}")
                lines.append("")
            
            lines.append("---\n")
        
        # Version comparison links
        if len(self.releases) > 1 and not self.releases[-1].is_prerelease:
            lines.append("## Version Comparison\n")
            for i, release in enumerate(self.releases[:-1]):
                next_release = self.releases[i + 1]
                if not release.is_prerelease and not next_release.is_prerelease:
                    lines.append(f"- [{release.version}...{next_release.version}](/{next_release.version}...{release.version})")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_html(self) -> str:
        """Generate HTML changelog"""
        markdown = self._generate_markdown()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 30px; }}
        h3 {{ margin-top: 20px; color: #555; }}
        h4 {{ margin-top: 15px; color: #666; margin-left: 10px; }}
        ul {{ margin-left: 20px; }}
        li {{ margin: 5px 0; }}
        .breaking {{ background-color: #fff3f3; border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; }}
        .version {{ color: #2c3e50; }}
        .date {{ color: #7f8c8d; font-size: 0.9em; }}
        hr {{ margin: 30px 0; }}
        .contributor {{ color: #3498db; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 5px;
        }}
        .badge-feature {{ background: #4caf50; color: white; }}
        .badge-fix {{ background: #f44336; color: white; }}
        .badge-security {{ background: #ff9800; color: white; }}
        .badge-breaking {{ background: #9c27b0; color: white; }}
    </style>
</head>
<body>
    <div class="changelog">
        {self._markdown_to_html(markdown)}
    </div>
</body>
</html>"""
        return html
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (simplified)"""
        html = markdown
        
        # Headers
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Lists
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\g<0></ul>', html, flags=re.DOTALL)
        
        # Code blocks
        html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
        
        # Paragraphs
        html = re.sub(r'\n\n', r'</p><p>', html)
        html = f'<p>{html}</p>'
        html = re.sub(r'<p>\s*<h', r'<h', html)
        html = re.sub(r'</h\d>\s*</p>', r'</h\d>', html)
        html = re.sub(r'<p>\s*<ul>', r'<ul>', html)
        html = re.sub(r'</ul>\s*</p>', r'</ul>', html)
        html = re.sub(r'<p>\s*<li>', r'<li>', html)
        html = re.sub(r'</li>\s*</p>', r'</li>', html)
        
        return html
    
    def _generate_json(self) -> str:
        """Generate JSON changelog"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "repository": str(self.repo_path),
            "releases": [r.to_dict() for r in self.releases],
            "contributors": dict(self.contributors.most_common()),
            "statistics": {
                "total_commits": len(self.commits),
                "total_releases": len(self.releases),
                "total_contributors": len(self.contributors)
            }
        }
        
        import json
        return json.dumps(data, indent=2)
    
    def _write_output(self, output_path: str, content: str, format: str) -> None:
        """Write changelog to output file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension
        ext_map = {
            "markdown": ".md",
            "html": ".html",
            "json": ".json"
        }
        
        if not output_file.suffix:
            output_file = output_file.with_suffix(ext_map.get(format, ".md"))
        
        file_utils.write_file(str(output_file), content)
        logger.info(f"Changelog written to {output_file}")
    
    def suggest_next_version(self, current_version: str) -> Tuple[str, VersionBump]:
        """
        Suggest next version based on commit history since last release.
        
        Args:
            current_version: Current version string
            
        Returns:
            Tuple of (next_version, bump_type)
        """
        # Parse current version
        parts = current_version.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Determine bump type from unreleased commits
        bump = VersionBump.NONE
        
        if self.releases and self.releases[-1].is_prerelease:
            for commit in self.releases[-1].commits:
                if commit.is_breaking:
                    bump = VersionBump.MAJOR
                    break
                elif commit.change_type == ChangeType.FEATURE:
                    if bump != VersionBump.MAJOR:
                        bump = VersionBump.MINOR
                elif commit.change_type in [ChangeType.FIX, ChangeType.SECURITY, ChangeType.PERFORMANCE]:
                    if bump not in [VersionBump.MAJOR, VersionBump.MINOR]:
                        bump = VersionBump.PATCH
        
        # Calculate next version
        if bump == VersionBump.MAJOR:
            next_version = f"{major + 1}.0.0"
        elif bump == VersionBump.MINOR:
            next_version = f"{major}.{minor + 1}.0"
        elif bump == VersionBump.PATCH:
            next_version = f"{major}.{minor}.{patch + 1}"
        else:
            next_version = current_version
        
        return next_version, bump
    
    def get_unreleased_changes(self) -> List[Commit]:
        """Get unreleased commits"""
        for release in self.releases:
            if release.is_prerelease:
                return release.commits
        return []
    
    def get_release_by_version(self, version: str) -> Optional[Release]:
        """Get release by version string"""
        for release in self.releases:
            if release.version == version:
                return release
        return None


# Convenience function
def generate_changelog(repo_path: str,
                      output_path: str = None,
                      since_tag: str = None,
                      until_tag: str = None,
                      include_unreleased: bool = True,
                      format: str = "markdown") -> Dict[str, Any]:
    """
    Generate changelog for a git repository.
    
    Args:
        repo_path: Path to git repository
        output_path: Output file path (default: repo_path/CHANGELOG.md)
        since_tag: Starting tag (exclusive)
        until_tag: Ending tag (inclusive)
        include_unreleased: Include unreleased changes
        format: Output format (markdown, html, json)
        
    Returns:
        Generation metadata
    """
    if output_path is None:
        output_path = str(Path(repo_path) / "CHANGELOG.md")
    
    generator = ChangelogGenerator(repo_path)
    
    return generator.generate(
        repo_path=repo_path,
        output_path=output_path,
        since_tag=since_tag,
        until_tag=until_tag,
        include_unreleased=include_unreleased,
        format=format
    )