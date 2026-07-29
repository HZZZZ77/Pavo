# PAVO-005

## Title

Unify glass UI styling

## Status

Completed

## Priority

P1

## Created

2026-07-27

## Objective

统一 Pavo 主要浮层与交互控件的玻璃视觉语言，并确保无媒体状态下 HUD 进度显示与播放器真实状态一致。

## Background

HUD 精修后，无媒体状态的进度条残留、Qt 默认进度条绘制、浮层边框差异和菜单样式不一致更加明显。

本任务在不改变播放器布局和功能的前提下，以底部 HUD 为视觉基准，逐步统一顶部 OSD、菜单、Empty State 和 Playlist，并修复空媒体状态进度不一致问题。

## Requirements

- 无媒体启动和 Clear Playlist 后，进度、时间和 seek 状态必须归零。
- 使用自绘进度条，保留 hover preview、seek 和 disabled 行为。
- 优化 HUD 按钮 hover、pressed、tooltip 和自动隐藏交互。
- 使用抗锯齿自绘统一 HUD、顶部 OSD、Empty State 按钮和 Playlist 的玻璃背景与边框。
- 统一设置、字幕和 Playlist 右键菜单的深色玻璃样式。
- 保持播放、播放列表、缩略图、PiP、全屏和文件打开功能不变。

## Scope

- `src/components/hud_panel.py`
- `src/main.py`

## Non Goals

- 不重做 HUD 或播放器布局。
- 不修改播放引擎和播放流程。
- 不修改 `src/engine.py`。
- 不修改 `src/video_widget.py`。
- 不新增控制按钮、媒体库或其他产品功能。

## Acceptance Criteria

- 无媒体状态下进度条不显示蓝色进度或 handle，且不可 seek：通过。
- Clear Playlist 后时间和进度正确归零：通过。
- 播放媒体后进度条、hover preview 和 seek 正常：通过。
- HUD 显示隐藏、按钮反馈和菜单操作正常：通过。
- HUD、顶部 OSD、菜单、Empty State 按钮和 Playlist 玻璃视觉一致：通过。
- Playlist 拖放、右键菜单、滚动、双击播放和淡入淡出保持正常：通过。
- 播放、暂停、PiP、全屏和文件打开无回归：通过。

## Testing

运行：

```bash
venv/bin/python -m compileall src
git diff --check
```

测试结果：

- `python3 -m compileall src`：通过。
- `venv/bin/python -m compileall src`：通过。
- `git diff --check`：通过。
- 用户实机视觉测试：通过。
- 用户实机交互与播放回归测试：通过。

## Notes

- `HoverSlider` 使用 `QPainter` 和 `QStyle.sliderPositionFromValue()` 自绘轨道、进度和 handle。
- HUD、顶部 OSD、Empty State 按钮和 Playlist 容器使用抗锯齿圆角玻璃绘制。
- `QMenu` 保留原生 popup 行为，仅统一深色玻璃样式。
- Playlist 的 `QListWidget` 保持原有数据与交互职责，外层增加独立玻璃容器承载视觉和透明度动画。
- 未修改播放逻辑、播放引擎或视频渲染模块。

## Commit

`Pending`
