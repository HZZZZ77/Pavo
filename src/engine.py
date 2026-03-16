import os
import sys

import bootstrap
bootstrap.setup_pavo_env()

import mpv

class PavoEngine:
    def __init__(self):
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
            # 👑 记录当前的画面比例状态，默认为 Auto
            self.current_aspect = "Auto"
            print(f"[Engine] Initialization successful. (mpv version: {self.player.mpv_version})")
        except Exception as e:
            print(f"[Engine] Error: Initialization failed - {e}")
            self.player = None

    def play(self, media_path):
        if self.player:
            print(f"[Engine] Loading media: {media_path}")
            self.player.play(media_path)

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

    # ==========================================
    # 👑 新增：画面比例强制覆盖
    # ==========================================
    def set_aspect_ratio(self, ratio: str):
        if self.player:
            try:
                self.current_aspect = ratio
                if ratio == "Auto":
                    # mpv 中使用 "-1" 代表恢复视频的原始默认比例
                    self.player.video_aspect_override = "-1"
                else:
                    self.player.video_aspect_override = ratio
                print(f"[Engine] Aspect ratio set to: {ratio}")
            except Exception as e:
                print(f"[Engine] Error setting aspect ratio: {e}")

    # ==========================================
    # 轨道读取与切换系统
    # ==========================================
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