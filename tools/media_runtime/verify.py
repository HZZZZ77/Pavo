#!/usr/bin/env python3
"""Validate Pavo's macOS media runtime artifacts."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("sources.json")
DIST_DIR = PROJECT_ROOT / "build" / "media-runtime" / "dist"
TOOLS_BIN = PROJECT_ROOT / "build" / "media-runtime" / "tools-venv" / "bin"
MINIMUM_MACOS = (13, 0)
FORBIDDEN_PATHS = ("/opt/homebrew", "/usr/local", "/opt/local")
ALLOWED_SYSTEM_DEPENDENCY_PREFIXES = ("/System/Library/", "/usr/lib/")


def output(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_version(value: str) -> tuple[int, int]:
    parts = value.split(".")
    return int(parts[0]), int(parts[1])


def read_rpaths(path: Path) -> list[str]:
    lines = output(["otool", "-l", str(path)]).splitlines()
    rpaths = []
    for index, line in enumerate(lines):
        if line.strip() != "cmd LC_RPATH":
            continue
        for detail in lines[index + 1 : index + 5]:
            value = detail.strip()
            if value.startswith("path "):
                rpaths.append(value.removeprefix("path ").split(" (offset", 1)[0])
                break
    return rpaths


def inspect_macho(
    path: Path,
    *,
    allowed_rpath_dependencies: tuple[str, ...] = (),
) -> dict:
    file_output = output(["file", str(path)])
    if "arm64" not in file_output or "x86_64" in file_output:
        raise RuntimeError(f"{path.name} is not arm64-only: {file_output}")

    build_output = output(["vtool", "-show-build", str(path)])
    match = re.search(r"\bminos\s+([0-9.]+)", build_output)
    if not match:
        raise RuntimeError(f"Unable to read minimum macOS version from {path}")
    minimum = match.group(1)
    if parse_version(minimum) != MINIMUM_MACOS:
        raise RuntimeError(f"{path.name} requires macOS {minimum}, expected exactly 13.0")

    dependencies = output(["otool", "-L", str(path)]).splitlines()[1:]
    dependency_paths = [line.strip().split(" (", 1)[0] for line in dependencies]
    rpaths = read_rpaths(path)
    forbidden = [
        value
        for value in dependency_paths + rpaths
        if any(marker in value for marker in FORBIDDEN_PATHS)
    ]
    if forbidden:
        raise RuntimeError(f"{path.name} contains forbidden load paths: {forbidden}")
    if rpaths:
        raise RuntimeError(f"{path.name} contains unexpected LC_RPATH entries: {rpaths}")
    unexpected = [
        dependency
        for dependency in dependency_paths
        if dependency not in allowed_rpath_dependencies
        and not dependency.startswith(ALLOWED_SYSTEM_DEPENDENCY_PREFIXES)
    ]
    if unexpected:
        raise RuntimeError(f"{path.name} contains non-system dependencies: {unexpected}")

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "sha256": sha256(path),
        "size": path.stat().st_size,
        "file": file_output,
        "minimum_macos": minimum,
        "dependencies": dependency_paths,
        "rpaths": rpaths,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Write the generated artifact manifest into the dist directory.",
    )
    args = parser.parse_args()

    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise RuntimeError("Verification requires an arm64 macOS host.")

    ffmpeg = DIST_DIR / "bin" / "ffmpeg"
    libmpv = DIST_DIR / "lib" / "libmpv.2.dylib"
    for artifact in (ffmpeg, libmpv):
        if not artifact.is_file():
            raise RuntimeError(f"Missing artifact: {artifact}")

    libmpv_id = output(["otool", "-D", str(libmpv)]).splitlines()
    if len(libmpv_id) < 2 or libmpv_id[1] != "@rpath/libmpv.2.dylib":
        raise RuntimeError(f"Unexpected libmpv install name: {libmpv_id}")
    libmpv_handle = ctypes.CDLL(str(libmpv))
    libmpv_handle.mpv_client_api_version.restype = ctypes.c_ulong
    client_api_version = libmpv_handle.mpv_client_api_version()

    with CONFIG_PATH.open(encoding="utf-8") as stream:
        source_config = json.load(stream)

    manifest = {
        "schema_version": 1,
        "target": source_config["target"],
        "build_tools": source_config["build_tools"],
        "observed_build_host": {
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "macos_sdk": output(["xcrun", "--show-sdk-version"]),
            "clang": output(["clang", "--version"]).splitlines()[0],
            "meson": output([str(TOOLS_BIN / "meson"), "--version"]),
            "ninja": output([str(TOOLS_BIN / "ninja"), "--version"]),
        },
        "build_configuration": source_config["build_configuration"],
        "patches": source_config["patches"],
        "sources": source_config["sources"],
        "artifacts": {
            "ffmpeg": inspect_macho(ffmpeg),
            "libmpv": inspect_macho(
                libmpv,
                allowed_rpath_dependencies=("@rpath/libmpv.2.dylib",),
            ),
        },
        "licenses": sorted(
            str(path.relative_to(DIST_DIR))
            for path in (DIST_DIR / "licenses").rglob("*")
            if path.is_file()
        ),
    }
    manifest["artifacts"]["libmpv"]["install_name"] = libmpv_id[1]
    manifest["artifacts"]["libmpv"]["client_api_version"] = (
        f"{client_api_version >> 16}.{client_api_version & 0xFFFF}"
    )

    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    print(rendered)
    if args.write_manifest:
        manifest_path = DIST_DIR / "media-runtime-manifest.json"
        manifest_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
