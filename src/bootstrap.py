from contextlib import contextmanager
import ctypes.util
import os
import locale
import logging
from pathlib import Path
import shutil
import sys

from logging_config import setup_logging


logger = logging.getLogger("pavo.bootstrap")


LIBMPV_FILENAME = "libmpv.2.dylib"
FFMPEG_FILENAME = "ffmpeg"


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def _bundled_runtime_candidates(filename):
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / filename)

    if is_frozen():
        contents_dir = Path(sys.executable).resolve().parent.parent
        candidates.append(contents_dir / "Frameworks" / filename)

    return candidates


def _first_existing_file(candidates, *, executable=False):
    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file() and (not executable or os.access(path, os.X_OK)):
            return str(path.resolve())
    return None


def resolve_libmpv_path():
    """Return the libmpv path for the packaged app or source development."""
    if is_frozen():
        return _first_existing_file(_bundled_runtime_candidates(LIBMPV_FILENAME))

    override = os.environ.get("PAVO_LIBMPV_PATH")
    if override:
        resolved = _first_existing_file([override])
        if resolved:
            return resolved
        logger.warning("PAVO_LIBMPV_PATH does not point to a file: %s", override)

    system_library = ctypes.util.find_library("mpv")
    if system_library:
        return system_library

    return _first_existing_file(
        [
            "/opt/homebrew/lib/libmpv.2.dylib",
            "/opt/homebrew/lib/libmpv.dylib",
            "/usr/local/lib/libmpv.2.dylib",
            "/usr/local/lib/libmpv.dylib",
        ]
    )


@contextmanager
def use_resolved_libmpv():
    """Direct python-mpv's import-time lookup to Pavo's selected libmpv."""
    libmpv_path = resolve_libmpv_path()
    if is_frozen() and not libmpv_path:
        raise OSError("Bundled libmpv.2.dylib is missing from Pavo.app.")
    if not libmpv_path:
        yield
        return

    original_find_library = ctypes.util.find_library

    def find_library(name):
        if name == "mpv":
            return libmpv_path
        return original_find_library(name)

    runtime_kind = "bundled" if is_frozen() else "development"
    logger.info("Using %s libmpv: %s", runtime_kind, libmpv_path)
    ctypes.util.find_library = find_library
    try:
        yield
    finally:
        ctypes.util.find_library = original_find_library


def resolve_ffmpeg_path():
    """Return the bundled FFmpeg path, or a source-development fallback."""
    if is_frozen():
        return _first_existing_file(
            _bundled_runtime_candidates(FFMPEG_FILENAME),
            executable=True,
        )

    override = os.environ.get("PAVO_FFMPEG_PATH")
    if override:
        resolved = _first_existing_file([override], executable=True)
        if resolved:
            return resolved
        logger.warning("PAVO_FFMPEG_PATH is not executable: %s", override)

    system_ffmpeg = shutil.which(FFMPEG_FILENAME)
    if system_ffmpeg:
        return system_ffmpeg

    return _first_existing_file(
        [
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
        ],
        executable=True,
    )


def setup_pavo_env():
    """为 Pavo 运行配置必要的 macOS 环境变量 (纯净开发版)"""
    setup_logging()
    try:
        locale.setlocale(locale.LC_NUMERIC, 'C')
    except Exception:
        logger.exception("Failed to set the numeric locale to C")

    # 渲染后端配置
    os.environ["QSG_RHI_BACKEND"] = "opengl"
    os.environ["QT_MAC_WANTS_LAYER"] = "1"

if __name__ == "__main__":
    setup_pavo_env()
