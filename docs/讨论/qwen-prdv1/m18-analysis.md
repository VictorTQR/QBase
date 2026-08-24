# M18：深度分析（多模板分析产物）

2026-08-24 讨论定稿并实施。定位：**总结服务快速浏览（短、泛），分析服务
深度使用（长、结构化、带时间锚点）**。新增一类派生产物 `analysis`：一个
资产 × 一个分析模板 = 一份分析文件。模板即预设提示词，首批内置「授课
分析」（李宏毅机器学习这类授课音视频：讲了什么、怎么讲的、哪些手法可
化用到自己的课）与「访谈分析」（晚点聊 1对1 / 钱婧 1对N 这类访谈播客：
话题脉络、逐段观点、主持技巧与可引用摘录）两个模板。

---

## 0. 已定决策（讨论结论，不再开放）

1. **分析是独立产物类型，不改造总结**。总结与打标行为完全不变（含 M16
   打标输入优先总结的链路，分析产物不参与打标输入）。「已有该模板分析」
   的跳过判定按文件名反解 preset（路径无关），与总结的 kind 级判定同为
   宽松语义。
2. **模板文件化，不做 UI 编辑器**：`.knowledge/presets/{preset_id}.md`，
   frontmatter（name / description / types）+ 正文即提示词（占位符
   `{title}` 替换为资产标题，str.replace 实现避免花括号冲突）。开库时
   `ensure_builtin_presets()` 生成内置模板，**已存在一律不覆盖**——改
   文件即改提示词、加文件即加新分析类型。preset_id 限
   `[a-z0-9][a-z0-9_-]*`，与产物文件名反解规则一致。（讨论时推荐项，
   用户未逐条复核。）
3. **输入带时间戳**：从 active 的 `.transcript.json` segments 构造
   `[MM:SS] 说话人: 文本` 每段一行（speaker 缺失省略，由模型推断并注
   明）。时间戳信息不再像总结那样在进 LLM 前丢失——两个内置模板的输
   出骨架都强制带时间锚点，为后续「点击时间戳跳转回看」留抓手。纯文本
   转录（-f txt / 普通 txt）没有时间分段，明确报错引导用 -f json 重转
   录，不降级为无时间戳分析。
4. **v1 时间戳仅展示**：分析产物里的时间戳以文本呈现，点击 seek 跳转
   留后续里程碑（markdown 渲染内嵌点击交互代价高，先保内容质量）。
5. **分析产物用 markdown 渲染**（详情页派生 tabs，剥 frontmatter 后
   `ui.markdown`，超长沿用 1 万字分页）；总结、转录维持纯文本不变——
   全项目首个 markdown 渲染点。
6. **独立 `[llm.analysis]` 配置节**（沿用 M16 tagging 独立成节的先例）：
   分析是长输入长输出（2 小时课程转录约 4-6 万字），默认指向长上下文
   模型（默认值 `Qwen/Qwen3-235B-A22B`，可换 GLM / DeepSeek 等任意
   OpenAI 兼容端点），max_tokens 6000、timeout 600s、max_input_chars
   100000、window_minutes 15。
7. **超长输入按时间窗切块**（时间感知版 map-reduce，替代总结的按字符
   切）：超过 max_input_chars 时按行首时间戳聚成 window_minutes 窗，
   逐窗调用（附「只分析该时间窗」指令）再合并；合并指令要求保留时间
   戳与模板结构。无时间戳无法分窗时明确报错。
8. **任务形态复用 M17 全套**：新任务类型 `analysis`（tasks.type 自由
   TEXT 零迁移），每资产每模板一条任务、同资产同类型去重、batch_runner
   消费 max_workers、open_library 重启恢复、任务中心展示 + 失败重试
   （preset_id 取自 params_json）。批量入口在资产列表（选模板 + 跳过
   已有/全部重新生成）。
9. **适用范围 v1 = 音视频**（需 JSON 转录）：内置模板 types 标注
   `audio, video`；机制上 types 字段留扩展（未来可加文档类模板）。
10. **范围外（明确不做）**：模板 UI 编辑器、时间戳点击跳转、分析产物
    的版本对比、按模板的全库批量入口（批量仍按当前多选资产）。

