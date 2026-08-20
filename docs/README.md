# 文档索引

## 权威文档

- [PRD.md](./PRD.md) - 产品需求文档 v1.1（唯一权威 spec：数据模型 / API / UI / 配置 / 里程碑 M0-M8）
- [../CLAUDE.md](../CLAUDE.md) - 开发原则与环境指南

## 里程碑实施记录

每进入一个里程碑，新增一页记录实施决策（只记 PRD 未定的细节与偏差，不重复 PRD 内容）。

- M0 项目骨架 - 已完成（2026-08-16），无偏差，见 PRD §28
  - 备注：NiceGUI `@ui.page` 注册要求包 `__init__.py` 显式导入子模块
- M1 知识库与扫描 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m1.md，已适配 M0 结构
  - 偏差/补充（m1.md 未覆盖、由实施补齐）：
    - `app/database.py`：sqlite3 连接（WAL + Row 工厂）+ assets 建表（DDL 取自 PRD §19.1）
    - `app/services/library_service.py`：open_library / close_library / get_library_status；打开时写默认 `.knowledge/config.toml`（模板取自 PRD §20）
    - `app/api/library.py`：REST 端点（open/close/status/scan/assets），替代 m1.md 的 register_library_api
    - `app/main.py`：未按 m1.md 整体替换，保留 M0 的配置/日志/健康检查，仅追加 API 路由
    - `app/state.py`、`app/rules.py`、`app/utils.py`、`app/repositories/asset_repository.py`、`app/services/scanner_service.py`、`app/ui/pages/assets.py` 按 m1.md 落地（资产页并入 page_frame 导航布局，新增类型过滤）
- M2 派生文件识别 + 资产详情页 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m2.md，已适配 M1 结构
  - 偏差/补充（m2.md 未覆盖、由实施补齐）：
    - `database.py` 保留 M1 的 WAL/get_conn，SCHEMA 扩至 PRD §19.1 全部 5 表 + artifacts 索引 + chunks_fts（FTS5，M4 搜索用）
    - `list_assets` 保留 M1 的类型过滤参数，叠加 has_transcript/has_summary/note EXISTS 徽章列
    - `assets.py` 保留 page_frame 布局与类型过滤，合并徽章列与详情链接
    - 新增 `GET /api/assets/{asset_id}` 详情端点（含 artifacts）
  - 决策记录：
    - 派生匹配键 = (relative_dir, stem.lower())；转录类只匹配音视频资产，其余 kind 匹配任意资产
    - 同 stem 多候选 -> 歧义不绑定；无候选 -> 孤儿（stats 计数，UI warning 提示）
    - 普通 {stem}.txt 在同目录存在同 stem 音视频时识别为转录，否则仍是文档资产
- M3 转录任务 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m3.md（QVoice CLI 集成），已适配 M2 结构
  - 偏差/补充（m3.md 未覆盖、由实施补齐）：
    - `app/services/config_service.py`：`transcribe_cwd` 空字符串归一为 None（否则 subprocess WinError 123）
    - `app/services/transcription_service.py`：任务 command 字段统一存 json.dumps（m3.md 的 run 阶段误存 str(list) repr）；补 loguru 日志
    - `app/ui/pages/asset_detail.py`：转录卡片/覆盖确认对话框并入 page_frame 版详情页（m3.md 版本丢了布局）
    - `app/ui/pages/tasks.py`：任务中心包 page_frame，资产列链接到详情页，替换占位页
    - 新增 API：`POST /api/assets/{id}/transcribe`、`GET /api/tasks`、`GET /api/tasks/{id}`
    - `DEFAULT_LIBRARY_CONFIG` 的 [cli] 段更新为数组格式 + transcribe_cwd + timeout（原为旧字符串格式）
  - 决策记录：
    - 验收用 mock CLI（kb-test/.knowledge/mock_transcribe.py）跑通 success/failed/超时去重三条路径；真实 QVoice 配置已写入默认模板，用户改库级 config 即可切换
    - 并发去重：同资产同类型存在 pending/running 任务时拒绝（HTTP 400）
