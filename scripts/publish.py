#!/usr/bin/env python3
"""
Two-command publish script (uv-friendly).

Commands to remember:
  uv run scripts/publish.py         -> publish to PyPI
  uv run scripts/publish.py --test  -> publish to TestPyPI + install-check

Expected .env at repo root (NOT committed):
  PYPI_TOKEN=pypi-...
  TESTPYPI_TOKEN=pypi-...
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
    """Run a command from repo root, echoing stdout/stderr (useful for twine)."""
    print(f"\n$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n")
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    return proc


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


def setup_twine_auth(target: str) -> None:
    """
    Map the correct token into Twine's expected env vars.
    - PyPI uses PYPI_TOKEN
    - TestPyPI uses TESTPYPI_TOKEN
    """
    if target == "pypi":
        token = os.environ.get("PYPI_TOKEN") or os.environ.get("PYPI_API_TOKEN")
        var_name = "PYPI_TOKEN"
    else:
        token = os.environ.get("TESTPYPI_TOKEN") or os.environ.get("TEST_PYPI_TOKEN")
        var_name = "TESTPYPI_TOKEN"

    if not token:
        raise SystemExit(
            f"Missing {var_name}.\n"
            "Your .env should contain:\n"
            "  PYPI_TOKEN=pypi-...\n"
            "  TESTPYPI_TOKEN=pypi-...\n"
        )

    # Twine token auth convention:
    os.environ["TWINE_USERNAME"] = "__token__"
    os.environ["TWINE_PASSWORD"] = token


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
    # Install build+twine into the uv-managed venv.
    run([sys.executable, "-m", "pip", "install", "-U", "build", "twine"])


def clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)


def build() -> None:
    run([sys.executable, "-m", "build"])


def twine_check() -> None:
    run(["twine", "check", "dist/*"])


def upload(target: str) -> None:
    # target: "pypi" or "testpypi"
    args = ["twine", "upload"]
    if target == "testpypi":
        args += ["--repository", "testpypi"]
    args += ["dist/*"]
    run(args)


def install_check_from_testpypi(package_name: str) -> None:
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
    p = argparse.ArgumentParser(
        description="Publish to PyPI by default, or to TestPyPI with --test."
    )
    p.add_argument(
        "--test",
        action="store_true",
        help="Publish to TestPyPI (and run install-check automatically).",
    )

    # Keep a few practical knobs (optional)
    p.add_argument("--skip-git-checks", action="store_true", help="Skip git safety checks")
    p.add_argument("--no-build", action="store_true", help="Skip build step (assumes dist/ is fresh)")
    p.add_argument("--no-clean", action="store_true", help="Do not delete dist/ before build")
    p.add_argument("--package-name", default="assetflow", help="Package name for TestPyPI install-check")
    p.add_argument("--dotenv", default=".env", help="Path to .env file (default: .env at repo root)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    target = "testpypi" if args.test else "pypi"

    # Load .env first
    load_dotenv((ROOT / args.dotenv).resolve())

    # Configure Twine auth depending on target
    setup_twine_auth(target)

    # Safety + tools
    git_checks(skip=args.skip_git_checks)
    ensure_tools()

    # Build
    if not args.no_build:
        if not args.no_clean:
            clean_dist()
        build()

    # Check + upload
    twine_check()

    if target == "testpypi":
        print("\n[info] Uploading to TestPyPI…")
        upload("testpypi")

        # Always do install-check for --test (no extra flag)
        print("\n[info] Install-check from TestPyPI…")
        install_check_from_testpypi(args.package_name)
    else:
        print("\n[info] Uploading to PyPI…")
        upload("pypi")

    print("\n[done] ✅ Publish completed.")


if __name__ == "__main__":
    main()
