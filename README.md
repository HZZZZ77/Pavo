# Pavo

<div align="center">
  <strong>A quiet, local-first media player for macOS.</strong>
  <br><br>
  Open a file and start watching. Pavo keeps playback focused, familiar, and out of the way.
  <br><br>
  <sub>macOS 13+ · Apple Silicon · Open source</sub>
</div>

<br>

<div align="center">
  <strong>Hero screenshot coming soon</strong>
  <br>
  <sub>Main playback window with the HUD and playlist.</sub>
</div>

## Why Pavo

Pavo is built for people who want a focused desktop player instead of a media library, streaming service, or account-based platform.

- **Made for macOS** — a restrained interface designed around familiar desktop interactions.
- **Local first** — open media from your Mac without accounts or online services.
- **Playback focused** — essential controls stay close at hand without taking over the screen.
- **Lightweight by design** — Pavo aims to remain a small, dependable player rather than grow into a media-management suite.
- **Open source** — the code, product direction, and release work are developed in the open.

## Features

- Open one or multiple local media files with `Command-O`, the File menu, or drag and drop.
- Play, pause, seek, skip forward or backward, adjust volume, and mute.
- Manage a playlist, reorder files, remove items, clear the queue, and continue automatically to the next item.
- Reopen recently used files from the File menu.
- Preview video thumbnails while hovering over the progress bar.
- Switch playback speed, aspect ratio, audio tracks, and subtitles.
- Use fullscreen or Picture in Picture for a more focused viewing experience.
- Return cleanly to a guided empty state when no media is loaded.

Pavo uses mpv for playback and is intended to handle common local media formats. Format and hardware compatibility are being audited as part of release preparation.

## Screenshots

| Playback | Empty State | Playlist and Picture in Picture |
| --- | --- | --- |
| _Screenshot coming soon: main playback view, controls, and thumbnail preview._ | _Screenshot coming soon: first-launch guidance and Open File action._ | _Screenshot coming soon: playlist panel and compact playback window._ |

## Installation

Pavo is preparing its first signed and notarized public macOS release. A production-ready download is not available yet.

Until that release is ready, developers and early testers can [build Pavo from source](#build-from-source). Future public builds will be published on the [GitHub Releases](https://github.com/HZZZZ77/Pavo/releases) page.

## Build from Source

The current build baseline targets Apple Silicon Macs running macOS 13 or later.

### Prerequisites

- macOS 13+
- Apple Silicon
- Xcode Command Line Tools
- Python 3.14 for building the bundled media runtime
- Python 3.13.12 for building the application

### Build

```bash
git clone https://github.com/HZZZZ77/Pavo.git
cd Pavo

python3.14 tools/media_runtime/build.py

python3.13 -m venv .venv-build
.venv-build/bin/python -m pip install -r requirements-build.txt
.venv-build/bin/python -m PyInstaller --clean --noconfirm Pavo.spec

python3.14 tools/media_runtime/verify_bundle.py dist/Pavo.app
```

The application is generated at `dist/Pavo.app`. The bundle includes the arm64 media runtime required by Pavo and does not require a separate Homebrew installation of mpv or FFmpeg.

See the [media runtime build notes](tools/media_runtime/README.md) for pinned source versions, verification details, and license information.

## Roadmap

Pavo is currently focused on release readiness and playback reliability.

- **Now** — validate mainstream playback formats, hardware decoding, packaging, and macOS compatibility.
- **Next** — refine preferences, file handling, playlist workflows, and everyday usability.
- **Later** — strengthen internal module boundaries, automated testing, and the signed release pipeline.

The detailed plan is available in the [project roadmap](docs/ROADMAP.md).

## Contributing

Bug reports and focused pull requests are welcome. Changes should preserve playback stability, local privacy, and Pavo's macOS-first product direction.

For larger changes, please open an issue first so the scope and expected behavior can be discussed.

## License

Pavo is open-source software released under the [MIT License](LICENSE).
