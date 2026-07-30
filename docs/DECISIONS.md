# Pavo Technical Decisions

本文档记录 Pavo 当前已经存在的重要技术决策。未来维护者在修改架构、替换依赖或改变平台策略前，应先阅读本文件，并在新增重大决策时补充记录。

# 播放引擎选择

Pavo 当前选择 mpv/libmpv 作为播放引擎，并通过 `python-mpv` 在 Python 中调用。

选择原因：

- mpv 是成熟、稳定、格式支持广泛的媒体播放引擎。
- libmpv 提供可嵌入应用的 API，适合桌面播放器集成。
- mpv 自带音轨、字幕轨、倍速、画面比例、硬件解码等播放器核心能力，Pavo 不需要自行实现复杂的媒体解码。
- Python 层可以通过 `python-mpv` 以相对简单的方式调用播放控制和属性监听。

没有选择其他方案的原因：

- 直接使用 FFmpeg 解码和渲染会显著增加实现复杂度，不适合当前阶段。
- 使用 VLC 也可行，但 UI 嵌入、OpenGL 渲染和 Python 绑定的控制方式与当前目标不如 libmpv 直接。
- 使用系统原生 AVFoundation 可以获得更强 macOS 原生性，但会把项目推向 Swift/AppKit 或更复杂的 Python 桥接路线，与当前 Python + PySide6 技术路线不一致。

当前影响：

- `src/engine.py` 负责封装 mpv 播放器。
- `src/video_widget.py` 负责将 mpv 渲染输出接入 Qt OpenGL 画布。
- 后续新增播放相关能力时，应优先使用 mpv 已有能力，而不是自行实现媒体底层逻辑。

# GUI 框架选择

Pavo 当前选择 PySide6/Qt Widgets 作为 GUI 框架。

选择原因：

- PySide6 是成熟的 Python 桌面 GUI 框架，适合快速构建本地应用。
- Qt Widgets 提供稳定的窗口、菜单、按钮、滑条、列表、拖放和事件系统。
- Qt 支持 `QOpenGLWidget`，能够承载 mpv OpenGL render context。
- QSS 可以支持当前项目追求的半透明、圆角、毛玻璃感 UI 风格。
- 对 Python 初学者和 AI 辅助开发而言，PySide6 的开发反馈速度较快。

当前影响：

- 主窗口基于 `QMainWindow`。
- 播放列表基于 `QListWidget`。
- HUD 使用 `QWidget`、`QPushButton`、`QSlider`、`QLabel` 等组件组合。
- 菜单使用 Qt 的 `QMenu` 和 `QAction`。

维护约束：

- 不应轻易替换 GUI 框架。
- 新 UI 应遵循现有 Qt Widgets + QSS 风格。
- 不应在没有明确收益的情况下混入另一套 GUI 框架。

# 视频渲染方案

Pavo 当前使用 `QOpenGLWidget` + mpv OpenGL render context 进行视频渲染。

方案说明：

- `src/video_widget.py` 定义 `PavoVideoWidget`，继承自 `QOpenGLWidget`。
- 初始化 OpenGL 时创建 `mpv.MpvRenderContext`。
- mpv 通过 OpenGL FBO 渲染到 Qt 提供的画布中。
- mpv 更新画面时触发回调，再通过 Qt 队列调用刷新画布。

选择原因：

- 该方案可以把 mpv 的高质量播放能力嵌入 PySide6 窗口。
- 视频区域仍然属于 Qt 应用的一部分，方便叠加 HUD、播放列表和 OSD。
- 比外部独立 mpv 窗口更适合做统一的桌面应用体验。

当前影响：

- `src/video_widget.py` 不应承担播放列表、历史记录或菜单逻辑。
- 渲染状态需要依赖 `PavoEngine.current_media_path` 判断是否存在当前媒体。
- Clear Playlist 等空状态操作必须同步清理引擎状态并触发视频画布重绘，避免残留最后一帧。

