# M17：批量任务（批量总结 + 批量 AI 打标）

2026-08-23 定稿并实施。PRD §31 后续规划的两项之一（另一项「收藏与
稍后处理」仍留待后续）。范围 = 资产列表页多选 + 批量总结 / 批量 AI
打标两个批量操作，任务形态复用现有 tasks 系统。只做主项目已有能力
的批量版——批量 AI 总结、批量 AI 打标（复用现有 [llm.summary] /
[llm.tagging] 配置）；不做批量转录（PRD §3 明确不做）、不做批量解析。

---

## 0. 已定决策（讨论结论，不再开放）

1. **批量打标 = 自动追加写入**：LLM 建议经宽松清洗后自动保存，追加
   到已有标签之后，绝不删除已有标签；实际写入的标签记入任务
   params_json（任务详情可审计）；清洗后为空 → 任务 failed
   （"AI 未返回可用标签"）。修订 M16「AI 结果不写库」原则的适用
   范围——该原则保留于单条交互流程（详情页建议预填编辑器）；
   批量场景按 m15 讨论稿预留的「批量自动打标」语义落地为自动写。
   （讨论时推荐项，用户未逐条复核，如有异议单条流程不受影响。）
2. **批量总结 × 已有总结 = 弹窗让用户选**：点击时统计已选中已有
   总结的数量，弹窗提供「跳过已有，总结其余」（overwrite=false）/
   「全部重新生成（旧文件自动备份）」（overwrite=true）两个选项。
   备份机制沿用单条流程的 .knowledge/backups/。
3. **任务形态 = 每资产一条任务**：完全复用 tasks 表、任务中心展示、
   失败重试、同资产同类型 pending/running 去重（count_running_tasks）。
   批量编排器只负责「预检 + 建一批 pending 任务 + 拉起 worker 消费」。
   新任务类型 tagging（AI 打标）进任务中心——M16 单条建议是秒级
   同步调用不走任务系统，批量 N 次 LLM 调用属于重活，走任务系统；
   单条建议流程完全不动。
4. **并发 = 消费 [task] max_workers**（配置自 m1 起就存在、设置页
   可编辑、从未被读取，本次接通；默认 1 = 串行）。串行对打标有额外
   收益：前面资产新打的标签会进入后续资产 prompt 的已有标签列表，
   引导标签收敛、防同义标签膨胀。
5. **重启恢复 = 仿 resume_running_parse_tasks**：open_library 时把
   pending/running 的 summarization / tagging 任务重新拉起 worker
   消费（总结重新生成有备份、打标合并去重，均幂等；running 状态
   的任务线程已随旧进程消失，直接重跑）。
6. **范围外（明确不做）**：批量转录、批量解析、按筛选条件全选
   （跨页全库选中）、批量删除标签、批量取消任务、进度条组件
   （进度 = 任务中心逐条任务状态，沿用每 5 秒轮询）。

---

## 1. 现状事实（代码依据）

```text
summarization_service
  .start_summarization     单条总结：校验 + create_task(pending) +
                           起独立 daemon 线程执行；批量直接复用会
                           N 线程并发打 LLM
  .run_summarization_task  执行体按 task_id 自包含（取任务→置
                           running→LLM→备份→写文件→刷新→success/
                           failed），可直接被批量 worker 串行调用
tag_service
  .suggest_asset_tags      单条建议链路：校验→get_tagging_llm_config
                           →get_summary_input_text→list_tags→
                           llm_service.suggest_tags→宽松清洗；不写库
  .set_asset_tags          整体替换写库（M15）
task_repository
  .count_running_tasks     同资产同类型 pending/running 去重
parse_service
  .resume_running_parse_tasks
                           open_library 恢复钩子先例（library_service
                           .open_library 尾部调用）
config_service             [task] max_workers 已在 validate_config
                           校验（:400）、设置页可编辑，但执行侧
                           零消费
tasks.py 任务中心          TYPE_LABELS 按 type 显示中文；失败重试按
                           type 分发「创建新任务」；每 5 秒轮询
assets.py 资产列表         手工渲染表格行、50/页分页、筛选排序；
                           无任何多选先例
M16 决策 7                 「批量打标留待批量任务里程碑」——即本稿
```

## 2. 实施蓝图

### 2.1 `app/services/batch_runner.py`（新增）

```text
get_max_workers()               读 config [task].max_workers，默认 1，
                                异常回退 1
execute_tasks(task_ids,
              run_task)         起 daemon 线程消费任务列表：
                                max_workers<=1 逐条串行调
                                run_task(task_id)；>1 用
                                ThreadPoolExecutor(max_workers)。
                                供批量总结/批量打标/重启恢复共用
```

### 2.2 `app/repositories/artifact_repository.py`

```text
has_active_artifact(conn,
                    asset_id, kind)
                                EXISTS 查询；assets 列表徽章的同类
                                子查询抽公共函数，批量总结用它判断
                                「已有总结」
```

### 2.3 `app/services/summarization_service.py`

```text
_create_summarization_task(conn, asset_id)
                                从 start_summarization 抽出「校验 +
                                建任务」段：返回 (task_id, None) 或
                                (None, 跳过原因)（资产不存在 / 已有
                                任务在跑 / 未启用 / 输入文本为空 /
                                无转录解析等中文原因）。单条路径改调
                                它，行为不变
start_batch_summarization(
    asset_ids, overwrite=False)
                                → {"created": [task_id...], "skipped":
                                [{"asset_id","title","reason"}...]}；
                                先整体检查 [llm.summary] enabled（未
                                启用抛 ValueError，一个任务都不建）；
                                逐资产预检建任务（overwrite=False 时
                                已有 active summary 跳过，原因「已有
                                总结」）；最后 batch_runner.execute_
                                tasks 消费
resume_pending_summarization_
tasks()                         查 pending/running 的 summarization
                                任务，execute_tasks 重跑（幂等）
```

