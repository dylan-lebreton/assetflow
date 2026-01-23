#!/usr/bin/env python3
"""
Build & publish this package to TestPyPI or PyPI using uv + build + twine.

Usage:
  uv run scripts/publish.py --test
  uv run scripts/publish.py --test --install-check
  uv run scripts/publish.py --pypi

Environment (recommended via a local .env file, NOT committed):
  Option 1 (simplest): only token
    PYPI_TOKEN=pypi-xxxxxxxxxxxxxxxxxxxxxxxx

  Option 2 (classic twine):
    TWINE_USERNAME=__token__
    TWINE_PASSWORD=pypi-xxxxxxxxxxxxxxxxxxxxxxxx

Notes:
- PyPI is immutable per version: once uploaded, you can't re-upload the same version.
- This script refuses to publish if git repo is dirty or branch isn't main/master
  (unless --skip-git-checks).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT, check=check)


def capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT).decode().strip()


def load_dotenv(dotenv_path: Path) -> None:
    """Tiny .env loader (no external deps)."""
    if not dotenv_path.exists():
        return

    for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Don't override existing env vars (useful for CI)
        os.environ.setdefault(key, value)


def ensure_twine_env() -> None:
    """
    Accept either:
      - PYPI_TOKEN (preferred)
      - or TWINE_USERNAME/TWINE_PASSWORD
    """
    token = os.environ.get("PYPI_TOKEN") or os.environ.get("PYPI_API_TOKEN")
    if token:
        os.environ.setdefault("TWINE_USERNAME", "__token__")
        os.environ.setdefault("TWINE_PASSWORD", token)

    user = os.environ.get("TWINE_USERNAME")
    pwd = os.environ.get("TWINE_PASSWORD")
    if not user or not pwd:
        raise SystemExit(
            "Missing credentials.\n"
            "Provide either:\n"
            "  PYPI_TOKEN=pypi-...   (recommended)\n"
            "or:\n"
            "  TWINE_USERNAME=__token__\n"
            "  TWINE_PASSWORD=pypi-...\n"
            "\nTip: put it in a local .env (and add .env to .gitignore)."
        )


def git_checks(skip: bool) -> None:
    if skip:
        print("\n[info] Skipping git checks.")
        return

    try:
        capture(["git", "rev-parse", "--is-inside-work-tree"])
    except Exception as e:
        raise SystemExit(f"Not a git repository (or git not available): {e}")

    branch = capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch not in {"main", "master"}:
        raise SystemExit(
            f"Refusing to publish from branch '{branch}'. "
            "Switch to 'main'/'master' or use --skip-git-checks."
        )

    status = capture(["git", "status", "--porcelain"])
    if status:
        raise SystemExit(
            "Working tree is not clean. Commit/stash your changes before publishing.\n"
            f"git status --porcelain:\n{status}"
        )

    print(f"\n[ok] Git checks passed (branch={branch}, clean working tree).")


def ensure_tools() -> None:
    # In a uv venv, this installs build+twine into the environment.
    run([sys.executable, "-m", "pip", "install", "-U", "build", "twine"])


def clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)


def build() -> None:
    run([sys.executable, "-m", "build"])


def twine_check() -> None:
    run(["twine", "check", "dist/*"])


def upload(repository: str) -> None:
    # repository: "pypi" or "testpypi"
    args = ["twine", "upload"]
    if repository == "testpypi":
        args += ["--repository", "testpypi"]
    args += ["dist/*"]
    run(args)


def install_check_testpypi(package_name: str) -> None:
    # Sanity install from TestPyPI, but allow deps from PyPI via extra-index-url.
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            package_name,
            "-i",
            "https://test.pypi.org/simple/",
            "--extra-index-url",
            "https://pypi.org/simple",
        ]
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build & publish the package to (Test)PyPI.")
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--test", action="store_true", help="Upload to TestPyPI")
    target.add_argument("--pypi", action="store_true", help="Upload to PyPI")

    p.add_argument(
        "--skip-git-checks",
        action="store_true",
        help="Skip branch/clean working tree checks",
    )
    p.add_argument(
        "--no-build",
        action="store_true",
        help="Skip building (assumes dist/ already contains fresh artifacts)",
    )
    p.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not delete dist/ before building",
    )
    p.add_argument(
        "--install-check",
        action="store_true",
        help="After uploading to TestPyPI, try installing the package from TestPyPI",
    )
    p.add_argument(
        "--package-name",
        default="assetflow",
        help="Package name to install-check (default: assetflow)",
    )
    p.add_argument(
        "--dotenv",
        default=".env",
        help="Path to a .env file (default: .env at repo root)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Load .env first (if present)
    dotenv_path = (ROOT / args.dotenv).resolve()
    load_dotenv(dotenv_path)

    # Map PYPI_TOKEN -> TWINE_USERNAME/TWINE_PASSWORD
    ensure_twine_env()

    git_checks(skip=args.skip_git_checks)
    ensure_tools()

    if not args.no_build:
        if not args.no_clean:
            clean_dist()
        build()

    twine_check()

    if args.test:
        print("\n[info] Uploading to TestPyPI…")
        upload("testpypi")
        if args.install_check:
            print("\n[info] Install-check from TestPyPI…")
            install_check_testpypi(args.package_name)
    else:
        print("\n[info] Uploading to PyPI…")
        upload("pypi")

    print("\n[done] ✅ Publish completed.")


if __name__ == "__main__":
    main()
