# Active Task

## Task ID

`PAVO-012`

## Title

Prepare Pavo v1.2.1 Beta

## Status

`Release Metadata Ready - Final Build Pending`

## Priority

`P0`

## Created

`2026-08-07`

## Objective

为包含 PAVO-011 极简 PiP 改进的 Pavo 1.2.1 Beta 生成可验证的 arm64 应用包和 ZIP 候选，但不创建 Tag、GitHub Release 或执行 push。

## Background

Pavo 1.2.0 Beta 已建立自包含 arm64 打包基线。PAVO-011 已通过自动化测试、macOS 实机视觉验收并合并到 `main`，本任务在不改变产品功能与媒体 Runtime 的前提下更新维护版本元数据、发布说明和候选产物。

## Requirements

- 将应用版本更新为 `1.2.1`，Build Number 从 `1` 递增为 `2`。
- Release Notes 重点记录极简 PiP 控制层、自动显隐、原生 macOS 圆角与阴影，以及按视频比例初始化窗口。
- 使用固定 Python 3.13.12 与依赖重新生成 arm64 `Pavo.app`。
- 生成 `Pavo-1.2.1-beta-macos-arm64.zip` 及 SHA-256。
- 验证 bundle 元数据、架构、deployment target、媒体 Runtime、动态依赖和许可证。
- 执行现有 PiP 自动化测试和发布回归检查。

## Scope

- `Pavo.spec`
- `INSTALL.md`
- `FAQ.md`
- `docs/release/KNOWN_ISSUES.md`
- `docs/release/RELEASE_NOTES_v1.2.1.md`（新增）
- `docs/release/RELEASE_CHECKLIST_v1.2.1-beta.md`（新增）
- `docs/tasks/ACTIVE.md`
- Git 忽略的 `dist/Pavo.app`
- Git 忽略的 `dist/Pavo-1.2.1-beta-macos-arm64.zip`

## Non Goals

- 不修改播放器功能代码、UI 或播放逻辑。
- 不重新构建或修改 Phase 2A 媒体 Runtime。
- 不修改签名、公证、DMG 或 GitHub Release 流程。
- 不创建 Tag、Release，不 push。
- 不宣称完整 HDR 支持或已完成真实 macOS 13 验收。

## Acceptance Criteria

- `Pavo.app` 的短版本为 `1.2.1`，Build Number 为 `2`。
- 主程序、所有必要第三方 Mach-O 和媒体 Runtime 均为 arm64，最低系统版本不高于 macOS 13.0。
- bundle 不依赖 Homebrew、`/opt/homebrew`、`/usr/local` 或 `/opt/local`。
- bundle 内 libmpv 初始化、FFmpeg 烟测和许可证验证通过。
- PiP 自动化测试、`compileall` 和 `git diff --check` 通过。
- 新 ZIP 可解压并通过完整 bundle 验证，SHA-256 已记录。
- 发布阻塞项被明确记录，未执行任何发布操作。

## Testing

- `venv/bin/python -m compileall src tests tools/media_runtime`
- `QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -v`
- `python3.14 tools/media_runtime/verify.py`
- `python3.14 tools/media_runtime/verify_bundle.py dist/Pavo.app`
- `codesign --verify --deep --strict dist/Pavo.app`
- 检查 `Info.plist`、Mach-O 架构、动态依赖和 ZIP 解压副本。
- `git diff --check`

## Notes

Planning 已完成。开始时 `main` 与 `origin/main` ahead/behind 均为 `0`，工作区干净，HEAD 为 PAVO-011 Squash 提交 `2daccd1`。应用构建要求 Python 3.13.12；当前通用 `venv` 使用 Python 3.14.3，因此发布包将使用独立的干净 Python 3.13.12 环境构建。

Implementation 和自动检查结果：

- 全新 Python 3.13.12 虚拟环境成功安装 `requirements-build.txt` 的全部固定依赖。
- PyInstaller 6.19.0 成功生成 arm64 `dist/Pavo.app`。
- `Info.plist`：版本 `1.2.1`、Build `2`、Bundle Identifier `io.github.hzzzz77.pavo`、最低 macOS `13.0`。
- Phase 2A Runtime 验证通过：FFmpeg 8.0.3 与 libmpv 0.41.0 均为 arm64、最低 macOS 13.0，且无禁止路径依赖。
- bundle 验证扫描 54 个 Mach-O，无 deployment target 违规或 Homebrew、MacPorts、`/usr/local` 依赖；libmpv 初始化、FFmpeg 烟测和 17 份许可证验证通过。
- `codesign --verify --deep --strict` 对构建产物和 ZIP 解压副本均通过，签名仍为 ad-hoc。
- 在仅系统 `PATH` 的隔离 HOME 中启动打包应用，确认使用 bundle 内 libmpv，mpv 和 OpenGL 初始化成功，应用退出码为 0。
- PiP 自动化回归 10 项全部通过，覆盖极简控件、自动显隐、播放状态、导航、进度、进入与恢复，以及 Clear Playlist。
- `compileall` 与 `git diff --check` 通过。
- 生成 `dist/Pavo-1.2.1-beta-macos-arm64.zip`，大小 `64,139,677` bytes，SHA-256：`5161928a0dc381c53b6529d227199589e47618a55c30e9994dcc247677b35842`。
- ZIP 解压副本再次通过完整 bundle、签名和版本元数据验证。

