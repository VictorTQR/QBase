# QBase M8 体验优化 — 给讨论用的上下文文档

> 用途：把 QBase 项目的现状、架构、已落地约定，以及 M8 各项任务各自对应的现有代码与行为，浓缩成一份**自包含**文档。
> 读者不需要访问仓库代码即可基于本文讨论 M8 的实现方案。
> 最后同步于 2026-08-16，代码状态对应提交 `497eac6`（M0-M7 全部完成）。
> 2026-08-16 更新：新增 2 项补充任务（资产列表排序+分页、导航栏当前页高亮+面包屑），见 §6.2 / §7.6 / §7.7。

---

## 1. 项目一句话定位

QBase 是一个**本地优先（local-first）的个人知识管理中心**：用户选择一个本地目录作为「知识库」，应用在该目录下创建 `.knowledge/` 子目录，自动扫描其中的音频 / 视频 / 文档，识别其「派生文件」（转录稿、AI 总结、笔记等），并提供文件名搜索 + 全文搜索 + 向量语义搜索 + AI 总结能力。密钥与配置走本地文件，不上云、不污染系统环境。

核心设计哲学：**文件系统是唯一数据源，数据库（SQLite / LanceDB）只是可重建的索引缓存** —— 删除 `.knowledge/` 后重新扫描即可恢复 Asset/Artifact 关系。

---

## 2. 技术栈与运行方式

- 语言/框架：**Python + NiceGUI（前端，声明式 UI，运行在浏览器）+ FastAPI（后端 API）+ uvicorn + loguru**
- 包管理：**uv**；虚拟环境在仓库内 `.venv/`
- 监听地址：`127.0.0.1:8765`（应用级 `config.toml` 可改 host/port）
- 启动入口：`python -m app.main`（根目录另有 `start.bat` 一键启动）
- 前端约定：所有页面用 `@ui.page("/xxx")` 装饰，且必须在 `app/ui/pages/__init__.py` 显式 import 才能注册；页面统一用 `page_frame(title)` 包裹生成侧边导航 + 标题。
- 异步：耗时 IO 一律 `await run.io_bound(...)` 包成后台任务，避免阻塞 NiceGUI 事件循环；异常统一 `ui.notify(str(exc), type="negative")` 兜底。

---

## 3. 数据层

### 3.1 SQLite（库级，位于 `<library_root>/.knowledge/db.sqlite`）
5 张表：

- `assets`：原始资产（音频/视频/文档）。关键列：`id, title, type(audio|video|document), relative_path(UNIQUE), absolute_path, size, mtime, parse_status, file_hash, duration_seconds`
- `artifacts`：派生文件（转录/总结/笔记/解析结果/元数据）。关键列：`id, asset_id, kind, relative_path(UNIQUE), absolute_path, status, generator, model`
- `tasks`：转录/总结等异步任务。关键列：`id, asset_id, type, status, command, error, pid, started_at, finished_at`
- `chunks`：索引片段（全文/向量共用）。关键列：`id, asset_id, artifact_id, kind, relative_path, chunk_index, content, content_hash`
- `embedding_cache`：向量缓存，避免重复 embedding。关键列：`content_hash(PK), model, vector(BLOB), dimension`

另有 FTS5 虚拟表 `chunks_fts`（基于 `chunks` 的 `content` 列），用于全文搜索。

> 注意：`assets` 表里**没有** `has_transcript / has_summary / has_note` 列 —— 资产列表页的派生徽章是在 `list_assets()` 查询里用 JOIN 聚合出来的（见 §7.1）。

### 3.2 LanceDB（库级，位于 `<library_root>/.knowledge/vector/lancedb`）
向量语义搜索用 LanceDB 存储 embedding，命中后回查 `assets` 拿标题。

---

## 4. 文件即数据源 / `.knowledge` 目录结构

```text
<知识库目录>/
├── podcasts/  videos/  documents/   ← 用户原始文件
└── .knowledge/
    ├── config.toml        ← 库级配置（普通配置，可分享/编辑）
    ├── secrets.toml       ← 本地密钥（[keys] 段，不提交 Git）
    ├── db.sqlite          ← SQLite 索引（可重建）
    ├── vector/            ← LanceDB
    ├── cache/  backups/  logs/  tasks/
```

