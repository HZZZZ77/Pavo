# Active Task

## Task ID

`PAVO-006`

## Title

macOS Release Readiness Audit

## Status

`Phase 1 Complete`

## Priority

`P0`

## Created

`2026-07-29`

## Objective

建立可重复的 macOS Apple Silicon 打包基线，使维护者能够从干净 clone 使用固定工具链生成未签名的 `Pavo.app`。

## Background

此前 `Pavo.spec` 被 `.gitignore` 排除，依赖版本未锁定，应用缺少明确的 bundle identifier、版本和目标架构。现有本地产物也不是可验证的发布候选。

第一阶段只建立 arm64 `.app` 构建基线，不处理媒体二进制整合、签名或公证。

## Requirements

- 将 `Pavo.spec` 纳入 Git 管理。
- 固定 PySide6、python-mpv 和 PyInstaller 版本。
- 配置应用名称、版本、bundle identifier、图标和 arm64 target。
- 记录 macOS 13.0 最低版本基线。
- 提供唯一构建命令和明确产物位置。
- 从全新虚拟环境验证依赖安装和 `.app` 构建。
- 不打包仓库中的 x86_64 FFmpeg。
- 不复制或依赖 Homebrew libmpv 作为打包输入。

## Scope

- `.gitignore`
- `Pavo.spec`
- `requirements.txt`
- `requirements-build.txt`
- `README.md`
- `docs/tasks/ACTIVE.md`

## Non Goals

- 不修改 UI 或播放逻辑。
- 不修改 `src/` 下任何文件。
- 不集成 libmpv 或 FFmpeg。
- 不配置 Developer ID、entitlements、Hardened Runtime 或公证。
- 不创建 DMG、GitHub Release 或公开发布产物。
- 不支持 Intel 或 universal2。

## Acceptance Criteria

- `Pavo.spec` 不再被 Git 忽略。
- 全新虚拟环境可安装锁定依赖。
- 唯一构建命令能够生成 `dist/Pavo.app`。
- 主可执行文件为 `arm64`。
- Info.plist 包含正确名称、版本、bundle identifier 和 macOS 13.0 最低版本。
- `pavo.icns` 正确进入应用包。
- 应用包不包含仓库中的 x86_64 `ffmpeg`。
- 应用包不包含或复制 Homebrew `libmpv`。
- `compileall` 和 `git diff --check` 通过。

## Testing

```bash
python3.14 -m venv /private/tmp/pavo-release-baseline-venv
/private/tmp/pavo-release-baseline-venv/bin/python -m pip install -r requirements-build.txt
/private/tmp/pavo-release-baseline-venv/bin/python -m PyInstaller --clean --noconfirm Pavo.spec
/private/tmp/pavo-release-baseline-venv/bin/python -m compileall src
git diff --check
```

构建后检查：

- `plutil -p dist/Pavo.app/Contents/Info.plist`
- `file dist/Pavo.app/Contents/MacOS/Pavo`
- 检查应用包中不存在 `ffmpeg` 和 `libmpv`。

### Phase 1 Results

- Python 3.14.2 全新虚拟环境创建成功。
- PySide6 6.10.2、python-mpv 1.0.8 和 PyInstaller 6.19.0 安装成功。
- `dist/Pavo.app` 构建成功。
- 主可执行文件确认为 `arm64`。
- Info.plist 名称、版本、bundle identifier 和 macOS 13.0 最低版本检查通过。
- `pavo.icns` 已包含在应用包中。
- 应用包未包含 `ffmpeg` 或 `libmpv`。
- `python -m compileall src` 通过。
- `git diff --check` 通过。
- 本阶段未进行应用运行验证；媒体运行仍依赖后续 arm64 libmpv 整合。

## Notes

后续阶段仍需解决：

- arm64 libmpv 及其传递依赖。
- arm64 FFmpeg。
- bundle 内动态库路径和加载策略。
- Qt、python-mpv、mpv、FFmpeg 第三方许可证与来源记录。
- Developer ID 签名、Hardened Runtime、Apple 公证和 Gatekeeper 验证。

第一阶段产物只用于打包基线验证，不是可公开分发版本。

## Commit

`Pending`