用户已确认打包后的 1.2.1 实机播放与 PiP 验收通过。发布前仍需：提交发布元数据后从最终提交重新执行干净构建并计算最终 SHA-256；完成真实 macOS 13 主机验证及第三方许可证义务复核。Developer ID 签名与公证仍不可用，因此本候选只能作为明确标注的 unsigned Beta。

---

# Completed Task

## Task ID

`PAVO-011`

## Title

Minimal PiP Experience

## Status

`Completed`

## Priority

`P1`

## Created

`2026-08-06`

## Objective

将现有缩小版主窗口式画中画改为专用的极简播放界面，同时继续复用同一个 mpv/OpenGL 视频画布和主窗口播放编排逻辑。

## Background

当前 PiP 通过改变主窗口 flags、尺寸并调用 `HUDPanel.set_pip_mode()` 隐藏部分控件，完整 HUD、时间和可交互进度仍然存在。视频渲染由单个 `PavoVideoWidget` 和 mpv OpenGL render context 承担，创建第二套视频窗口会增加上下文重建和播放状态分叉风险。

## Requirements

- PiP 默认只显示视频画面，鼠标活动时显示专用控制层。
- 播放时控制层在鼠标离开或无操作后自动隐藏；暂停时保持显示。
- 中央只显示 Previous、Play/Pause、Next。
- 左上角提供返回主窗口，右上角提供关闭 PiP。
- 隐藏完整 HUD、音量、时间文本、可交互进度、OSD、播放列表和缩略图。
- 底部显示极细、只读的播放进度提示。
- 保持窗口置顶、拖动、自由缩放和圆角表现。
- PiP 控件复用主窗口已有 Previous、Next 和播放状态逻辑，并与 mpv 实际状态同步。
- 增加覆盖专用控制层状态、进度和交互信号的自动化测试。

## Scope

- `src/main.py`
- `src/components/pip_overlay.py`（新增）
- `tests/test_pip_overlay.py`（新增）
- `tests/test_pip_main_integration.py`（新增）
- `docs/tasks/ACTIVE.md`

## Non Goals

- 不创建第二个 mpv 实例或第二套 OpenGL 渲染上下文。
- 不修改 `src/engine.py`、`src/video_widget.py` 或现有 HUD 的布局与功能。
- 不修改 Runtime、打包配置、README 或发布文档。
- 不增加音量、字幕、时间文本、可交互 seek 或其他 PiP 功能。
- 不重构播放列表和播放引擎架构。

## Acceptance Criteria

- 进入 PiP 后只显示视频、专用控制层和只读细进度提示，完整 HUD 不可见。
- Previous、Play/Pause、Next 调用现有主窗口逻辑，首尾禁用状态正确。
- 播放状态由 engine 信号同步到主 HUD 与 PiP 控件。
- 播放时控制层能自动隐藏并可由鼠标活动唤醒；暂停时保持显示。
- 返回和关闭 PiP 均恢复标准主窗口，播放不中断。
- PiP 保持置顶、可拖动、可缩放；退出后恢复原窗口几何和可见面板状态。
- `python -m compileall`、相关自动化测试和 `git diff --check` 通过。

## Testing

- `venv/bin/python -m compileall src tests`
- `QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -v`
- `git diff --check`
- 实机验证进入/退出 PiP、播放与暂停自动显隐、播放列表导航、拖动和缩放。

自动检查结果：

- `venv/bin/python -m compileall src tests`：通过。
- `QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -v`：10 项通过。
- `git diff --check`：通过。
- 主窗口伪 engine/视频画布集成测试覆盖 PiP 进入与恢复、播放和列表按钮复用、Clear Playlist 空状态。
- macOS Cocoa 原生窗口烟测：CALayer 连续圆角启用与恢复通过。
- 实机视觉验收：窗口圆角、视频比例、无边框半透明控件和只读进度提示通过。

## Notes