---

## 1. 现状事实（代码依据）

```text
llm_service.SYSTEM_PROMPT 等   总结/打标提示词硬编码模块常量，无多模板概念
summarization_service          单条 + 批量 + 恢复的任务编排骨架（镜像对象）
tasks / artifacts 表           type / kind 均自由 TEXT 无约束 → 零迁移
utils.load_transcript_segments transcript.json → segments[{start,end,text,speaker}]
                               （m12 详情页分段视图数据源）
utils.format_clock             秒 → [MM:SS] / [H:MM:SS]
extract_transcript_json_text   总结/打标输入走纯文本提取（时间戳丢弃）
rules.ARTIFACT_SUFFIXES /      精确后缀/dict 匹配，无变长模式分支
SIDECAR_FILE_KINDS
rules.derived_output_path      sidecar 存在写目录内否则平铺（m11 跟随现状）
batch_runner.execute_tasks     max_workers 并发 + in-flight 去重（m17）
config_service                 [llm.summary]/[llm.tagging] 读取/校验/测试先例
index_service.INDEX_ARTIFACT_KINDS
                               全文索引 kind 白名单（需加 analysis）
asset_repository._HAS_BADGE_COLUMNS /
search_service._get_derived_badges
                               has_* 徽章子查询（需加 has_analysis）
```

---

## 2. 实施蓝图

### 2.1 `app/services/analysis_preset_service.py`（新增）

```text
BUILTIN_PRESETS                teaching / interview 两个内置模板全文
parse_preset_content           极简 frontmatter 解析（--- 分隔 + key: value
                               行，不引依赖）；name 缺省回退 preset_id，
                               types 缺省 {audio, video}
ensure_builtin_presets         开库钩子：建 .knowledge/presets/ + 写内置
                               模板，已存在不覆盖
list_analysis_presets          列表（非法文件名/空正文跳过记日志）
get_analysis_preset            按 id 取，缺失/非法抛 ValueError（中文）
format_analysis_prompt         正文 .replace("{title}", title)
```

### 2.2 `app/rules.py`

```text
FLAT_ANALYSIS_NAME_RE          ^(?P<stem>.+)\.analysis\.(?P<preset>...)\.md$
SIDECAR_ANALYSIS_NAME_RE       ^analysis\.(?P<preset>...)\.md$
flat_analysis_artifact / sidecar_analysis_preset
                               文件名反解（平铺 → (stem, preset_id)）
explicit_artifact_kind/_stem、sidecar_file_kind
                               先于既有后缀/dict 匹配做 analysis 分支
```

已知取舍（与 `{stem}.summary.md` 同类）：真实命名为 `foo.analysis.bar.md`
的 md 资产会被误绑为 `foo` 的分析产物，接受。

### 2.3 `app/services/llm_service.py`

```text
TIMESTAMP_LINE_RE / _line_start_seconds / _format_seconds
                               行首 [MM:SS] / [H:MM:SS] 解析与格式化
split_by_time_windows          按时间戳聚窗（无时间戳行归当前窗；完全无
                               时间戳返回单窗）
analyze_text(system_prompt, text, config)
                               短输入单次调用；超长分窗：逐窗（ANALYSIS_
                               WINDOW_PROMPT）→ 合并（ANALYSIS_MERGE_PROMPT，
                               要求保留时间戳与结构、跨窗去重）
```

### 2.4 `app/services/analysis_service.py`（新增，镜像 summarization_service）

```text
build_timestamped_input        active JSON 转录 segments → [MM:SS] 说话人:
                               文本；仅音视频；非 JSON 转录报错引导重转录
analysis_output_filename       analysis.<preset_id>.md（derived_output_path
                               决定 sidecar/平铺，m11 跟随现状）
build_analysis_frontmatter     type/preset/preset_name/source/generator/
                               model/created_at
backup_existing_analysis       覆盖前备份 .knowledge/backups/
has_active_analysis            按 artifacts 文件名反解 preset（路径无关）
_create_analysis_task          预检（资产/在跑去重/enabled/模板存在且适用
                               类型/输入可构造）→ 建 pending 任务（params 记
                               preset_id + preset_name）
start_analysis / start_batch_analysis / resume_pending_analysis_tasks
run_analysis_task              执行体：LLM → 备份 → 写文件 → 重扫描 +
                               重建全文索引 → success/failed（失败不影响
                               其他任务）
```

