"""Strategy pattern — versioning strategies for document writers."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any


class VersionIncrement(str, Enum):
    """Which part of a semantic version to increment."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class VersionWriteStrategy(str, Enum):
    """How to handle versioning when writing a file."""
    OVERWRITE = "overwrite"
    NEW_VERSION = "new_version"
    AUTO_INCREMENT = "auto_increment"


class VersioningContext:
    """Strategy context — encapsulates versioning logic for document writers.

    Separates file versioning (path computation, version incrementing)
    from the document writer itself. Supports OVERWRITE, NEW_VERSION,
    and AUTO_INCREMENT strategies.
    """

    def __init__(
        self,
        strategy: VersionWriteStrategy = VersionWriteStrategy.NEW_VERSION,
        increment_level: VersionIncrement = VersionIncrement.PATCH,
    ) -> None:
        self.strategy = strategy
        self.increment_level = increment_level

    def versioned_path(self, original: Path, version: str | None) -> Path:
        if self.strategy == VersionWriteStrategy.OVERWRITE:
            return original
        ver = version or "1.0.0"
        stem = original.stem
        if not stem.endswith(f"_v{ver}"):
            stem = f"{stem}_v{ver}"
        return original.with_name(f"{stem}{original.suffix}")

    def auto_increment_version(self, target: Path) -> str:
        base_stem = target.stem
        ext = target.suffix
        parent = target.parent
        pattern = re.compile(
            re.escape(base_stem) + r"_v(\d+)\.(\d+)\.(\d+)" + re.escape(ext)
        )
        max_major, max_minor, max_patch = 0, 0, -1
        for path in parent.glob(f"{base_stem}*{ext}"):
            m = pattern.match(path.name)
            if m:
                major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if (major, minor, patch) > (max_major, max_minor, max_patch):
                    max_major, max_minor, max_patch = major, minor, patch
        if max_patch == -1:
            return "1.0.0"
        return self._increment_version(f"{max_major}.{max_minor}.{max_patch}")

    def _increment_version(self, version_str: str) -> str:
        try:
            parts = list(map(int, version_str.split('.')))
            if len(parts) != 3:
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid semantic version: {version_str}")

        if self.increment_level == VersionIncrement.MAJOR:
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif self.increment_level == VersionIncrement.MINOR:
            parts[1] += 1
            parts[2] = 0
        else:
            parts[2] += 1
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