Planning、Implementation、自动化测试和实机验收均已完成。实施采用单一视频画布和专用 PiP overlay，避免复制播放控制逻辑及重建 mpv OpenGL render context。参考截图仅用于交互层级，不复用其视觉素材。实机首轮验收后加入了 macOS 原生 CALayer 连续圆角裁切，未使用 `QRegion` 或 `setMask`。第二轮验收确认顶部和底部黑条来自 PiP 初始窗口沿用主画布 `5:3` 比例，而实际视频为 `16:9`，并确认灰白光晕来自 overlay 自绘边线与原生阴影叠加。最终实现改用 mpv 实际显示尺寸计算 PiP 初始比例，显式保持 central layout 零 margin/spacing，删除全部 Qt 外轮廓绘制并将 CALayer border 设为 0，仅保留原生圆角裁切和窗口阴影。PiP 控件使用单层 QPainterPath 半透明填充，无 QSS border 或重复背景绘制。

---

# Related Active Task

## Task ID

`PAVO-009`

## Title

Prepare Beta Release Package

## Status

`Package Prepared - Publication Blockers Remaining`

## Priority

`P0`

## Created

`2026-07-30`

## Objective

在没有 Apple Developer 账号的前提下，为 Pavo 1.2.0 Beta 生成可验证的 arm64 发布包、安装指南、FAQ 和发布检查清单。

## Scope

- `docs/release/RELEASE_CHECKLIST_v1.2.0-beta.md`
- `docs/release/RELEASE_NOTES_v1.2.0.md`
- `docs/release/KNOWN_ISSUES.md`
- `INSTALL.md`
- `FAQ.md`
- `docs/tasks/ACTIVE.md`
- 本地生成且由 Git 忽略的 `dist/Pavo.app`
- 本地生成且由 Git 忽略的 `dist/Pavo-1.2.0-beta-macos-arm64.zip`

## Non Goals

- 不修改播放器功能代码。
- 不修改媒体 Runtime、README 或打包配置。
- 不配置 Developer ID、Hardened Runtime 或 Apple 公证。
- 不上传 GitHub Release，不 commit，不 push。

## Results

- 使用 Python 3.13.12 和 PyInstaller 6.19.0 从当前提交重新构建 `Pavo.app`。
- `verify_bundle.py` 扫描 54 个 Mach-O，无 deployment target 违规或 Homebrew、MacPorts、`/usr/local` 依赖。
- bundle 内 libmpv 初始化、FFmpeg 烟测、17 份许可证检查通过。
- `codesign --verify --deep --strict` 通过；签名类型为 ad-hoc，无 Team Identifier。
- 使用仅系统 PATH 的隔离环境启动成功，确认 bundle 内 libmpv、mpv 和 OpenGL 初始化。
- 打包应用成功打开并显示 HEVC 4K 测试文件，并以退出码 0 关闭。
- ZIP 解压副本通过完整 bundle 验证。
- 生成 61 MB 的 `Pavo-1.2.0-beta-macos-arm64.zip`。
- SHA-256：`5adc58a30ab6e000f6b7024129be49f701aa4b8ede979ed6237260b6db15224a`。

## Remaining Blockers

- PAVO-008 仍需真实字幕和多文件播放手动回归。
- 发布前需要复核第三方许可证、静态链接源码提供和 relinking 义务。
- 仍未在物理 macOS 13 Apple Silicon 主机验收。
- 无 Developer ID 和公证，因此只能作为明确标注的 unsigned beta 发布。

---

# Related Active Task

## Task ID

`PAVO-008`

## Title

Fix Release Blocking P1 Bugs

## Status

`Testing - Manual Verification Pending`

## Priority

`P1`

## Created

`2026-07-30`

## Objective

修复 PAVO-006 Release Audit 发现的字幕关闭、播放列表手动导航和删除当前播放项三个 P1 问题，使首发候选的播放状态保持一致。

## Background

Phase 3A 播放审计确认 libmpv 支持 `sid=no`，但当前 UI 没有字幕关闭入口；播放列表仅支持自动下一项，没有手动 Previous/Next；删除当前播放项后 `current_idx` 会变为 `-1`，导致后续自动下一项失去上下文。

## Requirements

- 字幕菜单提供用户可见的 `Subtitle Off`，并通过现有引擎接口设置 `sid=no`。
- 字幕菜单每次打开时根据 libmpv 当前选轨状态同步勾选项。
- 提供 Previous 和 Next 操作，并与 `current_idx` 保持一致。
- 自动下一项与手动 Next 复用同一播放列表导航逻辑。
- 删除当前播放项后选择有效的替代项；播放列表为空时进入完整空状态。
- 删除非当前播放项不得重新加载或中断当前媒体。

## Scope

- `src/main.py`
- `docs/tasks/ACTIVE.md`

## Non Goals

- 不修改 Runtime、`src/engine.py` 或视频渲染。
- 不修改 HUD 布局或整体 UI 风格。
- 不修改 README 或打包配置。
- 不增加循环播放、随机播放或其他播放列表功能。
- 不进行架构重构。

