# QBase 开发原则与环境指南

本文档定义项目的核心开发原则、规范和运行方式。

## 代码质量原则

### 奥卡姆剃刀

简单的解决方案通常是最好的。在面对多个可行方案时，优先选择最简单、最直接的那个。

### KISS 原则

Keep It Simple, Stupid。写最清晰、最直接、最容易理解的代码，而不是炫技。

### YAGNI 原则

You Ain't Gonna Need It（你以后用不着它的）。不要在当前版本中写那些"以后可能有用"的功能。这增加了不必要的实体（代码），增加了维护成本。

## 语言偏好

- 使用中文编写文档
- 注释使用中文
- commit 消息使用中文

## 项目依赖管理

- 项目使用 uv 管理 Python 虚拟环境，Python 3.12+，venv 位于仓库根 `.venv/`
- 依赖声明在根目录 `pyproject.toml`，修改后执行 `uv lock && uv sync`

## 运行与开发

```bash
# 启动（浏览器访问 http://127.0.0.1:8765）
.venv/Scripts/python.exe -m app.main

# 环境变量覆盖配置（可选）
QBASE_HOST / QBASE_PORT / QBASE_LOG_LEVEL / QBASE_OPEN_BROWSER
```

## 目录结构

```text
app/
├── main.py          # 入口：create_app + uvicorn 启动
├── config.py        # 应用级配置（config.toml + 环境变量）
├── logging_conf.py  # loguru 日志
├── state.py         # 运行时状态（当前知识库）
├── database.py      # SQLite 连接与建表
├── rules.py         # 文件类型/忽略规则
├── utils.py         # 大小/时间格式化、打开文件/目录
├── api/             # REST 路由
├── repositories/    # 数据访问层
├── services/        # 业务层（library/scanner/parse + parsers/ 解析器注册表）
└── ui/              # NiceGUI 页面（layout.py 统一 page_frame 框架 + tokens.py 设计 token + components.py 共享徽章 + pages/ 各页面）
config.toml          # 应用级默认配置
docs/PRD.md          # 唯一权威 spec
```

## UI 约定

- 布局统一走 `app/ui/layout.py` 的 `page_frame`（顶栏 + 标题行 + 内容容器 + 页脚），不另写页面骨架
- 样式统一引用 `app/ui/tokens.py`：颜色用 `C`（Quasar 调色板名，`color=` 参数），类串用 `CLS`（Tailwind）；不在页面内写裸色值或散落类串
- 派生文件徽章统一用 `app/ui/components.py` 的 `render_derived_badges`，不重复实现

## 测试和质量保证

- 你只需要给出测试步骤，而不自动进行测试，测试由开发人员手动进行
- 安装依赖时，你只需要给出命令，而不自动执行

## 当前进度

