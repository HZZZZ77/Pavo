# Pavo 1.2.0

> Draft release copy. Do not publish until the final archive has been signed,
> notarized, attached to the GitHub Release, and tested on a supported Mac.

Pavo is a quiet, local-first media player designed for macOS. Version 1.2.0 is
the first public release candidate, focused on reliable everyday playback and a
clean desktop experience.

## Highlights

- Open local media with the File menu, `Command-O`, or drag and drop.
- Open multiple files at once and manage them in a lightweight playlist.
- Play, pause, seek, adjust volume, change playback speed, and select aspect ratio.
- Select available audio and subtitle tracks.
- Preview video frames by hovering over the progress bar.
- Use fullscreen and Picture in Picture.
- Reopen recent files without building a media library or signing in.

## A Focused macOS Experience

Pavo keeps controls available when needed and lets them recede while watching.
The guided empty state, glass-style controls, playlist, menus, and on-screen
feedback share one restrained visual language.

## Self-Contained Playback

The release build includes the arm64 mpv and FFmpeg runtime used by Pavo. Users
do not need to install Python, Homebrew, mpv, or FFmpeg separately.

## System Requirements

- Apple Silicon Mac
- macOS 13 or later

Intel Macs are not supported by this release.

## Install

1. Download the macOS arm64 archive from the GitHub Release assets.
2. Extract `Pavo.app`.
3. Move Pavo to the Applications folder.
4. Open Pavo and choose a local media file.

The final archive name and installation check must be confirmed before this
draft is published.

## Known Limitations

- Manual Previous and Next playlist commands are not available.
- Removing the currently playing playlist item can interrupt automatic
  continuation at the end of that file.
- Subtitles can be selected, but the current menu does not provide an explicit
  Off command or subtitle timing adjustment.
- Compatibility has not yet been validated on a physical macOS 13 host.
- HDR10 and HLG files can be opened in current testing, but end-to-end HDR
  output and visual quality have not been certified.

See [Known Issues](KNOWN_ISSUES.md) for details and current workarounds.

## Feedback

Please read [Support](../../SUPPORT.md) before opening an issue. Bug reports
should include clear reproduction steps, the macOS version, Mac model, and
relevant Pavo logs with private file paths removed.

Security vulnerabilities should be reported privately according to
[Security Policy](../../SECURITY.md).

## Open Source

Pavo is released under the [MIT License](../../LICENSE). Third-party components
included in the application retain their respective licenses.