- `config.toml` 段位：`[cli] / [llm.summary] / [embedding] / [index] / [library] / [task]`
- **安全红线（PRD §3）**：应用内绝不明文存储/输入 API Key。密钥来源优先级：**进程环境变量 → `secrets.toml` → `config.toml` 明文 `api_key`（仅兼容+警告）**。`config.toml` 里只写 `api_key_env = "密钥名"`，由 `config_service.get_api_key()` 解析真实密钥。
- 派生文件命名约定（`app/rules.py` 的 `ARTIFACT_SUFFIXES`，顺序重要，长后缀优先）：
  - `.transcript.txt` → transcript
  - `.transcript.json` → transcript_meta
  - `.summary.md` → summary
  - `.notes.md` → note
  - `.parsed.md` → parsed
  - `.meta.json` → meta

---

## 5. 已完成里程碑（M0–M7）

| 里程碑 | 内容 | 关键文件 |
|---|---|---|
| M0 | 项目骨架 | `app/main.py`、`app/config.py`、`app/logging_conf.py` |
| M1 | 知识库与扫描 | `library_service.py`、`scanner_service.py`、`app/state.py` |
| M2 | 派生文件识别 | `app/rules.py`、`artifact_repository.py` |
| M3 | 转录任务 | `transcription_service.py`、`cli_runner.py`、任务中心 `tasks.py` |
| M4 | 全文搜索 | `search_service.py`、`index_service.py`、FTS5 |
| M5 | 向量搜索 | `vector_service.py`、`lancedb` |
| M6 | AI 总结 | `summarization_service.py`、`llm_service.py` |
| M7 | 设置与任务中心 + 配置 UI 化 + secrets.toml | `config_service.py`、`api/settings.py`、`ui/pages/settings.py` |

首页 `MILESTONES` 常量（`app/ui/pages/home.py`）已标记 M0–M7 为 `True`、M8 为 `False`。

---

## 6. M8 目标（PRD §28 原文 + 补充项）

### 6.1 PRD 原有 5 项

```text
M8：体验优化
目标：
- 状态徽章
- 搜索高亮
- 大文本分页/折叠
- 错误提示优化
- Windows 路径兼容性优化
```

### 6.2 补充项（2026-08-16 新增，共 3 项）

基于代码现状走查，补充 3 项高性价比体验优化（改动小、体感提升大）：

```text
6. 搜索结果关键词高亮（补充：已在第 2 项覆盖，此处强调质量要求）
7. 资产列表排序 + 分页（补充：新增）
8. 导航栏当前页高亮 + 面包屑（补充：新增）
```

> 说明：第 6 项「搜索结果关键词高亮」与 §6.1 第 2 项「搜索高亮」是同一件事，合并到 7.2 讨论，不重复计数。
> **实际新增为 2 项：资产列表排序+分页、导航栏当前页高亮+面包屑。**
> 加上 PRD 原有 5 项，M8 共 **7 个子任务**。

下面 §7 把每一项对应到现有代码现状，供讨论落地设计。

---

## 7. 五项任务：现有代码现状与改进点

### 7.1 状态徽章（status badges）

**当前已有雏形，但不统一、信息不完整：**

- 资产列表页 `app/ui/pages/assets.py`（第 76–108 行）已根据 `asset["has_transcript"] / has_summary / has_note` 渲染绿/蓝/紫徽章（转录/总结/笔记）。但：
  - 缺「已解析（parsed）」「转录元数据」等状态展示；
  - `parse_status`（音频/视频为 `not_required`，其他文档 `pending`/`unknown`）没有在列表里可视化；
  - 徽章只出现在列表页，**首页、搜索结果页没有统一的资产状态概览**。
- 资产详情页 `app/ui/pages/asset_detail.py`（第 75–89 行）已有一组徽章：类型 + 转录(绿)/总结(蓝)/笔记(紫)/已解析(teal)。
- 搜索结果页 `app/ui/pages/search.py`（第 80–86 行）只显示 `kind` 和 `asset_type` 徽章（grey / blue-grey），**没有派生完成度**。

**讨论方向：**
- 是否需要一套统一的「资产健康度/完成度」模型（如：已转录？已总结？有笔记？可搜索？），在列表/详情/搜索三处复用？
- 是否引入「待处理」语义（如 `parse_status=pending` 的文档提示「待解析」，无 `summary` 的音视频提示「可总结」）？
- `has_*` 字段目前由 `asset_repository.list_assets` 的 SQL 聚合产生，详情页是查 `artifacts` 后用 Python 聚合 `kinds` 集合 —— 两处逻辑不一致，是否统一到仓储层？

