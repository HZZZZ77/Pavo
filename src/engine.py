import os
import sys

import bootstrap
bootstrap.setup_pavo_env()

import mpv

class PavoEngine:
    def __init__(self):
        print("⚙️ 正在初始化 Pavo 引擎 (最终点火版)...")
        try:
            self.player = mpv.MPV(
                hwdec="auto",      # 【已修复】：正确的写法是 hwdec="auto"
                vo="libmpv",       # 必须保留，指定输出给 Qt 画板
                keep_open="yes"
            )
            print(f"✅ 引擎初始化成功！(mpv version: {self.player.mpv_version})")
        except Exception as e:
            print(f"❌ 引擎初始化失败: {e}")
            self.player = None

    def play(self, media_path):
        if self.player:
            print(f"▶️ 接收到播放指令: {media_path}")
            self.player.play(media_path)