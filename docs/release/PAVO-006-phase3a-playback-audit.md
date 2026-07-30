# PAVO-006 Phase 3A Playback Compatibility Audit

## Status

`Audit Complete - Findings Await Review`

This audit records playback evidence only. It does not certify a public release,
HDR visual fidelity, or compatibility with a real macOS 13 host.

## Test Environment

- Audit date: 2026-07-30
- Source commit: `46fddd3`
- Host: MacBook Air, Apple M4, arm64, 24 GB memory
- Host OS: macOS 26.5.2 (25F84)
- Release toolchain: Python 3.13.12, PySide6 6.9.3, PyInstaller 6.19.0
- Media runtime: mpv 0.41.0, FFmpeg 8.0.3
- Application: unsigned `/private/tmp/pavo-phase3a/dist/Pavo.app`
- Runtime isolation: codec probes used the final bundle's `libmpv.2.dylib` and
  `ffmpeg`; application state tests used an isolated temporary `HOME`
- Test corpus: `/private/tmp/pavo-phase3a/assets`, not tracked by Git
- Corpus manifest: `tools/release_audit/corpus-manifest.json`

The automated probe imports the production `PavoEngine`, `PavoVideoWidget`, and
`PavoPlayer`, creates the real QOpenGLWidget render context, and forces runtime
resolution to the final app bundle. Separate Computer Use smoke tests launched
the packaged executable itself and verified native Open File, visible 4K
rendering, fullscreen, and PiP.

## Container And Video Matrix

| Container | Video | Audio | Resolution | Result | Actual hwdec |
| --- | --- | --- | --- | --- | --- |
| MP4 | H.264 | AAC | 1080p30 | Pass | `videotoolbox-copy` |
| MOV | HEVC | AAC | 1080p30 | Pass | `videotoolbox-copy` |
| WebM | VP9 | Opus | 352x288 | Pass | `videotoolbox-copy` |
| MKV | AV1 Main 10 | FLAC | 1080p60 | Pass | `videotoolbox-copy` |
| MP4 | HEVC | AAC | 4K60, about 56 Mbps | Pass | `videotoolbox-copy` |
| MP4 | H.264 | none | 720p, 2 hours | Pass | `videotoolbox-copy` |

All four target video codecs used VideoToolbox hardware decoding with copy-back.
No tested video used software decoding, and none used a zero-copy interop path.

Five-second sustained playback samples for H.264 1080p, AV1 1080p60, HEVC
4K60, HDR10, and HLG recorded zero decoder-frame-drop and zero VO-frame-drop
delta. Rapid media changes in the short matrix did increment the cumulative VO
drop counter during startup, so the sustained samples are the relevant
steady-state evidence.

## Audio Matrix

| Codec | Test form | Result |
| --- | --- | --- |
| AAC | M4A and MKV track | Pass |
| MP3 | Public MP3 transcode | Pass |
| FLAC | FLAC and MKV track | Pass |
| Opus | Ogg and WebM track | Pass |
| AC-3 | Raw stream and MKV track | Pass |
| E-AC-3 | Raw stream and MKV track | Pass |

The three embedded MKV audio tracks (AAC, AC-3, E-AC-3) were selected in turn,
and `audio-codec-name` changed to the expected decoder each time.

## Subtitle Matrix

- Embedded SRT: loaded, selected, and produced the expected cue at 1.0 seconds.
- Embedded ASS: loaded, selected, and produced the expected cue at 1.0 seconds.
- External SRT: added through `PavoEngine`, selected, and produced the expected cue.
- External ASS: added through `PavoEngine`, selected, and produced the expected cue.
- Runtime subtitle off: `sid=no` works in libmpv.
- Default synchronization: `sub-delay=0.0`; generated cue timing matched 1.0 seconds.
- User-facing subtitle off: **not implemented in the current subtitle menu**.
- User-facing subtitle delay adjustment: **not implemented**.

## Playback And UI Regression