### 7.2 搜索高亮（search highlighting）

**当前完全无高亮：**
- `search_service.make_snippet(content, query, radius=80)`（`app/services/search_service.py` 第 26–44 行）只生成「前后截取 + `...`」的纯文本片段，**命中词没有标记**。
- 前端 `app/ui/pages/search.py` 第 97–99 行：`ui.label(result["snippet"]).classes("text-sm mt-2 whitespace-pre-wrap")` —— 直接渲染纯文本，**没有高亮元素**。
- 文件名搜索（`search_filename`）snippet 直接用 `relative_path`，也无高亮。
- 向量搜索（语义）的「命中词」概念较弱（是语义相似，不是子串），高亮语义需讨论（是否高亮最相关片段？）。

**讨论方向：**
- 高亮实现方式：前端把 `snippet` 里的命中词用 `<mark>` 包裹（NiceGUI 支持 `ui.html` 或 `ui.label` + 富文本）。需要后端返回「命中位置」或「命中词列表」，还是前端拿到 query + snippet 自行切分？
- 中文无空格分词：当前 `make_snippet` 用 `content_lower.find(query_lower)` 做整串匹配；若用户输入多词，需按 `build_fts_query` 的拆词逻辑（`query.split()`）逐个高亮。
- 安全：snippet 来自用户文件内容，前端若用 `ui.html` 渲染高亮必须做 HTML 转义，防止文件内容里的 `<script>` 注入。

### 7.3 大文本分页/折叠（large text pagination/folding）

**当前仅做了「截断预览」：**

- 资产详情页 `app/ui/pages/asset_detail.py` 第 267–286 行：对文本类派生文件（transcript/summary/note/parsed 且 `.txt`/`.md`）调用 `read_text_preview(path, max_chars=2000)`，放进 `ui.expansion("预览")` 里，**只显示前 2000 字符**，截断时仅提示「预览已截断」，用户看不到全文。
- `app/utils.py` 的 `read_text_preview`（第 95–115 行）和多处文件读取都做了 UTF-8 / UTF-8-SIG / GBK 编码兜底。
- 搜索 snippet 也是截断到 160 字符（`make_snippet`）。

**讨论方向：**
- 详情页预览：长转录（数万字）是否改为「默认折叠 + 展开看全文」或「按段落/按字符分页（上一页/下一页）」？
- 是否需要「滚动加载」或「虚拟滚动」？NiceGUI 本身没有虚拟列表组件，可能要用分页或分段 `ui.expansion`。
- 全文阅读体验：是否提供「在新标签页打开原始 .md/.txt」的明确入口（已有「打开文件」按钮，但是系统默认程序打开）。

### 7.4 错误提示优化（error message optimization）

**当前兜底很原始：**

- 几乎每个 `except Exception as exc: ui.notify(str(exc), type="negative")` 都直接把异常字符串甩给用户（见 `assets.py` 45/135、`asset_detail.py` 46/106/162、`search.py` 121/138/156、`settings.py` 多处）。
- 对用户不友好的例子：
  - 密钥缺失：`config_service` 抛 `ValueError("未获取到 LLM API Key，请设置环境变量：XXX（或在 .knowledge/secrets.toml 配置）")` —— 这条已较友好，但其他异常仍裸奔。
  - 索引未建：用户点搜索但没重建索引，FTS5 报错被 `except sqlite3.OperationalError: pass` 静默吞掉（`search_service.py` 121 行），用户只看到空结果，不知原因。
  - 文件不存在、编码无法识别（`read_text_preview` 抛 `ValueError("无法识别文本编码")`）等。

**讨论方向：**
- 是否建立一套「用户友好错误」映射：把常见底层异常翻译成中文动作指引（如「未找到转录工具 mytool，请先安装」「向量索引未建立，请先点『重建向量索引』」）。
- 是否用 `loguru` 记录完整堆栈到 `.knowledge/logs/`，前端只给精简提示 + 「详情见日志」？
- 是否对「可恢复错误」（索引未建、配置缺失）给出一键操作入口（按钮直接触发重建/跳转设置）？
- 静默吞掉的 FTS5 `OperationalError` 是否应改为引导用户重建索引？

### 7.6 资产列表排序 + 分页（asset list sorting & pagination）

**当前完全无排序、无分页：**

