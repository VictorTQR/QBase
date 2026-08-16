# QBase

本地优先的个人知识库管理应用。以**文件系统为唯一数据源**，扫描目录中的音视频、文档及其转录/总结等派生文件，提供全文搜索、语义搜索与 AI 总结。

> 设计理念：文件就是数据，不把内容锁进私有数据库。所有元数据与索引都落在知识库目录下的 `.knowledge/` 中，换机器、换软件都能直接读到原文。

## 功能现状（M0–M8 已完成）

- **知识库管理**：打开任意目录作为知识库，自动扫描并建立资产清单
- **派生文件识别**：自动识别转录（`.transcript.txt`）、总结（`.summary.md`）、笔记（`.notes.md`）等 sidecar 文件并绑定到对应资产
- **转录任务**：集成外部转录 CLI（默认 QVoice），后台任务化，支持并发去重与失败重试
- **全文搜索**：FTS5 全文检索 + 文件名搜索，中文子串用 LIKE 兜底
- **语义搜索**：LanceDB 向量索引，OpenAI 兼容 Embedding API，带 embedding 缓存（已嵌入片段不重复计费）
- **AI 总结**：对文档或转录内容调用 LLM 生成总结，长文本自动分段合并，覆盖前自动备份
- **设置页 + 任务中心**：配置总览（只读）、索引管理、任务详情与失败重试
- **最近打开的 5 个知识库**：首页一键切换最近使用的知识库
- **向量索引状态卡片**：设置页展示向量索引健康状态（模型 / 维度 / 覆盖度 / 最后重建），支持全量重建与清空缓存
- **体验优化**：搜索高亮、状态徽章、大文本折叠、统一错误提示、排序分页、全站统一导航

M8 体验优化已全部完成（搜索高亮 / 状态徽章 / 大文本折叠 / 错误提示 / 排序分页 / 统一导航 / 最近打开 / 向量状态卡片）。下一步规划见 [docs/讨论/qwen-prdv1/m8.md §15](./docs/讨论/qwen-prdv1/m8.md) 与 [vector-manage.md](./docs/讨论/qwen-prdv1/vector-manage.md)。

## 技术栈

- Python 3.13 + [uv](https://github.com/astral-sh/uv)（虚拟环境管理）
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
3. **搜索**：搜索页支持「全文 / 文件名 / 语义」三种模式；首次语义搜索前先「重建向量索引」
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
transcribe_command = ["uv", "run", "qvoice", "transcribe", "{input}", "--output", "{output}"]
transcribe_cwd = "E:/Code/00Code/GitBank/QVoice"
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
```

> **密钥管理**：配置里只写环境变量名（`api_key_env`），实际密钥通过系统环境变量提供（如 `set SILICONFLOW_API_KEY=xxx`，或在 shell 配置中持久化），各知识库自动继承，无需逐库填明文。
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
└── ui/              # NiceGUI 页面（layout.py 框架 + pages/ 各页面）
config.toml          # 应用级默认配置
start.bat            # 一键启动（Windows）
docs/PRD.md          # 唯一权威 spec
```

## 相关文档

- [docs/PRD.md](./docs/PRD.md) — 产品需求文档 v1.0（权威 spec：数据模型 / API / UI / 配置 / 里程碑）
- [docs/README.md](./docs/README.md) — 文档索引与里程碑实施记录
- [docs/项目梳理报告.md](./docs/项目梳理报告.md) — 项目全景梳理
- [CLAUDE.md](./CLAUDE.md) — 开发原则与环境指南

## 许可证

[LICENSE](./LICENSE)
