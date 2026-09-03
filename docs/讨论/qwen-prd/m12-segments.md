# M12：transcript JSON segments（结构化转录分段视图）

2026-08-21 定稿。对应 PRD §31 后续阶段规划第 1 项「transcript JSON segments」。
范围 = 数据解析 + 详情页分段展示：把 `.transcript.json`（QVoice `-f json` 产物）
中的 segments（时间戳 / 说话人）从「仅保留在原文件中」升级为详情页可浏览的
分段视图。音频播放器与点击跳转属下一项「音频字幕级跳转」（M13），本里程碑
不引入播放器。

---

## 0. 已定决策（讨论结论，不再开放）

1. **范围 = 解析 + 展示**。只做 `load_transcript_segments` 数据层与详情页
   分段视图；不做播放器 / 点击跳转（§31 第 2 项）、不改索引内容（索引 /
   向量 / 总结输入继续走纯文本提取，行为不变）、不加 REST 端点（NiceGUI
   服务端渲染直接读文件）、不做搜索结果定位到段。
2. **segments 按需解析、不入库**。文件即事实源（项目惯例，artifacts 表只存
   路径），详情页打开时解析 JSON；转录 JSON 通常几百 KB 量级，解析毫秒级。
3. **json 转录 tab 默认分段视图**，替换原「纯文本预览 + 展开全文」——分段
   视图信息严格包含纯文本（段文本拼接即全文），原始 JSON 可用 tab 内
   「文件」按钮外部打开。segments 缺失 / 解析失败自动回退纯文本预览
   （`_render_text_section` 现状行为）；txt 转录（`.transcript.txt` / `.txt`）
   完全不变。
4. **展示形态**：每段一行 `[MM:SS] [说话人徽章] 文本`；时间戳不足 1 小时为
   `MM:SS`、以上为 `H:MM:SS`，缺失则不显示；说话人缺省不显示；信息行显示
   段数 / 时长 / 语言（有才显示），`duration` 缺失时用最后一段的 `end` 推导。
5. **分页 100 段/页**，上一页 / 下一页 + 页码，容器限高内部滚动——对齐大文本
   分段翻页的既有交互；长转录（数千段）不一次渲染全部节点。
6. **顺带修复 m11 遗留 bug**：sidecar 目录内固定名 `transcript.json` 无 stem
   前缀，不命中 `.transcript.json` 后缀判定 → 此前索引 / 向量 / AI 总结输入
   读入的是**原始 JSON 文本**、详情页无预览。修复 = 判定统一为「文件名 =
   `transcript.json` 或后缀 `.transcript.json`」（`rules.is_transcript_json_name`），
   utils 与详情页共用。平铺库中独立存在的 `transcript.json` 不命中任何资产 /
   产物规则，精确匹配收紧无副作用。已有库需手动重建全文索引纠正旧内容。
7. **范围外（明确不做）**：说话人筛选 / 重命名、segments 编辑、时间轴控件、
   字幕文件（srt/vtt）导出、meta.json 结构定义。

---

## 1. 现状事实（代码依据）

```text
utils._is_transcript_json      仅 endswith(".transcript.json") -> sidecar
                                transcript.json 不命中（见决策 6）
read_text_for_index/preview/full  索引(index_service)、向量、总结输入
                                (summarization_service)、详情页预览全走它
asset_detail.is_text_artifact   同样的 endswith 判定 -> sidecar 转录 tab 无预览
详情页 json 转录现状             extract_transcript_json_text 纯文本预览 +
                                展开全文 / 分段翻页（无时间轴、无说话人）
extract_transcript_json_text    text 优先、回退拼接 segments[].text（保持不动，
                                索引 / 总结输入继续用它）
```

## 2. 实施蓝图

### 2.1 `app/rules.py`

```python
is_transcript_json_name(filename)
    # 平铺 <stem>.transcript.json（后缀）或固定名 transcript.json（精确），
    # 大小写不敏感；meta.json / 普通 json 不命中
```

### 2.2 `app/utils.py`

