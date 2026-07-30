#!/usr/bin/env python3
"""Generate Pavo's local playback audit corpus with the bundled FFmpeg."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ffmpeg_command(ffmpeg: Path, output: Path, *arguments: str) -> list[str]:
    return [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        *arguments,
        str(output),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vp9-source", type=Path, required=True)
    parser.add_argument("--av1-source", type=Path, required=True)
    args = parser.parse_args()

    ffmpeg = args.ffmpeg.resolve()
    output = args.output.resolve()
    vp9_source = args.vp9_source.resolve()
    av1_source = args.av1_source.resolve()
    for path in (ffmpeg, vp9_source, av1_source):
        if not path.is_file():
            parser.error(f"required input is missing: {path}")
    output.mkdir(parents=True, exist_ok=True)

    tone = output / "tone.wav"
    run(
        ffmpeg_command(
            ffmpeg,
            tone,
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=12",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
        )
    )

    audio_outputs = {
        "audio-aac.m4a": ("aac", "192k"),
        "audio-flac.flac": ("flac", None),
        "audio-opus.opus": ("opus", "128k"),
        "audio-ac3.ac3": ("ac3", "384k"),
        "audio-eac3.eac3": ("eac3", "384k"),
    }
    for filename, (codec, bitrate) in audio_outputs.items():
        arguments = ["-i", str(tone), "-c:a", codec]
        if bitrate:
            arguments.extend(["-b:a", bitrate])
        if codec == "opus":
            arguments.extend(["-strict", "experimental"])
        run(ffmpeg_command(ffmpeg, output / filename, *arguments))

    h264_1080p = output / "mp4-h264-aac-1080p.mp4"
    run(
        ffmpeg_command(
            ffmpeg,
            h264_1080p,
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1920x1080:rate=30:duration=12",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=660:sample_rate=48000:duration=12",
            "-c:v",
            "h264_videotoolbox",
            "-b:v",
            "8M",
            "-maxrate",
            "12M",
            "-bufsize",
            "16M",
            "-pix_fmt",
            "nv12",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        )
    )

    run(
        ffmpeg_command(
            ffmpeg,
            output / "mov-hevc-aac-1080p.mov",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1920x1080:rate=30:duration=12",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:sample_rate=48000:duration=12",
            "-c:v",
            "hevc_videotoolbox",
            "-b:v",
            "10M",
            "-maxrate",
            "15M",
            "-bufsize",
            "20M",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "nv12",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
        )
    )

    hlg_raw = output / "mp4-hevc-hlg-1080p-raw.mp4"
    hlg_output = output / "mp4-hevc-hlg-1080p.mp4"
    run(
        ffmpeg_command(
            ffmpeg,
            hlg_raw,
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1920x1080:rate=30:duration=12",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=550:sample_rate=48000:duration=12",
            "-vf",
            "format=p010le",
            "-c:v",
            "hevc_videotoolbox",
            "-profile:v",
            "main10",
            "-b:v",
            "12M",
            "-maxrate",
            "18M",
            "-bufsize",
            "24M",
            "-tag:v",
            "hvc1",
            "-color_primaries",
            "bt2020",
            "-color_trc",
            "arib-std-b67",
            "-colorspace",
            "bt2020nc",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        )
    )
    run(
        ffmpeg_command(
            ffmpeg,
            hlg_output,
            "-i",
            str(hlg_raw),
            "-map",
            "0",
            "-c",
            "copy",
            "-bsf:v",
            (
                "hevc_metadata=colour_primaries=9:"
                "transfer_characteristics=18:matrix_coefficients=9"
            ),
        )
    )
    hlg_raw.unlink()

    run(
        ffmpeg_command(
            ffmpeg,
            output / "mp4-hevc-4k60-high-bitrate.mp4",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x2160:rate=60:duration=15",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=990:sample_rate=48000:duration=15",
            "-c:v",
            "hevc_videotoolbox",
            "-b:v",
            "60M",
            "-maxrate",
            "80M",
            "-bufsize",
            "120M",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "nv12",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
        )
    )

    run(
        ffmpeg_command(
            ffmpeg,
            output / "mp4-h264-long-2h.mp4",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1280x720:rate=1:duration=7200",
            "-c:v",
            "h264_videotoolbox",
            "-b:v",
            "500k",
            "-maxrate",
            "800k",
            "-bufsize",
            "1M",
            "-g",
            "30",
            "-pix_fmt",
            "nv12",
            "-an",
            "-movflags",
            "+faststart",
        )
    )

    run(
        ffmpeg_command(
            ffmpeg,
            output / "webm-vp9-opus.webm",
            "-stream_loop",
            "180",
            "-i",
            str(vp9_source),
            "-stream_loop",
            "1",
            "-i",
            str(output / "audio-opus.opus"),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-t",
            "10",
            "-c",
            "copy",
        )
    )

    run(
        ffmpeg_command(
            ffmpeg,
            output / "mkv-av1-flac.mkv",
            "-i",
            str(av1_source),
            "-stream_loop",
            "1",
            "-i",
            str(output / "audio-flac.flac"),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-t",
            "12",
            "-c",
            "copy",
        )
    )

    run(
        ffmpeg_command(
            ffmpeg,
            output / "mkv-h264-multiaudio-subs.mkv",
            "-i",
            str(h264_1080p),
            "-i",
            str(output / "audio-ac3.ac3"),
            "-i",
            str(output / "audio-eac3.eac3"),
            "-i",
            str(output / "external-en.srt"),
            "-i",
            str(output / "external-styled.ass"),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-map",
            "1:a:0",
            "-map",
            "2:a:0",
            "-map",
            "3:0",
            "-map",
            "4:0",
            "-c",
            "copy",
            "-metadata:s:a:0",
            "language=eng",
            "-metadata:s:a:0",
            "title=AAC",
            "-metadata:s:a:1",
            "language=fra",
            "-metadata:s:a:1",
            "title=AC-3",
            "-metadata:s:a:2",
            "language=deu",
            "-metadata:s:a:2",
            "title=E-AC-3",
            "-metadata:s:s:0",
            "language=eng",
            "-metadata:s:s:0",
            "title=SRT",
            "-metadata:s:s:1",
            "language=eng",
            "-metadata:s:s:1",
            "title=ASS",
        )
    )

    for path in sorted(output.iterdir()):
        if path.is_file():
            print(f"{path.name}\t{path.stat().st_size}\t{sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
