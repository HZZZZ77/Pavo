#!/usr/bin/env python3
"""Prepare exact corresponding-source assets for a Pavo release."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import tarfile
import time
import urllib.request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("sources.json")
MEDIA_CONFIG_PATH = PROJECT_ROOT / "tools" / "media_runtime" / "sources.json"
MEDIA_DOWNLOADS = PROJECT_ROOT / "build" / "media-runtime" / "downloads"
SOURCE_ARCHIVES = PROJECT_ROOT / "dist" / "source-archives"
QT_ARCHIVES = SOURCE_ARCHIVES / "qt"
QT_EMBEDDED_ARCHIVES = SOURCE_ARCHIVES / "qt-embedded"
MEDIA_ARCHIVES = SOURCE_ARCHIVES / "media-runtime"
PYTHON_ARCHIVES = SOURCE_ARCHIVES / "python-runtime"
BUILD_MATERIALS = SOURCE_ARCHIVES / "build-materials"
GENERATED_LICENSES = PROJECT_ROOT / "build" / "release-compliance" / "licenses"
DOWNLOAD_CHUNK = 4 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified(path: Path, source: dict) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == source["size"]
        and sha256(path) == source["sha256"]
    )


def download(source: dict, *, offline: bool, restart: bool) -> Path:
    destination = QT_ARCHIVES / source["archive"]
    if verified(destination, source):
        print(f"Using verified {destination.name}")
        return destination
    if offline:
        raise RuntimeError(f"Verified source archive is unavailable: {destination}")

    destination.unlink(missing_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".download")
    parts_directory = destination.with_suffix(destination.suffix + ".parts")
    expected_size = source["size"]
    if restart:
        temporary.unlink(missing_ok=True)
        shutil.rmtree(parts_directory, ignore_errors=True)
    parts_directory.mkdir(exist_ok=True)

    def fetch_range(start: int, end: int) -> bytes:
        request = urllib.request.Request(source["url"], headers={"Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(request, timeout=90) as response:
            content_range = response.headers.get("Content-Range")
            expected_range = f"bytes {start}-{end}/{expected_size}"
            if getattr(response, "status", None) != 206 or content_range != expected_range:
                raise RuntimeError(
                    f"Unexpected range response for {source['archive']}: {content_range!r}"
                )
            data = response.read()
        if len(data) != end - start + 1:
            raise RuntimeError(
                f"Short range for {source['archive']}: {start}-{end}, got {len(data)} bytes"
            )
        return data

    for start in range(0, expected_size, DOWNLOAD_CHUNK):
        end = min(start + DOWNLOAD_CHUNK, expected_size) - 1
        part = parts_directory / f"{start:012d}-{end:012d}.part"
        accepted = False
        for attempt in range(1, 9):
            try:
                candidate = fetch_range(start, end)
                if part.exists() and part.read_bytes() == candidate:
                    accepted = True
                    break
                confirmation = fetch_range(start, end)
                if candidate == confirmation:
                    part.write_bytes(candidate)
                    accepted = True
                    break
            except Exception as exc:
                if attempt == 8:
                    raise RuntimeError(
                        f"Failed to verify range {start}-{end} for {source['archive']}: {exc}"
                    ) from exc
                time.sleep(attempt)
        if not accepted:
            raise RuntimeError(f"Could not verify range {start}-{end} for {source['archive']}")
        completed = end + 1
        print(f"Downloading {source['archive']}: {completed}/{expected_size} bytes", flush=True)

    with temporary.open("wb") as output:
        for part in sorted(parts_directory.glob("*.part")):
            with part.open("rb") as stream:
                shutil.copyfileobj(stream, output, 1024 * 1024)
    if temporary.stat().st_size != expected_size:
        raise RuntimeError(f"Assembled size mismatch for {source['archive']}")

    if sha256(temporary) != source["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch for {source['archive']}")
    temporary.replace(destination)
    shutil.rmtree(parts_directory)
    print(f"Downloaded and verified {destination.name}")
    return destination


def copy_media_sources(media_config: dict) -> list[dict]:
    records = []
    MEDIA_ARCHIVES.mkdir(parents=True, exist_ok=True)
    for source in media_config["sources"]:
        original = MEDIA_DOWNLOADS / source["archive"]
        if not original.is_file() or sha256(original) != source["sha256"]:
            raise RuntimeError(
                f"Missing Phase 2A source {original}; run tools/media_runtime/build.py first."
            )
        destination = MEDIA_ARCHIVES / source["archive"]
        if not destination.exists() or sha256(destination) != source["sha256"]:
            shutil.copy2(original, destination)
        records.append(
            {
                **source,
                "release_path": destination.relative_to(SOURCE_ARCHIVES).as_posix(),
                "size": destination.stat().st_size,
            }
        )
    return records


def prepare_python_sources(config: dict, *, offline: bool) -> list[dict]:
    records = []
    PYTHON_ARCHIVES.mkdir(parents=True, exist_ok=True)
    for source in config["python_runtime_sources"]:
        destination = PYTHON_ARCHIVES / source["archive"]
        if not verified(destination, source):
            if offline:
                raise RuntimeError(f"Verified source archive is unavailable: {destination}")
            temporary = destination.with_suffix(destination.suffix + ".download")
            temporary.unlink(missing_ok=True)
            urllib.request.urlretrieve(source["url"], temporary)
            if not verified(temporary, source):
                raise RuntimeError(f"Downloaded source failed verification: {source['archive']}")
            temporary.replace(destination)
        records.append(
            {
                **source,
                "release_path": destination.relative_to(SOURCE_ARCHIVES).as_posix(),
            }
        )
    return records


def prepare_direct_sources(
    sources: list[dict], destination_directory: Path, *, offline: bool
) -> list[dict]:
    records = []
    destination_directory.mkdir(parents=True, exist_ok=True)
    for source in sources:
        destination = destination_directory / source["archive"]
        if not verified(destination, source):
            if offline:
                raise RuntimeError(f"Verified source archive is unavailable: {destination}")
            temporary = destination.with_suffix(destination.suffix + ".download")
            temporary.unlink(missing_ok=True)
            urllib.request.urlretrieve(source["url"], temporary)
            if not verified(temporary, source):
                raise RuntimeError(f"Downloaded source failed verification: {source['archive']}")
            temporary.replace(destination)
        records.append(
            {
                **source,
                "release_path": destination.relative_to(SOURCE_ARCHIVES).as_posix(),
            }
        )
    return records


def copy_build_materials() -> list[dict]:
    relative_paths = [
        "requirements.txt",
        "requirements-build.txt",
        "Pavo.spec",
        "tools/media_runtime/README.md",
        "tools/media_runtime/build.py",
        "tools/media_runtime/sources.json",
        "tools/media_runtime/verify.py",
        "tools/media_runtime/verify_bundle.py",
        "tools/media_runtime/patches/mpv-0.41.0-darwin-utils.patch",
        "tools/release_compliance/audit_bundle.py",
        "tools/release_compliance/prepare_source_archives.py",
        "tools/release_compliance/sources.json",
    ]
    records = []
    for relative in relative_paths:
        source = PROJECT_ROOT / relative
        destination = BUILD_MATERIALS / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        records.append(
            {
                "path": destination.relative_to(SOURCE_ARCHIVES).as_posix(),
                "sha256": sha256(destination),
                "size": destination.stat().st_size,
            }
        )
    return records


def extract_license_directories(
    qt_archives: list[Path], qt_embedded_sources: list[dict]
) -> list[str]:
    if GENERATED_LICENSES.exists():
        shutil.rmtree(GENERATED_LICENSES)
    GENERATED_LICENSES.mkdir(parents=True)
    extracted = []
    for archive in qt_archives:
        component = archive.name.split("-everywhere-src", 1)[0]
        if component == "pyside-setup":
            component = "qt-for-python"
        destination = GENERATED_LICENSES / component
        with tarfile.open(archive) as tar:
            license_members = [
                member
                for member in tar.getmembers()
                if member.isfile() and "/LICENSES/" in member.name
            ]
            if not license_members:
                raise RuntimeError(f"No LICENSES directory found in {archive}")
            destination.mkdir()
            for member in license_members:
                name = Path(member.name).name
                extracted_file = tar.extractfile(member)
                if extracted_file is None:
                    raise RuntimeError(f"Could not extract {member.name}")
                target = destination / name
                target.write_bytes(extracted_file.read())
                extracted.append(target.relative_to(GENERATED_LICENSES).as_posix())

            attribution_members = [
                member
                for member in tar.getmembers()
                if member.isfile() and member.name.endswith("qt_attribution.json")
            ]
            attribution_root = GENERATED_LICENSES / "qt-attributions" / component
            for member in attribution_members:
                extracted_file = tar.extractfile(member)
                if extracted_file is None:
                    raise RuntimeError(f"Could not extract {member.name}")
                source_root = Path(member.name).parts[0]
                relative = Path(member.name).relative_to(source_root)
                target = attribution_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(extracted_file.read())
                extracted.append(target.relative_to(GENERATED_LICENSES).as_posix())

    for source in qt_embedded_sources:
        archive = QT_EMBEDDED_ARCHIVES / source["archive"]
        with tarfile.open(archive) as tar:
            for license_name in source["license_files"]:
                matches = [
                    member
                    for member in tar.getmembers()
                    if member.isfile() and member.name.endswith(f"/{license_name}")
                ]
                if len(matches) != 1:
                    raise RuntimeError(
                        f"Expected one {license_name} in {archive.name}, found {len(matches)}"
                    )
                extracted_file = tar.extractfile(matches[0])
                if extracted_file is None:
                    raise RuntimeError(f"Could not extract {matches[0].name}")
                target = GENERATED_LICENSES / "qt-embedded" / source["name"] / license_name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(extracted_file.read())
                extracted.append(target.relative_to(GENERATED_LICENSES).as_posix())

    python_license = Path(__import__("sys").base_prefix) / "lib" / "python3.13" / "LICENSE.txt"
    if not python_license.is_file():
        raise RuntimeError(f"Python license is missing: {python_license}")
    shutil.copy2(python_license, GENERATED_LICENSES / "CPython-3.13.txt")

    for distribution_name, output_prefix in (
        ("python-mpv", "python-mpv"),
        ("PyInstaller", "PyInstaller"),
    ):
        distribution = importlib.metadata.distribution(distribution_name)
        license_files = [
            file
            for file in distribution.files or []
            if "license" in file.name.lower() or "copying" in file.name.lower()
        ]
        if not license_files:
            raise RuntimeError(f"No license files found for {distribution_name}")
        for file in license_files:
            source = Path(distribution.locate_file(file))
            target = GENERATED_LICENSES / f"{output_prefix}-{file.name}"
            shutil.copy2(source, target)
            extracted.append(target.relative_to(GENERATED_LICENSES).as_posix())
    extracted.append("CPython-3.13.txt")
    return sorted(extracted)


def write_manifest(
    qt_config: dict,
    media_records: list[dict],
    python_records: list[dict],
    qt_embedded_records: list[dict],
    build_records: list[dict],
    licenses: list[str],
) -> None:
    qt_records = []
    for source in qt_config["qt_sources"]:
        archive = QT_ARCHIVES / source["archive"]
        qt_records.append(
            {
                **source,
                "release_path": archive.relative_to(SOURCE_ARCHIVES).as_posix(),
            }
        )
    manifest = {
        "schema_version": 1,
        "release": qt_config["release"],
        "qt_sources": qt_records,
        "media_runtime_sources": media_records,
        "python_runtime_sources": python_records,
        "qt_embedded_sources": qt_embedded_records,
        "build_materials": build_records,
        "generated_bundle_licenses": licenses,
    }
    manifest_path = SOURCE_ARCHIVES / "source-archive-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_path = SOURCE_ARCHIVES / "SHA256SUMS"
    files = sorted(path for path in SOURCE_ARCHIVES.rglob("*") if path.is_file() and path != checksum_path)
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(SOURCE_ARCHIVES).as_posix()}\n" for path in files),
        encoding="utf-8",
    )


def write_source_bundle(config: dict) -> Path:
    bundle = PROJECT_ROOT / "dist" / config["source_bundle"]
    temporary = bundle.with_suffix(bundle.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    archive_root = bundle.name.removesuffix(".tar.xz")
    with tarfile.open(temporary, "w:xz", format=tarfile.PAX_FORMAT) as tar:
        for path in sorted(SOURCE_ARCHIVES.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(SOURCE_ARCHIVES)
            info = tar.gettarinfo(path, arcname=f"{archive_root}/{relative.as_posix()}")
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            with path.open("rb") as stream:
                tar.addfile(info, stream)
    temporary.replace(bundle)
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Do not download missing Qt sources.")
    parser.add_argument(
        "--restart-downloads",
        action="store_true",
        help="Discard incomplete Qt download fragments before fetching.",
    )
    args = parser.parse_args()
    qt_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    media_config = json.loads(MEDIA_CONFIG_PATH.read_text(encoding="utf-8"))
    QT_ARCHIVES.mkdir(parents=True, exist_ok=True)
    qt_archives = [
        download(source, offline=args.offline, restart=args.restart_downloads)
        for source in qt_config["qt_sources"]
    ]
    media_records = copy_media_sources(media_config)
    python_records = prepare_python_sources(qt_config, offline=args.offline)
    qt_embedded_records = prepare_direct_sources(
        qt_config["qt_embedded_sources"], QT_EMBEDDED_ARCHIVES, offline=args.offline
    )
    build_records = copy_build_materials()
    licenses = extract_license_directories(qt_archives, qt_config["qt_embedded_sources"])
    write_manifest(
        qt_config,
        media_records,
        python_records,
        qt_embedded_records,
        build_records,
        licenses,
    )
    source_bundle = write_source_bundle(qt_config)
    print(f"Prepared source assets in {SOURCE_ARCHIVES}")
    print(f"Prepared release asset {source_bundle} ({sha256(source_bundle)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
