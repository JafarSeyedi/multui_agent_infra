"""
Ultra-Pro __init__.py Generator
Enterprise-grade API surface builder.

Features:
- Smart export filtering
- Enum / TypedDict / dataclass / Pydantic detection
- Constant detection
- Deprecated filtering
- Utility function filtering
- Versioned API support
- Deterministic output
- Optional star-import support
"""
import ast
from pathlib import Path

# ==========================================================
# CONFIG
# ==========================================================

PACKAGE_API_STAR_IMPORT = False
INCLUDE_CONSTANTS = True
API_VERSION = None  # e.g. "v1" to export only matching version
REQUIRE_PUBLIC_FLAG = False  # if True, requires __public_api__ = True

UTILITY_PREFIXES = (
    "parse_",
    "build_",
    "validate_",
    "create_",
    "helper_",
    "test_",
)

EXCLUDED_NAMES = {"main", "cli", "run"}

# ==========================================================
# AST DETECTION HELPERS
# ==========================================================


def has_decorator(node: ast.ClassDef, name: str) -> bool:
    for deco in node.decorator_list:
        if isinstance(deco, ast.Name) and deco.id == name:
            return True
        if isinstance(deco, ast.Attribute) and deco.attr == name:
            return True
    return False


def is_enum(node: ast.ClassDef) -> bool:
    return any(
        isinstance(base, ast.Name) and base.id == "Enum"
        or isinstance(base, ast.Attribute) and base.attr == "Enum"
        for base in node.bases
    )


def is_typeddict(node: ast.ClassDef) -> bool:
    return any(
        isinstance(base, ast.Name) and base.id == "TypedDict"
        or isinstance(base, ast.Attribute) and base.attr == "TypedDict"
        for base in node.bases
    )


def is_pydantic_model(node: ast.ClassDef) -> bool:
    return any(
        isinstance(base, ast.Name) and base.id == "BaseModel"
        or isinstance(base, ast.Attribute) and base.attr == "BaseModel"
        for base in node.bases
    )


def is_dataclass(node: ast.ClassDef) -> bool:
    return has_decorator(node, "dataclass")


# ==========================================================
# FILTERING LOGIC
# ==========================================================


def is_constant(node: ast.Assign) -> list[str]:
    names = []
    for target in node.targets:
        if isinstance(target, ast.Name):
            if target.id.isupper():
                names.append(target.id)
    return names


def is_deprecated(node: ast.AST) -> bool:
    if isinstance(node, ast.ClassDef):
        return has_decorator(node, "deprecated")
    return False


def has_public_flag(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__public_api__":
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        return True
    return False


def matches_version(tree: ast.Module) -> bool:
    if API_VERSION is None:
        return True
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__api_version__":
                    if isinstance(node.value, ast.Constant):
                        return node.value.value == API_VERSION
    return False


# ==========================================================
# EXPORT EXTRACTION
# ==========================================================


def extract_exports(py_file: Path) -> list[str]:
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return []

    if REQUIRE_PUBLIC_FLAG and not has_public_flag(tree):
        return []

    if not matches_version(tree):
        return []

    exports = []

    for node in tree.body:

        # ----- Class -----
        if isinstance(node, ast.ClassDef):
            name = node.name

            if name.startswith("_") or name in EXCLUDED_NAMES:
                continue
            if is_deprecated(node):
                continue

            exports.append(name)

        # ----- Function -----
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name

            if name.startswith("_"):
                continue
            if name in EXCLUDED_NAMES:
                continue
            if name.startswith(UTILITY_PREFIXES):
                continue

            exports.append(name)

        # ----- Constant -----
        elif INCLUDE_CONSTANTS and isinstance(node, ast.Assign):
            exports.extend(is_constant(node))

    return sorted(set(exports))


# ==========================================================
# INIT GENERATOR
# ==========================================================


def generate_init(folder: Path, dry_run=False):
    modules = {}

    for py_file in sorted(folder.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        names = extract_exports(py_file)
        if names:
            modules[py_file.stem] = names

    if not modules:
        return None

    lines = []
    all_names = []

    for module, names in modules.items():
        lines.append(f"from .{module} import {', '.join(names)}")
        if PACKAGE_API_STAR_IMPORT:
            lines.append(f"from .{module} import *")
        lines.append("")
        all_names.extend(names)

    all_names_sorted = sorted(set(all_names))
    lines.append("__all__ = [")
    for name in all_names_sorted:
        lines.append(f'    "{name}",')
    lines.append("]")
    lines.append("")

    content = "\n".join(lines)

    if dry_run:
        print(content)
        return content

    (folder / "__init__.py").write_text(content, encoding="utf-8")
    print(f"✅ wrote {folder / '__init__.py'}")
    return content


# ==========================================================
# CLI
# ==========================================================


def run(root: str, dry_run=False):
    root_path = Path(root).resolve()
    count = 0

    for folder in sorted(root_path.rglob("*")):
        if folder.is_dir():
            result = generate_init(folder, dry_run=dry_run)
            if result:
                count += 1

    print(f"\nGenerated {count} package APIs")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ultra-Pro API generator")
    parser.add_argument("path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
