import os
import locale

def setup_pavo_env():
    """为 Pavo 运行配置必要的 macOS 环境变量 (纯净开发版)"""
    try:
        locale.setlocale(locale.LC_NUMERIC, 'C')
    except:
        pass

    # 踏踏实实地使用系统里完好的 Homebrew mpv
    brew_paths = ["/opt/homebrew/lib", "/usr/local/lib"]
    current_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
    new_paths = [p for p in brew_paths if os.path.exists(p)]
    
    if new_paths:
        os.environ["DYLD_LIBRARY_PATH"] = ":".join(new_paths) + (":" + current_dyld if current_dyld else "")

    # 渲染后端配置
    os.environ["QSG_RHI_BACKEND"] = "opengl"
    os.environ["QT_MAC_WANTS_LAYER"] = "1"
    
    print("🚀 Pavo 环境引导完成 (开发模式)")

if __name__ == "__main__":
    setup_pavo_env()