# Pavo 1.2.1 Beta

> Draft beta release copy. Do not publish until the release archive, checksum,
> runtime verification, and remaining release blockers have been reviewed.

Pavo 1.2.1 Beta is a focused maintenance update for the macOS Picture in
Picture experience. It keeps the self-contained playback foundation from
1.2.0 while making PiP quieter, clearer, and better suited to watching video
alongside other work.

## What's New

### Minimal Picture in Picture

- A dedicated PiP control layer replaces the reduced main-window HUD.
- The center controls contain only Previous, Play/Pause, and Next.
- Return-to-window and close-PiP actions remain available in the top corners.
- A subtle read-only progress indicator shows playback position without
  introducing interactive seeking controls.

### Controls That Recede While Watching

- PiP controls appear when the pointer enters or moves over the window.
- Controls automatically hide while video is playing.
- Controls remain visible while playback is paused.
- Play and playlist navigation state stay synchronized with the main window and
  the active mpv playback state.

### Native macOS Window Treatment

- PiP uses native macOS continuous corners and window shadow.
- The video canvas is clipped cleanly inside the rounded window.
- Control buttons use restrained, borderless translucent backgrounds.

### Video-Aware Initial Size

- The initial PiP window uses the active video's display aspect ratio.
- The video canvas fills the PiP window, avoiding layout space reserved for the
  main HUD or playlist.
- The window remains always on top, movable, and freely resizable.

## Existing Playback Features

Pavo continues to support local file opening, drag and drop, playlists, Recent
Files, subtitles and audio tracks, playback speed, thumbnail previews,
fullscreen, and the complete empty state after Clear Playlist.

## System Requirements

- Apple Silicon Mac
- macOS 13 or later

Intel Macs are not supported by this beta.

## Installation

Download `Pavo-1.2.1-beta-macos-arm64.zip` from the GitHub Release assets and
follow the [installation guide](../../INSTALL.md).

This beta is ad-hoc signed rather than signed with an Apple Developer ID, and
it is not notarized. macOS therefore requires explicit approval on first
launch.

## Download Verification

The final SHA-256 is calculated from the clean build produced after the release
metadata commit. Publish that checksum alongside the GitHub Release asset.

## Known Limitations

- Entering PiP from a maximized main window restores the previous geometry on
  exit but does not explicitly restore the maximized window state.
- Subtitle timing adjustment is not available.
- Compatibility has not been validated on a physical macOS 13 host.
- HDR10 and HLG files can be opened in current testing, but end-to-end HDR
  output and visual quality have not been certified.

See [Known Issues](KNOWN_ISSUES.md) for the complete current list.

## Feedback And Open Source

Please read [Support](../../SUPPORT.md) before opening a bug report. Security
issues should follow the private process in [Security Policy](../../SECURITY.md).

Pavo is released under the [MIT License](../../LICENSE). Bundled third-party
components retain their respective licenses.