### 2.5 配置（library_service / config_service / 设置页）

```text
DEFAULT_LIBRARY_CONFIG         新增 [llm.analysis] 节（见 §0.6 默认值）
get_analysis_llm_config        镜像 summary 版（enabled=false 不校验）
validate_config                llm.analysis 校验块（enabled 时各数值 > 0）
_mask_api_keys / get_key_status / has_plain_api_key / test_connection
                               均纳入 analysis（测试 kind = llm_analysis）
open_library                   ensure_builtin_presets + 恢复链追加
                               resume_pending_analysis_tasks
设置页                          「AI 分析配置」卡片（enabled/base_url/
                               model/api_key_env + 测试按钮）+「分析模板」
                               只读列表卡（名称/id/描述/适用类型 + 编辑指引）
```

### 2.6 索引与徽章

```text
INDEX_ARTIFACT_KINDS           + analysis（全文索引白名单，占位符同步 +1）
_HAS_BADGE_COLUMNS / _get_derived_badges
                               + has_analysis 子查询
components.render_derived_badges + 「分析」徽章（C.ANALYSIS = deep-purple）
```

### 2.7 REST API

```text
GET  /api/analysis-presets                 模板列表
POST /api/assets/{asset_id}/analyze        {preset_id} → {task_id, status}
POST /api/assets/batch-analyze             {asset_ids, preset_id, overwrite}
                                           → {created, task_ids, skipped}
```

### 2.8 UI

```text
详情页                         「AI 分析」卡片（模板下拉 + 描述/已有提示 +
                               生成 + 覆盖确认对话框；无模板/非音视频/无
                               JSON 转录时禁用并说明）。派生 tabs：kind=
                               analysis 的 tab 名「分析·{模板名}」（模板
                               删除后回退 preset_id），内容 _render_
                               markdown_section（剥 frontmatter、ui.markdown、
                               超长分页复用）
资产列表页                      批量操作栏 + 「批量分析」；对话框 = 模板选择
                               （切换时刷新描述与已有计数）+ 跳过已有/全部
                               重新生成
任务中心                        TYPE_LABELS + analysis（AI 分析）；失败重试
                               分支从 params_json 取 preset_id 重建任务
```

### 2.9 内置模板输出骨架

授课分析：课程概览（主题/带时间锚点大纲/受众难度）→ 逐段拆解（5-12 段：
内容要点/引入方式/讲解手法/亮点，标题带 `[起–止]` 时间）→ 可迁移教学
手法清单（表格：手法/出现时间/用法要点/迁移提示）→ 化用建议（3-5 条）。

访谈分析：节目概览（主题脉络/嘉宾与角色 1对1或1对N/话题块结构）→ 逐段
分析（4-10 段：核心观点注明说话人/关键问答/金句数据案例/分歧碰撞）→
主持技巧拆解（提问/追问转折/控场，附实例时间戳）→ 观点摘录（按主题归类
带时间戳）。

两模板共同要求：不编造（未提及要标注）、时间引用一律带时间戳、简体中文
Markdown、不输出骨架外开场白。

---

## 3. 测试步骤（UI 手动验收）

前置：知识库内有音视频资产且已用 `-f json` 生成转录；设置页开启
`[llm.analysis]` 并填好长上下文模型与 Key，测试通过。

1. **模板生成**：删除 `.knowledge/presets/` 后重新打开知识库 → 目录
   重建且出现 teaching.md / interview.md；手工改 teaching.md 的 name 后
   重开库 → 内容保持用户版本。
2. **设置页**：出现「AI 分析配置」与「分析模板」卡片；模板卡列出两个
   内置模板（名称/描述/适用 audio / video）；保存配置后 config.toml
   出现 `[llm.analysis]`。
3. **单条分析**：打开一个课程视频详情页 →「AI 分析」卡片选「授课分析」
   → 生成 → 任务中心出现「AI 分析」任务并完成 → 详情页派生 tabs 出现
   「分析·授课分析」，内容以 markdown 渲染（标题/表格/列表），含时间戳；
   列表页该资产行出现「分析」徽章。