- M4 全文搜索 + 文件名搜索 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m4.md，已适配 M3 结构
  - 偏差/补充（m4.md 未覆盖、由实施补齐）：
    - `app/ui/pages/search.py`：搜索页包 page_frame（m4.md 版本无布局，手写导航链接已去除）
    - 未按 m4.md 替换 main.py，页面经 `pages/__init__.py` 注册；/search 占位页移除
    - 新增 API：`GET /api/search?q&mode`、`POST /api/search/rebuild`
    - 采纳 m4.md §6 可选项：转录成功后自动 scan + rebuild_fulltext_index（已验证端到端）
    - `utils.read_text_for_index`：与 read_text_preview 并列的索引用读取（max_chars=500K）
  - 决策记录：
    - 全文搜索 = FTS5 优先 + LIKE 兜底（FTS5 默认分词对中文子串不可靠，个人库规模 LIKE 可接受）
    - 索引来源：active 状态的 transcript/summary/note/parsed 派生 + .md/.txt 文档资产（parse_status=not_required）
    - 重建策略为全量清空重建；大库可优化为按资产增量索引
- M5 LanceDB 向量搜索 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m5.md，已适配 M4 结构
  - 偏差/补充（m5.md 未覆盖、由实施补齐）：
    - `app/ui/pages/search.py`：搜索页包 page_frame（m5.md 版本手写导航已去除），新增「语义」模式与「重建向量索引」按钮、distance 显示
    - 新增 API：`POST /api/search/vector/rebuild`；`GET /api/search` 的 mode 放行 vector
    - `DEFAULT_LIBRARY_CONFIG` 的 [embedding] 模板补 dimension/batch_size/timeout，示例 SiliconFlow BAAI/bge-m3 (1024)；enabled 默认 false（避免误触发 API 费用）
    - 未采纳 m5.md §10 的自动重建向量索引（转录成功只自动重建全文索引，向量索引手动触发，同 m5.md 建议）
  - 决策记录：
    - 向量库位置 `<library_root>/.knowledge/vector/lancedb`，表名 chunks，全量重建（drop + create）
    - embedding 缓存 key = `chunk|query:{model}:{sha256(text)}`，存 embedding_cache 表（M2 已建），JSON 向量
    - 验收用本地 mock embeddings 服务（kb-test/.knowledge/mock_embeddings.py，字符频率向量，端口 8790）跑通：首次重建 7 片段全量嵌入 → 二次重建 7 缓存命中 0 新调用 → 「知识管理」语义命中 ep001 总结（distance 1.20 vs 其他 ≥1.79）→ enabled=false 时 HTTP 400 明确报错
- M6 AI 总结生成 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m6.md，已适配 M5 结构
  - 偏差/补充（m6.md 未覆盖、由实施补齐）：
    - `app/ui/pages/asset_detail.py`：AI 总结卡片并入 page_frame 版详情页（m6.md 版本丢了布局），按钮禁用态 + 覆盖确认对话框
    - 新增 API：`POST /api/assets/{id}/summarize`（m6.md 未提供，与 transcribe 端点对齐）
    - `backup_existing_summary` 简化：直接用 state.library_root 定位 `.knowledge/backups/`（m6.md 向上遍历目录的写法不必要）
    - `DEFAULT_LIBRARY_CONFIG` 的 [llm.summary] 模板补 temperature/max_tokens/timeout/max_input_chars/chunk_chars（SiliconFlow Qwen2.5-72B 示例）；enabled 默认 false（与 [embedding] 一致，防误触发费用）
  - 决策记录：
    - 前置校验在 start_summarization 同步完成（无转录/不支持类型/空文本 → HTTP 400，不产生任务）；LLM 调用失败则在任务内标记 failed，错误信息任务中心可查
    - 总结成功后自动 scan + rebuild_fulltext_index（失败仅记 warning，不影响任务 success）
    - 验收用本地 mock LLM（kb-test/.knowledge/mock_llm.py，端口 8791，内容含「触发失败」时返回 500）：短文直出 / 长文分段合并（601 字原文 → 合并请求 1091 字符）/ 覆盖备份（.knowledge/backups/）/ 自动刷新索引（新总结立即可搜）全部通过
