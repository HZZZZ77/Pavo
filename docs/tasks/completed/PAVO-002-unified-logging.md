# PAVO-002

## Title

Establish a unified logging system

## Status

Completed

## Priority

P1

## Created

2026-07-24

## Objective

为 Pavo 建立统一、可维护的日志系统，使启动、播放引擎、视频渲染和缩略图相关故障能够被一致记录，提升开发调试和用户问题排查能力。

## Background

- 此前日志输出分散，主要依赖少量 `print()`，缺少统一格式、级别和持久化策略。
- `src/main.py`、`src/engine.py`、`src/video_widget.py` 和 `src/bootstrap.py` 中存在静默异常或独立错误输出，问题发生后难以还原上下文。
- `docs/ROADMAP.md` 将错误提示和日志列为 V1.1 稳定性优化任务。
- 本任务采用符合 macOS 习惯且不引入新依赖的最小方案。

## Requirements

- 使用 Python 标准库 `logging`，不引入第三方依赖。
- 提供单一日志初始化入口，避免各模块重复配置 handler。
- 同时支持开发控制台日志和持久化文件日志。
- macOS 日志文件保存到 `~/Library/Logs/Pavo/pavo.log`。
- 使用轮转文件 handler，限制单个日志文件大小及历史文件数量。
- 日志至少包含时间、级别、模块名称和消息。
- 各模块通过命名 logger 记录启动、引擎初始化、播放、视频渲染和缩略图异常。
- 日志目录创建或文件 handler 初始化失败时，应用仍可启动，并保留控制台日志。
- 保持现有用户可见错误提示和运行行为不变。

## Scope

- `src/logging_config.py`
- `src/bootstrap.py`
- `src/main.py`
- `src/engine.py`
- `src/video_widget.py`

## Non Goals

- 不重构现有模块或调整架构职责。
- 不修改 HUD UI 或其他界面风格。
- 不改变现有弹窗、OSD 或错误提示文案。
- 不实现远程日志上传、崩溃报告或遥测。
- 不引入第三方日志框架或新依赖。
- 不处理与日志接入无关的播放逻辑或功能缺陷。
- 不修改 `requirements.txt`、`Pavo.spec` 或用户数据格式。

## Acceptance Criteria

- 控制台启动日志格式统一：通过。
- `~/Library/Logs/Pavo/pavo.log` 包含对应启动日志：通过。
- 重复初始化不会产生重复 handler 或重复日志行：通过。
- mpv、媒体播放、FFmpeg 缩略图和 OpenGL 异常包含诊断上下文：通过定向验证。
- 日志轮转及历史文件数量限制：通过定向验证。
- 文件日志初始化失败时应用保留控制台日志且不会退出：通过定向验证。
- 播放、暂停、播放列表、Recent Files、Clear Playlist 和缩略图预览无功能回归：通过。
- `python3 -m compileall src`：通过。

## Testing

运行：

```bash
python3 -m compileall src
```

自动及定向验证结果：

- Python 源码编译检查通过。
- 日志初始化幂等性、轮转、默认路径和文件 handler 失败降级测试通过。
- mpv 初始化失败、播放失败和 FFmpeg 缺失的日志路径测试通过。
- Pavo 正常启动，mpv 和 OpenGL render context 初始化成功。
- 日志文件包含启动、媒体打开和正常退出记录，未发现 Pavo `WARNING`、`ERROR`、`CRITICAL` 或 traceback。

手动回归结果：

- 打开媒体、播放、暂停、快进、快退和进度定位通过。
- 多个播放项加入、切换、删除和 Clear Playlist 通过。
- 缩略图正常显示、快速移动进度条和媒体切换隔离通过。
- 全屏和 PiP 进入、退出通过。

未覆盖风险：

- 原生文件选择器多选未在本轮手动测试中重新验证。
- 未等待媒体自然播放结束，自动跳转下一项未在本轮手动测试中覆盖。
- Clear Playlist 后空状态进度条仍可被点击并改变视觉值，但不会播放、定位或显示缩略图。
- 控制台存在 Qt/macOS 字体、样式和键盘映射警告，未影响功能且未进入 Pavo 日志。

## Notes

- 使用 `logging.handlers.RotatingFileHandler` 实现文件轮转。
- 日志初始化早于核心模块的首次业务日志，并保持幂等。
- 日志避免记录不必要的敏感信息；媒体日志仅记录文件名。

## Commit

`Pending`
