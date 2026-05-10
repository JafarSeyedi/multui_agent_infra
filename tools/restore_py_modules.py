#!/usr/bin/env python3
"""
Emergency recovery script for corrupted virtual environment.

This script:
  1. Saves all currently installed packages (excluding pip, setuptools, wheel) to requirements.txt.
  2. Asks for confirmation, then uninstalls all of them.
  3. Reinstalls them from the freshly created requirements.txt.

Run this script from OUTSIDE the broken venv, or at least ensure it's saved in a safe place
because the uninstall step will remove everything, possibly including this script if it's inside the venv.
"""

import subprocess
import sys
import os
from pathlib import Path

REQUIREMENTS_FILE = "requirements_recovery.txt"

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def get_installed_packages() -> list[str]:
    """Return list of installed packages in 'name==version' format, excluding build essentials."""
    ret, out, err = run_command([sys.executable, "-m", "pip", "freeze"])
    if ret != 0:
        print(f"Error running pip freeze: {err}")
        sys.exit(1)

    # Keep only packages that are not pip, setuptools, wheel (you can add more if needed)
    excluded_prefixes = ("pip==", "setuptools==", "wheel==")
    packages = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(excluded_prefixes):
            continue
        # Also skip any line that is just a local path (editable installs)
        if line.startswith("-e ") or "@" in line:
            # Keep it if you want, but better to skip to avoid issues
            continue
        packages.append(line)
    return packages

def write_requirements(packages: list[str], filepath: Path) -> None:
    filepath.write_text("\n".join(packages) + "\n", encoding="utf-8")
    print(f"✅ {len(packages)} packages written to {filepath}")

def uninstall_all(packages: list[str]) -> None:
    if not packages:
        print("No packages to uninstall.")
        return

    print("⚠️  About to uninstall all packages (except pip/setuptools/wheel).")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() != "yes":
        print("❌ Aborted.")
        sys.exit(0)

    # Uninstall using pip uninstall -y -r requirements file is easiest
    tmp_req = Path("_tmp_uninstall_reqs.txt")
    tmp_req.write_text("\n".join(packages))
    ret, out, err = run_command([sys.executable, "-m", "pip", "uninstall", "-y", "-r", str(tmp_req)])
    tmp_req.unlink(missing_ok=True)
    if ret != 0:
        print(f"❌ Uninstall failed:\n{err}\n{out}")
        sys.exit(1)
    print("✅ All packages uninstalled.")

def reinstall_all(requirements_file: Path) -> None:
    print("🔄 Reinstalling packages...")
    ret, out, err = run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
    if ret != 0:
        print(f"❌ Reinstall failed:\n{err}\n{out}")
        sys.exit(1)
    print("✅ All packages reinstalled successfully.")

def main():
    # Ensure we are running in the intended environment
    print(f"Using Python: {sys.executable}")
    packages = get_installed_packages()
    if not packages:
        print("No packages to process. Exiting.")
        return

    req_path = Path(REQUIREMENTS_FILE)
    write_requirements(packages, req_path)
    uninstall_all(packages)
    reinstall_all(req_path)

if __name__ == "__main__":
    main()