from __future__ import annotations

import shutil
from pathlib import Path


def remove_pycache(root: Path) -> None:
    removed = 0

    for path in root.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            print(f"Removed: {path}")
            removed += 1

    print(f"\nTotal __pycache__ removed: {removed}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    remove_pycache(project_root)
