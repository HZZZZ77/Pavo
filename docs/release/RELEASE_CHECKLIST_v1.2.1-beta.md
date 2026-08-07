# Pavo 1.2.1 Beta Release Checklist

## Candidate

- [x] Source base commit: `2daccd1f2b60bf9fac5d8fead201decbea035c92`
- [x] Final release metadata commit: this release preparation commit
- [x] Application: `dist/Pavo.app`
- [x] Archive: `dist/Pavo-1.2.1-beta-macos-arm64.zip`
- [x] Archive size: `64,139,677` bytes (approximately 62 MB)
- [ ] Archive SHA-256: recalculate from the clean post-commit build and publish
      alongside the release asset
- [x] Target: Apple Silicon, macOS 13+

The application and archive are generated files and are not tracked by Git.
No Tag, GitHub Release, upload, or push was performed while preparing this
candidate.

## Reproducible Build

- [x] Media runtime input is present under `build/media-runtime/dist`.
- [x] A clean Python 3.13.12 virtual environment installed all fixed
      `requirements-build.txt` dependencies.
- [x] Release build uses PyInstaller 6.19.0.
- [x] `Pavo.spec` validated media runtime hashes and all expected licenses.
- [x] Build command completed successfully:

```bash
/private/tmp/pavo-1.2.1-build-20260807/venv/bin/python \
  -m PyInstaller --clean --noconfirm Pavo.spec
```

## Bundle Metadata

- [x] `CFBundleDisplayName`: `Pavo`
- [x] `CFBundleName`: `Pavo`
- [x] `CFBundleExecutable`: `Pavo`
- [x] `CFBundleIdentifier`: `io.github.hzzzz77.pavo`
- [x] `CFBundleShortVersionString`: `1.2.1`
- [x] `CFBundleVersion`: `2`
- [x] `LSMinimumSystemVersion`: `13.0`
- [x] Main executable architecture: arm64
- [x] `pavo.icns` is present and referenced by `CFBundleIconFile`.

## Runtime And Packaging Verification

- [x] Phase 2A FFmpeg and libmpv verification passed.
- [x] Bundle verification scanned 54 Mach-O files.
- [x] No deployment target exceeds macOS 13.0.
- [x] No dependency refers to `/opt/homebrew`, `/usr/local`, or `/opt/local`.
- [x] Bundled libmpv client API 2.5 initialized successfully.
- [x] Bundled FFmpeg 8.0.3 smoke test passed.
- [x] Media runtime manifest and 17 license files are present.
- [x] `codesign --verify --deep --strict` passed with ad-hoc signatures.

Commands:

```bash
python3.14 tools/media_runtime/verify.py
python3.14 tools/media_runtime/verify_bundle.py dist/Pavo.app
codesign --verify --deep --strict dist/Pavo.app
```

## Application And PiP Regression

- [x] Packaged application started with an isolated HOME and system-only PATH.
- [x] Startup selected `Contents/Frameworks/libmpv.2.dylib`.
- [x] mpv initialized successfully.
- [x] OpenGL render context initialized successfully.
- [x] PiP automated regression: 10 tests passed.
- [x] PiP controls, navigation, playback state, progress, automatic visibility,
      return path, and Clear Playlist are covered by tests.
- [x] Final packaged-app playback and PiP manual acceptance with real media.

Commands:

```bash
/private/tmp/pavo-1.2.1-build-20260807/venv/bin/python \
  -m compileall src tests tools/media_runtime

HOME=/private/tmp/pavo-1.2.1-build-20260807/test-home \
QT_QPA_PLATFORM=offscreen \
/private/tmp/pavo-1.2.1-build-20260807/venv/bin/python \
  -m unittest discover -s tests -v
```

## Archive Verification

- [x] Archive created with macOS resource metadata preserved:

```bash
ditto -c -k --sequesterRsrc --keepParent \
  dist/Pavo.app \
  dist/Pavo-1.2.1-beta-macos-arm64.zip
```

- [x] Archive extracted into a clean temporary directory.
- [x] Extracted application passed full bundle verification.
- [x] Extracted application passed strict code-signature verification.
- [x] Extracted `Info.plist` reports version `1.2.1` and Build `2`.
- [ ] Final post-commit archive SHA-256 must be published with the release asset.

## Publication Blockers

- [x] Commit the release metadata and documentation, then build the candidate
      from that clean source state.
- [x] Run final real-media playback and PiP acceptance against the packaged
      1.2.1 application.
- [ ] Review third-party license, source availability, and relinking
      obligations for the bundled media runtime.
- [ ] Validate launch, OpenGL, playback, and thumbnails on a physical macOS 13
      Apple Silicon Mac.
- [ ] Obtain a Developer ID Application signature and notarization for a normal
      first-launch experience.

The last item is an accepted limitation only for an explicitly labeled
unsigned Beta. HDR output remains unverified and is not claimed as fully
supported.