## Acceptance Criteria

- 字幕菜单始终显示 `Subtitle Off`，选择后 libmpv 的字幕轨为 `no`。
- 切换媒体后字幕菜单勾选状态反映当前媒体的真实选轨状态。
- Previous 和 Next 能够加载相邻播放列表项目，首尾边界不崩溃。
- 播放结束通过与手动 Next 相同的逻辑继续下一项。
- 删除当前项后 `current_idx` 指向有效项目，后续自动下一项仍可工作。
- 删除唯一项目后播放器进入空状态。
- 删除非当前项不改变当前播放媒体。
- `python3 -m compileall src` 和 `git diff --check` 通过。

## Testing

- 运行 `python3 -m compileall src`。
- 运行 `git diff --check`。
- 验证有字幕、无字幕和切换媒体后的 `Subtitle Off` 状态。
- 验证 Previous、Next、自动下一项和首尾边界。
- 验证删除当前项、唯一项、队尾当前项和非当前项。

自动检查结果：

- `python3 -m compileall src`：通过。
- `git diff --check`：通过。
- 内存状态测试：Previous、Next、播放结束自动 Next、首尾边界通过。
- 内存状态测试：删除当前项、删除非当前项和删除唯一项通过。
- 菜单状态测试：`Subtitle Off` 勾选同步及调用 `set_subtitle_track("no")` 通过。

仍需使用真实媒体手动验证字幕渲染、菜单交互、播放切换和删除后的连续播放。

## Notes

Planning 和 Implementation 已完成。实施限制为主窗口编排层的最小状态修复，没有新增播放模式，也没有改变现有播放与视觉架构。

---

# Related Release Audit Task

## Task ID

`PAVO-006`

## Title

macOS Release Readiness Audit

## Status

`Phase 3A Audit Complete - Findings Await Review`

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
- `tools/media_runtime/`
- `Pavo.spec`
- `src/bootstrap.py`
- `src/engine.py`
- runtime integration documentation and validation helpers
- Phase 2C dependency pins and macOS deployment-target validation
- `requirements.txt`
- `requirements-build.txt`
- `README.md`

## Non Goals

- 不修改 UI 或播放逻辑。
- 不修改 `src/` 下任何文件。
- 不集成 libmpv 或 FFmpeg。
- 不配置 Developer ID、entitlements、Hardened Runtime 或公证。
- 不创建 DMG、GitHub Release 或公开发布产物。
- 不支持 Intel 或 universal2。
- Phase 2A 不修改 `Pavo.spec`，不把媒体运行时集成进应用包。
- Phase 2A 不修改 `src/bootstrap.py`、`src/engine.py`、UI 或播放逻辑。
- Phase 2B 不修改 UI、播放行为或 OpenGL 渲染实现。
- Phase 2B 不处理 Developer ID 签名、Hardened Runtime、公证、DMG 或 GitHub Release。
- Phase 2B 不支持 Intel 或 universal2，也不重新构建 Phase 2A 媒体运行时。
- Phase 2C 不修改 UI、播放逻辑或媒体运行时实现。
- Phase 2C 不开始签名、公证、DMG 或 GitHub Release 工作。
- Phase 2C 不把最低系统要求提高到 macOS 15。
- Phase 2C 不从源码构建 PySide6，除非合理的官方 wheel 组合全部失败。

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

### Phase 2A Acceptance Criteria

- mpv、FFmpeg 及必要构建依赖均固定版本和源码 SHA-256。
- 单一脚本可从干净 clone 构建 arm64、macOS 13.0 的媒体运行时。
- FFmpeg 与 mpv 使用 LGPL 兼容配置，不启用 GPL、version3 或 nonfree 组件。
- `ffmpeg` 和 `libmpv.2.dylib` 不依赖 Homebrew、MacPorts 或 `/usr/local`。
- manifest 记录源码、构建参数、工具版本、产物 SHA-256、动态依赖和许可证。
- `file`、`vtool`、`otool` 与独立验证脚本检查通过。

### Phase 2B Acceptance Criteria

- `Pavo.app/Contents/Frameworks` 包含 Phase 2A 的 `libmpv.2.dylib` 和 `ffmpeg`。
- `Pavo.app/Contents/Resources/media-runtime` 包含 manifest 和完整许可证目录。
- 打包模式下 `python-mpv` 只加载 bundle 内的 `libmpv.2.dylib`。
- 缩略图生成在打包模式下只使用 bundle 内的 `ffmpeg`。
- 源码开发模式仍支持系统或显式配置的 libmpv 与 FFmpeg。
- 应用包内所有 Mach-O 文件均不引用 Homebrew、`/opt/homebrew`、`/usr/local` 或 `/opt/local`。
- `Pavo.spec` 在打包前校验媒体运行时输入与 Phase 2A manifest 的 SHA-256 一致。
- bundle 内媒体产物通过架构、最低系统版本、install name、动态依赖、加载及执行验证；允许 PyInstaller 的 Mach-O 处理和临时 ad-hoc 签名改变文件哈希。
- 应用能够启动，mpv 初始化成功，FFmpeg 和基础播放路径完成回归验证。

