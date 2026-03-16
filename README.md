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
    pip install -r requirements.txt
    python src/main.py
    ```

---

### 📝 开发者寄语

现在的 Pavo 依然有很多“稚嫩”的地方。如果你在代码中发现了不规范的写法，或有更优雅的实现方式，请务必开一个 **Issue** 告诉我。对于一个初学者来说，这是最珍贵的反馈。

---

### 📄 License
本项目基于 [MIT] 协议开源。