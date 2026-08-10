# Pavo Known Issues

This document lists confirmed limitations relevant to the Pavo 1.2.1 release
candidate. It is not a complete feature roadmap.

## Subtitles

### No Subtitle Timing Adjustment

Pavo does not currently expose subtitle delay controls. Media with incorrectly
timed subtitles must be corrected outside Pavo.

## Unsigned Beta

Pavo 1.2.1 Beta is ad-hoc signed rather than signed with an Apple Developer ID,
and it is not notarized. macOS will identify the developer as unverified on the
first launch.

Follow the [installation guide](../../INSTALL.md) to approve the app through
Finder or System Settings. Only install archives downloaded from Pavo's official
GitHub Releases page, and compare the SHA-256 checksum with the release notes.

## Platform Coverage

- Pavo 1.2.1 targets Apple Silicon Macs running macOS 13 or later.
- Intel Macs and universal binaries are not supported.
- The current release candidate has been tested on newer Apple Silicon
  hardware, but final validation on a physical macOS 13 host is still pending.

## Picture In Picture

### Maximized Window State Is Not Explicitly Restored

When Picture in Picture is entered from a maximized main window, Pavo restores
the previous window geometry on exit but does not explicitly restore the
maximized window state. Normal and fullscreen return paths are unaffected. This
is tracked as a non-blocking maintenance issue.

## HDR Validation

HDR10 and HLG metadata are recognized in current playback tests. End-to-end HDR
output, tone mapping, and visual quality have not been validated on a confirmed
HDR display. Pavo 1.2.1 therefore does not claim complete HDR support.

## Media Not Covered

The current release audit does not cover:

- Damaged or partially downloaded files
- Encrypted or DRM-protected media
- Blu-ray or DVD playback
- Dolby Vision
- Network streams
- Multi-gigabyte file stress testing

## Reporting a New Issue

Before reporting a problem, check the latest version of this document and search
existing GitHub issues. New reports should use the
[bug report template](https://github.com/HZZZZ77/Pavo/issues/new/choose).

Pavo logs are stored at `~/Library/Logs/Pavo/pavo.log`. Remove private file paths
or filenames before attaching logs publicly.