### Phase 2C Acceptance Criteria

- 明确记录 Python、PySide6、PySide6-Essentials、PySide6-Addons、shiboken6 与 PyInstaller 的固定版本和官方 wheel 来源。
- 使用 `vtool` 扫描最终 `Pavo.app`，所有必要第三方 Mach-O 文件的最低系统版本均不高于 macOS 13.0。
- 至少验证 Python 3.12、Python 3.13 与兼容的较早 PySide6 官方 wheel 组合。
- 最终固定组合能够构建 arm64 `Pavo.app`，并通过启动、mpv 初始化、OpenGL、播放、Open File 和缩略图烟测。
- 当前 UI、播放功能和 Phase 2B bundle 内媒体运行时保持不变。
- README 与验证脚本准确记录固定工具链和 deployment target 检查方式。

### Phase 3A Acceptance Criteria

- 使用打包后的 `Pavo.app` 和 bundle 内媒体运行时完成主流封装、视频编码、音频编码和字幕矩阵测试。
- 记录每个测试素材的来源、媒体信息和 SHA-256，不向 Git 添加大型媒体文件。
- 验证 1080p、4K、高码率、长视频、大文件定位及播放器核心交互回归。
- 使用 `hwdec-current` 或等价运行时属性记录 VideoToolbox、软件解码或 copy-back 的实际状态。
- 对 HDR10 与 HLG 分别记录元数据识别、解码、输出和色调映射状态，不将文件可播放等同于完整 HDR 支持。
- 明确标记当前主机无法完成的 macOS 13 与真实 HDR 显示视觉验收。
- 发现问题时先记录和汇报，不修改 UI、播放逻辑或其他产品功能代码。

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

### Phase 2A Testing

```bash
python3.14 tools/media_runtime/build.py
python3.14 tools/media_runtime/build.py --offline
python3.14 tools/media_runtime/verify.py
file build/media-runtime/dist/bin/ffmpeg
file build/media-runtime/dist/lib/libmpv.2.dylib
vtool -show-build build/media-runtime/dist/bin/ffmpeg
vtool -show-build build/media-runtime/dist/lib/libmpv.2.dylib
otool -L build/media-runtime/dist/bin/ffmpeg
otool -L build/media-runtime/dist/lib/libmpv.2.dylib
```

### Phase 2B Testing

```bash
venv/bin/python -m compileall src tools/media_runtime
venv/bin/python -m PyInstaller --clean --noconfirm Pavo.spec
python3.14 tools/media_runtime/verify_bundle.py
git diff --check
```

构建后检查：

- 核对 `Contents/Frameworks` 中的 `libmpv.2.dylib` 和 `ffmpeg`。
- 核对 `Contents/Resources/media-runtime` 中的 manifest 与许可证。
- 使用 `file`、`vtool`、`otool` 和 SHA-256 检查 bundle 内媒体产物。
- 启动 `Pavo.app`，确认使用 bundle 内 libmpv 且无需 Homebrew。
- 回归打开媒体、播放/暂停、进度定位和缩略图预览。

### Phase 2C Testing

每个候选组合均在 `/private/tmp` 中创建独立干净虚拟环境，并执行：

```bash
<candidate-python> -m venv <candidate-venv>
<candidate-venv>/bin/python -m pip install \
  "PySide6==<candidate-version>" \
  "python-mpv==1.0.8" \
  "PyInstaller==6.19.0"
<candidate-venv>/bin/python -m PyInstaller \
  --clean --noconfirm \
  --workpath <candidate-work> \
  --distpath <candidate-dist> \
  Pavo.spec
python3.14 tools/media_runtime/verify_bundle.py \
  <candidate-dist>/Pavo.app
```

通过自动检查的候选还需执行：

- 启动应用并确认使用 bundle 内 `libmpv.2.dylib`。
- 确认 OpenGL render context 初始化成功。
- 通过 Open File 打开测试视频并完成播放烟测。
- 悬停进度条并确认 bundle 内 FFmpeg 缩略图链路可用。
- 运行 `venv/bin/python -m compileall src tools/media_runtime`。
- 运行 `git diff --check`。

### Phase 3A Test Plan