风险：

- OpenGL、Qt 和 mpv 的生命周期顺序比较敏感。
- macOS 不同版本、硬件架构和 Qt 渲染后端可能影响稳定性。
- 未来如果替换渲染方案，需要完整回归播放、全屏、PiP、空状态和 HUD 覆盖效果。

# 项目结构设计

Pavo 当前采用小型 Python 桌面项目结构，核心源码集中在 `src/` 下。

当前职责划分：

- `src/main.py`
  - 应用入口和主窗口。
  - 负责连接引擎、视频画布和 HUD。
  - 管理 File 菜单、Open File、Recent Files、Clear Playlist。
  - 管理播放列表、当前索引、播放历史、OSD、快捷键、全屏、PiP 和缩略图弹窗。

- `src/engine.py`
  - 封装 mpv 播放器。
  - 管理播放、停止、暂停、音量、静音、倍速、画面比例、音轨、字幕轨。
  - 监听播放结束、媒体加载、暂停状态。
  - 负责缩略图抽帧请求和 FFmpeg 路径查找。

- `src/video_widget.py`
  - 提供 OpenGL 视频画布。
  - 将 mpv render context 渲染到 Qt widget。
  - 处理文件拖放、鼠标点击/双击、滚轮调音量。
  - 在无媒体时清空画面。

- `src/components/hud_panel.py`
  - 提供底部 HUD 控制栏。
  - 管理按钮、滑条、图标、布局和进度条悬停信号。
  - 通过 Qt Signal 对外通知用户操作。

- `src/bootstrap.py`
  - 配置 macOS 运行环境。
  - 设置 locale、动态库搜索路径和 Qt/OpenGL 相关环境变量。

设计原则：

- UI 组件通过信号通信，尽量避免直接跨层操作内部状态。
- mpv 相关操作应优先集中在 `engine.py`。
- 视频画布只处理渲染和画布交互。
- 播放列表和持久化目前集中在 `main.py`，未来可以逐步拆分，但不应在小修中大规模重构。

# macOS 优先策略

Pavo 当前以 macOS 作为主要目标平台。

选择原因：

- 项目定位强调 macOS 原生观感和半透明玻璃质感。
- 当前环境初始化依赖 macOS 常见设置，例如 `DYLD_LIBRARY_PATH`、`QT_MAC_WANTS_LAYER` 和 Homebrew 路径。
- README 中的运行说明使用 `brew install mpv`。
- 打包目标是 macOS `.app`。
- UI 行为包含 macOS 常见习惯，例如 `Cmd+O`、顶部菜单和 PiP 风格窗口。

当前影响：

- 新功能应优先保证 macOS 可用和体验一致。
- 不应为了名义上的跨平台支持破坏 macOS 体验。
- 如果未来支持 Windows 或 Linux，应作为独立兼容任务处理，并明确记录新决策。

风险：

- Homebrew 路径、动态库加载、签名、公证和硬件架构会影响分发稳定性。
- 当前仓库内存在本地 `ffmpeg` 二进制，长期需要明确分发和架构策略。

# 未来需要记录的决策

以下主题尚未形成最终决策，未来一旦实施，应补充到本文档：

- 是否继续使用 PyInstaller，或迁移到其他 macOS 打包方案。
- `ffmpeg` 是随包分发、要求用户安装，还是构建时下载/注入。
- 是否引入正式日志系统，以及日志文件保存位置。
- 是否拆分 `src/main.py`，以及拆分后的模块边界。
- 是否引入 `storage.py` 管理 `~/.pavo_data.json` 的 schema version 和迁移。
- 是否独立实现 `ThumbnailService`，以及缩略图缓存策略。
- 是否引入测试框架、lint、格式化和 CI。
- 是否实现真正的 i18n，以及默认语言策略。
- 是否支持 Windows/Linux，以及跨平台支持的优先级。
- macOS 发布是否进行代码签名、公证和 DMG 分发。
