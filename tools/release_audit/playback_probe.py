#!/usr/bin/env python3
"""Probe Pavo playback with its production engine, OpenGL widget, and bundled runtime."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time


def wait_until(app, predicate, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    app.processEvents()
    return bool(predicate())


def pump_events(app, duration: float, interval: float = 0.002) -> None:
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(interval)
    app.processEvents()


def property_value(player, name):
    try:
        return player._get_property(name)
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def compact_track(track: dict) -> dict:
    fields = (
        "id",
        "type",
        "src-id",
        "title",
        "lang",
        "codec",
        "decoder-desc",
        "selected",
        "external",
        "albumart",
    )
    return {field: track.get(field) for field in fields if field in track}


def capture_state(window) -> dict:
    player = window.engine.player
    tracks = property_value(player, "track-list") or []
    return {
        "path": property_value(player, "path"),
        "file_format": property_value(player, "file-format"),
        "duration": property_value(player, "duration"),
        "time_pos": property_value(player, "time-pos"),
        "pause": property_value(player, "pause"),
        "video_codec": property_value(player, "video-codec"),
        "audio_codec_name": property_value(player, "audio-codec-name"),
        "hwdec_current": property_value(player, "hwdec-current"),
        "hwdec_interop": property_value(player, "hwdec-interop"),
        "video_params": property_value(player, "video-params"),
        "video_out_params": property_value(player, "video-out-params"),
        "current_vo": property_value(player, "current-vo"),
        "vo_configured": property_value(player, "vo-configured"),
        "decoder_frame_drop_count": property_value(
            player, "decoder-frame-drop-count"
        ),
        "frame_drop_count": property_value(player, "frame-drop-count"),
        "mistimed_frame_count": property_value(player, "mistimed-frame-count"),
        "target_trc_option": property_value(player, "options/target-trc"),
        "target_prim_option": property_value(player, "options/target-prim"),
        "target_peak_option": property_value(player, "options/target-peak"),
        "tone_mapping_option": property_value(player, "options/tone-mapping"),
        "tracks": [compact_track(track) for track in tracks],
    }


def load_and_probe(app, window, path: Path, play_seconds: float = 1.2) -> dict:
    started = time.monotonic()
    window.load_local_video(str(path))
    loaded = wait_until(
        app,
        lambda: (property_value(window.engine.player, "duration") or 0) > 0,
        timeout=12.0,
    )
    load_ms = round((time.monotonic() - started) * 1000)
    start_position = property_value(window.engine.player, "time-pos") or 0
    wait_until(
        app,
        lambda: (property_value(window.engine.player, "time-pos") or 0)
        >= start_position + play_seconds,
        timeout=max(6.0, play_seconds + 4.0),
    )
    end_position = property_value(window.engine.player, "time-pos") or 0
    window.engine.set_playing(False)
    wait_until(app, lambda: property_value(window.engine.player, "pause") is True)
    state = capture_state(window)
    state.update(
        {
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "loaded": loaded,
            "load_ms": load_ms,
            "time_advanced": end_position > start_position + 0.4,
            "start_position": start_position,
            "end_position": end_position,
        }
    )
    return state


def run_control_regression(app, window, media: Path) -> dict:
    result = {"media": media.name}
    window.load_local_video(str(media))
    result["loaded"] = wait_until(
        app,
        lambda: (property_value(window.engine.player, "duration") or 0) > 0,
    )

    window.engine.set_playing(False)
    wait_until(app, lambda: property_value(window.engine.player, "pause") is True)
    paused_at = property_value(window.engine.player, "time-pos") or 0
    time.sleep(0.35)
    app.processEvents()
    paused_later = property_value(window.engine.player, "time-pos") or 0
    result["pause_stable"] = abs(paused_later - paused_at) < 0.2

    window.engine.set_playing(True)
    resumed = wait_until(
        app,
        lambda: (property_value(window.engine.player, "time-pos") or 0)
        > paused_later + 0.4,
    )
    result["resume_advanced"] = resumed

    window.engine.set_speed(1.5)
    result["speed_1_5"] = wait_until(
        app,
        lambda: abs((property_value(window.engine.player, "speed") or 0) - 1.5)
        < 0.01,
    )
    window.engine.set_speed(1.0)

    window.engine.set_volume(35)
    result["volume_35"] = wait_until(
        app,
        lambda: abs((property_value(window.engine.player, "volume") or 0) - 35)
        < 0.5,
    )

    duration = property_value(window.engine.player, "duration") or 0
    started = time.monotonic()
    window.engine.seek_to_percent(0.5)
    result["seek_completed"] = wait_until(
        app,
        lambda: abs(
            (property_value(window.engine.player, "time-pos") or 0)
            - duration * 0.5
        )
        < max(3.0, duration * 0.1),
    )
    result["seek_ms"] = round((time.monotonic() - started) * 1000)
    result["seek_position"] = property_value(window.engine.player, "time-pos")
    return result


def run_subtitle_regression(app, window, assets: Path) -> dict:
    media = assets / "generated" / "mkv-h264-multiaudio-subs.mkv"
    window.load_local_video(str(media))
    loaded = wait_until(
        app,
        lambda: (property_value(window.engine.player, "duration") or 0) > 0,
    )
    player = window.engine.player
    window.engine.set_playing(False)
    wait_until(app, lambda: property_value(player, "pause") is True)
    embedded = window.engine.get_subtitle_tracks()
    embedded_results = []
    for track in embedded:
        window.engine.set_subtitle_track(track["id"])
        selected = wait_until(
            app,
            lambda track_id=track["id"]: property_value(player, "sid")
            == track_id,
        )
        player.command("seek", 1.0, "absolute", "exact")
        wait_until(
            app,
            lambda: abs((property_value(player, "time-pos") or 0) - 1.0) < 0.2,
        )
        wait_until(app, lambda: property_value(player, "sub-text") is not None)
        embedded_results.append(
            {
                "track": track,
                "selected": selected,
                "sub_text": property_value(player, "sub-text"),
            }
        )

    external_results = []
    for filename in ("external-en.srt", "external-styled.ass"):
        path = assets / "generated" / filename
        before = {track["id"] for track in window.engine.get_subtitle_tracks()}
        window.engine.add_external_subtitle(str(path))
        added = wait_until(
            app,
            lambda: len(window.engine.get_subtitle_tracks()) > len(before),
        )
        external_tracks = [
            track
            for track in window.engine.get_subtitle_tracks()
            if track["id"] not in before
        ]
        selected = False
        subtitle_text = None
        if external_tracks:
            track_id = external_tracks[-1]["id"]
            window.engine.set_subtitle_track(track_id)
            selected = wait_until(
                app, lambda: property_value(player, "sid") == track_id
            )
            player.command("seek", 1.0, "absolute", "exact")
            wait_until(
                app,
                lambda: abs((property_value(player, "time-pos") or 0) - 1.0)
                < 0.2,
            )
            wait_until(app, lambda: property_value(player, "sub-text") is not None)
            subtitle_text = property_value(player, "sub-text")
        external_results.append(
            {
                "name": filename,
                "added": added,
                "selected": selected,
                "sub_text": subtitle_text,
            }
        )

    player.sid = "no"
    off_runtime = wait_until(app, lambda: property_value(player, "sid") in (False, "no"))
    return {
        "loaded": loaded,
        "embedded": embedded_results,
        "external": external_results,
        "off_runtime": off_runtime,
        "sub_delay": property_value(player, "sub-delay"),
        "ui_off_action_present": False,
    }


def run_audio_track_regression(app, window, media: Path) -> dict:
    window.load_local_video(str(media))
    loaded = wait_until(
        app,
        lambda: (property_value(window.engine.player, "duration") or 0) > 0,
    )
    player = window.engine.player
    tracks = window.engine.get_audio_tracks()
    results = []
    for track in tracks:
        window.engine.set_audio_track(track["id"])
        selected = wait_until(
            app,
            lambda track_id=track["id"]: property_value(player, "aid")
            == track_id,
        )
        results.append(
            {
                "track": track,
                "selected": selected,
                "audio_codec_name": property_value(player, "audio-codec-name"),
            }
        )
    return {"loaded": loaded, "tracks": results}


def run_sustained_performance(app, window, media: list[Path]) -> list[dict]:
    results = []
    for path in media:
        window.load_local_video(str(path))
        loaded = wait_until(
            app,
            lambda: (property_value(window.engine.player, "duration") or 0) > 0,
            timeout=12.0,
        )
        pump_events(app, 1.0)
        player = window.engine.player
        start_position = property_value(player, "time-pos") or 0
        start_decoder_drops = property_value(player, "decoder-frame-drop-count") or 0
        start_vo_drops = property_value(player, "frame-drop-count") or 0
        pump_events(app, 5.0)
        end_position = property_value(player, "time-pos") or 0
        end_decoder_drops = property_value(player, "decoder-frame-drop-count") or 0
        end_vo_drops = property_value(player, "frame-drop-count") or 0
        results.append(
            {
                "name": path.name,
                "loaded": loaded,
                "time_advanced": end_position - start_position,
                "hwdec_current": property_value(player, "hwdec-current"),
                "decoder_frame_drop_delta": (
                    end_decoder_drops - start_decoder_drops
                ),
                "vo_frame_drop_delta": end_vo_drops - start_vo_drops,
                "video_params": property_value(player, "video-params"),
            }
        )
    return results


def run_thumbnail_regression(app, window, media: Path) -> dict:
    window.load_local_video(str(media))
    loaded = wait_until(
        app,
        lambda: (property_value(window.engine.player, "duration") or 0) > 0,
    )
    received = []

    def on_thumbnail(media_path, generation_id, time_key, image):
        received.append(
            {
                "media_path": media_path,
                "generation_id": generation_id,
                "time_key": time_key,
                "bytes": len(image),
            }
        )

    window.engine.thumbnail_ready.connect(on_thumbnail)
    window.engine.get_thumbnail(2)
    ready = wait_until(app, lambda: bool(received), timeout=15.0)
    window.engine.thumbnail_ready.disconnect(on_thumbnail)
    return {
        "loaded": loaded,
        "ready": ready,
        "result": received[-1] if received else None,
    }


def run_playlist_regression(app, window, media: list[Path]) -> dict:
    window.clear_playlist()
    window.handle_dropped_files([str(path) for path in media])
    first_loaded = wait_until(
        app, lambda: window.engine.current_media_path == str(media[0])
    )
    playlist_count = len(window.playlist)
    recent_count = len(window.recent_files)

    second_item = window.playlist_ui.item(1)
    window._on_playlist_item_clicked(second_item)
    second_loaded = wait_until(
        app, lambda: window.engine.current_media_path == str(media[1])
    )
    window.playlist_ui.setCurrentRow(1)
    window.delete_selected_items()
    current_delete_state = {
        "playlist_count": len(window.playlist),
        "current_idx": window.current_idx,
        "media_path": window.engine.current_media_path,
    }

    window.add_recent_files([str(media[0])])
    recent_deduplicated = (
        window.recent_files.count(str(media[0])) == 1
        and window.recent_files[0] == str(media[0])
    )

    window.clear_playlist()
    window.handle_dropped_files([str(media[0]), str(media[1])])
    wait_until(app, lambda: window.engine.current_media_path == str(media[0]))
    duration = property_value(window.engine.player, "duration") or 0
    window.engine.player.command(
        "seek", max(0, duration - 0.25), "absolute", "exact"
    )
    window.engine.set_playing(True)
    auto_next_loaded = wait_until(
        app,
        lambda: window.engine.current_media_path == str(media[1]),
        timeout=5.0,
    )
    auto_next_playing = auto_next_loaded and wait_until(
        app,
        lambda: property_value(window.engine.player, "pause") is False
        and (property_value(window.engine.player, "time-pos") or 0) > 0.2,
    )

    window.clear_playlist()
    window.open_recent_file(str(media[0]))
    recent_opened = wait_until(
        app, lambda: window.engine.current_media_path == str(media[0])
    )

    window.clear_playlist()
    clear_state = {
        "playlist_empty": not window.playlist,
        "current_idx": window.current_idx,
        "media_path": window.engine.current_media_path,
        "empty_state_visible": window.empty_state.isVisible(),
        "progress_value": window.hud.progress_slider.value(),
        "progress_enabled": window.hud.progress_slider.isEnabled(),
        "thumbnail_hidden": window.thumb_popup.isHidden(),
    }
    return {
        "first_loaded": first_loaded,
        "second_loaded": second_loaded,
        "playlist_count": playlist_count,
        "recent_count": recent_count,
        "recent_deduplicated": recent_deduplicated,
        "recent_opened": recent_opened,
        "current_delete_state": current_delete_state,
        "auto_next_loaded": auto_next_loaded,
        "auto_next_playing": auto_next_playing,
        "clear_state": clear_state,
        "previous_next_controls_present": False,
    }


def run_window_regression(app, window, media: Path) -> dict:
    window.load_local_video(str(media))
    loaded = wait_until(
        app,
        lambda: (property_value(window.engine.player, "duration") or 0) > 0,
    )
    window.toggle_fullscreen()
    fullscreen_entered = wait_until(app, window.isFullScreen)
    window.toggle_fullscreen()
    fullscreen_exited = wait_until(app, lambda: not window.isFullScreen())

    window.toggle_pip()
    pip_entered = wait_until(app, lambda: window._is_pip)
    pip_hidden_controls = {
        "volume": window.hud.vol_slider.isHidden(),
        "subtitle": window.hud.subtitle_btn.isHidden(),
        "playlist": window.hud.playlist_btn.isHidden(),
        "settings": window.hud.settings_btn.isHidden(),
        "fullscreen": window.hud.fullscreen_btn.isHidden(),
    }
    window.toggle_pip()
    pip_exited = wait_until(app, lambda: not window._is_pip)
    return {
        "loaded": loaded,
        "fullscreen_entered": fullscreen_entered,
        "fullscreen_exited": fullscreen_exited,
        "pip_entered": pip_entered,
        "pip_hidden_controls": pip_hidden_controls,
        "pip_exited": pip_exited,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--section",
        action="append",
        choices=(
            "video",
            "audio",
            "controls",
            "long-seek",
            "performance",
            "audio-tracks",
            "subtitles",
            "thumbnail",
            "playlist",
            "window",
        ),
        help="Run only the selected section; may be repeated.",
    )
    parser.add_argument(
        "--video-name",
        action="append",
        help="Limit the video matrix to specific asset filenames.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    app_bundle = args.app.resolve()
    assets = args.assets.resolve()
    bundled_runtime = app_bundle / "Contents" / "Frameworks"
    os.environ["PAVO_LIBMPV_PATH"] = str(bundled_runtime / "libmpv.2.dylib")
    os.environ["PAVO_FFMPEG_PATH"] = str(bundled_runtime / "ffmpeg")
    sys.path.insert(0, str(project_root / "src"))

    from PySide6.QtWidgets import QApplication
    from main import PavoPlayer

    application = QApplication(["Pavo Phase 3A playback probe"])
    window = PavoPlayer()
    window.resize(960, 540)
    window.show()
    opengl_ready = wait_until(
        application, lambda: window.video_canvas.render_ctx is not None
    )

    generated = assets / "generated"
    downloaded = assets / "downloaded"
    video_cases = [
        generated / "mp4-h264-aac-1080p.mp4",
        generated / "mov-hevc-aac-1080p.mov",
        generated / "webm-vp9-opus.webm",
        generated / "mkv-av1-flac.mkv",
        generated / "mp4-hevc-4k60-high-bitrate.mp4",
        generated / "mp4-h264-long-2h.mp4",
        downloaded / "jellyfin-hevc-hdr10-1080p-3m.mp4",
        generated / "mp4-hevc-hlg-1080p.mp4",
    ]
    audio_cases = [
        generated / "audio-aac.m4a",
        downloaded / "wikimedia-110-sine-wave.mp3",
        generated / "audio-flac.flac",
        generated / "audio-opus.opus",
        generated / "audio-ac3.ac3",
        generated / "audio-eac3.eac3",
    ]

    errors = []
    window.engine.error_occurred.connect(errors.append)
    sections = set(args.section or ())
    run_all = not sections
    if args.video_name:
        selected_names = set(args.video_name)
        video_cases = [path for path in video_cases if path.name in selected_names]

    report = {
        "opengl_render_context": opengl_ready,
        "bundle_libmpv": os.environ["PAVO_LIBMPV_PATH"],
        "bundle_ffmpeg": os.environ["PAVO_FFMPEG_PATH"],
        "errors": errors,
    }
    if run_all or "video" in sections:
        report["video_matrix"] = [
            load_and_probe(application, window, path) for path in video_cases
        ]
    if run_all or "audio" in sections:
        report["audio_matrix"] = [
            load_and_probe(application, window, path, play_seconds=0.8)
            for path in audio_cases
        ]
    if run_all or "controls" in sections:
        report["controls"] = run_control_regression(
            application, window, generated / "mp4-h264-aac-1080p.mp4"
        )
    if run_all or "long-seek" in sections:
        report["long_seek"] = run_control_regression(
            application, window, generated / "mp4-h264-long-2h.mp4"
        )
    if run_all or "performance" in sections:
        report["performance"] = run_sustained_performance(
            application,
            window,
            [
                generated / "mp4-h264-aac-1080p.mp4",
                generated / "mkv-av1-flac.mkv",
                generated / "mp4-hevc-4k60-high-bitrate.mp4",
                downloaded / "jellyfin-hevc-hdr10-1080p-3m.mp4",
                generated / "mp4-hevc-hlg-1080p.mp4",
            ],
        )
    if run_all or "audio-tracks" in sections:
        report["audio_tracks"] = run_audio_track_regression(
            application, window, generated / "mkv-h264-multiaudio-subs.mkv"
        )
    if run_all or "subtitles" in sections:
        report["subtitles"] = run_subtitle_regression(
            application, window, assets
        )
    if run_all or "thumbnail" in sections:
        report["thumbnail"] = run_thumbnail_regression(
            application, window, generated / "mp4-h264-aac-1080p.mp4"
        )
    if run_all or "playlist" in sections:
        report["playlist"] = run_playlist_regression(
            application,
            window,
            [
                generated / "mp4-h264-aac-1080p.mp4",
                generated / "mov-hevc-aac-1080p.mov",
                generated / "webm-vp9-opus.webm",
            ],
        )
    if run_all or "window" in sections:
        report["window_modes"] = run_window_regression(
            application, window, generated / "mp4-h264-aac-1080p.mp4"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    window.close()
    application.processEvents()
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
