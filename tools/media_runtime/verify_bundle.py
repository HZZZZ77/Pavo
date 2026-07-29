#!/usr/bin/env python3
"""Validate Pavo.app's bundled media runtime and Mach-O dependencies."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNTIME = PROJECT_ROOT / "build" / "media-runtime" / "dist"
DEFAULT_APP = PROJECT_ROOT / "dist" / "Pavo.app"
FORBIDDEN_PATHS = ("/opt/homebrew", "/usr/local", "/opt/local")
ALLOWED_ABSOLUTE_DEPENDENCY_PREFIXES = ("/System/Library/", "/usr/lib/")
TARGET_MINIMUM_MACOS = (13, 0)


def output(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_version(value: str) -> tuple[int, int]:
    major, minor, *_ = value.split(".")
    return int(major), int(minor)


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


def inspect_macho(path: Path) -> dict:
    file_output = output(["file", str(path)])
    if "arm64" not in file_output or "x86_64" in file_output:
        raise RuntimeError(f"{path} is not arm64-only: {file_output}")

    build_output = output(["vtool", "-show-build", str(path)])
    minimum_versions = re.findall(r"\bminos\s+([0-9.]+)", build_output)
    if not minimum_versions:
        raise RuntimeError(f"Unable to read minimum macOS version from {path}")
    deployment_target_violations = [
        version
        for version in minimum_versions
        if parse_version(version) > TARGET_MINIMUM_MACOS
    ]

    dependency_lines = output(["otool", "-L", str(path)]).splitlines()[1:]
    dependencies = [line.strip().split(" (", 1)[0] for line in dependency_lines]
    rpaths = read_rpaths(path)
    load_paths = dependencies + rpaths
    forbidden = [
        value
        for value in load_paths
        if any(marker in value for marker in FORBIDDEN_PATHS)
    ]
    if forbidden:
        raise RuntimeError(f"{path} contains forbidden load paths: {forbidden}")

    unexpected_absolute = [
        dependency
        for dependency in dependencies
        if dependency.startswith("/")
        and not dependency.startswith(ALLOWED_ABSOLUTE_DEPENDENCY_PREFIXES)
    ]
    if unexpected_absolute:
        raise RuntimeError(
            f"{path} contains non-system absolute dependencies: {unexpected_absolute}"
        )

    return {
        "path": str(path),
        "minimum_macos": minimum_versions,
        "deployment_target_violations": deployment_target_violations,
        "dependencies": dependencies,
        "rpaths": rpaths,
    }


def collect_macho_files(app_path: Path) -> list[Path]:
    macho_files = []
    for path in app_path.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        if "Mach-O" in output(["file", "-b", str(path)]):
            macho_files.append(path)
    return sorted(macho_files)


def validate_runtime_provenance(
    manifest: dict,
    bundled_ffmpeg: Path,
    bundled_libmpv: Path,
) -> dict:
    source_artifacts = {
        "ffmpeg": SOURCE_RUNTIME / "bin" / "ffmpeg",
        "libmpv": SOURCE_RUNTIME / "lib" / "libmpv.2.dylib",
    }
    bundled_artifacts = {
        "ffmpeg": bundled_ffmpeg,
        "libmpv": bundled_libmpv,
    }
    results = {}
    for name, source_path in source_artifacts.items():
        if not source_path.is_file():
            raise RuntimeError(f"Phase 2A source artifact is missing: {source_path}")
        expected = manifest["artifacts"][name]["sha256"]
        source_hash = sha256(source_path)
        if source_hash != expected:
            raise RuntimeError(
                f"Phase 2A source SHA-256 mismatch for {name}: "
                f"expected {expected}, got {source_hash}"
            )
        results[name] = {
            "phase2a_sha256": source_hash,
            "bundled_sha256": sha256(bundled_artifacts[name]),
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "app",
        nargs="?",
        type=Path,
        default=DEFAULT_APP,
        help="Path to Pavo.app (default: dist/Pavo.app).",
    )
    args = parser.parse_args()
    app_path = args.app.resolve()
    contents = app_path / "Contents"
    frameworks = contents / "Frameworks"
    resources_runtime = contents / "Resources" / "media-runtime"

    required_paths = {
        "main executable": contents / "MacOS" / "Pavo",
        "bundled FFmpeg": frameworks / "ffmpeg",
        "bundled libmpv": frameworks / "libmpv.2.dylib",
        "runtime manifest": resources_runtime / "media-runtime-manifest.json",
        "runtime licenses": resources_runtime / "licenses",
    }
    missing = [f"{name}: {path}" for name, path in required_paths.items() if not path.exists()]
    if missing:
        raise RuntimeError("Bundle runtime is incomplete:\n  " + "\n  ".join(missing))

    bundled_ffmpeg = required_paths["bundled FFmpeg"]
    bundled_libmpv = required_paths["bundled libmpv"]
    bundled_manifest = required_paths["runtime manifest"]
    source_manifest = SOURCE_RUNTIME / "media-runtime-manifest.json"
    if sha256(bundled_manifest) != sha256(source_manifest):
        raise RuntimeError("Bundled media runtime manifest differs from Phase 2A output.")

    with bundled_manifest.open(encoding="utf-8") as stream:
        manifest = json.load(stream)

    expected_licenses = set(manifest["licenses"])
    actual_licenses = {
        str(path.relative_to(resources_runtime))
        for path in (resources_runtime / "licenses").rglob("*")
        if path.is_file()
    }
    if actual_licenses != expected_licenses:
        missing_licenses = sorted(expected_licenses - actual_licenses)
        extra_licenses = sorted(actual_licenses - expected_licenses)
        raise RuntimeError(
            "Bundled license set differs from the manifest: "
            f"missing={missing_licenses}, extra={extra_licenses}"
        )

    provenance = validate_runtime_provenance(
        manifest,
        bundled_ffmpeg,
        bundled_libmpv,
    )

    macho_files = collect_macho_files(app_path)
    macho_results = [inspect_macho(path) for path in macho_files]
    deployment_target_violations = [
        {
            "path": str(Path(result["path"]).relative_to(app_path)),
            "minimum_macos": result["deployment_target_violations"],
        }
        for result in macho_results
        if result["deployment_target_violations"]
    ]

    libmpv_id = output(["otool", "-D", str(bundled_libmpv)]).splitlines()
    if len(libmpv_id) < 2 or libmpv_id[1] != "@rpath/libmpv.2.dylib":
        raise RuntimeError(f"Unexpected bundled libmpv install name: {libmpv_id}")

    libmpv = ctypes.CDLL(str(bundled_libmpv))
    libmpv.mpv_client_api_version.restype = ctypes.c_ulong
    client_api_version = libmpv.mpv_client_api_version()
    client_api = f"{client_api_version >> 16}.{client_api_version & 0xFFFF}"

    libmpv.mpv_create.restype = ctypes.c_void_p
    libmpv.mpv_initialize.argtypes = [ctypes.c_void_p]
    libmpv.mpv_initialize.restype = ctypes.c_int
    libmpv.mpv_terminate_destroy.argtypes = [ctypes.c_void_p]
    handle = libmpv.mpv_create()
    if not handle:
        raise RuntimeError("Bundled libmpv failed to create an mpv handle.")
    try:
        initialize_result = libmpv.mpv_initialize(handle)
        if initialize_result != 0:
            raise RuntimeError(
                f"Bundled libmpv initialization failed with code {initialize_result}."
            )
    finally:
        libmpv.mpv_terminate_destroy(handle)

    ffmpeg_version = output([str(bundled_ffmpeg), "-hide_banner", "-version"]).splitlines()[0]
    subprocess.run(
        [
            str(bundled_ffmpeg),
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=size=16x16:rate=1",
            "-frames:v",
            "1",
            "-f",
            "null",
            "-",
        ],
        check=True,
    )

    report = {
        "app": str(app_path),
        "macho_files_checked": len(macho_results),
        "deployment_target_violations": deployment_target_violations,
        "forbidden_paths": list(FORBIDDEN_PATHS),
        "media_runtime": {
            "ffmpeg": provenance["ffmpeg"],
            "ffmpeg_smoke_test": "passed",
            "ffmpeg_version": ffmpeg_version,
            "libmpv": provenance["libmpv"],
            "libmpv_client_api": client_api,
            "libmpv_initialize_test": "passed",
            "libmpv_install_name": libmpv_id[1],
            "licenses": len(actual_licenses),
        },
        "result": "failed" if deployment_target_violations else "passed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if deployment_target_violations:
        print(
            "Bundle contains components requiring a macOS version newer than 13.0.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    if sys.platform != "darwin":
        raise SystemExit("Pavo.app verification requires macOS.")
    raise SystemExit(main())
