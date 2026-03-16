import os
import sys
import subprocess
import threading
import shutil

import bootstrap
bootstrap.setup_pavo_env()

import mpv
from PySide6.QtCore import QObject, Signal

class PavoEngine(QObject):
    thumbnail_ready = Signal(int, bytes)
    # 👑 新增：向外界汇报播放状态的专线
    file_ended = Signal()
    file_loaded = Signal()

    def __init__(self):
        super().__init__()
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
            
            self.thumb_cache = {}
            self.current_media_path = None
            
            # 👑 埋入探针：监听视频结尾和加载完成
            self.player.observe_property('eof-reached', self._on_eof)
            self.player.observe_property('duration', self._on_duration)
            
        except Exception as e:
            self.player = None

    def _on_eof(self, name, value):
        if value:
            self.file_ended.emit()

    def _on_duration(self, name, value):
        if value is not None and value > 0:
            self.file_loaded.emit()

    def play(self, media_path):
        if self.player:
            self.current_media_path = media_path
            self.thumb_cache.clear()
            self.player.play(media_path)

    def get_thumbnail(self, time_sec):
        if not self.current_media_path: return
        time_key = int(time_sec)
        
        if time_key in self.thumb_cache:
            self.thumbnail_ready.emit(time_key, self.thumb_cache[time_key])
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
                            ffmpeg_cmd = 'ffmpeg'
                            
                cmd = [
                    ffmpeg_cmd, '-y', '-ss', str(time_key), '-i', self.current_media_path,
                    '-vframes', '1', '-q:v', '2', '-vf', 'scale=160:-1', '-f', 'image2', 'pipe:1'
                ]
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
                print(f"[Engine] Extract error: {e}")
                
        threading.Thread(target=_extract, daemon=True).start()

    def set_playing(self, is_playing: bool):
        if self.player:
            self.player.pause = not is_playing

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
            except: pass

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
        except: pass

    def set_aspect_ratio(self, ratio: str):
        if self.player:
            try:
                self.current_aspect = ratio
                if ratio == "Auto":
                    self.player.video_aspect_override = "-1"
                else:
                    self.player.video_aspect_override = ratio
            except: pass

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
        except: pass
        return tracks

    def get_audio_tracks(self):
        return self.get_tracks('audio')

    def get_subtitle_tracks(self):
        return self.get_tracks('sub')

    def set_audio_track(self, track_id):
        if self.player:
            try:
                self.player.aid = track_id
            except: pass

    def set_subtitle_track(self, track_id):
        if self.player:
            try:
                self.player.sid = track_id
            except: pass

    def add_external_subtitle(self, file_path):
        if self.player:
            try:
                self.player.sub_add(file_path)
            except: pass