- [x] M0 项目骨架（2026-08-16 完成）
- [x] M1 知识库与扫描（2026-08-16 完成）
- [x] M2 派生文件识别 + 资产详情页（2026-08-16 完成）
- [x] M3 转录任务（2026-08-16 完成，QVoice CLI 集成）
- [x] M4 全文搜索（2026-08-16 完成，FTS5 + LIKE 兜底 + 文件名搜索 + 转录后自动重建索引）
- [x] M5 LanceDB 向量搜索（2026-08-16 完成，OpenAI 兼容 Embedding API + 语义搜索 + embedding 缓存）
- [x] M6 AI 总结（2026-08-16 完成，OpenAI 兼容 LLM + 长文分段摘要合并 + 覆盖备份 + 自动刷新索引）
- [x] M7 设置页 + 任务中心增强（2026-08-16 完成，配置总览/索引管理/任务详情/失败重试）
- [x] M7 补完：配置 UI 化（2026-08-16 完成，表单写回 config.toml / 环境变量检测 / 连通性测试 / 明文 Key 打码 / dimension 变更告警）
- [x] M8 体验优化（2026-08-16 完成，状态徽章/搜索高亮/大文本折叠/错误提示/排序分页/统一导航 + 最近打开/向量状态卡片）
- [x] M9 文档解析接入 MinerU（2026-08-20 代码落地，验收步骤见 docs/讨论/qwen-prd/m9-parse.md §8）：解析器 provider 抽象（parsers/）+ 批量上传 batch-of-1 + 重启恢复轮询 + parsed.md 进索引 + PDF 总结输入切换；2026-08-23 后补：pptx/ppt/xlsx/xls 补入扫描扩展名（PRD §15.2 既有宣称，扫描层缺口），html/htm 改无需解析
- [x] M10 EPUB 内容索引（2026-08-21 代码落地，脚本验证已通过，UI 验收步骤见 docs/讨论/qwen-prd/m10-epub.md §3）：内置本地 EpubParser（标准库 only）+ to_markdown 接口扩展 + 按扩展名路由（.epub 免 token）+ parsed.md 全链路复用
- [x] M11 sidecar 目录 .kb（2026-08-21 代码落地，验收步骤见 docs/讨论/qwen-prd/m11-sidecar.md §3）：<原始文件名>.kb/ 目录识别（目录名精确绑定，无歧义）+ 总结/解析跟随现状写入（有目录才归集）+ 转录平铺不变（{output} 变量预留）；后补：详情页「创建 .kb 派生目录」按钮（service + REST + UI，只建目录不移动文件）
- [x] M12 transcript JSON segments（2026-08-21 代码落地，冒烟验证见讨论稿 m12-segments.md 附录 A，UI 验收步骤见 §3）：详情页 json 转录分段视图（时间戳/说话人/100 段分页）+ 判定统一 is_transcript_json_name（修复 m11 遗留：sidecar transcript.json 此前不命中后缀判定，索引/总结输入读入原始 JSON）
- [x] M13 音频/视频播放器与字幕级跳转（2026-08-21 代码落地，UI 验收步骤见讨论稿 m13-audio-seek.md §3）：详情页「播放」卡片（原生 ui.audio/ui.video，NiceGUI 自动托管本地文件 Range 流式）+ json 转录分段时间戳点击跳转（seek + play）；源文件缺失/无播放器降级纯文本；不做反向同步，API/服务层零改动
- [x] M14 混合搜索排序（2026-08-21 代码落地，RRF 融合逻辑自测通过，UI 验收步骤见讨论稿 m14-hybrid-search.md §3）：搜索服务 search_hybrid（全文+向量两路 RRF，k=60，chunk 级去重，双命中合并标注来源）+ 搜索页「综合搜索」主按钮（回车触发）+ REST mode=hybrid（响应附 degraded_reason）；单路不可用降级为另一路并提示，不报错
- [x] M15 标签系统（2026-08-21 代码落地，验收步骤见讨论稿 m15-tags.md §3）：tags/asset_tags 两表（仅 SQLite，uuid5 稳定标签 ID）+ 详情页手动打标（PUT 整体替换、零引用自动清理）+ 列表标签列与多选筛选（OR）+ 四种搜索模式标签过滤（向量路 top-K 回表后过滤）；纯手动、扁平、无管理页
- [x] M16 AI 建议标签（2026-08-21 代码落地，验收步骤见讨论稿 m16-ai-tags.md §3）：独立 [llm.tagging] 配置（设置页精简卡片 + llm_tagging 连通测试）+ 详情页「AI 建议标签」按钮（同步调用，建议预填编辑器、宽松清洗，不写库）；修订 m15 决策——AI 只建议人确认；批量打标由 M17 实现
- [x] M17 批量任务（2026-08-23 代码落地，冒烟已通过，UI 验收步骤见讨论稿 m17-batch-tasks.md §3）：资产列表多选（跨页保留）+ 批量操作栏 + 批量总结（弹窗选跳过已有/全部重新生成，旧文件自动备份）+ 批量 AI 打标（建议清洗后自动追加写库不删已有，applied 记入任务参数可审计）；每资产一条任务复用任务系统（新任务类型 tagging），[task].max_workers 首次被消费（默认 1 串行，串行引导标签收敛），open_library 重启恢复未完结总结/打标任务；单条总结与 M16/M15 既有行为不变
- [x] M18 深度分析（2026-08-24 代码落地，冒烟已通过，UI 验收步骤见讨论稿 m18-analysis.md §3）：多模板分析产物（一个资产 × 一个模板 = 一份 analysis.<preset_id>.md，区别于快速浏览的总结）+ 模板文件化 .knowledge/presets/*.md（frontmatter + 提示词正文，内置授课分析/访谈分析，已存在不覆盖）+ 带时间戳输入（transcript.json segments → [MM:SS] 说话人: 文本；超长按时间窗切块逐窗分析再合并）+ 独立 [llm.analysis] 配置（长上下文预算）+ 任务复用 M17 全套（单条/批量/恢复/重试，新任务类型 analysis）；详情页 markdown 渲染分析产物（全项目首个 markdown 渲染点）+「分析」徽章 + 分析进全文索引；总结/打标行为不变
- [x] M19 资产列表文件夹层级浏览（2026-08-24 代码落地，浏览器冒烟已通过）：文件管理器式导航（面包屑祖先可点返回 + 子文件夹行递归计数/打开目录 + 当前层直接文件表格）+「按文件夹 / 平铺」切换（默认按文件夹，切换记住所在文件夹）+ 文件名关键词改全库搜索（忽略当前文件夹，结果平铺带完整路径列，清空回到原文件夹）+ 类型/标签筛选跟随浏览/搜索范围（文件夹计数同步变化）；数据层 relative_path 前缀 + 直接文件判定（escape_like 转义特殊字符），list_child_folders 单条 GROUP BY 递归计数，不新增表列；分页仅作用文件行，多选/批量/排序不变，扫描后回根目录
- [x] M20 LLM 异步对话补全（2026-09-03 代码落地，MockTransport 全分支自检通过）：chat_completion 按 [llm.*] mode 分支（sync 默认行为不变 / async 智谱提交+轮询：POST {base_url}/async/chat/completions → 轮询 GET /async-result/{id}，端点从 base_url 推导不硬编码域名）+ 共享 payload/结果校验抽取（_build_payload/_extract_content）+ thinking 显式开关（enabled/disabled 才附带 {"type":...}，未配置完全不传）+ 异步特有 finish_reason 中文报错（sensitive/network_error/model_context_window_exceeded）+ 提交 404/405 提示改回 sync（不静默降级，兼容 DeepSeek/硅基流动等无异步接口的提供商）+ 轮询容忍瞬时异常至 max_wait_seconds 截止（默认 1800，间隔默认 5；401/403 早失败）；总结/打标/分析三功能独立开关，设置页三卡片加「调用模式」「thinking」下拉；异步 max_tokens 上限 128K 治理思考型模型推理 token 截断；重启后任务整体重跑不续轮（与 sync 一致）；不引入 provider 抽象层（差异仅一对端点+一个参数）
- [x] M21 LLM Batch 批处理模式（2026-09-03 代码落地，mock 全链路自检通过：提交→进度→completed 回填→success / expired 无输出→failed / 构建失败不影响整批 / 重启续查不重复提交）：[llm.*] mode 增加第三取值 batch（智谱 / 硅基流动五折、不受在线限流约束、预计 24h 内完成），OpenAI 风格 files+batches 三段式共用一套实现（新文件 llm_batch.py 纯客户端：endpoint 从 base_url 末段推导 /v4、/v1/chat/completions，JSONL 构建/上传/建批/轮询/下载，单文件 ≤4000 行自动拆分）；工作单元变化——一次入口 = N 条资产任务（pending）+ 1 条 type="batch" 任务（batch_id / custom_id 映射 / 进度入 params_json，同一事务登记 batch_task_id），custom_id={task_id}_{序号}，轮询 daemon 线程（间隔 batch_poll_interval_seconds 默认 60）下载输出/错误文件后逐任务回填（expired/cancelled/failed 先回收已完成请求再判失败；401/403 与 404 整批早失败）；长文 merge 在下载后本地 sync 执行（merge 输入远小于原文，免去第二轮批任务状态机）；重启恢复绝不重新提交（避免双倍计费，resume_batch_jobs 只续查，三个 resume_pending 跳过 batch 托管任务）；提交在调用线程同步完成避免「已建任务未提交」竞态；新增配置 completion_window（默认 24h，留空不传，智谱已废弃）+ batch_poll_interval_seconds；llm_service 抽叶子请求构建（build_summary/analysis_leaf_messages、build_tagging_messages）与 merge（merge_summary_summaries、merge_analysis_partials），sync 路径行为不变；落盘抽取 write_summary/analysis_artifact + refresh_*_indexes（批量回填统一刷一次索引）；设置页三卡片 mode 下拉加「Batch 批处理（五折）」并暴露 batch 字段，任务中心 type="batch" 徽章与进度文案（completed/total+厂商状态）、不支持重试，批量入口 notify 注明五折与 24h 预期

里程碑详细目标见 [docs/PRD.md](./docs/PRD.md) §28。

## 相关文档

- [docs/PRD.md](./docs/PRD.md) - 权威 spec
- [docs/README.md](./docs/README.md) - 文档索引与里程碑记录
