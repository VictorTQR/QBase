# 文档索引

## 权威文档

- [PRD.md](./PRD.md) - 产品需求文档 v1.0（唯一权威 spec：数据模型 / API / UI / 配置 / 里程碑 M0-M8）
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

## 项目文档

- [项目梳理报告.md](./项目梳理报告.md) - 2026-08-16 项目全景梳理（历史演进 / 技术转向 / 架构决策）

## 原始讨论存档（只读，不更新）

- [讨论/](./讨论/) - 与各 AI 模型的设计讨论原始记录，PRD 的推导过程
