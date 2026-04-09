"""
tools/generate_inits.py
Generates __init__.py files for all packages in the project.
Exports public classes and functions found in each module.
"""

import ast
from pathlib import Path


def get_public_names(py_file: Path) -> list[str]:
    """Extract public class and function names from a Python file."""
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    names = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.append(node.name)

    return names


def generate_init(folder: Path, dry_run: bool = False) -> str | None:
    """Generate __init__.py content for a folder."""
    lines = []

    for py_file in sorted(folder.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        names = get_public_names(py_file)
        if not names:
            continue

        module = py_file.stem
        names_str = ", ".join(names)
        lines.append(f"from .{module} import {names_str}")

    if not lines:
        return None

    content = "\n".join(lines) + "\n"

    init_file = folder / "__init__.py"

    if dry_run:
        print(f"\n{'='*50}")
        print(f"📁 {init_file}")
        print(content)
        return content

    # Backup existing __init__.py if it has content
    if init_file.exists():
        existing = init_file.read_text(encoding="utf-8").strip()
        if existing and existing != content.strip():
            backup = init_file.with_suffix(".py.bak")
            backup.write_text(existing, encoding="utf-8")
            print(f"  ⚠️  Backed up existing {init_file.name} → {backup.name}")

    init_file.write_text(content, encoding="utf-8")
    print(f"  ✅ {init_file}")
    return content


def is_package(folder: Path) -> bool:
    """A folder is a package if it contains .py files (excluding __init__.py itself)."""
    return any(
        f for f in folder.glob("*.py")
        if not f.name.startswith("_")
    )


def run(root: str, dry_run: bool = False):
    root_path = Path(root).resolve()

    # Folders to skip
    skip = {"__pycache__", ".git", ".venv", "venv", "node_modules", "dist", "build"}

    print(f"{'[DRY RUN] ' if dry_run else ''}Scanning: {root_path}\n")

    count = 0
    for folder in sorted(root_path.rglob("*")):
        if not folder.is_dir():
            continue
        if any(part in skip for part in folder.parts):
            continue
        if not is_package(folder):
            continue

        result = generate_init(folder, dry_run=dry_run)
        if result:
            count += 1

    print(f"\n{'Would generate' if dry_run else 'Generated'} {count} __init__.py file(s)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate __init__.py files for Python packages")
    parser.add_argument("path", help="Root path of the project")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    run(args.path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
