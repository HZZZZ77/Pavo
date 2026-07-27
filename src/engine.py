import os
import sys
import subprocess
import threading
import shutil
import logging

import bootstrap
bootstrap.setup_pavo_env()

logger = logging.getLogger("pavo.engine")

import mpv
from PySide6.QtCore import QObject, Signal

class PavoEngine(QObject):
    thumbnail_ready = Signal(str, int, int, bytes)
    # 👑 新增：向外界汇报播放状态的专线
    file_ended = Signal()
    file_loaded = Signal()
    error_occurred = Signal(str)
    play_state_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.thumb_cache = {}
        self.thumb_inflight = set()
        self.thumb_lock = threading.Lock()
        self.thumbnail_generation_id = 0
        self.current_media_path = None
        try:
            self.player = mpv.MPV(
                hwdec="auto",
                vo="libmpv",
                keep_open="yes",
                cache="yes",
                demuxer_max_bytes="100M",
                demuxer_max_back_bytes="50M"
            )
            self.playback_speed = 1.0
            self.current_aspect = "Auto"
            
            # 👑 埋入探针：监听视频结尾和加载完成
            self.player.observe_property('eof-reached', self._on_eof)
            self.player.observe_property('duration', self._on_duration)
            self.player.observe_property('pause', self._on_pause)
            
        except Exception as e:
            logger.exception("Failed to initialize mpv")
            self.player = None
            self.init_error = str(e)
        else:
            logger.info("mpv initialized")
            self.init_error = None

    def _on_eof(self, name, value):
        if value:
            self.file_ended.emit()

    def _on_duration(self, name, value):
        if value is not None and value > 0:
            self.file_loaded.emit()

    def _on_pause(self, name, value):
        if value is not None:
            self.play_state_changed.emit(not value)

    def play(self, media_path):
        if not self.player:
            logger.error("Playback requested without an initialized mpv player")
            self.error_occurred.emit("Playback engine failed to initialize.")
            return False

        media_name = os.path.basename(media_path)
        if not os.path.exists(media_path):
            logger.warning("Media file not found: %s", media_name)
            self.error_occurred.emit(f"File not found: {os.path.basename(media_path)}")
            return False

        try:
            logger.info("Opening media: %s", media_name)
            with self.thumb_lock:
                self.thumbnail_generation_id += 1
                self.current_media_path = media_path
                self.thumb_cache.clear()
                self.thumb_inflight.clear()
            self.player.play(media_path)
            self.player.pause = False
            self.play_state_changed.emit(True)
            return True
        except Exception as e:
            logger.exception("Playback failed for %s", media_name)
            self.error_occurred.emit(f"Playback failed: {e}")
            return False

    def get_thumbnail(self, time_sec):
        with self.thumb_lock:
            media_path = self.current_media_path
            generation_id = self.thumbnail_generation_id
            if not media_path: return
            time_key = int(time_sec)
            request_key = (media_path, time_key)
            if request_key in self.thumb_cache:
                cached = self.thumb_cache[request_key]
            else:
                cached = None
                if request_key in self.thumb_inflight:
                    return
                self.thumb_inflight.add(request_key)

        if cached is not None:
            self.thumbnail_ready.emit(media_path, generation_id, time_key, cached)
            return

        def _extract():
            try:
                ffmpeg_cmd = None
                
                # 👑 核心魔法：PyInstaller 打包后的专属路径寻址 (sys._MEIPASS)
                if hasattr(sys, '_MEIPASS'):
                    bundled_ffmpeg = os.path.join(sys._MEIPASS, 'ffmpeg')
                    if os.path.exists(bundled_ffmpeg):
                        ffmpeg_cmd = bundled_ffmpeg
                
                # 如果没打包（本地写代码测试时），用系统里的 ffmpeg
                if not ffmpeg_cmd:
                    ffmpeg_cmd = shutil.which('ffmpeg')
                    if not ffmpeg_cmd:
                        if os.path.exists('/opt/homebrew/bin/ffmpeg'):
                            ffmpeg_cmd = '/opt/homebrew/bin/ffmpeg'
                        elif os.path.exists('/usr/local/bin/ffmpeg'):
                            ffmpeg_cmd = '/usr/local/bin/ffmpeg'
                        else:
                            logger.warning("FFmpeg not found; thumbnail preview is unavailable")
                            self.error_occurred.emit("FFmpeg not found. Thumbnail preview is unavailable.")
                            return
                            
                cmd = [
                    ffmpeg_cmd, '-y', '-ss', str(time_key), '-i', media_path,
                    '-vframes', '1', '-q:v', '2', '-vf', 'scale=160:-1', '-f', 'image2', 'pipe:1'
                ]
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                out, _ = process.communicate()

                if process.returncode != 0:
                    logger.warning(
                        "FFmpeg thumbnail extraction failed for %s at %ss with exit code %s",
                        os.path.basename(media_path),
                        time_key,
                        process.returncode,
                    )
                    return
                if not out:
                    logger.warning(
                        "FFmpeg produced no thumbnail for %s at %ss",
                        os.path.basename(media_path),
                        time_key,
                    )
                    return

                with self.thumb_lock:
                    should_emit = media_path == self.current_media_path and generation_id == self.thumbnail_generation_id
                    if not should_emit:
                        return
                    self.thumb_cache[request_key] = out
                self.thumbnail_ready.emit(media_path, generation_id, time_key, out)
            except Exception:
                logger.exception(
                    "Thumbnail extraction failed for %s at %ss",
                    os.path.basename(media_path),
                    time_key,
                )
            finally:
                with self.thumb_lock:
                    self.thumb_inflight.discard(request_key)
                
        threading.Thread(target=_extract, daemon=True).start()

    def set_playing(self, is_playing: bool):
        if self.player:
            self.player.pause = not is_playing

    def stop(self):
        with self.thumb_lock:
            self.thumbnail_generation_id += 1
            self.current_media_path = None
            self.thumb_cache.clear()
            self.thumb_inflight.clear()
        if self.player:
            try:
                self.player.command('stop')
            except Exception:
                logger.debug("mpv stop command failed; trying fallback", exc_info=True)
                try:
                    self.player.stop()
                except Exception:
                    logger.exception("Failed to stop mpv")
        self.play_state_changed.emit(False)

    def set_volume(self, volume: int):
        if self.player:
            self.player.volume = volume

    def set_mute(self, is_mute: bool):
        if self.player:
            self.player.mute = is_mute

    def set_speed(self, speed: float):
        if self.player:
            try:
                self.player.speed = speed
                self.playback_speed = speed
            except Exception:
                logger.warning("Failed to set playback speed to %s", speed, exc_info=True)

    def get_progress(self):
        try:
            if self.player:
                t = self.player.time_pos
                d = self.player.duration
                if t is not None and d is not None and d > 0:
                    return t, d
        except: pass
        return 0, 0

    def seek_to_percent(self, percent: float):
        try:
            if self.player:
                d = self.player.duration
                if d is not None and d > 0:
                    target_time = d * percent
                    self.player.seek(target_time, reference="absolute", precision="keyframes")
        except Exception:
            logger.warning("Failed to seek to %.2f%%", percent * 100, exc_info=True)

    def set_aspect_ratio(self, ratio: str):
        if self.player:
            try:
                self.current_aspect = ratio
                if ratio == "Auto":
                    self.player.video_aspect_override = "-1"
                else:
                    self.player.video_aspect_override = ratio
            except Exception:
                logger.warning("Failed to set aspect ratio to %s", ratio, exc_info=True)

    def get_tracks(self, track_type):
        tracks = []
        try:
            if not self.player: return tracks
            for t in getattr(self.player, 'track_list', []):
                if t.get('type') == track_type:
                    t_id = t.get('id')
                    lang = t.get('lang', '')
                    title = t.get('title', '')
                    
                    if title and lang: name = f"[{lang}] {title}"
                    elif title: name = title
                    elif lang: name = f"Track {t_id} ({lang})"
                    else: name = f"Track {t_id}"
                    
                    tracks.append({
                        'id': t_id,
                        'name': name,
                        'selected': t.get('selected', False)
                    })
        except Exception:
            logger.warning("Failed to read %s tracks", track_type, exc_info=True)
        return tracks

    def get_audio_tracks(self):
        return self.get_tracks('audio')

    def get_subtitle_tracks(self):
        return self.get_tracks('sub')

    def set_audio_track(self, track_id):
        if self.player:
            try:
                self.player.aid = track_id
            except Exception:
                logger.warning("Failed to select audio track %s", track_id, exc_info=True)

    def set_subtitle_track(self, track_id):
        if self.player:
            try:
                self.player.sid = track_id
            except Exception:
                logger.warning("Failed to select subtitle track %s", track_id, exc_info=True)

    def add_external_subtitle(self, file_path):
        if self.player:
            try:
                self.player.sub_add(file_path)
            except Exception:
                logger.warning(
                    "Failed to load external subtitle %s",
                    os.path.basename(file_path),
                    exc_info=True,
                )
