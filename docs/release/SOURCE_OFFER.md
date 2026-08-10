# Pavo 1.2.1 Beta Corresponding Source

Pavo 1.2.1 Beta is distributed with dynamically linked LGPL Qt/PySide6
libraries and an LGPL media runtime. The exact corresponding-source set is
provided as release assets alongside the binary distribution and is also
prepared locally under `dist/source-archives/` by the release workflow.

## Source Set

The source set contains:

- Qt Base 6.9.3 and Qt SVG 6.9.3.
- Qt for Python 6.9.3, containing PySide6 and shiboken6.
- libjpeg-turbo 3.0.3, matching the version string in the official Qt wheel's
  bundled JPEG plugin; the Qt 6.9.3 source tree alone identifies a newer
  libjpeg-turbo revision and is therefore not used as a substitute.
- python-mpv 1.0.8 and the PyInstaller 6.19.0 bootloader/runtime source.
- FFmpeg 8.0.3, mpv 0.41.0, libplacebo 7.360.0, FreeType 2.14.2,
  FriBidi 1.0.16, HarfBuzz 13.0.1, libass 0.17.4, and every pinned
  media-runtime subproject and build input.
- The Pavo PyInstaller specification, fixed Python requirements, media build
  script, complete build options, and the Pavo mpv patch.
- `source-archive-manifest.json` and `SHA256SUMS` covering every supplied file.

The release workflow packages this directory as
`dist/Pavo-1.2.1-beta-corresponding-source.tar.xz`. Upload that aggregate
archive alongside the application ZIP; it contains the unchanged upstream
archives, build materials, manifest, and checksums as one Release Asset.

Run the following command from a clean Pavo checkout to prepare or verify the
same set:

```bash
python3.13 tools/release_compliance/prepare_source_archives.py
python3.13 tools/release_compliance/prepare_source_archives.py --offline
```

The first command may download the three official Qt source archives,
libjpeg-turbo, and the exact Python runtime source distributions. Media
sources must already have been fetched by `tools/media_runtime/build.py`. The
offline command succeeds only when all exact archives are present and valid.

## Written Offer

For any recipient of the Pavo 1.2.1 Beta binary, the Pavo project offers to
provide the same machine-readable corresponding source and build materials at
no charge other than a reasonable physical distribution cost. This offer is
valid for at least three years from the last distribution of this binary.

The intended public location is the Pavo 1.2.1 Beta GitHub Release. If an
asset is unavailable, open an issue at:

<https://github.com/hzzzz77/Pavo/issues>

Identify the requested release as `Pavo 1.2.1 Beta`, and include the binary
ZIP SHA-256 from its release page. Upstream links alone are not the source
offer; the checksummed copies controlled and distributed by the Pavo project
are the offered materials.
