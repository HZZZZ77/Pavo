# Pavo Known Issues

This document lists confirmed limitations relevant to the Pavo 1.2.0 release
candidate. It is not a complete feature roadmap.

## Playlist Navigation

### No Manual Previous or Next Commands

Pavo automatically continues to the next playlist item when playback ends, but
there are currently no manual Previous or Next buttons or menu commands.

**Workaround:** Open the playlist and select the desired item directly.

### Removing the Current Item Can Break Auto-Next

If the currently playing item is removed from the playlist, playback continues,
but the playlist can lose its current position. Automatic continuation may not
select the following item when playback ends.

**Workaround:** Select another playlist item after removing the current one.

## Subtitles

### No Subtitle Off Command

Available subtitle tracks can be selected, but the subtitle menu does not
currently provide an explicit Off command.

### No Subtitle Timing Adjustment

Pavo does not currently expose subtitle delay controls. Media with incorrectly
timed subtitles must be corrected outside Pavo.

## Platform Coverage

- Pavo 1.2.0 targets Apple Silicon Macs running macOS 13 or later.
- Intel Macs and universal binaries are not supported.
- The current release candidate has been tested on newer Apple Silicon
  hardware, but final validation on a physical macOS 13 host is still pending.

## HDR Validation

HDR10 and HLG metadata are recognized in current playback tests. End-to-end HDR
output, tone mapping, and visual quality have not been validated on a confirmed
HDR display. Pavo 1.2.0 therefore does not claim complete HDR support.

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
