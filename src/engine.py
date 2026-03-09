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