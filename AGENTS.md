# Pavo Agent Maintenance Guide

## 项目定位

Pavo 是一款面向 macOS 体验的极简视频播放器。它使用 Python 与 PySide6 构建桌面界面，并通过 mpv/libmpv 负责媒体播放。

Pavo 的长期目标是成为一个轻量、稳定、具有 macOS 原生审美的视频播放器。维护时应优先保证播放稳定性、交互一致性和打包可用性，再逐步增强播放列表、最近文件、字幕、偏好设置和发布流程。

## 技术栈

- 语言：Python
- GUI 框架：PySide6 / Qt Widgets
- 视频渲染：QOpenGLWidget + mpv OpenGL render context
- 播放引擎：python-mpv / libmpv
- 缩略图预览：FFmpeg 子进程抽帧
- 并发方式：Python threading
- 数据保存：用户目录下的 `~/.pavo_data.json`
- 构建打包：PyInstaller，目标产物为 macOS `.app`
- 主要运行平台：macOS，当前依赖 Homebrew 常见路径查找 mpv/ffmpeg 相关库

## 架构原则

- `src/main.py` 是主窗口和应用编排层，负责菜单、播放列表、OSD、快捷键、窗口模式和模块连接。不要继续无节制地把新业务逻辑塞进这里；较大的新功能应考虑拆分为小模块。
- `src/engine.py` 是播放引擎封装层，负责 mpv 控制、播放状态信号、音轨/字幕轨、倍速、比例、停止播放和缩略图抽帧。不要让 UI 组件直接操作 mpv 内部对象。
- `src/video_widget.py` 是视频画布层，负责 OpenGL 渲染、拖放、鼠标点击/双击和滚轮音量等画布交互。不要把播放列表或持久化逻辑放入这里。
- `src/components/hud_panel.py` 是 HUD 控制栏组件，负责控件布局、图标、进度条和用户操作信号。HUD 应通过信号与主窗口/引擎通信，不直接管理播放列表或文件数据。
- `src/bootstrap.py` 负责运行环境初始化。环境变量和平台兼容逻辑应集中在这里，避免在多个模块中散落。
- 保持现有模块职责边界。除非任务明确要求重构，不要大规模移动代码或改变公共信号/方法契约。

## 代码修改规则

- 修改前先分析当前代码、相关调用链和现有工作区状态。
- 不进行无意义重构，不做与任务无关的格式化、改名、迁移或风格统一。
- 修改多个文件时，必须能说明每个文件被修改的原因。
- 保持已有功能稳定，尤其是播放、暂停、进度、拖放、播放列表、Recent Files、Clear Playlist、PiP、全屏、字幕、音轨和缩略图预览。
- 优先复用现有信号、方法和 UI 风格，不随意引入新框架或新依赖。
- 避免裸 `except: pass` 扩散。新增错误处理时，尽量提供日志或用户可见提示。
- 修改播放状态时，以 mpv/engine 的真实状态为准，并同步 HUD 图标。
- 修改播放列表或最近文件时，注意同步内存状态、UI 状态和 `~/.pavo_data.json`。
- 不要修改用户已有的无关改动。发现未提交改动时，先识别是否与当前任务有关。

## Git 工作流程

- 修改前查看 `git status`，确认当前分支和未提交文件。
- 修改前后都要注意区分自己本次修改和用户已有修改。
- 提交前查看 `git diff`，确认没有包含无关变更。
- commit 信息应清晰、具体，推荐使用 Conventional Commits，例如：
  - `fix(player): clear media state after playlist reset`
  - `feat(menu): add recent files submenu`
  - `chore(build): update pyinstaller bundle assets`
- 不要在用户未要求时自动提交、推送或创建 PR。

## 测试要求

- 每次修改 Python 源码后，至少运行语法检查：
  - `python3 -m compileall src`
- 涉及播放状态时，手动验证：
  - 打开视频
  - 播放/暂停
  - 快进/快退
  - 播放结束自动跳转下一项
  - 播放按钮图标状态正确
- 涉及播放列表时，手动验证：
  - 多文件加入
  - 双击播放
  - 删除项目
  - 拖拽排序
  - Clear Playlist 后播放器回到空状态
- 涉及文件打开或 Recent Files 时，手动验证：
  - `Cmd+O`
  - `File > Open File...`
  - 多选文件
  - Recent Files 去重并移动到最前
  - 不存在文件被忽略
- 涉及缩略图时，手动验证：
  - 有媒体时悬停进度条出现预览
  - 无媒体或 Clear Playlist 后不出现预览
- 涉及打包时，检查 `Pavo.spec` 是否包含必要资源，并验证 `.app` 能启动、播放和显示图标。