- M7 统一导航 + 设置页 + 任务中心增强 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m7.md，已适配现有结构
  - 偏差/补充（m7.md 未覆盖、由实施补齐）：
    - m7.md §1 的 page_header/require_library 未采纳——统一导航自 M0 起已由 page_frame 提供（含设置入口），全部页面沿用
    - m7.md §4 资产列表页未替换——类型过滤 M1 已实现（DB 层 asset_type 参数，非页面端过滤）
    - `app/ui/pages/settings.py`：新建设置页（当前配置 TOML 总览 + CLI/Embedding/LLM 配置卡 + 索引管理），替换 placeholders.py 占位页；placeholders.py 删除
    - `_format_config`：嵌套 section 输出 `[llm.summary]` 风格标题；明文 api_key 显示为 ***（api_key_env 不打码）
    - 任务中心增强：详情对话框（类型/时间/输出路径/命令/参数/错误）、失败任务「重试」按钮（转录/总结分别调 start_transcription / start_summarization 创建新任务）
  - 决策记录：
    - 重试 = 创建新任务而非复用旧记录（任务表保留完整历史）；同资产存在 pending/running 任务时仍受并发去重约束（400）
    - m7.md §10 后续规划（M8 watch/M9 文档解析/M10 笔记编辑等）仅作参考，下一里程碑以 PRD 为准
- M7 补完（m7-config-ui）：配置 UI 化 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m7-config-ui.md（qwen 误标为 M8，已纠正为 M7 配置 UI 化补完，与 PRD v1.1 §20.2/§22.6/§23.5 对齐）
  - 偏差/补充（m7-config-ui.md 未覆盖、由实施补齐）：
    - 保留 M5/M6 既有 `get_embedding_config`/`get_summary_llm_config` 不被破坏；`config_service` 新增 `save_config`/`validate_config`/`get_key_status`/`has_plain_api_key`/`test_connection` 等
    - 新增 `app/api/settings.py`：`GET/PUT /api/settings` + `POST /api/settings/test-connection`，main.py 用 `include_router` 注册（沿用 M0 入口，不替换 main.py）
    - `app/ui/pages/settings.py`：重写保留 page_frame，表单编辑 LLM/Embedding/Index/Task/Library 高频项，CLI/App 只读展示 + 「打开 config.toml」按钮；明文 api_key 警告、密钥来源状态灯、测试 API 按钮、保存写回 + dimension/model 变更告警、重建索引；新增「编辑 secrets.toml」按钮
    - 明文 Key 处理：`GET /api/settings` 返回的 config 中 api_key 一律打码为 `***`；`has_plain_api_key` 单独检测用于警告；UI 绝不提供明文 Key 输入框
    - 依赖新增 `tomli-w`（TOML 写回）
