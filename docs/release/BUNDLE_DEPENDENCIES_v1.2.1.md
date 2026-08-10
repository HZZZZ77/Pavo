# Pavo 1.2.1 Beta Bundle Dependencies

This inventory is based on the files and Mach-O load commands in the final
`Pavo.app`, not on the Python requirements list. The machine-readable audit is
generated with:

```bash
python3.13 tools/release_compliance/audit_bundle.py \
  dist/Pavo.app --output dist/Pavo-1.2.1-bundle-audit.json
```

## Distributed Components

| Component | Version | License | Bundle evidence | Linkage |
| --- | --- | --- | --- | --- |
| Pavo | 1.2.1 (Build 2) | MIT | `Contents/MacOS/Pavo`, Python archive | Application |
| CPython | 3.13.12 | PSF License | `libpython3.13.dylib`, standard library | Embedded shared runtime |
| PyInstaller bootloader | 6.19.0 | GPL-2.0-or-later WITH Bootloader-exception | `Contents/MacOS/Pavo` | Launcher |
| PySide6 | 6.9.3 | LGPL-3.0-only | `PySide6/*.abi3.so`, `libpyside6` | Dynamic |
| shiboken6 | 6.9.3 | LGPL-3.0-only | `shiboken6/*.so`, `libshiboken6` | Dynamic |
| Qt Base | 6.9.3 | LGPL-3.0-only | QtCore, QtDBus, QtGui, QtWidgets, QtOpenGL, QtOpenGLWidgets | Dynamic frameworks |
| Qt SVG | 6.9.3 | LGPL-3.0-only | QtSvg framework and PySide6 binding | Dynamic framework |
| python-mpv | 1.0.8 | LGPL-2.1-or-later | Python archive imports `mpv` | Dynamic `ctypes` client |
| libmpv / mpv | 0.41.0 | LGPL-2.1-or-later | `libmpv.2.dylib` | Dynamic from Pavo; media dependencies static |
| FFmpeg | 8.0.3 | LGPL-2.1-or-later | `ffmpeg`, libav code in libmpv | Executable plus static media libraries |

## Qt-Embedded Components

The retained official Qt wheel binaries also contain statically incorporated
third-party code. This is established from binary strings in the final
Bundle and matched to the exact Qt 6.9.3 attribution records:

| Component | Version | License | Final Bundle evidence |
| --- | --- | --- | --- |
| PCRE2 and SLJIT | 10.46 | BSD-3-Clause with PCRE2 exception; BSD-2-Clause | PCRE2 diagnostics in QtCore |
| double-conversion | 3.3.1 | BSD-3-Clause | Conversion/Bignum implementation in QtCore and Qt attribution |
| FreeType | 2.14.1 | FTL | FreeType font engine in QtGui |
| HarfBuzz | 11.5.0 | MIT | HarfBuzz engine and version string in QtGui |
| libpng | 1.6.50 | Libpng AND libpng-2.0 | Exact version string in QtGui |
| libjpeg-turbo | 3.0.3 | IJG AND BSD-3-Clause | Exact version and copyright strings in `libqjpeg.dylib` |
| Emoji Segmenter | 0.4.0 | Apache-2.0 | Emoji segmenter implementation in QtGui and Qt attribution |
| XSVG-derived arc code | Unversioned | HPND-sell-variant | Incorporated in QtSvg |

The complete Qt upstream attribution records, including smaller hashing,
text, color, and platform routines without independent runtime version APIs,
are copied verbatim into the application under
`Contents/Resources/compliance/licenses/qt-attributions/`. Their source is in
the exact Qt archives; libjpeg-turbo 3.0.3 is separately archived because the
binary version differs from the revision recorded by the Qt 6.9.3 source tree.

The statically incorporated media components are FreeType 2.14.2, FriBidi
1.0.16, HarfBuzz 13.0.1, libass 0.17.4, libplacebo 7.360.0, fast_float
commit `97b54ca9`, and glad commit `73db193f`. Exact licenses and source hashes
are recorded in the source-archive and media-runtime manifests.

## Required Qt Runtime

- QtCore: object model, signals, timers, URLs, and application state.
- QtDBus: retained because the official QtGui wheel has a direct `@rpath/QtDBus` load command; the Python binding is excluded and Pavo does not use the DBus API.
- QtGui: painting, icons, actions, input events, and OpenGL context access.
- QtWidgets: all windows, menus, controls, layouts, and file dialogs.
- QtOpenGL and QtOpenGLWidgets: the `QOpenGLWidget` mpv render surface.
- QtSvg: `QSvgRenderer` used to render HUD and PiP symbols.
- Cocoa platform plugin and macOS style plugin: native Qt Widgets integration.
- JPEG imageformat plugin: decodes FFmpeg thumbnail preview frames.

Qt Virtual Keyboard, Qt PDF, Qt QML, Qt Quick, Qt Network, TLS,
network-information, touch-input, minimal/offscreen platform, and unrelated
imageformat plugins are intentionally excluded because Pavo does not import or
use them.

## Dynamic Relationship

PySide6 extension modules load `libpyside6`, `libshiboken6`, and the six Qt
frameworks through `@rpath`. `QtOpenGLWidgets` loads QtOpenGL, QtWidgets,
QtGui, and QtCore. QtSvg loads QtGui and QtCore. The Cocoa and macOS style
plugins load only the retained Qt frameworks and Apple system frameworks.

Pavo's python-mpv module loads the bundled `libmpv.2.dylib`; libmpv and the
bundled FFmpeg executable load only Apple system frameworks and `/usr/lib`
libraries. No Bundle Mach-O may reference Homebrew, MacPorts, `/usr/local`,
or any non-system absolute dependency.

## Final Audit Summary

- 23 Mach-O files: all classified, arm64, and with minimum macOS target no
  newer than 13.0.
- 7 Qt frameworks and 3 Qt plugins, with no unexpected or missing item.
- More than 100 bundled license and raw Qt attribution files; the final
  verifier records the authoritative count for each build.
- No unresolved `@rpath`, Homebrew, MacPorts, or `/usr/local` dependency.
