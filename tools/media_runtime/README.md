# Pavo macOS Media Runtime

This directory defines the reproducible Phase 2A build for Pavo's media
runtime. It builds an arm64, macOS 13 compatible `libmpv` and `ffmpeg` without
using Homebrew libraries.

## Requirements

- Apple Silicon Mac
- Xcode Command Line Tools with a macOS SDK
- Python 3.14
- Network access for the first build

No Homebrew packages are required.

The exact libplacebo submodule revisions used by its v7.360.0 tag are listed
as independent, checksummed source inputs in `sources.json`. The build script
assembles them without invoking Git or downloading Meson wraps.

The checksummed mpv patch in `patches/` compiles Darwin utility symbols needed
by CoreAudio and AVFoundation without enabling mpv's Cocoa UI implementation.

## Build

From the repository root:

```bash
python3.14 tools/media_runtime/build.py
```

Downloads, build tools, intermediate files, and final binaries are written
under the ignored `build/media-runtime` directory.

After a successful online build, the same downloaded inputs can be rebuilt
without network access:

```bash
python3.14 tools/media_runtime/build.py --offline
```

## Outputs

```text
build/media-runtime/dist/bin/ffmpeg
build/media-runtime/dist/lib/libmpv.2.dylib
build/media-runtime/dist/licenses/
build/media-runtime/dist/media-runtime-manifest.json
```

The manifest records source versions and checksums, exact feature options,
linkage choices, build tool versions, artifact checksums, minimum macOS
versions, dynamic dependencies, and included license files.

## Verification

```bash
python3.14 tools/media_runtime/verify.py
```

Verification fails if an artifact is not arm64-only, requires a macOS version
newer than 13.0, or references Homebrew, MacPorts, or `/usr/local`.

## Pavo.app Integration

`Pavo.spec` requires a verified Phase 2A runtime in the output paths above. It
checks the input artifact SHA-256 values against the manifest before packaging.
PyInstaller places `libmpv.2.dylib` and `ffmpeg` in `Contents/Frameworks`, and
places the manifest and licenses in `Contents/Resources/media-runtime`.

Build and validate the application bundle:

```bash
venv/bin/python -m PyInstaller --clean --noconfirm Pavo.spec
python3.14 tools/media_runtime/verify_bundle.py
```

The bundle verifier checks runtime provenance, bundle layout, licenses,
architecture, minimum macOS versions, install names, and every Mach-O load
path. It also loads the bundled libmpv and executes the bundled FFmpeg.

The current PySide6 6.10.2 wheel contains binding binaries whose Mach-O
deployment target is macOS 15.0 despite the wheel's macOS 13 platform tag.
`verify_bundle.py` intentionally exits with a failure until that release
blocker is resolved.
