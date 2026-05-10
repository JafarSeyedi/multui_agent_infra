#!/usr/bin/env python3
"""
Count mypy errors per file and sort descending.
Usage: python count_mypy_errors.py < mypy_errors.txt
       or place the file as 'mypy_errors.txt' in the same directory.
"""

import re
import sys
from collections import Counter

def extract_file_path(line: str) -> str | None:
    """Extract file path from a mypy error line."""
    # Pattern: "path/to/file.py:123: error: ..."
    match = re.match(r'^([^:]+):\d+:', line)
    return match.group(1) if match else None

def main():
    # Read from mypy_errors.txt if exists, else from stdin
    filename = "mypy_errors.txt"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = sys.stdin.readlines()

    error_counts = Counter()
    for line in lines:
        file_path = extract_file_path(line)
        if file_path:
            error_counts[file_path] += 1

    # Sort by count descending, then by file name
    for file_path, count in sorted(error_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{count:5d} {file_path}")

if __name__ == "__main__":
    main()