- M8 体验优化 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m8.md（与 qwen 基于 m8-context.md 讨论产出）
  - 落地内容：
    - `app/ui/layout.py`：保留 `page_frame`（新增 `active_nav` 高亮参数），新增 `page_header`/`breadcrumb`/`require_library`
    - `app/utils.py`：新增 `notify_error`（loguru 记录 + 中文友好提示）、`highlight_snippet`（HTML 转义 + `<mark>` 高亮）、`read_text_full`/`read_text_segment`
    - `app/repositories/asset_repository.py`：`list_assets` 扩展排序/分页（白名单防注入）+ `has_parsed`/`has_meta` 徽章列；`asset_detail.py` 改用 `get_asset_by_id`
    - `app/services/search_service.py`：返回 `highlight_words` + `derived_badges`；FTS5 `no such table` 改为引导「前往设置重建全文索引」
    - 页面重写/增强：`search.py`（高亮 + 派生徽章 + 保留重建索引按钮）、`assets.py`（排序 + 分页 + 统一徽章）、`asset_detail.py`（面包屑 + 大文本展开/分段翻页 + 统一徽章，保留转录/总结卡片防回归）
    - `home.py`：打开知识库增加路径校验（存在/可写/防 .knowledge 嵌套）；`MILESTONES` 中 M8 标记完成
    - `settings.py`/`tasks.py`：错误提示统一替换为 `notify_error`
  - 安全：高亮渲染经 `html.escape` 防 XSS；徽章来源统一为 artifacts 表 `status='active'` 派生计算
  - 偏差/补充（m8.md 未覆盖、由实施补齐）：
    - 保留 M3/M6 转录/总结卡片（m8.md §7 草稿遗漏，避免功能回归）
    - 搜索页保留「重建全文/向量索引」按钮（m8.md §5 草稿遗漏）
    - 首页/设置/任务页沿用 `page_frame(active_nav=...)` 而非切换 `page_header`，保证导航高亮一致且改动最小
  - 决策记录：
    - 配置唯一真相来源 = `.knowledge/config.toml`；保存走「加载原配置 → deep merge patch → 清理 None → 校验 → 写回」，未编辑字段与未来新增字段均保留（已验收 `future_test_field` 保留）
    - 环境变量安全：测试连通性时 `_get_api_key` 只读 `api_key_env` 对应环境变量，不读取/展示明文 Key
    - 验收（mock，零 API 费用）：GET 返回打码配置 + 明文警告 + 空 key_status；PUT 改 model 写回成功且未知字段保留；test-connection embedding/llm 经 `api_key_env` override 命中 mock 返回 200；缺失环境变量明确报错；校验失败（dimension=0）返回 HTTP 400 中文错误；dimension/model 变更告警为前端逻辑（已代码确认）
- M8 后补丁：transcribe_cwd 相对路径 + 子进程 UTF-8 输出（2026-08-20）
  - `app/services/config_service.py`：新增 `_resolve_cli_cwd`，`transcribe_cwd` 支持绝对路径 / `~` 展开（用户主目录）/ 相对路径（相对 QBase 应用根目录）；目录不存在时抛 `ValueError`，经既有 `ValueError → HTTP 400` 转换，点转录即时提示，无需到任务中心翻日志
  - `app/services/library_service.py`：`DEFAULT_LIBRARY_CONFIG` 的 `transcribe_cwd` 默认值由硬编码绝对路径改为 `"../QVoice"`（同级仓库相对路径）。仅影响新开的库，已有库的 config.toml 需手动改
  - `app/services/cli_runner.py`：子进程注入 `PYTHONUTF8=1`。修复中文 Windows 下管道输出回退 GBK 导致的 `UnicodeEncodeError`（QVoice 用 rich 打印含 `✗` 的失败信息即崩，退出码 1 且真实错误被掩盖），并与父进程 `encoding="utf-8"` 解码对齐，中文输出不再乱码；非 Python CLI 忽略该变量，无副作用
  - 决策记录：
    - 相对路径基准选 QBase 应用根（`Path(__file__).parents[2]`）而非知识库目录/进程 CWD——QVoice 与 QBase 为同级仓库，`../QVoice` 最贴合实际布局，且不受应用启动目录影响
    - `{input}` 保持绝对路径传入（子进程 cwd 会切到 CLI 项目目录，相对输入会指错位置）
