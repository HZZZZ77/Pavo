# Pavo 1.2.0 Beta Release Checklist

## Candidate

- [x] Source commit: `094b8f82cd6b`
- [x] Application: `dist/Pavo.app`
- [x] Archive: `dist/Pavo-1.2.0-beta-macos-arm64.zip`
- [x] Archive size: approximately 61 MB
- [x] Archive SHA-256:
  `5adc58a30ab6e000f6b7024129be49f701aa4b8ede979ed6237260b6db15224a`
- [x] Target: Apple Silicon, macOS 13+

The archive and app bundle are generated files and are not tracked by Git.

## Reproducible Build

- [x] Media runtime input is present under `build/media-runtime/dist`.
- [x] Release build uses Python 3.13.12.
- [x] Release build uses PyInstaller 6.19.0.
- [x] `Pavo.spec` validates media runtime inputs and license files.
- [x] Build command completed successfully:

```bash
/private/tmp/pavo-phase3a/venv/bin/python \
  -m PyInstaller --clean --noconfirm Pavo.spec
```

For a clean clone, create the fixed build environment documented in the
project README instead of relying on the temporary path above.

## Bundle Metadata

- [x] `CFBundleDisplayName`: `Pavo`
- [x] `CFBundleName`: `Pavo`
- [x] `CFBundleExecutable`: `Pavo`
- [x] `CFBundleIdentifier`: `io.github.hzzzz77.pavo`
- [x] `CFBundleShortVersionString`: `1.2.0`
- [x] `CFBundleVersion`: `1`
- [x] `LSMinimumSystemVersion`: `13.0`
- [x] Main executable architecture: arm64
- [x] `pavo.icns` is present and referenced by `CFBundleIconFile`.

## Bundled Runtime

- [x] `libpython3.13.dylib` is included.
- [x] PySide6, shiboken6, Qt frameworks, and Qt plugins are included.
- [x] `libmpv.2.dylib` is included in `Contents/Frameworks`.
- [x] FFmpeg 8.0.3 is included in `Contents/Frameworks`.
- [x] Media runtime manifest and 17 license files are included.
- [x] Bundle verification scanned 54 Mach-O files.
- [x] No Mach-O deployment target exceeds macOS 13.0.
- [x] No Mach-O dependency refers to `/opt/homebrew`, `/usr/local`, or `/opt/local`.
- [x] Bundled libmpv initialization test passed.
- [x] Bundled FFmpeg smoke test passed.

Verification command:

```bash
python3.14 tools/media_runtime/verify_bundle.py dist/Pavo.app
```

## Standalone Launch

- [x] Pavo launched with a system-only `PATH` that contained no Python,
      Homebrew, mpv, or FFmpeg commands.
- [x] Startup logs confirmed the bundled `libmpv.2.dylib`.
- [x] mpv initialized successfully.
- [x] OpenGL render context initialized successfully.
- [x] The empty state, File menu, and Playback menu appeared.
- [x] A bundled-runtime HEVC 4K test file opened and displayed.
- [x] The app exited normally with status 0.

This is strong evidence that the bundle does not require a user-installed
Python. Final confirmation still requires testing on a separate Mac that has
never had the development toolchain installed.

## Archive Verification

- [x] Archive created with macOS resource metadata preserved:

```bash
ditto -c -k --sequesterRsrc --keepParent \
  dist/Pavo.app \
  dist/Pavo-1.2.0-beta-macos-arm64.zip
```

- [x] Archive extracted into a clean temporary directory.
- [x] The extracted `Pavo.app` passed the complete bundle verification again.
- [x] Archive SHA-256 was recorded.

## Signing And Gatekeeper

- [x] `codesign --verify --deep --strict` passes.
- [x] The app and nested binaries have ad-hoc signatures.
- [ ] Developer ID Application signature.
- [ ] Hardened Runtime.
- [ ] Apple notarization and stapled ticket.
- [ ] Gatekeeper acceptance without manual approval.

The unchecked items require an Apple Developer account. They are accepted
limitations for an explicitly labeled unsigned beta, but they prevent a normal
double-click installation experience.

## Documentation

- [x] Release notes prepared.
- [x] Known issues documented.
- [x] Installation guide explains unsigned first launch.
- [x] FAQ explains trust, privacy, and feedback.
- [x] Bug, feature, pull request, security, and support templates are present.
- [ ] Final GitHub Release asset URL confirmed after upload.

## Required Before Public Upload

- [ ] Complete manual PAVO-008 regression with real subtitle and multi-file
      playback: Subtitle Off, Previous, Next, auto-next, and deleting the
      current item.
- [ ] Review third-party license obligations for the statically linked media
      runtime, including source availability and relinking requirements.
- [ ] Recalculate and publish the archive SHA-256 if the app is rebuilt.
- [ ] Confirm the GitHub Release is clearly labeled `Beta` and `Unsigned`.

## Recommended Follow-Up

- [ ] Validate launch, OpenGL, playback, and thumbnails on a physical macOS 13
      Apple Silicon Mac.
- [ ] Test the downloaded GitHub asset after upload so quarantine and Gatekeeper
      behavior match the installation guide.
- [ ] Obtain Developer ID signing and notarization before a stable release.
