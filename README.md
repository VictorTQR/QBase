# QBase

本地优先的个人知识库管理应用。以**文件系统为唯一数据源**，扫描目录中的音视频、文档及其转录/总结等派生文件，提供全文搜索、语义搜索与 AI 总结。

> 设计理念：文件就是数据，不把内容锁进私有数据库。所有元数据与索引都落在知识库目录下的 `.knowledge/` 中，换机器、换软件都能直接读到原文。

## 功能现状（M0–M21 已完成，里程碑详见 [docs/PRD.md](./docs/PRD.md) §28）

- **知识库管理**：打开任意目录作为知识库，自动扫描并建立资产清单
- **派生文件识别**：自动识别转录（`.transcript.json` / `.transcript.txt`）、总结（`.summary.md`）、笔记（`.notes.md`）等 sidecar 文件并绑定到对应资产；JSON 转录自动提取纯文本用于索引、总结与预览
- **转录任务**：集成外部转录 CLI（默认 QVoice），后台任务化，支持并发去重与失败重试
- **全文搜索**：FTS5 全文检索 + 文件名搜索，中文子串用 LIKE 兜底
- **语义搜索**：LanceDB 向量索引，OpenAI 兼容 Embedding API，带 embedding 缓存（已嵌入片段不重复计费）
- **综合搜索**：全文 + 向量结果 RRF 融合（Reciprocal Rank Fusion，k=60），chunk 级去重、双命中条目排前并标注来源；单路不可用时自动降级为另一路并提示
- **标签系统**：详情页手动打标（可选可输新名称），资产列表标签列与多选筛选（任一命中），四种搜索模式均支持标签过滤；零引用标签自动清理。**AI 建议标签**（m16）：独立打标 LLM 配置，建议预填编辑器，确认后入库
- **AI 总结**：对文档或转录内容调用 LLM 生成总结，长文本自动分段合并，覆盖前自动备份
- **批量任务**（m17）：资产列表多选（跨页保留）+ 批量总结 / 批量 AI 打标，复用任务系统（并发、重启恢复、失败重试）
- **深度分析**（m18）：多模板分析产物（presets 文件化，一个资产 × 一个模板 = 一份分析），带时间戳转录输入，详情页 markdown 渲染
- **资产列表文件夹层级浏览**（m19）：文件管理器式导航——面包屑 + 子文件夹行（子树递归计数）+ 当前层直接文件，默认视图可切「平铺」；文件名关键词为全库搜索（结果平铺带完整路径），类型/标签筛选跟随浏览/搜索范围
- **LLM 异步对话补全**（m20）：智谱专有异步接口（提交 + 轮询短请求，摆脱长连接超时），总结/打标/分析逐功能配置切换 sync/async；thinking 思考开关显式可控；异步模式 max_tokens 上限 128K，思考型模型长输出不再被推理 token 截断
- **LLM Batch 批处理模式**（m21）：总结/打标/分析可切 mode=batch——请求打包为厂商批任务（智谱 / 硅基流动，OpenAI 风格 files+batches 三段式），五折计费、不受在线限流约束，任务中心实时展示进度，结果预计 24 小时内自动回填；重启只续查不重复提交（不双倍计费），长文合并调用本地执行
- **设置页 + 任务中心**：配置总览（只读）、索引管理、任务详情与失败重试
- **最近打开的 5 个知识库**：首页一键切换最近使用的知识库
- **向量索引状态卡片**：设置页展示向量索引健康状态（模型 / 维度 / 覆盖度 / 最后重建），支持全量重建与清空缓存
- **体验优化**：搜索高亮、状态徽章、大文本折叠、统一错误提示、排序分页、全站统一导航与设计 token（统一布局框架 / WCAG AA 灰度对比度）

M8 体验优化已全部完成（搜索高亮 / 状态徽章 / 大文本折叠 / 错误提示 / 排序分页 / 统一导航 / 最近打开 / 向量状态卡片）。后续里程碑（M9 文档解析 / M10 EPUB / M11 sidecar 目录 / M12 转录分段视图 / M13 播放器与字幕跳转 / M14 混合搜索排序 / M15 标签系统 / M16 AI 建议标签 / M17 批量任务 / M18 深度分析 / M19 资产列表文件夹层级浏览 / M20 LLM 异步对话补全 / M21 LLM Batch 批处理模式）均已落地，下一步规划见 [docs/PRD.md](./docs/PRD.md) §31。

## 技术栈

