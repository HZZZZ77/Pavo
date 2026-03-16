import os
import sys
import subprocess
import threading

import bootstrap
bootstrap.setup_pavo_env()

import mpv
from PySide6.QtCore import QObject, Signal

class PavoEngine(QObject):
    # 👑 专属的缩略图信号传输通道
    thumbnail_ready = Signal(int, bytes)

    def __init__(self):
        super().__init__()
        print("[Engine] Initializing Pavo engine...")
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
            
            # 👑 缩略图缓存池和当前路径
            self.thumb_cache = {}
            self.current_media_path = None
            
            print(f"[Engine] Initialization successful. (mpv version: {self.player.mpv_version})")
        except Exception as e:
            print(f"[Engine] Error: Initialization failed - {e}")
            self.player = None

    def play(self, media_path):
        if self.player:
            print(f"[Engine] Loading media: {media_path}")
            # 播放新视频时，清空截图缓存
            self.current_media_path = media_path
            self.thumb_cache.clear()
            self.player.play(media_path)

    # ==========================================
    # 👑 核心黑科技：后台幽灵极速抽帧
    # ==========================================
    def get_thumbnail(self, time_sec):
        if not self.current_media_path:
            return
            
        time_key = int(time_sec)
        
        # 1. 如果内存里已经有这张截图，直接秒回！
        if time_key in self.thumb_cache:
            self.thumbnail_ready.emit(time_key, self.thumb_cache[time_key])
            return

        # 2. 如果没有，开启独立后台线程去截取（绝对不卡UI和主画面）
        def _extract():
            try:
                # 极其暴力的 FFmpeg 抽帧命令，-ss 放在前面保证极速关键帧 seek
                # 输出 160px 宽的小图，直接打入管道内存 (pipe:1)
                cmd = [
                    'ffmpeg', '-y', '-ss', str(time_key), '-i', self.current_media_path,
                    '-vframes', '1', '-q:v', '2', '-vf', 'scale=160:-1', '-f', 'image2', 'pipe:1'
                ]
                
                # Windows 下隐藏 FFmpeg 弹出的黑框
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                out, _ = process.communicate()
                
                if out:
                    self.thumb_cache[time_key] = out
                    self.thumbnail_ready.emit(time_key, out)
            except Exception as e:
                # 如果用户没装 FFmpeg，就优雅地静默失败，UI 不显示图片即可
                print(f"[Engine] FFmpeg extract error (Install ffmpeg for thumbnails): {e}")

        threading.Thread(target=_extract, daemon=True).start()

    def set_playing(self, is_playing: bool):
        if self.player:
            self.player.pause = not is_playing
            state_str = "Playing" if is_playing else "Paused"
            print(f"[Engine] State changed to: {state_str}")

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
                print(f"[Engine] Playback speed set to: {speed}x")
            except Exception as e:
                print(f"[Engine] Error setting speed: {e}")

    def get_progress(self):
        try:
            if self.player:
                t = self.player.time_pos
                d = self.player.duration
                if t is not None and d is not None and d > 0:
                    return t, d
        except Exception:
            pass
        return 0, 0

    def seek_to_percent(self, percent: float):
        try:
            if self.player:
                d = self.player.duration
                if d is not None and d > 0:
                    target_time = d * percent
                    self.player.seek(target_time, reference="absolute", precision="keyframes")
        except Exception:
            pass

    def set_aspect_ratio(self, ratio: str):
        if self.player:
            try:
                self.current_aspect = ratio
                if ratio == "Auto":
                    self.player.video_aspect_override = "-1"
                else:
                    self.player.video_aspect_override = ratio
                print(f"[Engine] Aspect ratio set to: {ratio}")
            except Exception as e:
                print(f"[Engine] Error setting aspect ratio: {e}")

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
        except Exception as e:
            print(f"[Engine] Error getting {track_type} tracks: {e}")
        return tracks

    def get_audio_tracks(self):
        return self.get_tracks('audio')

    def get_subtitle_tracks(self):
        return self.get_tracks('sub')

    def set_audio_track(self, track_id):
        if self.player:
            try:
                self.player.aid = track_id
                print(f"[Engine] Audio track switched to: {track_id}")
            except Exception as e:
                print(f"[Engine] Error setting audio track: {e}")

    def set_subtitle_track(self, track_id):
        if self.player:
            try:
                self.player.sid = track_id
                print(f"[Engine] Subtitle track switched to: {track_id}")
            except Exception as e:
                print(f"[Engine] Error setting subtitle track: {e}")

    def add_external_subtitle(self, file_path):
        if self.player:
            try:
                self.player.sub_add(file_path)
                print(f"[Engine] External subtitle loaded: {file_path}")
            except Exception as e:
                print(f"[Engine] Error loading subtitle: {e}")