4. **覆盖确认**：再次生成同模板分析 → 弹覆盖确认 → 确认后旧文件进
   `.knowledge/backups/`。
5. **第二模板**：同资产换「访谈分析」→ 生成 → tabs 出现第二个分析
   tab，两份分析并存。
6. **无转录/纯文本转录**：无转录音视频的卡片按钮禁用并提示；仅有
   `.transcript.txt` 的资产生成时报「不是 JSON 格式」中文错误。
7. **批量分析**：列表多选若干资产（混入文档资产与已有分析资产）→
   「批量分析」→ 选模板 →「跳过已有，分析其余」→ 通知 created/skipped
   数量；文档资产跳过原因含「不适用于 document」。
8. **任务重试**：人为制造失败（如改错 base_url）→ 任务中心该任务失败
   → 修正配置 → 点「重试」→ 创建新分析任务并成功。
9. **搜索**：全文搜索分析正文中的关键词 → 命中该资产。

---

## 4. 验收标准

```text
开库自动生成内置模板且不覆盖用户修改；改文件即改提示词生效
单条/批量分析走任务中心，失败可重试，重启后 pending/running 自动恢复
一个资产可同时持有多个模板的分析，tab 名「分析·{模板名}」
分析产物 markdown 渲染、带时间戳、覆盖前自动备份
分析内容进入全文索引（可搜索）；列表「分析」徽章正确显示
超长输入自动分窗逐窗分析再合并，不丢时间戳
总结 / 打标 / 转录 / 解析既有行为完全不变
```

---

## 5. PRD 同步清单

- §9.1 派生文件规则：新增 `episode-001.analysis.<preset_id>.md` 与
  sidecar 目录内 `analysis.<preset_id>.md` 命名及绑定说明
- §9.4 sidecar 目录：内部文件名映射补充 analysis 变长模式
- §13.8（新增小节）：AI 深度分析（多模板分析产物）功能定义
- §19.2 artifacts kind 列表：+ analysis
- §20 配置样例：+ [llm.analysis]
- §22.3 详情页 / §22.6 设置页：AI 分析卡片与模板列表卡
- §23.2 Assets API：analyze / batch-analyze / analysis-presets
- §28 里程碑：+ M18
- docs/README.md 里程碑记录 + CLAUDE.md 里程碑清单 + 项目现状同步

---

## 附录 A：冒烟验证（2026-08-24，脚本已跑通后删除）

临时库端到端（mock `llm_service.chat_completion`）：

```text
1. open_library → .knowledge/presets/ 生成 teaching/interview；覆盖用户
   修改后 ensure 不动它；解析 name/description/types/{title} 正确
2. 造 lecture01.mp3 + .transcript.json（含 speaker 缺失段与跨小时段）→
   扫描入库；build_timestamped_input 输出 [00:00] 老师: … /
   [00:05] …（无 speaker）/ [1:00:10] …，与预期逐行一致
3. start_analysis(teaching) → 任务 success；平铺 lecture01.analysis.
   teaching.md 含 frontmatter（type/preset/preset_name/model）；mock 收
   到的 system prompt {title} 已替换；artifacts 表 kind=analysis active
4. 批量 overwrite=False → 跳过「已有『授课分析』分析」；overwrite=True
   → 文档资产跳过（不适用于 document），音视频重建成功，.knowledge/
   backups/ 出现旧分析备份
5. 创建 .kb 目录后 start_analysis(interview) → 产物写入
   lecture01.mp3.kb/analysis.interview.md，平铺旧产物仍在
6. rules 反解：flat/sidecar 命中、summary.md/无 stem 形态不误判
7. 伪造 pending analysis 任务 → resume_pending_analysis_tasks 拉起执行
   success
8. rebuild_fulltext_index → chunks 中 kind='analysis' 计数 > 0
9. analyze_text 超长分窗：50 分钟输入 + max_input_chars=1000 +
   window_minutes=10 → 5 次窗口调用（含「第 1 / 5 窗」与覆盖区间）+
   1 次合并调用；短输入单次调用
```