- Python 3.12 + [uv](https://github.com/astral-sh/uv)（虚拟环境管理）
- [NiceGUI](https://nicegui.io/)（UI）+ FastAPI + uvicorn
- SQLite（资产/任务/分块元数据 + FTS5）+ LanceDB（向量）
- 日志：[loguru](https://github.com/Delgan/loguru)

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 启动应用

**方式一（推荐）**：双击仓库根目录的 `start.bat`

**方式二**：命令行启动

```bash
.venv/Scripts/python.exe -m app.main
```

启动后访问 <http://127.0.0.1:8765>。

### 3. 打开知识库

在首页选择你的资料目录（如 `E:/Storage/SoftCache/WorkBuddy/kb-test`）。首次打开会自动在该目录下生成 `.knowledge/config.toml`。

## 使用流程

1. **扫描**：打开知识库后点击「扫描」，识别音视频/文档及其派生文件
2. **转录**（可选）：在资产详情页对音视频发起转录（需配置转录 CLI）
3. **搜索**：搜索页支持「综合（全文+语义 RRF 融合）/ 全文 / 文件名 / 语义」模式，回车默认综合搜索；首次全文 / 语义搜索前先重建对应索引
4. **AI 总结**（可选）：资产详情页一键生成总结，结果写入 `{stem}.summary.md`
5. **任务中心**：查看转录/总结任务状态，失败任务可重试

## 配置

### 应用级配置（`config.toml`，仓库根）

仅控制运行参数，不含模型密钥：

```toml
host = "127.0.0.1"
port = 8765
log_level = "INFO"
open_browser = true
```

也可用环境变量覆盖：`QBASE_HOST` / `QBASE_PORT` / `QBASE_LOG_LEVEL` / `QBASE_OPEN_BROWSER`。

### 知识库级配置（`<库目录>/.knowledge/config.toml`）

每个知识库独立配置转录 CLI、Embedding、LLM。默认模板在首次打开时写入，`enabled` 默认 `false`（避免误触发 API 费用）。

以 SiliconFlow 为例：

```toml
[cli]
# -f json 输出 <stem>.transcript.json（含时间戳/说话人）；改为 -f txt 输出纯文本
transcribe_command = ["uv", "run", "qvoice", "transcribe", "{input}", "-f", "json"]
transcribe_cwd = "../QVoice"
transcribe_timeout_seconds = 14400

[embedding]
enabled = true
provider = "openai_compatible"
base_url = "https://api.siliconflow.cn/v1"
api_key_env = "SILICONFLOW_API_KEY"
model = "BAAI/bge-m3"
dimension = 1024
batch_size = 32
timeout = 60

[llm.summary]
enabled = true
provider = "openai_compatible"
base_url = "https://api.siliconflow.cn/v1"
api_key_env = "SILICONFLOW_API_KEY"
model = "Qwen/Qwen2.5-72B-Instruct"
max_input_chars = 24000
chunk_chars = 6000

[llm.tagging]
# AI 建议标签（m16）：建议预填编辑器，确认后保存；可与总结用不同模型
enabled = true
base_url = "https://api.siliconflow.cn/v1"
api_key_env = "SILICONFLOW_API_KEY"
model = "Qwen/Qwen2.5-72B-Instruct"
```

> **密钥管理**：配置里只写环境变量名（`api_key_env`），实际密钥通过系统环境变量提供（如 `set SILICONFLOW_API_KEY=xxx`，或在 shell 配置中持久化），各知识库自动继承，无需逐库填明文。
>
> **转录 CLI 路径**：`transcribe_cwd` 支持绝对路径、`~` 开头（用户主目录）与相对路径（相对 QBase 应用根目录，默认 `"../QVoice"` 即同级仓库）；目录不存在时发起转录会立即提示错误。
>
> **注意**：当前设置页为**只读展示**，修改配置需手动编辑上述 `config.toml` 文件。

## 目录结构

```text
app/
├── main.py          # 入口
├── config.py        # 应用级配置（config.toml + 环境变量）
├── logging_conf.py  # loguru 日志（logs/qbase.log 轮转）
├── state.py         # 运行时状态（当前知识库路径 / 数据库路径）
├── database.py      # SQLite 连接与建表（WAL）
├── rules.py         # 文件类型 / 忽略规则
├── utils.py         # 格式化、打开文件 / 目录
├── repositories/    # 数据访问层
├── services/        # 业务层（library / scanner / transcribe / index / search / vector / llm / summarization）
└── ui/              # NiceGUI 页面（layout.py 统一 page_frame + tokens.py 设计 token + components.py 共享徽章 + pages/ 各页面）
config.toml          # 应用级默认配置
start.bat            # 一键启动（Windows）
docs/PRD.md          # 唯一权威 spec
```

## 相关文档

- [docs/PRD.md](./docs/PRD.md) — 产品需求文档 v1.1（权威 spec：数据模型 / API / UI / 配置 / 里程碑）
- [docs/README.md](./docs/README.md) — 文档索引与里程碑实施记录
- [docs/项目梳理报告.md](./docs/项目梳理报告.md) — 项目全景梳理
- [CLAUDE.md](./CLAUDE.md) — 开发原则与环境指南

## 许可证

[LICENSE](./LICENSE)