| Area | Result | Evidence |
| --- | --- | --- |
| Packaged app launch | Pass | mpv and OpenGL initialized without application errors |
| Native Open File / Cmd+O | Pass | macOS file panel opened and 4K file loaded |
| Visible video rendering | Pass | packaged app displayed the generated 4K test pattern |
| Pause / resume | Pass | paused position stable; resume advanced |
| Seek | Pass | 12-second file reached 50% in 7 ms |
| Long-file seek | Pass | 2-hour, 134 MB file reached 01:00:00 in 3 ms |
| Playback speed | Pass | 1.5x property applied and restored |
| Volume | Pass | volume property changed to 35 |
| Audio track switching | Pass | AAC, AC-3, E-AC-3 selected |
| Playlist add and switch | Pass | three files added; second item loaded |
| End-of-file auto-next | Pass | next item loaded and continued playing |
| Recent Files | Pass | de-duplicated, moved to front, and reopened |
| Thumbnail extraction | Pass | bundle FFmpeg returned a 3,012-byte preview |
| Fullscreen | Pass | entered and exited in probe and packaged app |
| PiP | Pass | entered/exited; non-PiP HUD controls were hidden |
| Clear Playlist | Pass | media cleared, index `-1`, empty state visible, progress 0 and disabled, thumbnail hidden |

There are no dedicated Previous or Next commands or buttons. Auto-next works,
but manual previous/next navigation is currently unsupported.

Deleting the currently playing playlist item leaves playback running while
`current_idx` becomes `-1`. The remaining playlist stays intact, but end-of-file
auto-next can no longer continue from that state.

## HDR State

### HDR10

- File opened and played with `videotoolbox-copy`.
- mpv recognized HEVC Main 10, `p010`, BT.2020 primaries, BT.2020 non-constant
  matrix, PQ gamma, and a 10,000-nit mastering maximum.
- Renderer options remained `target-trc=auto`, `target-prim=auto`,
  `target-peak=auto`, and `tone-mapping=auto`.

### HLG

- File opened and played with `videotoolbox-copy`.
- mpv recognized HEVC Main 10, `p010`, BT.2020 primaries, BT.2020 non-constant
  matrix, HLG gamma/light, and a 1,000-nit nominal maximum.
- The first generated fixture lost transfer metadata in VideoToolbox. The corpus
  generator now writes HEVC VUI with the bundled `hevc_metadata` bitstream filter.
- Renderer options remained automatic, as for HDR10.

The current host did not expose verifiable HDR display data through
`system_profiler`. No claim is made that Pavo preserves HDR output end to end or
that tone mapping is visually correct. HDR10 and HLG still require real HDR
display acceptance, and the full app still requires a real macOS 13 host test.

## Findings

### P1

1. Add a user-facing subtitle Off action. libmpv supports it, but the menu does not.
2. Define and implement manual Previous/Next playlist navigation, or explicitly
   remove it from the release capability target.
3. Fix deletion of the currently playing playlist item so the current index and
   subsequent auto-next behavior remain coherent.

### P2

1. Perform the final launch, OpenGL, playback, and thumbnail run on a real
   macOS 13 Apple Silicon host.
2. Perform HDR10 and HLG visual acceptance on a known HDR display, including
   output transfer function and tone-mapping verification.
3. Add a multi-gigabyte local file test. The current large-file evidence is a
   synthetic 134 MB, two-hour file and a 105 MB high-bitrate file.
4. Update `tools/media_runtime/README.md`; its Phase 2C blocker description still
   references the superseded PySide6 6.10.2/macOS 15 result.

### P3

1. Qt reports that `QT_MAC_WANTS_LAYER` has no effect because layer backing is
   always enabled on the current platform.
2. Qt reports a one-time font alias population cost for the `-apple-system`
   family used by existing styles.

## Not Covered

- Real macOS 13 hardware
- Verified HDR-capable display output and visual quality
- Multi-gigabyte files
- Damaged or partially downloaded media
- Encrypted, DRM-protected, Blu-ray, DVD, Dolby Vision, or network streams
- Intel or universal2 builds
- Signing, Hardened Runtime, notarization, DMG, and Gatekeeper

## Commands

```bash
/private/tmp/pavo-phase3a/venv/bin/python \
  tools/release_audit/generate_corpus.py \
  --ffmpeg /private/tmp/pavo-phase3a/dist/Pavo.app/Contents/Frameworks/ffmpeg \
  --output /private/tmp/pavo-phase3a/assets/generated \
  --vp9-source /private/tmp/pavo-phase3a/assets/downloaded/vp9-webm-project.webm \
  --av1-source /private/tmp/pavo-phase3a/assets/downloaded/jellyfin-av1-1080p-10bit-3m.mp4

HOME=/private/tmp/pavo-phase3a/home \
/private/tmp/pavo-phase3a/venv/bin/python \
  tools/release_audit/playback_probe.py \
  --project-root "$PWD" \
  --app /private/tmp/pavo-phase3a/dist/Pavo.app \
  --assets /private/tmp/pavo-phase3a/assets \
  --output /private/tmp/pavo-phase3a/results/playback-probe.json
```
