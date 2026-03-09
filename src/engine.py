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
                keep_open="yes"
            )
            print(f"[Engine] Initialization successful. (mpv version: {self.player.mpv_version})")
        except Exception as e:
            print(f"[Engine] Error: Initialization failed - {e}")
            self.player = None

    def play(self, media_path):
        if self.player:
            print(f"[Engine] Loading media: {media_path}")
            self.player.play(media_path)

    # === 本次新增的“槽”函数：控制引擎的暂停与播放 ===
    def set_playing(self, is_playing: bool):
        if self.player:
            # mpv 底层的 pause 属性：True 代表暂停，False 代表播放
            # 所以我们要把传进来的 is_playing 状态反转一下赋给它
            self.player.pause = not is_playing
            
            # 打印严谨的英文日志，方便我们在终端追踪状态
            state_str = "Playing" if is_playing else "Paused"
            print(f"[Engine] State changed to: {state_str}")
            # === 本次新增的“槽”函数：控制音量与静音 ===
    def set_volume(self, volume: int):
        if self.player:
            # mpv 底层的 volume 属性接收 0-100 的数值
            self.player.volume = volume
            print(f"[Engine] Volume set to: {volume}")

    def set_mute(self, is_mute: bool):
        if self.player:
            # mpv 底层的 mute 属性接收 True/False
            self.player.mute = is_mute
            print(f"[Engine] Mute set to: {is_mute}")