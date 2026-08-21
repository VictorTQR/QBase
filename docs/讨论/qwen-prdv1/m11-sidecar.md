# M11：sidecar 目录 .kb

2026-08-21 定稿。对应 PRD §9.4 预留的 sidecar 目录方案、§9.3 歧义问题的
根治方案、§31 后续阶段规划第 1 项。复用现有 artifacts 表与全部下游链路
（索引 / 向量 / 总结输入 / 详情页），识别层新增一种产物形态，写入层只动
总结与解析两个落盘点。

---

## 0. 已定决策（讨论结论，不再开放）

1. **写入策略 = 跟随现状（opt-in）**。资产旁已存在 `<完整文件名>.kb\`
   目录时，应用生成的总结 / 解析产物写入目录内；否则维持平铺。用户手动
   建目录即启用，零配置项、零 UI 入口，旧库行为完全不变。
2. **转录按「不支持指定输出路径」设计**。QVoice 是否支持 `-o` / `--output`
   未确认，转录产物维持平铺同目录；`{output}` 变量已传入 `build_command`
   （命令模板随时可配，配了就生效）；CLI 结束后的产物查找候选扩展到
   `.kb\transcript.json` / `.kb\transcript.txt`（外部放进去的也能找到）。
3. **不做归集 / 迁移工具**（YAGNI）。旧平铺产物永久识别、永久可用；想
   归集的用户手动移动文件后刷新即可。
4. **绑定 = 目录名精确绑定**。`episode-001.mp3.kb\` 去掉 `.kb` 即原始
   文件完整文件名（含扩展名），按 relative_path 精确匹配资产——同 stem
   的 mp3 / mp4 共存也天然无歧义（§9.3 的根治方案）。资产不存在 → 该
   目录内容计入孤儿，不入库；资产恢复后刷新自动重新绑定。
5. **内部命名 = 固定文件名映射 kind**：

   ```text
   transcript.json -> transcript    transcript.txt -> transcript
   summary.md      -> summary       notes.md       -> note
   parsed.md       -> parsed        meta.json      -> meta
   ```

   未列出命名与隐藏文件忽略；不递归子目录。多个转录文件并存时全部识别
   （与平铺多转录文件现状一致）。
6. **共存无特判**。同一资产平铺与 `.kb\` 内同 kind 产物并存时均识别为
   active（artifacts 表按 relative_path 唯一），索引 / 读取走 artifacts
   表，不引入优先级规则。
7. **`.kb\` 目录内容永不产生资产记录**。顺带修复现状 bug：今天
   `<name>.kb\` 不是隐藏目录（不以 `.` 开头），会被 walk 且内部
   `summary.md` / `transcript.txt` 无 stem 前缀、不命中平铺后缀规则，
   会误入 assets 表成为文档资产。
8. **范围外（明确不做）**：归集按钮、`.kb` 内多版本产物（如
   `summary.20260821.md`）、sidecar 目录内再嵌套、meta.json 的结构定义。

---

## 1. 现状事实（代码依据）

```text
rules.ARTIFACT_SUFFIXES     平铺后缀 -> kind（.transcript.txt / .summary.md …）
scanner_service             按 (relative_dir, stem.lower()) 绑定：
                            同 stem 多候选 -> 歧义；无候选 -> 孤儿（均不入库）
should_ignore_dir           忽略隐藏目录；<name>.kb 不以 . 开头 -> 目前会被
                            walk，内部文件误入资产表（见决策 7）
总结写入                    summarization_service 两处 with_suffix(".summary.md")
解析写入                    parse_service._parsed_path with_suffix(".parsed.md")
                            覆盖备份命名基座 parsed.stem —— .kb 模式下 stem
                            恒为 "parsed"/"summary"，跨资产撞名，需改为资产 stem
转录写入                    QVoice 决定，平铺；_candidate_outputs 三级候选查找
build_command               str.format(**variables)，天然支持任意变量，现只传 {input}
消费方                      索引 / 向量 / 总结输入 / 详情页全部走 artifacts 表
                            absolute_path，识别层入库后自动受益，零改动
```

---

## 2. 实施蓝图

### 2.1 `app/rules.py`（新增 sidecar 命名规则）

```python
SIDECAR_DIR_SUFFIX = ".kb"
SIDECAR_FILE_KINDS = {固定文件名 -> kind，见决策 5}

is_sidecar_dir(dir_name)        # <name>.kb 且不是裸 ".kb"
sidecar_asset_filename(dir_name)  # episode.mp3.kb -> episode.mp3
sidecar_file_kind(filename)     # 目录内文件名 -> kind；未识别返回 None
sidecar_dir_of(asset_path)      # episode.mp3 -> episode.mp3.kb 目录路径
derived_output_path(asset_path, filename)
    # m11 跟随现状写入策略：.kb 目录已存在 -> .kb/filename；
    # 否则平铺 stem.filename（summary.md -> episode-001.summary.md）
```

### 2.2 `app/services/scanner_service.py`

```text
collect_files 返回 (普通文件, sidecar 文件) 二元组：
  os.walk 时从 dirnames 摘出 .kb 目录 -> _collect_sidecar_dir 收集
  （不递归、跳过隐藏文件与未识别命名），并从 dirnames 移除不再下钻
