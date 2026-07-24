#!/usr/bin/env python3
"""Project health checks for Pavo.

This script is intentionally lightweight:
- standard library only
- no imports from src/
- no writes to the project

It checks repository shape and local tool availability so maintainers can spot
environment problems before working on playback, packaging, or UI changes.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 11)

CORE_SOURCE_FILES = (
    Path("src/main.py"),
    Path("src/engine.py"),
    Path("src/video_widget.py"),
    Path("src/components/hud_panel.py"),
)

EXPECTED_REQUIREMENTS = (
    "PySide6",
    "python-mpv",
)

HOMEBREW_FFMPEG_PATHS = (
    Path("/opt/homebrew/bin/ffmpeg"),
    Path("/usr/local/bin/ffmpeg"),
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def ok(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "OK", detail)


def warn(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "WARN", detail)


def fail(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "FAIL", detail)


def check_python_version() -> CheckResult:
    current = sys.version_info[:3]
    current_text = ".".join(str(part) for part in current)
    minimum_text = ".".join(str(part) for part in MIN_PYTHON)

    if current >= MIN_PYTHON:
        return ok("Python version", f"{current_text} >= {minimum_text}")

    return fail("Python version", f"{current_text} < {minimum_text}")


def check_src_directory() -> CheckResult:
    src_dir = PROJECT_ROOT / "src"
    if src_dir.is_dir():
        return ok("src directory", str(src_dir.relative_to(PROJECT_ROOT)))
    return fail("src directory", "missing src/")


def check_core_source_files() -> CheckResult:
    missing = [str(path) for path in CORE_SOURCE_FILES if not (PROJECT_ROOT / path).is_file()]
    if not missing:
        return ok("core source files", f"{len(CORE_SOURCE_FILES)} files present")
    return fail("core source files", "missing: " + ", ".join(missing))


def check_requirements_file() -> CheckResult:
    requirements_path = PROJECT_ROOT / "requirements.txt"
    if not requirements_path.is_file():
        return fail("requirements.txt", "missing requirements.txt")

    try:
        lines = requirements_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return fail("requirements.txt", f"could not read file: {exc}")

    normalized = {line.strip().split("==", 1)[0] for line in lines if line.strip() and not line.startswith("#")}
    missing = [name for name in EXPECTED_REQUIREMENTS if name not in normalized]

    if missing:
        return warn("requirements.txt", "missing expected entries: " + ", ".join(missing))

    return ok("requirements.txt", "expected dependencies listed")


def run_git_status() -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def check_git_status() -> CheckResult:
    if not shutil.which("git"):
        return warn("git status", "git executable not found")

    returncode, stdout, stderr = run_git_status()
    if returncode != 0:
        detail = stderr or stdout or "git status failed"
        return warn("git status", detail)

    lines = stdout.splitlines()
    branch = lines[0] if lines else "unknown branch"
    changes = lines[1:]

    if changes:
        return warn("git status", f"{branch}; {len(changes)} changed or untracked entries")

    return ok("git status", f"{branch}; working tree clean")


def find_ffmpeg() -> list[Path]:
    found: list[Path] = []

    bundled = PROJECT_ROOT / "ffmpeg"
    if bundled.exists():
        found.append(bundled)

    system_path = shutil.which("ffmpeg")
    if system_path:
        found.append(Path(system_path))

    for path in HOMEBREW_FFMPEG_PATHS:
        if path.exists():
            found.append(path)

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in found:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)

    return unique


def check_ffmpeg_availability() -> CheckResult:
    candidates = find_ffmpeg()
    if not candidates:
        return warn("ffmpeg availability", "ffmpeg not found; thumbnail preview may be unavailable")

    executable = [path for path in candidates if path.is_file() and path.stat().st_mode & 0o111]
    if executable:
        shown = ", ".join(str(path) for path in executable)
        return ok("ffmpeg availability", shown)

    shown = ", ".join(str(path) for path in candidates)
    return warn("ffmpeg availability", "found but not executable: " + shown)


def collect_results() -> list[CheckResult]:
    return [
        check_python_version(),
        check_src_directory(),
        check_core_source_files(),
        check_requirements_file(),
        check_git_status(),
        check_ffmpeg_availability(),
    ]


def print_results(results: list[CheckResult]) -> None:
    print("Pavo Health Check")
    print("=" * 17)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Platform: {platform.platform()}")
    print()

    width = max(len(result.name) for result in results)
    for result in results:
        print(f"[{result.status:<4}] {result.name:<{width}}  {result.detail}")

    print()
    failures = sum(1 for result in results if result.status == "FAIL")
    warnings = sum(1 for result in results if result.status == "WARN")
    print(f"Summary: {failures} failure(s), {warnings} warning(s)")


def main() -> int:
    results = collect_results()
    print_results(results)
    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