- 资产列表页 `app/ui/pages/assets.py` 第 56 行：`list_assets(conn, limit=1000, asset_type=selected)` —— 直接取最多 1000 条全部渲染，没有分页、没有排序控制。
- 仓储层 `app/repositories/asset_repository.py` 的 `list_assets()` 查询里**没有 `ORDER BY`**，结果顺序依赖 SQLite 默认（rowid 插入顺序，即扫描时的文件系统遍历顺序），不稳定，也不符合用户预期。
- 只有类型过滤（`type_select`），没有排序切换，也没有按名称 / 按大小 / 按修改时间的选项。
- 计数用 `count_assets(conn, type)`，可以直接复用做分页总数。
- 列表头（第 67–74 行）是纯静态 row，点击没有排序交互。

**讨论方向：**
- 默认排序：建议默认 `mtime DESC`（最近修改的在最上面），符合个人知识库的使用习惯。
- 排序字段：名称、修改时间、大小、类型——哪些需要提供切换？
- 排序交互：表头点击切换（像传统表格）还是下拉选择？NiceGUI 列表头是普通 `ui.row` + `ui.label`，做点击排序需自己写状态。
- 分页方案：大库 1000 条一次性渲染是否够用？个人库一般几百个资产，是否需要分页？还是做「加载更多」按钮？
- 若做分页，需要后端配合：`list_assets` 增加 `order_by / offset / limit` 参数，前端加分页控件（上一页/下一页 + 当前页/总页数）。

---

### 7.7 导航栏当前页高亮 + 面包屑（navigation active highlight & breadcrumbs）

**当前无方位感：**

- 顶部导航 `app/ui/layout.py`（第 22–26 行）所有链接都是 `text-white/80 hover:text-white`，**没有当前页高亮**，用户不知道自己在哪个页面。
- 资产详情页 `app/ui/pages/asset_detail.py` 第 71 行只有一个「< 返回资产列表」文字链接，没有统一的面包屑组件。
- 搜索结果点进去详情页后，没有「返回搜索结果」的路径，用户容易迷路。
- 首页、设置页、任务页、搜索页都没有面包屑（其实这些一级页面不需要，但二级页面——资产详情——需要）。
- NiceGUI 没有内置面包屑组件，需要自己用 `ui.row` + `ui.link` 拼。

**讨论方向：**
- 当前页高亮：用 `ui.query` 检测当前路径？还是每个页面在 `page_frame` 里传一个 `active_key` 参数，由 layout 判断哪个导航项加高亮类？后者更简单可靠。
- 面包屑：是否抽一个通用组件 `breadcrumb(items)` 放在 `app/ui/layout.py` 或新建 `app/ui/components.py`？
- 面包屑深度：首页 / 资产 / 详情标题 三级是否够用？还是需要显示目录层级？
- 搜索 → 详情的回溯：详情页是否需要记住「从搜索页来」并显示「← 返回搜索结果」？可用 URL 参数（如 `?from=search&q=xxx`）实现，也为「搜索高亮联动」铺路（见 7.2）。

---

### 7.5 Windows 路径兼容性优化（Windows path compatibility）

**当前已有基础处理，但可加固：**

- `app/utils.py` 的 `open_file` / `open_folder`（第 37–72 行）已按 `sys.platform` 分支：Windows 用 `os.startfile` / `explorer /select,`；Mac 用 `open -R`；Linux 用 `xdg-open`。路径统一用 `pathlib.Path`。
- 编码兜底：`read_text_for_index` / `read_text_preview` 已依次尝试 UTF-8 / UTF-8-SIG / GBK。
- 首页输入知识库目录用的是普通 `ui.input`，用户手输 `D:/Knowledge` 或 `D:\Knowledge` 都可，但**没有路径合法性校验、没有「浏览文件夹」对话框**、没有把反斜杠统一处理。
- 长路径 / 含空格 / 含中文路径场景已能工作（Path 处理），但 NiceGUI 前端显示用的是 `str(state.library_root)`，Windows 下会显示反斜杠。

**讨论方向：**
- 是否引入「选择文件夹」原生对话框（NiceGUI 有 `ui.upload` 但主要是文件；文件夹选择可能要用 `@ui.refreshable` + 前端 `<input type="file" webkitdirectory>` 或引导用系统对话框）？
- 路径展示是否统一为更友好的形式（Windows 下保留反斜杠、长路径截断+tooltip）？
- 是否增加打开知识库前的路径校验（是否存在、是否可写、是否已在 `.knowledge` 内嵌套）？