1. 从当前提交使用固定 Python 3.13.12 环境构建并验证 `Pavo.app`，确认测试不依赖 Homebrew。
2. 优先使用 bundle 内 FFmpeg 生成合法的小型测试素材；仅在缺少必要编码器时下载公开测试向量，并记录 URL、SHA-256 与媒体信息。
3. 覆盖 MP4、MKV、MOV、WebM，H.264、HEVC、VP9、AV1，以及 AAC、MP3、FLAC、Opus、AC-3、E-AC-3。
4. 覆盖外挂 SRT、外挂 ASS、内嵌字幕以及字幕切换、关闭和同步。
5. 覆盖 1080p、4K、高码率、长视频、大文件快速打开和 seek，并回归播放控制、播放列表、缩略图、全屏、PiP、Clear Playlist 和 Recent Files。
6. 使用 bundle 内 libmpv 的真实运行属性采集解码器、`hwdec-current`、视频参数、HDR 元数据和输出色彩状态。
7. 将素材清单与测试报告写入小型文本文件，运行 `compileall` 和 `git diff --check`，不提交测试媒体或生成目录。

### Phase 3A Non Goals

- 不修改 UI、播放逻辑、媒体解码选项或画质策略。
- 不增加产品功能，不为测试通过而静默降低画质。
- 不开始签名、公证、DMG 或 GitHub Release。
- 不将测试素材、构建产物或其他大型生成文件提交到 Git。
- 不把当前 macOS 主机测试替代为 macOS 13 或真实 HDR 显示的最终视觉验收。

### Phase 3A Progress

- Phase 3A 于 2026-07-30 从暂停节点恢复；已完成测试矩阵和报告，未修改产品功能代码，未 commit 或 push。
- 测试主机已记录为 Apple M4、arm64、24 GB 内存、macOS 26.5.2；当前没有 macOS 13 主机或已确认的真实 HDR 显示环境。
- 已使用固定 Python 3.13.12 环境重新生成临时 `Pavo.app`，产物位于 `/private/tmp/pavo-phase3a/dist/Pavo.app`，未加入 Git。
- `verify_bundle.py` 已通过：检查 54 个 Mach-O 文件，无 deployment target 违规、无 Homebrew 等禁止路径；bundle 内 FFmpeg、libmpv 初始化和 17 份许可证检查通过。
- 已确认 bundle 内 FFmpeg 为 arm64，包含 VideoToolbox，以及 H.264、HEVC、VP9、AV1、AAC、MP3、FLAC、Opus、AC-3、E-AC-3 所需解码器。
- 已在 `/private/tmp/pavo-phase3a/assets/` 准备公开或自行生成的临时测试素材，覆盖 VP9、AV1、HDR10、MP3、AAC、FLAC、Opus、AC-3、E-AC-3、SRT、ASS、H.264、HEVC、HLG、4K60 高码率和两小时时长场景；素材未加入 Git。
- 公开素材来源、媒体信息和 SHA-256 已记录到 `tools/release_audit/corpus-manifest.json`。
- 完整测试结果和未覆盖范围已记录到 `docs/release/PAVO-006-phase3a-playback-audit.md`。

### Phase 3A Results

- MP4、MKV、MOV、WebM，以及 H.264、HEVC、VP9、AV1 播放通过。
- AAC、MP3、FLAC、Opus、AC-3、E-AC-3 播放通过；MKV 内 AAC、AC-3、E-AC-3 音轨切换通过。
- 所有视频编码实际使用 `videotoolbox-copy`，属于 VideoToolbox 硬解 copy-back；未观察到软件解码或零拷贝路径。
- H.264 1080p、AV1 1080p60、HEVC 4K60、HDR10 和 HLG 的五秒持续采样均为 0 decoder drop、0 VO drop。
- 外挂和内嵌 SRT/ASS 加载、选择和 1 秒 cue 同步通过；libmpv 可关闭字幕，但当前 UI 没有 Subtitle Off 操作，也没有字幕延迟调整。
- 暂停、恢复、倍速、音量、短文件 seek、两小时文件 seek、自动下一项、Recent Files、缩略图、全屏、PiP 和 Clear Playlist 通过。
- 打包应用通过原生 `Cmd+O` 打开 4K60 文件并实际显示视频画面；日志确认加载 bundle 内 libmpv，mpv 与 OpenGL 初始化成功。
- 当前没有手动 Previous/Next 功能；删除当前播放项后媒体继续播放但 `current_idx` 变为 `-1`，后续自动下一项失去上下文。
- HDR10 的 PQ/BT.2020 和 HLG 的 HLG/BT.2020 元数据均被 mpv 识别，两个文件均使用 `videotoolbox-copy`；输出与 tone mapping 仍为 `auto`，未完成真实 HDR 显示视觉验收。
- 真实 macOS 13、真实 HDR 显示器和多 GB 文件仍未覆盖，PAVO-006 不得据此标记为 Completed。
- `tools/media_runtime/README.md` 仍可能包含旧 PySide6 6.10.2/macOS 15 阻塞描述；本阶段只记录问题，未修改该文档。

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

