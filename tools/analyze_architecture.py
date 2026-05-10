# tools/analyze_architecture.py
"""
اجرا:
    python tools/analyze_architecture.py
خروجی:
    architecture.md در ریشه پروژه
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path


@dataclass
class ClassInfo:
    name: str
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    line: int = 0


@dataclass
class FileInfo:
    path: Path
    relative: str
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    lines: int = 0  # تعداد خطوط کد


class ASTParser:
    def parse(self, file_path: Path, root: Path) -> FileInfo:
        info = FileInfo(
            path=file_path,
            relative=str(file_path.relative_to(root)),
        )
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            # شمارش خطوط
            info.lines = len(source.splitlines())

            tree = ast.parse(source, filename=str(file_path))
            self._extract(tree, info)
        except SyntaxError as e:
            info.errors.append(f"SyntaxError: {e}")
        except Exception as e:
            info.errors.append(f"ParseError: {e}")
        return info

    def _extract(self, tree: ast.Module, info: FileInfo) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                info.classes.append(self._parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._is_top_level(tree, node):
                    info.functions.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    info.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [a.name for a in node.names]
                info.imports.append(f"{module} → {', '.join(names)}")

    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        bases = [self._name(b) for b in node.bases]
        methods = [
            n.name
            for n in ast.walk(node)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.col_offset > node.col_offset
        ]
        decorators = [self._name(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node)
        return ClassInfo(
            name=node.name,
            bases=bases,
            methods=methods,
            decorators=decorators,
            docstring=docstring,
            line=node.lineno,
        )

    @staticmethod
    def _is_top_level(tree: ast.Module, node: ast.AST) -> bool:
        return node in tree.body

    @staticmethod
    def _name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{ASTParser._name(node.value)}.{node.attr}"
        return ast.unparse(node)


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".tox",
    "site-packages",
}


class ProjectCollector:
    def __init__(self, root: Path):
        self.root = root
        self.parser = ASTParser()

    def collect(self) -> list[FileInfo]:
        results: list[FileInfo] = []
        for py_file in sorted(self._iter_python_files()):
            results.append(self.parser.parse(py_file, self.root))
        return results

    def _iter_python_files(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [
                d
                for d in dirnames
                if d not in SKIP_DIRS and not d.startswith(".")
            ]
            for filename in filenames:
                if filename.endswith(".py"):
                    yield Path(dirpath) / filename


class ArchitectureAnalyzer:
    def __init__(self, files: list[FileInfo]):
        self.files = files

    def folder_structure(self) -> str:
        """ساختار فولدرها بدون فایل‌ها"""
        dirs: set[str] = set()
        for f in self.files:
            parts = Path(f.relative).parts
            for i in range(1, len(parts)):
                dirs.add(str(Path(*parts[:i])))

        if not dirs:
            return "```\n📦 project/\n  (فولدری یافت نشد)\n```"

        lines = ["```", "📦 project/"]
        all_dirs = sorted(dirs)

        def get_depth(path: str) -> int:
            return len(Path(path).parts)

        def get_children(parent: str) -> list[str]:
            if parent == "":
                return [d for d in all_dirs if get_depth(d) == 1]
            return [d for d in all_dirs if str(Path(d).parent) == parent]

        def render(path: str, prefix: str):
            children = sorted(get_children(path))
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}📁 {Path(child).name}/")
                extension = "    " if is_last else "│   "
                render(child, prefix + extension)

        render("", "  ")
        lines.append("```")
        return "\n".join(lines)

    def folder_tree(self) -> str:
        """ساختار کامل فولدرها و فایل‌ها با نمایش تعداد خطوط"""
        dirs: set[str] = set()
        for f in self.files:
            parts = Path(f.relative).parts
            for i in range(1, len(parts)):
                dirs.add(str(Path(*parts[:i])))

        if not dirs and not self.files:
            return "```\n📦 project/\n  (خالی)\n```"

        lines = ["```", "📦 project/"]
        all_dirs = sorted(dirs)

        def get_depth(path: str) -> int:
            return len(Path(path).parts)

        def get_child_dirs(parent: str) -> list[str]:
            if parent == "":
                return [d for d in all_dirs if get_depth(d) == 1]
            return [d for d in all_dirs if str(Path(d).parent) == parent]

        def get_child_files(parent: str) -> list[FileInfo]:
            return [f for f in self.files if str(Path(f.relative).parent) == (parent or ".")]

        def render(path: str, prefix: str):
            child_dirs = sorted(get_child_dirs(path))
            child_files = sorted(get_child_files(path), key=lambda x: x.relative)

            items = len(child_dirs) + len(child_files)
            idx = 0

            for child_dir in child_dirs:
                idx += 1
                is_last = idx == items
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}📁 {Path(child_dir).name}/")
                extension = "    " if is_last else "│   "
                render(child_dir, prefix + extension)

            for child_file in child_files:
                idx += 1
                is_last = idx == items
                connector = "└── " if is_last else "├── "
                icon = "⚠️" if child_file.errors else "📄"
                # نمایش تعداد خطوط به همراه نام فایل
                lines.append(f"{prefix}{connector}{icon} {Path(child_file.relative).name} [{child_file.lines} lines]")

        render("", "  ")
        lines.append("```")
        return "\n".join(lines)

    def classes_table(self) -> str:
        rows: list[tuple[str, str, str, str]] = []
        for f in self.files:
            for cls in f.classes:
                methods_str = ", ".join(cls.methods[:6])
                if len(cls.methods) > 6:
                    methods_str += " ..."
                rows.append(
                    (
                        f.relative,
                        cls.name,
                        ", ".join(cls.bases) or "—",
                        methods_str,
                    )
                )
        if not rows:
            return "_کلاسی یافت نشد_"

        lines = [
            "| فایل | کلاس | والدین | متدها |",
            "|------|------|--------|-------|",
        ]
        for row in rows:
            lines.append(
                f"| `{row[0]}` | `{row[1]}` | `{row[2]}` | `{row[3]}` |"
            )
        return "\n".join(lines)

    def inheritance_map(self) -> str:
        lines = ["```"]
        found = False
        for f in self.files:
            for cls in f.classes:
                if cls.bases:
                    found = True
                for base in cls.bases:
                    lines.append(f"{base}  →  {cls.name}")
        if not found:
            lines.append("(وراثتی یافت نشد)")
        lines.append("```")
        return "\n".join(lines)

    def abstract_classes(self) -> str:
        items: list[str] = []
        for f in self.files:
            for cls in f.classes:
                is_abc = (
                    "ABC" in cls.bases
                    or "abc.ABC" in cls.bases
                    or any("abstractmethod" in str(d) for d in cls.decorators)
                )

                if is_abc:
                    methods_joined = "`, `".join(cls.methods)
                    items.append(
                        f"- **`{cls.name}`** (`{f.relative}`)\n"
                        f"  - متدها: `{methods_joined}`"
                    )
        return "\n".join(items) if items else "_کلاس Abstract یافت نشد_"

    def potential_issues(self) -> str:
        issues: list[str] = []

        parse_errors = [f for f in self.files if f.errors]
        if parse_errors:
            issues.append("### ⚠️ خطاهای Parse")
            for f in parse_errors:
                for e in f.errors:
                    issues.append(f"- `{f.relative}`: {e}")

        big_classes = [
            (f.relative, cls)
            for f in self.files
            for cls in f.classes
            if len(cls.methods) > 15
        ]
        if big_classes:
            issues.append(
                "\n### 🔴 کلاس‌های بزرگ "
                "(بیش از ۱۵ متد — نشانه نقض SRP)"
            )
            for rel, cls in big_classes:
                issues.append(
                    f"- `{cls.name}` در `{rel}` — {len(cls.methods)} متد"
                )

        empty = [
            f
            for f in self.files
            if not f.classes and not f.functions and not f.errors and Path(f.relative).name != "__init__.py"
        ]
        if empty:
            issues.append("\n### 🟡 فایل‌های خالی یا فقط شامل import")
            for f in empty:
                issues.append(f"- `{f.relative}` [{f.lines} lines]")

        keywords = ("backend", "bus", "strategy", "handler", "service")
        no_base = [
            (f.relative, cls)
            for f in self.files
            for cls in f.classes
            if not cls.bases and any(k in cls.name.lower() for k in keywords)
        ]
        if no_base:
            issues.append(
                "\n### 🟠 کلاس‌های بدون Base Class "
                "(احتمال عدم رعایت interface مشترک)"
            )
            for rel, cls in no_base:
                issues.append(f"- `{cls.name}` در `{rel}`")

        return "\n".join(issues) if issues else "✅ مشکل آشکاری یافت نشد."

    def summary_stats(self) -> dict[str, int]:
        total_lines = sum(f.lines for f in self.files)
        return {
            "فایل‌های Python": len(self.files),
            "کلاس‌ها": sum(len(f.classes) for f in self.files),
            "توابع سطح بالا": sum(len(f.functions) for f in self.files),
            "فایل‌های با خطا": sum(1 for f in self.files if f.errors),
            "مجموع خطوط کد": total_lines,
        }


class MarkdownRenderer:
    def __init__(self, root: Path, files: list[FileInfo]):
        self.root = root
        self.analyzer = ArchitectureAnalyzer(files)

    def render(self) -> str:
        stats = self.analyzer.summary_stats()
        stats_table = "\n".join(f"| {k} | {v} |" for k, v in stats.items())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        parts = [
            "# 📐 Architecture Report\n",
            "> تولید شده توسط `tools/analyze_architecture.py`  ",
            f"> تاریخ: {timestamp}  ",
            "---\n",
            "## 📊 آمار کلی\n",
            "| معیار | مقدار |",
            "|-------|-------|",
            stats_table,
            "\n---\n",
            "## 📂 ساختار فولدرها\n",
            self.analyzer.folder_structure(),
            "\n---\n",
            "## 🗂️ ساختار کامل (فولدرها + فایل‌ها + تعداد خطوط)\n",
            self.analyzer.folder_tree(),
            "\n---\n",
            "## 🏛️ کلاس‌ها و وراثت\n",
            "### جدول کامل کلاس‌ها\n",
            self.analyzer.classes_table(),
            "\n---\n",
            "### نقشه وراثت\n",
            self.analyzer.inheritance_map(),
            "\n---\n",
            "### کلاس‌های Abstract / Interface\n",
            self.analyzer.abstract_classes(),
            "\n---\n",
            "## 🔍 تحلیل مشکلات احتمالی\n",
            self.analyzer.potential_issues(),
            "\n---\n",
            "## 📝 یادداشت\n",
            "این گزارش به صورت **استاتیک** (تحلیل AST) تولید شده است.  ",
            "برای تحلیل runtime و dependency injection، "
            "ابزار تکمیلی لازم است.\n",
        ]

        return "\n".join(parts)


def find_project_root() -> Path:
    script_dir = Path(__file__).parent
    if script_dir.name == "tools":
        return script_dir.parent
    return Path.cwd()


def main():
    root = find_project_root()
    output = root / "architecture.md"

    print(f"🔍 اسکن پروژه: {root}")

    collector = ProjectCollector(root)
    files = collector.collect()

    total_lines = sum(f.lines for f in files)
    print(f"✅ {len(files)} فایل Python یافت شد. مجموع خطوط: {total_lines}")

    renderer = MarkdownRenderer(root, files)
    content = renderer.render()

    output.write_text(content, encoding="utf-8")
    print(f"📄 گزارش نوشته شد: {output}")


if __name__ == "__main__":
    main()
