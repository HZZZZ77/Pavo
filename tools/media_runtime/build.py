#!/usr/bin/env python3
"""Build Pavo's self-contained macOS arm64 media runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).with_name("sources.json")
BUILD_ROOT = PROJECT_ROOT / "build" / "media-runtime"
DOWNLOADS_DIR = BUILD_ROOT / "downloads"
SOURCES_DIR = BUILD_ROOT / "sources"
WORK_DIR = BUILD_ROOT / "work"
PREFIX_DIR = BUILD_ROOT / "prefix"
DIST_DIR = BUILD_ROOT / "dist"
TOOLS_VENV = BUILD_ROOT / "tools-venv"

MINIMUM_MACOS = "13.0"
ARCHITECTURE = "arm64"
MESON_VERSION = "1.9.1"
NINJA_VERSION = "1.13.0"


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    shown = " ".join(command)
    print(f"\n+ {shown}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def output(command: list[str]) -> str:
    return subprocess.check_output(command, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as stream:
        return json.load(stream)


def validate_host() -> str:
    if sys.platform != "darwin":
        raise RuntimeError("The media runtime can only be built on macOS.")
    if platform.machine() != ARCHITECTURE:
        raise RuntimeError(f"Expected an {ARCHITECTURE} host, found {platform.machine()}.")
    sdk_path = output(["xcrun", "--show-sdk-path"])
    if not Path(sdk_path).is_dir():
        raise RuntimeError(f"Active macOS SDK does not exist: {sdk_path}")
    return sdk_path


def ensure_tools(offline: bool) -> tuple[Path, Path]:
    python = TOOLS_VENV / "bin" / "python"
    if not python.exists():
        if offline:
            raise RuntimeError("The build tools venv is missing in offline mode.")
        run([sys.executable, "-m", "venv", str(TOOLS_VENV)])

    meson = TOOLS_VENV / "bin" / "meson"
    ninja = TOOLS_VENV / "bin" / "ninja"
    tools_ok = False
    if meson.exists() and ninja.exists():
        tools_ok = (
            output([str(meson), "--version"]) == MESON_VERSION
            and output([str(ninja), "--version"]).startswith(NINJA_VERSION)
        )

    if not tools_ok:
        if offline:
            raise RuntimeError("Pinned Meson/Ninja versions are unavailable in offline mode.")
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                f"meson=={MESON_VERSION}",
                f"ninja=={NINJA_VERSION}",
            ]
        )
    return meson, ninja


def download_sources(config: dict, offline: bool) -> None:
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    for source in config["sources"]:
        archive = DOWNLOADS_DIR / source["archive"]
        if archive.exists() and sha256(archive) == source["sha256"]:
            print(f"Using cached {source['archive']}")
            continue
        if offline:
            raise RuntimeError(f"Missing verified source archive: {archive}")
        temporary = archive.with_suffix(archive.suffix + ".download")
        if temporary.exists():
            temporary.unlink()
        print(f"Downloading {source['name']} {source['version']}")
        urllib.request.urlretrieve(source["url"], temporary)
        actual = sha256(temporary)
        if actual != source["sha256"]:
            temporary.unlink()
            raise RuntimeError(
                f"SHA-256 mismatch for {source['archive']}: expected "
                f"{source['sha256']}, got {actual}"
            )
        temporary.replace(archive)


def extract_sources(config: dict) -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    for source in config["sources"]:
        destination = SOURCES_DIR / source["directory"]
        if destination.is_dir():
            continue
        archive = DOWNLOADS_DIR / source["archive"]
        print(f"Extracting {source['archive']}")
        with tarfile.open(archive) as tar:
            tar.extractall(SOURCES_DIR, filter="data")
        if not destination.is_dir():
            raise RuntimeError(f"Archive did not create expected directory: {destination}")


def prepare_libplacebo_subprojects(config: dict) -> None:
    thirdparty = SOURCES_DIR / "libplacebo-v7.360.0" / "3rdparty"
    for source in config["sources"]:
        subproject = source.get("libplacebo_subproject")
        if not subproject:
            continue
        destination = thirdparty / subproject
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(SOURCES_DIR / source["directory"], destination)


def apply_source_patches(config: dict) -> None:
    source = SOURCES_DIR / "mpv-0.41.0"
    marker = "CoreAudio and AVFoundation also use these helpers"
    meson_file = source / "meson.build"
    if marker in meson_file.read_text(encoding="utf-8"):
        return
    patch_config = config["patches"][0]
    patch_file = Path(__file__).parent / patch_config["file"]
    if sha256(patch_file) != patch_config["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch for source patch: {patch_file}")
    run(
        [
            "patch",
            "-p1",
            "-i",
            str(patch_file),
        ],
        cwd=source,
    )


def build_environment(sdk_path: str, meson: Path, ninja: Path) -> dict[str, str]:
    env = os.environ.copy()
    tool_paths = [
        str(TOOLS_VENV / "bin"),
        str(PREFIX_DIR / "bin"),
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ]
    common_flags = f"-arch {ARCHITECTURE} -mmacosx-version-min={MINIMUM_MACOS}"
    env.update(
        {
            "PATH": os.pathsep.join(tool_paths),
            "SDKROOT": sdk_path,
            "MACOSX_DEPLOYMENT_TARGET": MINIMUM_MACOS,
            "CC": "clang",
            "CXX": "clang++",
            "AR": "ar",
            "RANLIB": "ranlib",
            "STRIP": "strip",
            "CFLAGS": f"{common_flags} -O2",
            "CXXFLAGS": f"{common_flags} -O2",
            "CPPFLAGS": f"-I{PREFIX_DIR / 'include'}",
            "LDFLAGS": f"{common_flags} -L{PREFIX_DIR / 'lib'}",
            "PKG_CONFIG_PATH": os.pathsep.join(
                [str(PREFIX_DIR / "lib" / "pkgconfig"), str(PREFIX_DIR / "share" / "pkgconfig")]
            ),
            "PKG_CONFIG_LIBDIR": os.pathsep.join(
                [str(PREFIX_DIR / "lib" / "pkgconfig"), str(PREFIX_DIR / "share" / "pkgconfig")]
            ),
            "MESON": str(meson),
            "NINJA": str(ninja),
        }
    )
    return env


def reset_output_directories() -> None:
    for path in (WORK_DIR, PREFIX_DIR, DIST_DIR):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)


def build_pkgconf(env: dict[str, str]) -> None:
    source = SOURCES_DIR / "pkgconf-2.5.1"
    build = WORK_DIR / "pkgconf"
    build.mkdir()
    run(
        [
            str(source / "configure"),
            f"--prefix={PREFIX_DIR}",
            "--disable-shared",
            "--enable-static",
        ],
        cwd=build,
        env=env,
    )
    run(["make", f"-j{os.cpu_count() or 4}"], cwd=build, env=env)
    run(["make", "install"], cwd=build, env=env)
    pkg_config = PREFIX_DIR / "bin" / "pkg-config"
    if not pkg_config.exists():
        pkg_config.symlink_to("pkgconf")
    env["PKG_CONFIG"] = str(PREFIX_DIR / "bin" / "pkgconf")


def meson_build(
    name: str,
    source_directory: str,
    options: list[str],
    env: dict[str, str],
    meson: Path,
    *,
    library: str = "static",
    prefer_static: bool = False,
) -> None:
    source = SOURCES_DIR / source_directory
    build = WORK_DIR / name
    command = [
        str(meson),
        "setup",
        str(build),
        str(source),
        "--prefix",
        str(PREFIX_DIR),
        "--libdir",
        "lib",
        "--buildtype",
        "release",
        "--default-library",
        library,
        "--wrap-mode",
        "nodownload",
    ]
    if prefer_static:
        command.append("--prefer-static")
    command.extend(options)
    run(command, env=env)
    run([str(meson), "compile", "-C", str(build)], env=env)
    run([str(meson), "install", "-C", str(build)], env=env)


def build_ffmpeg(env: dict[str, str], config: dict) -> None:
    source = SOURCES_DIR / "ffmpeg-8.0.3"
    build = WORK_DIR / "ffmpeg"
    build.mkdir()
    common_flags = f"-arch {ARCHITECTURE} -mmacosx-version-min={MINIMUM_MACOS} -O2"
    run(
        [
            str(source / "configure"),
            f"--prefix={PREFIX_DIR}",
            f"--pkg-config={PREFIX_DIR / 'bin' / 'pkgconf'}",
            *config["build_configuration"]["ffmpeg"],
            f"--extra-cflags={common_flags}",
            f"--extra-cxxflags={common_flags}",
            f"--extra-ldflags=-arch {ARCHITECTURE} -mmacosx-version-min={MINIMUM_MACOS}",
        ],
        cwd=build,
        env=env,
    )
    run(["make", f"-j{os.cpu_count() or 4}"], cwd=build, env=env)
    run(["make", "install"], cwd=build, env=env)


def build_dependencies(env: dict[str, str], meson: Path, config: dict) -> None:
    options = config["build_configuration"]
    meson_build(
        "freetype",
        "freetype-2.14.2",
        options["freetype"],
        env,
        meson,
    )
    meson_build(
        "fribidi",
        "fribidi-1.0.16",
        options["fribidi"],
        env,
        meson,
    )
    meson_build(
        "harfbuzz",
        "harfbuzz-13.0.1",
        options["harfbuzz"],
        env,
        meson,
    )
    meson_build(
        "libass",
        "libass-0.17.4",
        options["libass"],
        env,
        meson,
    )
    meson_build(
        "libplacebo",
        "libplacebo-v7.360.0",
        options["libplacebo"],
        env,
        meson,
    )


def build_mpv(env: dict[str, str], meson: Path, config: dict) -> None:
    meson_build(
        "mpv",
        "mpv-0.41.0",
        config["build_configuration"]["mpv"],
        env,
        meson,
        library="shared",
        prefer_static=True,
    )


def collect_artifacts(config: dict) -> None:
    bin_dir = DIST_DIR / "bin"
    lib_dir = DIST_DIR / "lib"
    licenses_dir = DIST_DIR / "licenses"
    bin_dir.mkdir(parents=True)
    lib_dir.mkdir(parents=True)
    licenses_dir.mkdir(parents=True)

    ffmpeg = PREFIX_DIR / "bin" / "ffmpeg"
    libmpv = PREFIX_DIR / "lib" / "libmpv.2.dylib"
    if not ffmpeg.is_file():
        raise RuntimeError(f"FFmpeg output is missing: {ffmpeg}")
    if not libmpv.exists():
        raise RuntimeError(f"libmpv output is missing: {libmpv}")

    shutil.copy2(ffmpeg, bin_dir / "ffmpeg")
    shutil.copy2(libmpv.resolve(), lib_dir / "libmpv.2.dylib")
    run(
        [
            "install_name_tool",
            "-id",
            "@rpath/libmpv.2.dylib",
            str(lib_dir / "libmpv.2.dylib"),
        ]
    )

    for source in config["sources"]:
        source_dir = SOURCES_DIR / source["directory"]
        destination = licenses_dir / source["name"]
        destination.mkdir()
        for relative in source["license_files"]:
            license_file = source_dir / relative
            if not license_file.is_file():
                raise RuntimeError(f"License file is missing: {license_file}")
            shutil.copy2(license_file, destination / license_file.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use only already downloaded sources and installed build tools.",
    )
    args = parser.parse_args()

    config = load_config()
    sdk_path = validate_host()
    meson, ninja = ensure_tools(args.offline)
    download_sources(config, args.offline)
    extract_sources(config)
    prepare_libplacebo_subprojects(config)
    apply_source_patches(config)
    reset_output_directories()
    env = build_environment(sdk_path, meson, ninja)

    build_pkgconf(env)
    build_ffmpeg(env, config)
    build_dependencies(env, meson, config)
    build_mpv(env, meson, config)
    collect_artifacts(config)

    verify = Path(__file__).with_name("verify.py")
    run([sys.executable, str(verify), "--write-manifest"])
    print(f"\nMedia runtime built successfully in {DIST_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