### Phase 2A Results

- mpv 0.41.0 与 FFmpeg 8.0.3 构建成功。
- FreeType 2.14.2、FriBidi 1.0.16、HarfBuzz 13.0.1、libass 0.17.4、libplacebo 7.360.0 和构建期子模块均使用固定版本或提交。
- 在线源码准备后，完整 `--offline` 干净重建通过。
- `ffmpeg` 与 `libmpv.2.dylib` 均为 arm64-only，最低 macOS 版本为 13.0。
- libmpv install name 为 `@rpath/libmpv.2.dylib`，两个产物均无额外 `LC_RPATH`。
- 动态依赖仅包含 macOS 系统 Framework 与 `/usr/lib`。
- 产物未引用 `/opt/homebrew`、`/usr/local` 或 `/opt/local`。
- manifest 已生成，包含 17 个许可证文件。
- `libmpv.2.dylib` 已通过 `ctypes` 动态加载及创建/初始化/销毁烟测，mpv client API 为 2.5。
- `ffmpeg` 已通过单帧合成视频处理烟测。
- `python3.14 tools/media_runtime/verify.py`、`venv/bin/python -m compileall src` 和 `git diff --check` 均通过。
- Phase 2A 尚未把产物集成到 `Pavo.app`，也未进行应用播放回归。

### Phase 2B Implementation Plan

1. 在 `Pavo.spec` 构建开始前校验 Phase 2A 产物完整性，将 libmpv 与 FFmpeg 作为二进制放入 `Contents/Frameworks`，将 manifest 和许可证作为数据放入 `Contents/Resources/media-runtime`。
2. 在 `src/bootstrap.py` 集中实现运行时路径解析；打包模式严格选择 bundle 内 libmpv，源码模式保留系统查找和显式路径覆盖。
3. 在导入 `python-mpv` 前临时覆盖其 `ctypes.util.find_library("mpv")` 结果，并在导入后恢复，避免全局永久修改。
4. 在 `src/engine.py` 使用 bootstrap 提供的 FFmpeg 路径；打包模式不回退到 Homebrew，源码模式保持现有开发体验。
5. 新增 bundle 验证脚本，校验布局、manifest 哈希、架构、最低系统版本和所有 Mach-O 动态依赖。
6. 更新运行时构建文档，构建应用并执行自动检查与基础运行回归。

### Phase 2B Results

- `Pavo.spec` 已在打包前校验 Phase 2A manifest、媒体产物 SHA-256 和许可证完整性。
- `libmpv.2.dylib` 与 `ffmpeg` 已进入 `Pavo.app/Contents/Frameworks`。
- manifest 与 17 个许可证文件已进入 `Pavo.app/Contents/Resources/media-runtime`。
- 打包应用启动日志确认只加载 bundle 内的 `libmpv.2.dylib`，mpv 和 OpenGL render context 初始化成功。
- 使用 bundle 内 FFmpeg 生成临时测试视频，并通过 Open File 成功打开和播放。
- 源码开发模式仍能解析并加载系统 libmpv 与 FFmpeg，也支持 `PAVO_LIBMPV_PATH` 和 `PAVO_FFMPEG_PATH` 显式覆盖。
- 扫描应用包内 105 个 Mach-O 文件，未发现 `/opt/homebrew`、`/usr/local`、`/opt/local` 或其他非系统绝对动态依赖。
- bundle 内 libmpv 保持 `@rpath/libmpv.2.dylib` install name，client API 2.5，动态加载及初始化通过。
- bundle 内 FFmpeg 8.0.3 执行和单帧处理烟测通过。
- 发现发布阻塞：PySide6 6.10.2 wheel 标记为 macOS 13，但 11 个 PySide6/shiboken Mach-O 文件的实际最低系统版本为 macOS 15.0。
- Phase 2B 媒体运行时集成已完成；在 PySide6 deployment target 问题解决并于真实 macOS 13 设备验证前，PAVO-006 不得标记为 Completed。

### Phase 2C Implementation Plan

1. 记录当前 Python 3.14、PySide6 6.10.2、shiboken6 6.10.2 基线及官方 PyPI wheel 元数据，并以 `vtool` 的最终 bundle 扫描结果为准。
2. 在隔离目录测试 Python 3.13 + PySide6 6.9.3 和 Python 3.12 + PySide6 6.9.3；每个组合均从干净虚拟环境安装、构建并扫描完整应用包。
3. 如果 PySide6 6.9.3 仍包含高于 macOS 13.0 的 Mach-O，再按最小回退原则测试较早的官方 PySide6 wheel。
4. 对通过 deployment target 检查的候选执行启动、mpv/OpenGL、Open File、播放和缩略图烟测。
5. 选择兼容性与维护周期最稳妥的组合，固定依赖版本，更新构建说明与任务记录。
6. 使用最终固定环境重新构建并执行完整 bundle 验证、`compileall` 和 `git diff --check`。