- M8 后补丁：支持 QVoice JSON 转录 `.transcript.json`（2026-08-20）
  - `app/rules.py`：`.transcript.json` 由 `transcript_meta`（只识别不索引）升级为 `transcript`，自动获得索引资格/转录徽章/总结前置条件；新增 `TRANSCRIPT_JSON_SUFFIX` 常量。`transcript_meta` kind 不再由扫描产生，scanner 绑定集合与 UI 标签保留以兼容存量库未重扫的旧行
  - `app/utils.py`：新增 `extract_transcript_json_text`（优先顶层 `text`，为空回退 `segments[].text` 按行拼接；解析失败抛 `ValueError`）；`read_text_for_index` / `read_text_preview` / `read_text_full` 按后缀分派，索引 / 总结 / 详情页预览三个消费方零改动
  - `app/services/transcription_service.py`：修复输出检测 bug——原先硬编码期望 `{stem}.txt`，而 QVoice 实际写 `{stem}.transcript.txt` / `.transcript.json`，CLI 成功后任务误报"没有找到输出文件"。改为按 `.transcript.json → .transcript.txt → .txt` 候选优先级查找，`output_path` 记录实际产物
  - `app/services/library_service.py`：`DEFAULT_LIBRARY_CONFIG` 的 `transcribe_command` 加 `-f json`（产物 `<stem>.transcript.json`，含时间戳/说话人，为后续字幕跳转预留）。仅影响新开的库，已有库手动在 config.toml 加 `-f json`
  - `app/ui/pages/asset_detail.py`：`is_text_artifact` 后缀判断放行 `.transcript.json`，详情页预览/展开全文/分段翻页显示提取后的纯文本
  - 决策记录：
    - 文本提取收在 utils 读取层而非各消费方，索引/总结/向量（chunks 表下游）全部自动受益
    - JSON 转录只提取纯文本入索引，segments 时间轴保留在原文件中不做字幕跳转（维持 PRD 第一阶段边界）
- M8 后补丁：UI 设计 token 与统一布局框架（2026-08-20）
  - 新增 `app/ui/tokens.py`：设计 token 单一来源——`C`（语义颜色，Quasar 调色板名，供 `color=` 参数）与 `CLS`（Tailwind 类串，供 `.classes()`），消除两类样式写法在各页面散落混用
  - 新增 `app/ui/components.py`：`render_derived_badges` 共享组件，统一 search / assets / asset_detail 三处重复的派生文件徽章渲染（转录/总结/笔记/已解析/元数据/待解析），颜色引用 `tokens.C`
  - `app/ui/layout.py`：移除 `page_header`，全部页面（含搜索/资产列表/资产详情三页迁移）统一走 `page_frame`（顶栏 + 标题行 + 居中内容容器 + 页脚）；标题行新增当前知识库路径徽章；样式全部引用 tokens
  - 灰度对比度统一：次要文字 `text-gray-400/500` 全部改为 `text-gray-600`（白底约 5.3:1，满足 WCAG AA）；主操作按钮（打开知识库/扫描/重建索引等）统一 `color="primary"` 主色
  - 顺带行为变化：资产列表页改异步加载 + spinner、支持横向滚动；资产详情页派生文件区改为多 tab 展示
  - 决策记录：
    - 徽章/按钮颜色只用 Quasar 调色板名（`color=` 参数），文字/布局类只用 Tailwind 类串（`.classes()`），两类入口分别收口到 `C` / `CLS`，禁止页面内再写裸色值
    - `page_header` 与 `page_frame` 双轨并存时两套页面骨架易漂移（M8 期间新增页面各选其一），收敛为单一 `page_frame` 后删除 `page_header`

## 项目文档

- [项目梳理报告.md](./项目梳理报告.md) - 2026-08-16 项目全景梳理（历史演进 / 技术转向 / 架构决策）

## 修复记录

上线后 bug 修复的根因分析与经验沉淀，按日期命名（`YYYY-MM-DD-slug.md`）。

- [2026-08-20 任务中心详情对话框自动关闭](./fixes/2026-08-20-task-detail-dialog-auto-close.md) - 事件处理器内创建的 dialog 挂进列表容器，被 5 秒定时刷新的 `container.clear()` 销毁
- [2026-08-20 向量状态卡片永远显示不一致](./fixes/2026-08-20-vector-stats-always-inconsistent.md) - 统计按不存在的 `kind='vector'` 过滤 chunks，覆盖度恒 0、重建后仍提示不一致

## 原始讨论存档（只读，不更新）

- [讨论/](./讨论/) - 与各 AI 模型的设计讨论原始记录，PRD 的推导过程
