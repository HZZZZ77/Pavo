# 🦉 Pavo

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/macOS-Native_Look-black?style=for-the-badge&logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/UI-Glassmorphism-A020F0?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Collaborator-Gemini_AI-orange?style=for-the-badge&logo=google-gemini&logoColor=white" />
</div>

<br/>

### 📖 项目简介

**Pavo** 是一款诞生于编程初学者手中的极简视频播放器。本项目的核心目标，是尝试在 Python 环境下复刻 macOS 原生应用中那种通透、精致的 **毛玻璃 (Glassmorphism)** 质感。

本项目由一名软件开发初学者在 **Gemini (AI)** 的全程协助下完成。这里记录了 AI 辅助下跨越“技术壁垒”、从零到一构建桌面应用的实战过程。

---

### 🌟 核心特性与学习笔记

| 特性 | 描述 | 技术实现 |
| :--- | :--- | :--- |
| **极致视觉尝试** | 为 HUD 控制栏、侧边栏及所有菜单定制了半透明圆角样式，追求系统级审美。 | **PySide6 / QSS** |
| **异步抽帧引擎** | 进度条悬停时实时查看视频预览画面，且不影响主播放流程。 | **FFmpeg / Multi-threading** |
| **交互式列表** | 支持**鼠标拖拽重排顺序**，且列表随控制栏同步“呼吸”隐藏。 | **QListWidget Customization** |
| **国际化定义** | 全界面采用专业地道的英文术语，支持多种主流画面比例与倍速调节。 | **Internationalization (i18n)** |

---

### 🧠 Gemini 在本项目中的角色

作为一个初学者，我发现 AI 不仅仅是一个代码生成器，更是一位“24 小时在线”的耐心导师：

* **从报错到理解**：面对复杂的渲染错误，Gemini 负责分析 Traceback 并解释底层的执行原理。
* **从逻辑到代码**：当我提出模糊想法时，它帮我完成原型并提供像素级的样式打磨建议。
* **疑难杂症攻克**：在处理多线程冲突和路径兼容性问题上，AI 提供了极其关键的指导。

---

### 🚀 开启 Pavo 体验

1.  **准备环境**：安装 Python 3.11+ 及 `mpv` 库 (`brew install mpv`)。
2.  **部署运行**：
    ```bash
    python3 -m pip install -r requirements.txt
    python3 src/main.py
    ```

---

### 📦 macOS arm64 打包基线

Pavo 第一阶段发布基线面向 Apple Silicon：

- 应用名称：`Pavo`
- 应用版本：`1.2.0`
- Bundle Identifier：`io.github.hzzzz77.pavo`
- 目标架构：`arm64`
- 最低系统版本：macOS 13.0
- 构建 Python：3.13.12
- Qt for Python：PySide6 / shiboken6 6.9.3

从干净 clone 先构建固定版本的 arm64 媒体运行时：

```bash
python3.14 tools/media_runtime/build.py
```

然后创建独立应用构建环境：

```bash
python3.13 -m venv .venv-build
.venv-build/bin/python -m pip install -r requirements-build.txt
```

应用打包命令：

```bash
.venv-build/bin/python -m PyInstaller --clean --noconfirm Pavo.spec
```

构建产物位于：

```text
dist/Pavo.app
```

验证 bundle 内媒体运行时和动态依赖：

```bash
python3.14 tools/media_runtime/verify_bundle.py
```

`Pavo.app` 会使用 `Contents/Frameworks` 中随包提供的 `libmpv.2.dylib` 和
`ffmpeg`，不要求用户安装 Homebrew、mpv 或 FFmpeg。当前产物仍未进行
Developer ID 签名或 Apple 公证，因此暂不用于公开分发。

发布构建固定使用 Python 3.13.12 和 PySide6 6.9.3。最终应用包必须执行：

```bash
python3.14 tools/media_runtime/verify_bundle.py dist/Pavo.app
```

验证以 `vtool` 读取的实际 Mach-O deployment target 为准，不以 wheel 文件名
或标签代替。当前固定组合的完整 bundle 扫描已通过 macOS 13.0 上限检查；公开
发布前仍必须在真实 macOS 13 Apple Silicon 设备完成启动、OpenGL 和播放验证。

---

### 📝 开发者寄语

现在的 Pavo 依然有很多“稚嫩”的地方。如果你在代码中发现了不规范的写法，或有更优雅的实现方式，请务必开一个 **Issue** 告诉我。对于一个初学者来说，这是最珍贵的反馈。

---

### 📄 License
本项目基于 [MIT](LICENSE) 协议开源。
