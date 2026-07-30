# PAVO-001

## Title

Prevent stale thumbnail preview after media switch

## Status

Completed

## Priority

P1

## Created

2026-07-24

## Objective

解决切换视频后短暂显示前一个视频缩略图的问题。

## Background

- 缩略图异步 FFmpeg 请求可能产生旧媒体结果。
- 缓存缺少媒体身份隔离。
- UI `thumb_label` 保留旧 pixmap。

## Requirements

- 防止旧媒体缩略图污染新媒体。
- 防止重复缩略图生成请求。
- 清理切换媒体时的旧缩略图 UI 状态。

## Scope

- `src/engine.py`
- `src/main.py`

## Non Goals

- 不重构 `ThumbnailService`。
- 不改变 HUD UI。
- 不优化缩略图生成性能。

## Acceptance Criteria

- 正常缩略图显示：通过。
- 快速拖动进度条：通过。
- 视频切换无旧缩略图：通过。
- Clear Playlist 后无缩略图：通过。

## Testing

运行：

```bash
python3 -m compileall src
```

结果：

- Python 源码编译检查通过。
- 正常缩略图显示手动测试通过。
- 快速拖动进度条手动测试通过。
- 视频切换无旧缩略图手动测试通过。
- Clear Playlist 后无缩略图手动测试通过。

## Commit

`b302de4 fix(thumbnail): prevent stale preview after media switch`