### Phase 2C Initial Findings

- 当前构建环境为 Python 3.14.3、PySide6 6.10.2、PySide6-Essentials 6.10.2、PySide6-Addons 6.10.2、shiboken6 6.10.2 和 PyInstaller 6.19.0。
- 上述 Qt for Python 包来自官方 Python package index，未包含本地路径或 VCS 安装来源。
- PySide6 6.10.2 wheel 标签为 `macosx_13_0_universal2`，但最终应用包中 11 个 PySide6/shiboken Mach-O 文件经 `vtool` 实测为 `minos 15.0`。
- Qt frameworks 本身为 `minos 13.0`；阻塞来自 PySide6/shiboken Python bindings，而不是 Phase 2A 的 libmpv 或 FFmpeg。
- 本机 PATH 当前没有 Python 3.12 或 3.13；候选解释器将在 `/private/tmp` 隔离安装，仅用于本阶段验证。

### Phase 2C Results

- 基线 Python 3.14.3 + PySide6 6.10.2 的最终 bundle 包含 11 个 `minos 15.0` 的 PySide6/shiboken Mach-O，未通过 macOS 13.0 上限检查。
- Python 3.12.12 与 3.13.12 候选使用 uv 管理的 `python-build-standalone` arm64 解释器；两个解释器本体经 `vtool` 实测均为 `minos 11.0`。
- Python 3.13.12 + PySide6 6.9.3 从干净虚拟环境构建成功；wheel 安装目录中的 392 个 PySide6/shiboken Mach-O 均为 `minos 12.0`。
- Python 3.12.12 + PySide6 6.9.3 从干净虚拟环境构建成功；使用相同的官方 `cp39-abi3-macosx_12_0_universal2` Qt for Python wheels。
- PySide6、PySide6-Addons、PySide6-Essentials、shiboken6、PyInstaller 和 python-mpv 候选包均从 PyPI 索引安装，dist-info 中不存在本地路径或 VCS `direct_url.json`。
- 两个 6.9.3 候选的最终 `Pavo.app` 均扫描 54 个 Mach-O：2 个为 `minos 11.0`、50 个为 `minos 12.0`、2 个为 `minos 13.0`，未发现更高 deployment target，也未发现 Homebrew、MacPorts 或 `/usr/local` 动态依赖。
- 两个候选均通过 bundle 内 libmpv 初始化、bundle 内 FFmpeg 执行、应用启动、OpenGL 初始化、原生 Open File、视频播放和缩略图抽帧烟测。
- 最终选择 Python 3.13.12 + PySide6 6.9.3；其兼容结果与 Python 3.12 相同，同时具有更长的 Python 上游维护周期。
- `requirements.txt` 显式固定 PySide6、PySide6-Addons、PySide6-Essentials 和 shiboken6 6.9.3；`requirements-build.txt` 固定已验证的 PyInstaller 构建依赖。
- `Pavo.spec` 拒绝非 Python 3.13.12 的发布构建，避免在未经验证的解释器上生成候选包。
- 从新的 Python 3.13.12 虚拟环境严格按最终 `requirements-build.txt` 离线安装成功，`pip check` 报告无破损依赖。
- 最终 requirements 驱动的 `Pavo.app` 构建成功，bundle 验证扫描 54 个 Mach-O，deployment target、动态依赖、libmpv 初始化和 FFmpeg 烟测全部通过。
- 最终应用启动成功，日志确认使用 bundle 内 libmpv，mpv 与 OpenGL render context 初始化成功。
- `/private/tmp/pavo-phase2c/final/venv/bin/python -m compileall src tools/media_runtime` 通过。
- `git diff --check` 通过。
- 本阶段没有修改 UI、播放逻辑或媒体运行时实现。
- 仍需在真实 macOS 13 Apple Silicon 主机执行最终启动、OpenGL、播放和缩略图验证。

## Notes

后续阶段仍需解决：

- 后续升级 Python、PySide6 或 shiboken6 时，必须重新执行最终 bundle 的 `vtool` 全量扫描。
- 在真实 macOS 13 Apple Silicon 设备执行启动与播放验证。
- Qt、python-mpv、mpv、FFmpeg 第三方许可证与来源记录。
- LGPL 静态链接发布所需的源码提供、可重新链接材料和用户通知。
- Developer ID 签名、Hardened Runtime、Apple 公证和 Gatekeeper 验证。

第一阶段产物只用于打包基线验证，不是可公开分发版本。

## Commit

- Phase 1: `7f8c4ff build: establish reproducible macOS app baseline`
- Phase 2A: `Pending`
