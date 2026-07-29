# -*- mode: python ; coding: utf-8 -*-

APP_NAME = "Pavo"
APP_VERSION = "1.2.0"
APP_BUILD = "1"
BUNDLE_IDENTIFIER = "io.github.hzzzz77.pavo"
TARGET_ARCH = "arm64"
MINIMUM_MACOS_VERSION = "13.0"

# Phase 1 intentionally excludes ffmpeg and libmpv. They will be integrated
# after architecture, runtime path, and license requirements are resolved.
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=TARGET_ARCH,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pavo.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon='pavo.icns',
    bundle_identifier=BUNDLE_IDENTIFIER,
    version=APP_VERSION,
    info_plist={
        'CFBundleDisplayName': APP_NAME,
        'CFBundleName': APP_NAME,
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_BUILD,
        'LSMinimumSystemVersion': MINIMUM_MACOS_VERSION,
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
    },
)