---

## 8. 关键约定与约束（设计时必须遵守）

1. **页面注册**：新增/修改 `@ui.page` 后，必须在 `app/ui/pages/__init__.py` import。
2. **布局统一**：所有页面用 `page_frame(title)` 包一层（来自 `app/ui/layout.py`），保证导航一致。
3. **异步 IO**：任何文件/网络/子进程操作必须 `await run.io_bound(fn, *args)`，不可在事件回调里同步阻塞。
4. **异常处理**：目前每个回调都有自己的 `try/except + ui.notify`；若要统一错误提示，建议抽一个 `notify_error(exc)` 工具函数放在 `app/utils.py`，全站复用（呼应 §7.4）。
5. **安全红线**：**绝不在 UI 或 TOML 出现明文 API Key**。设置页 `GET /api/settings` 返回 `api_key` 一律 `***`；密钥只走 `secrets.toml`/环境变量/兼容明文。
6. **配置即事实来源**：配置改动走 `config_service.save_config(patch)` → 校验 → 覆盖写回 `config.toml` → 热重载；**严禁把配置持久化进 SQLite**。
7. **编码**：读取用户文本一律 UTF-8 → UTF-8-SIG → GBK 兜底，避免 Windows 上 GBK 文件炸裂。
8. **HTML 转义**：凡是用 `ui.html` 渲染用户内容（如 §7.2 高亮），必须转义，防 XSS。
9. **文件即数据**：不要为了「状态」引入新数据库列而偏离「文件系统是源」；新状态应能从 `assets`/`artifacts` 派生计算。

---

## 9. 待讨论 / 决策点（抛给讨论方）

1. **范围与优先级**：7 项里的实施顺序？建议收益高+改动小的组合：
   - **第一批（核心体感）**：搜索高亮 + 导航栏当前页高亮+面包屑 + 资产列表排序
   - **第二批（完善体验）**：状态徽章统一 + 错误提示优化 + 资产列表分页 + 大文本折叠
   - **第三批（平台加固）**：Windows 路径兼容性优化
2. **排序默认值**：默认按 mtime 倒序（最新修改在最上）是否合理？还是按名称字母序？
3. **分页阈值**：个人知识库一般几百个资产，1000 条上限是否够用？是否需要做分页，还是做「加载更多」？
4. **导航高亮实现**：`page_frame` 增加 `active_nav` 参数 vs 前端读路径自动判断——哪个更简洁？
5. **面包屑组件位置**：放在 `page_frame` 里统一渲染（由页面传 items），还是每个页面自己拼？
6. **状态模型**：是否抽一个统一的「资产派生完成度」计算（放到 `asset_repository` 或新增 `status_service`），让列表/详情/搜索三处复用？还是各页面各自聚合？
7. **高亮渲染**：后端返回命中词列表 vs 前端自行切分？中文多词如何高亮？向量语义搜索要不要高亮、高亮什么？
8. **错误提示**：抽 `notify_error` 统一层 + 是否接 loguru 日志？静默吞掉的 FTS5 异常要不要改成引导？
9. **大文本**：折叠 vs 分页 vs 虚拟滚动？NiceGUI 能力边界？
10. **Windows 路径**：要不要做文件夹选择对话框？路径校验做到什么程度？

---

## 10. 相关文档索引（如需深入）

- `docs/PRD.md`：完整产品需求，M8 见 §28；安全红线 §3；配置 §20.2 / §22.6 / §26.2；验收 §29。
- `docs/讨论/qwen-prdv1/m7-config-ui.md`：M7 配置 UI 化设计（含 §19 secrets.toml 已实施记录），可参考其文档风格与拆解粒度来写 M8 设计文档。
- `docs/README.md`：各里程碑落地文件清单与函数清单。
- `docs/项目梳理报告.md`：M0-M7 实施现状说明。

---

## 11. 实施状态

> 本文档作为与 qwen 讨论 M8 的上下文输入。M8 已据此 + `m8.md` 完整落地实现（2026-08-16，未提交），详见 `docs/README.md` 里程碑记录与代码改动（layout/utils/asset_repository/search_service/search/assets/asset_detail/home/settings/tasks）。
> M8 遗留到后续的小项：搜索→详情回溯（`?from=search&q=xxx`）、详情页返回保持搜索状态。
