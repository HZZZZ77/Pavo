import os
import sys

import bootstrap
bootstrap.setup_pavo_env()

import mpv

class PavoEngine:
    def __init__(self):
        print("[Engine] Initializing Pavo engine...")
        try:
            # === 【性能优化 1】：扩充底层网络与解码缓存区 ===
            self.player = mpv.MPV(
                hwdec="auto",
                vo="libmpv",
                keep_open="yes",
                cache="yes",                    # 强制开启网络缓存
                demuxer_max_bytes="100M",       # 向前预读最大 100MB
                demuxer_max_back_bytes="50M"    # 向后保留最大 50MB (防回退卡顿)
            )
            # 👑 新增：初始化记录倍速状态
            self.playback_speed = 1.0
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

    # ==========================================
    # 👑 新增：倍速控制方法 (变速箱)
    # ==========================================
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
                    # === 【性能优化 2】：极速关键帧跳转 ===
                    # reference="absolute" 表示跳转到绝对时间
                    # precision="keyframes" 表示寻找最近的关键帧，0 算力延迟
                    self.player.seek(target_time, reference="absolute", precision="keyframes")
        except Exception:
            pass