# -*- mode: python ; coding: utf-8 -*-

import hashlib
import json
import sys
from pathlib import Path


APP_NAME = "Pavo"
APP_VERSION = "1.2.0"
APP_BUILD = "1"
BUNDLE_IDENTIFIER = "io.github.hzzzz77.pavo"
TARGET_ARCH = "arm64"
MINIMUM_MACOS_VERSION = "13.0"
BUILD_PYTHON = (3, 13, 12)

if sys.version_info[:3] != BUILD_PYTHON:
    expected = ".".join(str(part) for part in BUILD_PYTHON)
    actual = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(
        f"Pavo.app must be built with Python {expected}; current interpreter is {actual}."
    )

PROJECT_ROOT = Path(SPEC).resolve().parent
MEDIA_RUNTIME = PROJECT_ROOT / "build" / "media-runtime" / "dist"
MEDIA_MANIFEST = MEDIA_RUNTIME / "media-runtime-manifest.json"
MEDIA_LICENSES = MEDIA_RUNTIME / "licenses"
MEDIA_FFMPEG = MEDIA_RUNTIME / "bin" / "ffmpeg"
MEDIA_LIBMPV = MEDIA_RUNTIME / "lib" / "libmpv.2.dylib"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


required_runtime_paths = [
    MEDIA_MANIFEST,
    MEDIA_LICENSES,
    MEDIA_FFMPEG,
    MEDIA_LIBMPV,
]
missing_runtime_paths = [path for path in required_runtime_paths if not path.exists()]
if missing_runtime_paths:
    missing = "\n".join(f"  - {path}" for path in missing_runtime_paths)
    raise SystemExit(
        "Pavo's Phase 2A media runtime is incomplete:\n"
        f"{missing}\n"
        "Run: python3.14 tools/media_runtime/build.py"
    )

with MEDIA_MANIFEST.open(encoding="utf-8") as stream:
    media_manifest = json.load(stream)

runtime_artifacts = {
    "ffmpeg": MEDIA_FFMPEG,
    "libmpv": MEDIA_LIBMPV,
}
for artifact_name, artifact_path in runtime_artifacts.items():
    expected = media_manifest["artifacts"][artifact_name]["sha256"]
    actual = sha256(artifact_path)
    if actual != expected:
        raise SystemExit(
            f"Phase 2A SHA-256 mismatch for {artifact_path}: "
            f"expected {expected}, got {actual}"
        )

missing_licenses = [
    MEDIA_RUNTIME / relative
    for relative in media_manifest["licenses"]
    if not (MEDIA_RUNTIME / relative).is_file()
]
if missing_licenses:
    missing = "\n".join(f"  - {path}" for path in missing_licenses)
    raise SystemExit(f"Phase 2A license files are incomplete:\n{missing}")

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        (str(MEDIA_LIBMPV), '.'),
        (str(MEDIA_FFMPEG), '.'),
    ],
    datas=[
        (str(MEDIA_MANIFEST), 'media-runtime'),
        (str(MEDIA_LICENSES), 'media-runtime/licenses'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=TARGET_ARCH,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pavo.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon='pavo.icns',
    bundle_identifier=BUNDLE_IDENTIFIER,
    version=APP_VERSION,
    info_plist={
        'CFBundleDisplayName': APP_NAME,
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_BUILD,
        'LSMinimumSystemVersion': MINIMUM_MACOS_VERSION,
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
    },
)
