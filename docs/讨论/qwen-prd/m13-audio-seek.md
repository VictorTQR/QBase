# M13：音频/视频播放器与字幕级跳转

2026-08-21 定稿。对应 PRD §31 后续阶段规划第 1 项「音频字幕级跳转」，同时
补齐 PRD §11.2 对音频/视频详情页「浏览器原生播放器」的要求。范围 = 详情页
播放卡片 + json 转录分段视图时间戳点击跳转，音频与视频一并实现（机制相同，
PRD §11.2 本就要求两者都有播放器）。

---

## 0. 已定决策（讨论结论，不再开放）

1. **播放器用浏览器原生元素**（PRD §11.2 允许）：NiceGUI `ui.audio` /
   `ui.video`，带原生 controls（播放/暂停/进度条/音量）；不自研播放器 UI、
   不做倍速 / 波形 / 快捷键。
2. **本地文件由 NiceGUI 自动托管，不加 REST 端点**：`ui.audio(Path)` /
   `ui.video(Path)` 构造时自动注册媒体路由（`add_media_file` →
   `get_range_response`），支持 HTTP Range 流式——大文件边下边播、进度条可
   拖动；元素销毁时路由自动移除。API / services / repositories 层零改动。
3. **跳转交互 = 点击分段视图时间戳 → seek + 自动播放**：`player.seek(start)`
   后 `player.play()`；点击是用户手势，不受浏览器自动播放策略限制。
   txt 转录无结构化时间戳，不提供跳转。
4. **范围同时覆盖视频**：视频资产详情页用 `ui.video`（限宽限高
   `w-full max-h-[60vh]`），其 json 转录时间戳同样可点击跳转。浏览器不支持
   的容器（如部分 mkv/avi 编码）由原生元素自行报错，属浏览器能力边界。
5. **降级路径保持 m12 行为**：无播放器（文档资产旁的 transcript.json、
   源文件缺失）或段 `start` 缺失时，时间戳仍为纯文本；源文件缺失时播放卡片
   显示「源文件不存在于磁盘」提示，页面不白屏。
6. **不做反向同步**（播放中高亮 / 滚动到当前段）：需 ui.timer 轮询播放进度
   并持续重渲染分段列表，复杂度远超单向跳转，明确不做，需要时再立任务。
7. **范围外（明确不做）**：播放器与索引 / 搜索 / 总结的任何联动（这些层
   零改动）、字幕文件（srt/vtt）加载、播放历史 / 断点续播。

---

## 1. 现状事实（代码依据）

```text
NiceGUI Audio/Video 元素          均有 seek(seconds) / play() / pause()；
                                  传入本地 Path 自动注册 Range 媒体路由
                                  （core.app.add_media_file），元素销毁自动移除
                                  路由；文件不存在时构造抛 FileNotFoundError
asset_detail（m12 后）            json 转录 tab 走 _render_transcript_segments：
                                  [MM:SS] 时间戳纯文本 + 说话人徽章 + 文本，
                                  100 段/页分页；无播放器，音频/视频详情页
                                  也没有任何播放能力（§11.2 播放器欠账）
load_transcript_segments          segments[{start,end,text,speaker}] 已归一化，
                                  start 非数值置 None -> format_clock 返回空串
                                  （无时间戳段天然不可跳转）
```

## 2. 实施蓝图

### 2.1 `app/ui/pages/asset_detail.py`（唯一改动文件）

```text
_make_seek_handler(player, start)  工厂函数生成点击 handler（seek + play），
                                   避免循环内闭包晚绑定
播放卡片                           基本信息卡片之后，仅 audio/video：源文件
                                   存在 -> ui.audio / ui.video（保存引用
                                   media_player）；缺失 -> 橙色提示，player
                                   为 None
_render_transcript_segments(artifact, player=None)
                                   player 非 None 且段有 start：时间戳由纯文本
                                   改为 flat dense 蓝色 mono 按钮（props 沿用
                                   本页 "flat dense size=sm no-caps color=blue"
                                   惯例）；否则保持 m12 纯文本
tab 渲染分发                       _render_transcript_segments(artifact,
                                   media_player)；翻页/重渲染后点击仍有效
                                   （player 位于播放卡片，不受分段容器
                                   clear() 影响）
```

### 2.2 零改动确认

API 层、services、repositories、utils、rules、索引 / 向量 / 搜索 / 总结均
不动；播放能力完全在详情页 UI 层内闭合。

## 3. 测试步骤（开发人员手动执行）

```text
1. 库目录放 podcast.mp3 + podcast.transcript.json，刷新后进详情页 →
   基本信息卡片下方出现「播放」卡片，原生控件可播放 / 暂停、进度条可拖动
2. 转录 tab 分段视图时间戳变为可点击按钮 → 点击某段后播放器跳到该时间并
   自动播放；播放中再点击另一段时间立即切换
3. 长转录（>100 段）：翻到第 2 页后点击时间戳仍能跳转（跨页跳转有效）
4. 视频资产（如 .mp4）+ 同名 .transcript.json → 详情页为 ui.video 播放器
   （限宽限高），时间戳点击跳转同样有效
5. txt 转录（.transcript.txt / .txt）→ 纯文本预览，无时间戳无跳转，不变
6. 降级：外部移走 podcast.mp3 后刷新详情页 → 播放卡片显示「源文件不存在
   于磁盘」，分段视图时间戳回到纯文本，不白屏不报错
7. 无转录的音频资产 → 播放卡片正常显示（无跳转入口）
8. 回归：文档资产详情页无播放卡片；列表 / 搜索 / 设置 / 任务页不受影响
```

## 4. M13 验收标准

对应 PRD §29.13：

```text
音频/视频详情页显示原生播放器，可播放并拖动进度条
json 转录分段视图时间戳可点击，点击后播放器跳转到该段时间并播放
无播放器或时间戳缺失时降级为纯文本；源文件缺失显示明确提示
其余页面与索引/搜索/总结行为不变
```

## 5. PRD 同步清单（实施完成时）

```text
§3 移除「字幕级音频跳转」并更新总结句（M9-M13）
§9.2 / §12.1：点击跳转注记更新（m13 起支持）
§11.2：播放器条目注记 m13 已实现
§28 增 M13；§29 增 29.13；§31 移除第 1 项并重排；§34 移除「JSON segments 字幕跳转」
```
