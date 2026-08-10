# Install Pavo 1.2.1 Beta

Pavo 1.2.1 Beta supports Apple Silicon Macs running macOS 13 or later.

This beta is not signed with an Apple Developer ID and is not notarized. macOS
will ask you to approve the app the first time it is opened.

## Download

1. Open the official
   [Pavo GitHub Releases](https://github.com/HZZZZ77/Pavo/releases) page.
2. Download `Pavo-1.2.1-beta-macos-arm64.zip`.
3. Do not download Pavo from third-party mirrors.
4. Compare the downloaded file's SHA-256 checksum with the checksum published
   in the GitHub Release:

```bash
shasum -a 256 Pavo-1.2.1-beta-macos-arm64.zip
```

## Install

1. Double-click the ZIP archive to extract `Pavo.app`.
2. Move `Pavo.app` to the Applications folder.

## First Launch

### Finder

1. Open the Applications folder in Finder.
2. Control-click or right-click Pavo.
3. Choose **Open**.
4. Review the macOS warning and choose **Open** again.

### System Settings

If macOS blocks Pavo without offering an Open button:

1. Try opening Pavo once.
2. Open **System Settings**.
3. Choose **Privacy & Security**.
4. Scroll to the Security section.
5. Find the message that Pavo was blocked and choose **Open Anyway**.
6. Confirm that you want to open Pavo.

Only approve Pavo when it was downloaded from the official GitHub Release and
its checksum matches the published value.

## Use Pavo

- Choose **File > Open File...** or press `Command-O`.
- Drag one or more local media files into the Pavo window.
- Use the Playback menu to move to the previous or next playlist item.

Pavo includes its own Python, mpv, and FFmpeg runtime. You do not need to
install Python or Homebrew.

## Remove Pavo

Quit Pavo and move `Pavo.app` from Applications to the Trash.

Pavo stores local application data in `~/.pavo_data.json` and logs in
`~/Library/Logs/Pavo/`. Remove those paths separately if you also want to delete
local recent-file and diagnostic data.
