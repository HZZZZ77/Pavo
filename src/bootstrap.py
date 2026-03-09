import os
import sys
import locale

def setup_pavo_env():
    """为 Pavo 运行配置必要的 macOS 环境变量"""
    
    # 1. 处理语言环境，防止 mpv 在某些区域设置下解析浮点数崩溃
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # 2. 自动定位 Homebrew 安装的动态库路径 (兼容 M 系列和 Intel 芯片)
    brew_paths = ["/opt/homebrew/lib", "/usr/local/lib"]
    current_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    
    # 将存在的 brew 路径加入系统搜索路径
    new_paths = [p for p in brew_paths if os.path.exists(p)]
    if new_paths:
        os.environ["DYLD_LIBRARY_PATH"] = ":".join(new_paths) + (":" + current_dyld if current_dyld else "")

    # 3. 强制 Qt6 使用 OpenGL 渲染后端（这是后续嵌入 mpv 的绝对关键）
    os.environ["QSG_RHI_BACKEND"] = "opengl"
    
    # 4. 强制 macOS 开启窗口图层支持
    os.environ["QT_MAC_WANTS_LAYER"] = "1"

    print("🚀 Pavo 环境引导完成: 已配置渲染后端与引擎底层路径。")

if __name__ == "__main__":
    # 仅用于独立测试此文件是否报错
    setup_pavo_env()