```text
_is_transcript_json        改走 rules.is_transcript_json_name（sidecar 修复点）
load_transcript_segments(path) -> {duration, language, segments}
                           归一化：无文本段跳过、start/end 非数值置 None、
                           speaker 空串归 None、duration 缺失用末段 end 推导；
                           解析失败抛 ValueError（与 extract 风格一致）
format_clock(seconds)      MM:SS（<1h）/ H:MM:SS（≥1h）；None/负数 -> 空串
```

### 2.3 `app/ui/pages/asset_detail.py`

```text
is_text_artifact           .transcript.json 判定改走 rules helper（sidecar
                           转录 tab 恢复预览）
is_json_transcript(artifact) 产物级判定：走分段视图 or 纯文本
_render_transcript_segments(artifact)
                           信息行（段数/时长/语言）+ 100 段/页分页列表
                           （时间戳 + 说话人徽章 + 文本）+ 上一页/下一页；
                           异常 / 空 segments 回退 _render_text_section
tab 渲染分发                json 转录 -> 分段视图；其余文本产物 -> 纯文本
```

### 2.4 零改动确认

索引分块策略、vector_service、search_service、summarization_service、API 层、
tasks 页均不动；sidecar 修复通过 utils 判定统一自动生效（旧索引需手动重建）。

## 3. 测试步骤（开发人员手动执行）

```text
1. 库目录放 podcast.mp3 + podcast.transcript.json（QVoice 生成，或手工放置
   合成 JSON：顶层 text/language/duration + segments[{start,end,text,speaker}]），
   刷新后进详情页 → 转录 tab 为分段视图：[MM:SS] 时间戳 + 说话人徽章 + 文本，
   信息行显示 段数 · 时长 · 语言
2. 长转录（>100 段）：上一页/下一页可用，首页/末页按钮禁用，容器内部滚动
3. sidecar 形态：建 podcast.mp3.kb\ 放入 transcript.json（同一 JSON）→ 详情页
   分段视图正常（bug 修复验证）；设置页重建全文索引后，全文搜索能命中转录文本
   （修复前索引用的是原始 JSON 文本）
4. 仅 .kb 内 json 转录的资产生成 AI 总结 → 总结基于提取文本而非 JSON 原文
5. txt 转录（.transcript.txt / .txt）详情页仍为纯文本预览 + 展开全文，不变
6. segments 为空的 json（只有顶层 text）→ 回退纯文本预览；损坏 JSON → 同样
   回退并显示「（无法读取预览）」，不白屏
7. 无 speaker / 无 language / 无 duration 的 JSON → 对应项不显示，不报错
8. 回归：无 json 转录的库，详情页 / 索引 / 总结行为与之前完全一致
```

## 4. M12 验收标准

对应 PRD §29.12：

```text
json 转录详情页显示分段视图：时间戳/说话人/文本，长转录分页浏览
sidecar transcript.json 与平铺同待遇：预览/索引/总结输入均为提取文本
txt 转录行为不变；segments 缺失/损坏 JSON 回退纯文本或明确提示
```

## 5. PRD 同步清单（实施完成时）

```text
§9.2 / §12.1：时间轴/说话人注释更新（m12 起详情页分段展示，点击跳转仍属后续）
§28 增 M12；§29 增 29.12；§31 移除第 1 项并重排；§35 顺序增 M12
```

---

## 附录 A：冒烟验证（2026-08-21 已通过）

临时脚本验证（无 UI，跑完即删），32 项断言全部通过，覆盖点：

```text
判定：平铺 .transcript.json / sidecar 固定名 transcript.json / 大小写 /
     meta.json 与普通 json 不命中
归一化：无文本段、无 text 键段、非 dict 段跳过；文本 strip；说话人保留 /
     缺失 / 空串三种形态；非数值 start 置 None；duration 与 language 读取；
     duration 缺失用末段 end 推导
读取链路（bug 修复核心）：sidecar transcript.json 走 read_text_for_index /
     read_text_preview / read_text_full 均得提取文本而非原始 JSON；
     text 为空回退拼接 segments（原逻辑保持）
异常：损坏 JSON 抛 ValueError；segments 为空返回空列表（UI 回退纯文本）
format_clock：00:00 / 四舍五入 / 59:59 / 1:02:05 / None 与负数返回空串
详情页判定：平铺与 sidecar json 均判文本产物且走分段视图；txt 不走
```
