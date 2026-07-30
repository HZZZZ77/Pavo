# PAVO-003

## Title

Improve empty state guidance

## Status

Completed

## Priority

P1

## Created

2026-07-27

## Objective

改善 Pavo 无媒体状态下的首次使用引导，同时保持 macOS 极简高级播放器定位。

## Background

当前 Pavo 在没有媒体时主要显示空白视频区域。虽然功能正确，但首次打开应用时缺少产品感和引导能力。

根据 `PRODUCT.md`，Pavo 应提供完整的空状态体验，而不是简单等待用户操作。

## Requirements

- 完善现有无媒体状态的首次使用引导。
- 保持 macOS 简洁、克制、高级的视觉方向。
- 提供清晰的首次使用引导。
- 不影响已有播放、拖放、菜单和快捷键流程。

## Scope

- 新增 `src/components/empty_state.py`。
- 修改 `src/main.py`。
- 未新增 `assets` UI 资源。

## Non Goals

- 不重构播放架构。
- 不修改 mpv 播放逻辑。
- 不修改 HUD。
- 不增加媒体库。
- 不增加账号、网络功能。
- 不重做 UI，不增加欢迎页或复杂动画。

## Acceptance Criteria

- 应用启动无媒体时显示新的空状态：通过。
- 拖入视频后空状态正确消失：通过。
- Clear Playlist 后正确恢复空状态：通过。
- `Cmd+O` 打开文件流程保持正常：通过。
- 不影响播放和视频渲染：通过。

## Testing

运行：

```bash
python3 -m compileall src
```

测试结果：

- 空状态视觉：通过。
- Open File：通过。
- 拖放：通过。
- Clear Playlist：通过。

## Commit

`Pending`