### 2.4 `app/services/tag_service.py`

```text
run_tagging_task(task_id)       执行体：取资产 → 复用建议链路
                                （get_tagging_llm_config →
                                get_summary_input_text → list_tags →
                                llm_service.suggest_tags →
                                _clean_suggestions）→ 与已有标签合并
                                （existing + 新建议去重追加，截断
                                MAX_TAGS_PER_ASSET）→ set_asset_tags
                                写库 → success 且 params_json 记
                                {"applied": [...]}；清洗后为空 →
                                failed("AI 未返回可用标签")；输入不
                                可用 → failed 带原有中文原因
start_tagging(asset_id)         单条入口（重试用）：建任务 + 消费
start_batch_tagging(asset_ids)  同批量总结编排；去重类型 tagging；
                                追加语义无「已有标签跳过」，全量跑
resume_pending_tagging_tasks()  同 2.3
（suggest_asset_tags 单条建议流程零改动）
```

### 2.5 `app/services/library_service.py`

```text
open_library                    resume_running_parse_tasks() 旁追加
                                调用 resume_pending_summarization_
                                tasks / resume_pending_tagging_tasks
```

### 2.6 `app/api/library.py`

```text
POST /api/assets/batch-summarize
                                body {asset_ids, overwrite=false} →
                                {"created", "task_ids", "skipped"}；
                                400 未开库 / 空 asset_ids / LLM 未启用
POST /api/assets/batch-tag       body {asset_ids} → 同结构；400 同上
```

### 2.7 `app/ui/pages/assets.py`

```text
勾选列                          行首 ui.checkbox + 表头「全选本页」；
                                选择集按 asset_id 跨页/跨筛选保留
批量操作栏                      列表工具行：「已选 N 项」+「批量总结」
                                「批量打标」+「清除选择」（N=0 禁用）
批量总结对话框                  io_bound 统计已选中已有总结数 M，
                                文案「已选 N 项，其中 M 项已有总结」，
                                两按钮：跳过已有（overwrite=false）/
                                全部重新生成（备份提示）；提交 →
                                io_bound(start_batch_summarization) →
                                notify「已创建 X 个总结任务，跳过 Y
                                项，进度见任务中心」
批量打标对话框                  确认文案「自动追加保存（不删除已有
                                标签）」→ io_bound(start_batch_
                                tagging) → notify 同风格
（表格 min-width 加一列宽度；遵守 page_frame / tokens / components
三约束）
```

### 2.8 `app/ui/pages/tasks.py`

```text
TYPE_LABELS                     增 "tagging": "AI 打标"
重试分发                        增 tagging 分支 → start_tagging
                                （沿用「重试=创建新任务」约定）
```

### 2.9 零改动确认

数据库 schema、tag_repository、asset_repository（除抽公共查询）、
search_service、详情页（单条总结 / M16 建议标签 / M15 手动打标）、
设置页、转录与解析链路均不动；单条 summarize/suggest-tags 端点行为
不变。

## 3. 测试步骤（开发人员手动执行）

```text
1. 未启用 [llm.summary] / [llm.tagging] 时点批量按钮 → 中文报错，
   不创建任何任务
2. 多选：跨页勾选保留、「全选本页」、筛选后勾选、「清除选择」、
   N=0 时按钮禁用
3. 批量总结-跳过路径：混选已有/未有总结的资产 → 弹窗数字正确 →
   「跳过已有」→ 仅未有总结的建任务，notify 数字正确，任务中心
   出现逐资产任务并逐个完成
4. 批量总结-覆盖路径：「全部重新生成」→ .knowledge/backups/ 出现
   旧总结备份，新总结覆盖
5. 选中含无转录音频 / 未解析文档 → 跳过并在结果中体现（不建任务
   不报错中断）
6. 批量打标：已有标签的资产打标后旧标签保留、新标签追加；任务详情
   参数区可见 applied 列表；同批后处理的资产建议出现先处理的标签
   （串行收敛）
7. 空建议 / LLM 返回异常 → 对应任务 failed，错误信息可读；任务中心
   「重试」创建新任务
8. 同资产在任务 pending/running 时再次批量 → 跳过原因「已有任务
   正在运行」
9. 重启应用重新打开库 → pending/running 的总结/打标任务自动恢复
   消费
10. [task] max_workers 调到 2+ → 批量任务并发执行
11. 回归：单条总结、M16 单条「AI 建议标签」、M15 手动打标、资产
    列表筛选/排序/分页、转录与解析任务均不受影响
```

## 4. M17 验收标准

对应 PRD §29.17（新增）：

```text
资产列表可多选（跨页保留），批量总结 / 批量打标按钮在选中数 > 0 时可用
批量总结弹窗展示已有总结统计，支持「跳过已有」与「全部重新生成（自动备份）」
批量打标自动追加写入、不删除已有标签；写入内容可在任务详情审计
批量任务逐资产进入任务中心，支持失败重试与同资产去重；重启后 pending/running 任务恢复
[task] max_workers 生效（默认 1 串行）；单条总结与 M16/M15 既有行为完全不变
```

## 5. PRD 同步清单（实施完成时）

```text
§3 / §31 注记：批量任务已由 m17 实现（批量总结 + 批量自动打标）；收藏仍留后续
§11.1 资产列表页增多选与批量操作栏描述
§23.2 增 POST /api/assets/batch-summarize、POST /api/assets/batch-tag
§28 增 M17；§29 增 29.17
§20 [task] max_workers 注记「m17 起被批量任务消费」
README / CLAUDE.md 功能描述同步
```
