# Pavo Beta FAQ

## Why Does macOS Say Pavo Is From An Unidentified Developer?

Pavo 1.2.1 Beta is not signed with an Apple Developer ID and has not been
notarized by Apple. macOS therefore cannot verify the publisher automatically.

Follow the [installation guide](INSTALL.md) to approve the unsigned beta
manually.

## Why Is Pavo Not Apple-Signed?

The project does not currently have an Apple Developer account. Developer ID
signing and Apple notarization require that account and will be considered for a
future stable release.

The beta still uses internal ad-hoc signatures so macOS can validate the
integrity of the assembled app bundle, but an ad-hoc signature does not verify
the publisher.

## Is Pavo Safe?

Pavo is open source, and its release build is produced from the public
repository with pinned dependencies and a reproducible bundled media runtime.
The beta package is checked for unexpected Homebrew or other non-system dynamic
dependencies.

No software can be guaranteed safe solely because it is open source. Because
this beta is not Apple-signed or notarized:

- Download it only from the official Pavo GitHub Releases page.
- Compare the archive's SHA-256 checksum with the release notes.
- Do not install copies from third-party mirrors.
- Build Pavo from source if you need to inspect the complete build path.

## Does Pavo Collect Data?

Pavo does not include accounts, analytics, telemetry, advertising, or cloud
sync. It does not send your playback history to the project.

Pavo stores recent files and local playback state in `~/.pavo_data.json`.
Diagnostic logs are written to `~/Library/Logs/Pavo/pavo.log`. These files stay
on your Mac unless you choose to share them.

Logs can contain media filenames or paths. Remove private information before
posting logs publicly.

## Do I Need Python, Homebrew, mpv, Or FFmpeg?

No. The macOS beta bundle includes the Python, PySide6, mpv, and FFmpeg runtime
needed by Pavo.

## Which Macs Are Supported?

Pavo 1.2.1 Beta targets Apple Silicon Macs running macOS 13 or later. Intel Macs
are not supported by this release.

## How Do I Report A Bug?

1. Review the current [Known Issues](docs/release/KNOWN_ISSUES.md).
2. Search existing [GitHub Issues](https://github.com/HZZZZ77/Pavo/issues).
3. Open a new report using the
   [bug report template](https://github.com/HZZZZ77/Pavo/issues/new/choose).

Include your Pavo version, macOS version, Mac model, reproduction steps, and
relevant media details. Do not upload copyrighted or private media.

For security vulnerabilities, follow the private reporting process in
[SECURITY.md](SECURITY.md) instead of opening a public issue.
