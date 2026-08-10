#!/usr/bin/env python3
"""Inventory third-party Mach-O content in a built Pavo.app."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APP = PROJECT_ROOT / "dist" / "Pavo.app"
FORBIDDEN_QT_COMPONENTS = (
    "QtNetwork",
    "QtPdf",
    "QtQml",
    "QtQuick",
    "QtVirtualKeyboard",
)
EXPECTED_QT_FRAMEWORKS = {
    "QtCore",
    "QtDBus",
    "QtGui",
    "QtOpenGL",
    "QtOpenGLWidgets",
    "QtSvg",
    "QtWidgets",
}
EXPECTED_QT_PLUGINS = {
    "PySide6/Qt/plugins/imageformats/libqjpeg.dylib",
    "PySide6/Qt/plugins/platforms/libqcocoa.dylib",
    "PySide6/Qt/plugins/styles/libqmacstyle.dylib",
}


def output(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def is_macho(path: Path) -> bool:
    return "Mach-O" in output(["file", "-b", str(path)])


def dependencies(path: Path) -> list[str]:
    lines = output(["otool", "-L", str(path)]).splitlines()[1:]
    return [line.strip().split(" (", 1)[0] for line in lines]


def component_for(relative: str) -> str:
    if relative == "Contents/MacOS/Pavo":
        return "Pavo and PyInstaller bootloader"
    if relative.endswith("libpython3.13.dylib"):
        return "CPython 3.13.12"
    if "/shiboken6/" in relative:
        return "shiboken6 6.9.3"
    if "/PySide6/Qt/lib/Qt" in relative or "/PySide6/Qt/plugins/" in relative:
        return "Qt 6.9.3"
    if "/PySide6/" in relative:
        return "PySide6 6.9.3"
    if relative.endswith("/libmpv.2.dylib"):
        return "mpv 0.41.0 media runtime"
    if relative.endswith("/ffmpeg"):
        return "FFmpeg 8.0.3 media runtime"
    return "unclassified"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", nargs="?", type=Path, default=DEFAULT_APP)
    parser.add_argument("--output", type=Path, help="Write the JSON report to this path.")
    args = parser.parse_args()
    app = args.app.resolve()
    if not (app / "Contents" / "MacOS" / "Pavo").is_file():
        raise RuntimeError(f"Not a Pavo application bundle: {app}")

    files = []
    for path in sorted(app.rglob("*")):
        if path.is_symlink() or not path.is_file() or not is_macho(path):
            continue
        relative = path.relative_to(app).as_posix()
        files.append(
            {
                "path": relative,
                "component": component_for(relative),
                "dependencies": dependencies(path),
            }
        )

    bundle_paths = {
        path.relative_to(app / "Contents" / "Frameworks").as_posix()
        for path in (app / "Contents" / "Frameworks").rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    qt_frameworks = {
        path.name.removesuffix(".framework")
        for path in (app / "Contents" / "Frameworks" / "PySide6" / "Qt" / "lib").glob("Qt*.framework")
    }
    qt_plugins = {path for path in bundle_paths if path.startswith("PySide6/Qt/plugins/")}
    forbidden = sorted(
        path
        for path in bundle_paths
        if any(component in path for component in FORBIDDEN_QT_COMPONENTS)
    )
    unclassified = sorted(item["path"] for item in files if item["component"] == "unclassified")
    macho_names = {Path(item["path"]).name for item in files}
    unresolved_rpath_dependencies = sorted(
        {
            dependency
            for item in files
            for dependency in item["dependencies"]
            if dependency.startswith("@rpath/")
            and Path(dependency).name not in macho_names
        }
    )
    report = {
        "app": str(app),
        "macho_file_count": len(files),
        "macho_files": files,
        "qt_frameworks": sorted(qt_frameworks),
        "qt_plugins": sorted(qt_plugins),
        "forbidden_qt_content": forbidden,
        "unexpected_qt_frameworks": sorted(qt_frameworks - EXPECTED_QT_FRAMEWORKS),
        "missing_qt_frameworks": sorted(EXPECTED_QT_FRAMEWORKS - qt_frameworks),
        "unexpected_qt_plugins": sorted(qt_plugins - EXPECTED_QT_PLUGINS),
        "missing_qt_plugins": sorted(EXPECTED_QT_PLUGINS - qt_plugins),
        "unclassified_macho_files": unclassified,
        "unresolved_rpath_dependencies": unresolved_rpath_dependencies,
    }
    failed = any(
        report[key]
        for key in (
            "forbidden_qt_content",
            "unexpected_qt_frameworks",
            "missing_qt_frameworks",
            "unexpected_qt_plugins",
            "missing_qt_plugins",
            "unclassified_macho_files",
            "unresolved_rpath_dependencies",
        )
    )
    report["result"] = "failed" if failed else "passed"
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