scan_current_library：
  sidecar 文件全部进 artifact_candidates（带 sidecar 标记）
  资产写入阶段顺手建 relative_path.lower() -> asset_id 映射
  绑定阶段：sidecar 候选按 (目录父路径, 去掉.kb的文件名) 精确查映射，
  命中即 active 入库，未命中计孤儿；平铺候选逻辑不变
```

### 2.3 `app/services/summarization_service.py`

两处 `with_suffix(".summary.md")` 改 `derived_output_path(asset, "summary.md")`
（start 记录期望路径 + run 实际写入）。

### 2.4 `app/services/parse_service.py`

```text
_parsed_path 改 derived_output_path(asset, "parsed.md")
覆盖备份 / 产物留档命名基座改为资产 stem（.kb 模式下 parsed.stem 撞名）：
  {stem}.{ts}.bak.md（平铺行为不变） / {stem}.parsed.md{PRODUCT_BACKUP_SUFFIX}
```

### 2.5 `app/services/transcription_service.py`

```text
_candidate_outputs 追加 .kb/transcript.json、.kb/transcript.txt（排在平铺之后）
build_command 变量表增 "output"（默认模板不含 {output}，不生效，纯预留）
```

### 2.6 零改动确认

UI（详情页 / 徽章 / 预览）、index_service、vector_service、search_service、
API 层全部走 artifacts 表，不需要动。`read_text_for_index` 按后缀分派，
`.kb/transcript.json` 等文件名后缀与平铺一致，自动正确。

---

## 3. 测试步骤（开发人员手动执行）

```text
1. 库目录放 episode.mp3，扫描确认资产存在；手动创建 episode.mp3.kb\ 目录，
   放入 summary.md（随便写点内容）与 transcript.txt，点刷新
   → 详情页出现总结/转录徽章，派生文件 tab 显示两个产物，
     路径含 .kb；资产列表无新增资产记录
2. 对该资产生成 AI 总结 → 产物写入 episode.mp3.kb\summary.md（覆盖确认
   备份到 .knowledge/backups/，备份名含 episode 而非 summary/parsed）
3. 放入 paper.pdf，先不建 .kb 目录发起解析 → 产物仍为平铺 paper.parsed.md；
   再建 paper.pdf.kb\ 后重新解析（覆盖确认）→ 产物写入 paper.pdf.kb\parsed.md
4. 同 stem 歧义对照：同目录放 talk.mp3 + talk.mp4 + talk.mp3.kb\transcript.txt，
   刷新 → talk.mp3 显示已转录，talk.mp4 仍为未转录（平铺 talk.txt 才会歧义）
5. 全文搜索命中 .kb 内的总结/转录内容；向量索引统计 chunks 增加
6. 音视频总结输入：.kb 内有 transcript 的资产可直接生成总结
7. 删除 episode.mp3（保留 .kb 目录）→ 刷新后产物不绑定（孤儿计数）；
   恢复文件再刷新 → 重新绑定
8. 回归：无 .kb 目录的库，转录/总结/解析行为与之前完全一致
```

---

## 4. M11 验收标准

对应 PRD §29.11：

```text
手动创建 .kb 目录并放入固定命名产物，刷新后按目录名精确绑定（无歧义）
存在 .kb 目录的资产：总结/解析产物写入目录内；无目录资产维持平铺
.kb 内产物进入索引与搜索；AI 总结输入可读取 .kb 内转录/解析结果
旧平铺产物行为不变；不做归集工具
```

## 5. PRD 同步清单（实施完成时）

```text
§9.1 派生文件规则：提及 sidecar 目录形态
§9.3 歧义处理：sidecar 目录已支持（m11）
§9.4 sidecar 目录：由「预留」改为已实现描述（命名/绑定/写入策略）
§28 里程碑：增 M11；§29 增 29.11 验收；§31 移除第 1 项；§35 顺序增 M11
```

---

## 附录 A：冒烟验证（2026-08-21 已通过）

合成目录树脚本验证（无 UI，临时脚本跑完即删），覆盖点与结果：

```text
rules helper：is_sidecar_dir 大小写不敏感、裸 .kb 拒绝；文件名映射 kind 正确
derived_output_path：有 .kb 目录 → 目录内原名；无 → 平铺 stem.filename（与
                     with_suffix 行为一致）
collect_files：.kb 内容（含未识别命名 junk.bin / 隐藏文件）绝不进入普通文件
               列表，sidecar 收集恰好命中 4 个固定命名文件
全链路扫描：ep.mp3.kb 的 summary/transcript 绑定 ep.mp3；同 stem 的 ep.mp4
           不被误绑（精确文件名绑定）；sub/paper.pdf.kb/parsed.md 跨目录绑定；
           平铺 talk.txt 歧义保留（1）；orphan.mp3.kb 计孤儿不入库（1）；
           .kb 内容零资产记录（assets 恰为 6 个真实文件）
转录候选：_candidate_outputs 平铺三级在前，.kb/transcript.json|txt 殿后
```
