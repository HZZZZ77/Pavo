# Rebuilding and Relinking Pavo 1.2.1 Beta

Pavo uses dynamic linking for Qt, PySide6, shiboken6, and libmpv. The
distributed macOS application is not an immutable device: recipients may
replace modified compatible libraries, apply an ad-hoc signature, and run the
resulting application.

## Reproduce the Release Inputs

Use Apple Silicon, the macOS SDK, Python 3.13.12 for the application build,
and Python 3.14 with Meson 1.9.1 and Ninja 1.13.0 for the media runtime.

```bash
python3.14 tools/media_runtime/build.py --offline
python3.13 tools/release_compliance/prepare_source_archives.py --offline
python3.13 -m venv .venv-build
.venv-build/bin/python -m pip install -r requirements-build.txt
.venv-build/bin/python -m PyInstaller --clean --noconfirm Pavo.spec
```

The full FFmpeg and Meson options are recorded in
`tools/media_runtime/sources.json` and in the bundled
`media-runtime-manifest.json`. Pavo applies one checksummed patch,
`tools/media_runtime/patches/mpv-0.41.0-darwin-utils.patch`; no Qt, PySide6,
shiboken6, FFmpeg, or libplacebo source patches are applied.

## Replace Dynamic Libraries

Compatible rebuilt Qt frameworks may replace their counterparts below:

```text
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtCore.framework
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtDBus.framework
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtGui.framework
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtWidgets.framework
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtOpenGL.framework
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtOpenGLWidgets.framework
Pavo.app/Contents/Frameworks/PySide6/Qt/lib/QtSvg.framework
```

Rebuilt PySide6 and shiboken6 dynamic libraries and extension modules may be
replaced under `Contents/Frameworks/PySide6/` and
`Contents/Frameworks/shiboken6/`. They must preserve the ABI and `@rpath`
install names expected by the other bundled modules.

The official PySide6 wheel is the source of the distributed Qt binaries. Its
retained JPEG plugin identifies libjpeg-turbo 3.0.3 at runtime, so that exact
source is supplied separately. Other Qt-carried third-party source and raw
upstream attributions are contained in the Qt source archives and copied into
the application's compliance resources by the source preparation tool.

Rebuilt libmpv may replace
`Contents/Frameworks/libmpv.2.dylib`. It must retain the install name
`@rpath/libmpv.2.dylib` and a compatible libmpv client API. The FFmpeg helper
may replace `Contents/Frameworks/ffmpeg`. Media dependencies linked statically
inside libmpv or FFmpeg are changed by rebuilding the Phase 2A runtime and
then replacing those two outputs.

All replacement Mach-O files must contain arm64 code and target macOS 13.0 or
earlier. After replacement, apply an ad-hoc signature and verify the bundle:

```bash
codesign --force --deep --sign - Pavo.app
codesign --verify --deep --strict Pavo.app
python3.14 tools/media_runtime/verify_bundle.py Pavo.app
python3.13 tools/release_compliance/audit_bundle.py Pavo.app
```

Gatekeeper may require the user to approve the locally modified application.
No Pavo term prohibits reverse engineering for the purpose of debugging these
library modifications.
