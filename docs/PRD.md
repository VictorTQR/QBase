# 本地知识管理应用 PRD v1.1

## 0. 版本变更历史

本 PRD 是项目唯一权威 spec。版本演进摘要记录于此，逐行 diff 见 git 提交历史。

### v1.1 (2026-08-16)

主题：知识库配置 UI 化（渐进式分层设计）。

- 标题 `v1.0 → v1.1`
- §2 第一阶段目标第 13 条：明确「通过 UI 表单修改核心 API/模型配置（含环境变量状态检测与连通性测试），高级配置保留 TOML 直编」
- §3 明确不做：新增红线「在应用内明文存储和输入 API Key（坚持使用系统环境变量）」
- §20.2（新增）UI 与配置交互原则：配置严禁持久化到 SQLite，走 `UI 表单 → 后端校验 → 覆盖写回 .knowledge/config.toml → 触发热重载` 链路；UI 表单层（高频易错）/ 极客直编层（低频复杂）分层
- §22.6 设置页：重写为渐进式分层设计（高频表单区 / 极客直编区 `[在编辑器中打开]` / Env Inspector 红绿灯 / Test Connection 连通性测试 / 修改 dimension 或 embedding.model 时的危险操作拦截）
- §23.5 Settings API：新增 `POST /api/settings/test-connection`
- §28 M7：目标与完成标志对齐「渐进式 UI 表单化 + 环境变量检测 + API 连通性测试 + 维度变更重建告警」
- §29.7 配置验收：重写为 6 条可验收标准

**与现状偏差（已收口）**：§20.2 / §22.6 / §23.5 中的表单写回、Env Inspector、Test Connection、dimension/model 变更告警均已在 M7 补完（m7-config-ui，2026-08-16）落地。PRD v1.1 与代码现状现已对齐。

### v1.0 (2026-08-16 早)

主题：MVP 初版完整 spec。

- 覆盖 M0–M7 设计：知识库与扫描、派生文件识别、转录任务、全文搜索、向量搜索、AI 总结、设置与任务中心
- 确立核心原则：本地文件优先、文件系统为真实数据源、数据库仅索引缓存可重建、CLI 可独立使用

## 1. 产品名称与定位

### 1.1 产品名称

暂定：

```text
Local Knowledge Hub
```

中文名暂定：

```text
本地知识管理中心
```

---

### 1.2 产品定位

一个面向个人用户的本地知识管理应用，用于管理：

```text
播客音频
视频文件
文档文件
```

并围绕这些内容提供：

```text
统一查看
文件管理状态展示
转录任务触发
AI 总结生成
笔记文件管理
文件名搜索
全文搜索
向量语义搜索
```

系统以本地文件系统为真实数据源，不改变用户原有文件组织方式。

---

### 1.3 核心原则

```text
1. 本地文件优先，应用不移动、不重命名、不删除用户原始文件。
2. 派生文件落盘可见，可被外部 CLI 或手动编辑产生。
3. 应用数据库只是索引和缓存，可重建。
4. CLI 能力可独立使用，不依赖主应用。
5. 主应用负责查看、管理、任务调度和搜索。
6. 第一阶段只服务个人本地使用，不做多用户和云端能力。
```

---

## 2. 第一阶段目标

第一阶段要实现一个可自用的本地知识管理 MVP：

```text
1. 打开或新建本地知识库目录。
2. 在库目录下创建 .knowledge/ 应用数据目录。
3. 扫描音频、视频、文档文件。
4. 展示资产列表和详情页。
5. 识别已有转录 txt 文件。
6. 支持手动触发转录 CLI。
7. 支持手动刷新后识别外部 CLI 生成的文件。
8. 支持 AI 总结生成，调用 OpenAI 兼容 API。
9. 支持文件名搜索。
10. 支持全文搜索。
11. 支持基于 LanceDB 的向量语义搜索。
12. 支持笔记文件识别、只读预览和外部编辑器打开。
13. 支持通过 UI 表单修改核心 API 与模型配置（含环境变量状态检测与连通性测试），高级配置保留 TOML 直编，并支持索引重建。
```

---

## 3. 第一阶段明确不做

```text
多用户系统
登录认证
云端同步
移动端
团队协作
插件系统
复杂标签体系
双链关系图
应用内富文本笔记编辑器
TTS 朗读
字幕级音频跳转
自动批量转录
文件监听自动更新
自动整理/移动/重命名文件
文档版本历史
总结版本对比
复杂权限管理
在应用内明文存储和输入 API Key（密钥通过环境变量或库级 .knowledge/secrets.toml 提供，不明文存储）
```

其中文档解析与 sidecar 目录已实现（M9-M11）；文件监听与笔记编辑暂缓（见 §31 待实现）。

---

## 4. 用户角色

只有一个角色：

```text
个人用户
```

拥有所有权限：

```text
打开知识库
扫描文件
触发转录
生成总结
查看笔记
打开外部编辑器
搜索
修改配置
重建索引
```

---

## 5. 核心概念

### 5.1 Library，知识库

一个本地目录作为知识库根目录。

例如：

```text
D:\Knowledge\
```

应用在该目录下创建：

```text
D:\Knowledge\.knowledge\
```

用于存放：

```text
配置
SQLite 数据库
全文索引
LanceDB 向量数据
任务记录
缓存
日志
备份
```

第一阶段只支持当前打开的一个知识库。

---

### 5.2 Asset，原始知识资产

原始文件。

例如：

```text
podcasts\episode-001.mp3
videos\talk-001.mp4
documents\paper.pdf
notes\reading.md
```

Asset 类型：

```text
audio
video
document
```

---

### 5.3 Artifact，派生产物

围绕 Asset 产生的文件。

例如：

```text
episode-001.txt
episode-001.summary.md
episode-001.notes.md
paper.parsed.md
```

Artifact 类型：

```text
transcript
summary
note
parsed
meta
```

第一阶段重点是：

```text
transcript
summary
note
```

---

### 5.4 Task，任务

主应用触发的后台任务。

第一阶段任务类型：

```text
transcription
summarization
rebuild_fts
rebuild_vector
scan
```

任务状态：

```text
pending
running
success
failed
cancelled
```

---

### 5.5 Search Index，搜索索引

搜索分三类：

```text
文件名搜索
全文搜索
向量语义搜索
```

技术选择：

```text
文件名搜索：SQLite
全文搜索：SQLite FTS5
向量搜索：LanceDB
```

---

## 6. 运行环境

### 6.1 操作系统

第一阶段优先支持：

```text
Windows
```

代码层面尽量使用 Python 跨平台写法，但不保证 macOS/Linux 完整体验。

---

### 6.2 Python 版本

建议：

```text
Python 3.11+
```

---

### 6.3 启动方式

第一阶段不打包成 exe。

启动方式：

```bash
python -m app.main
```

或：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

默认浏览器访问：

```text
http://127.0.0.1:8765
```

---

### 6.4 网络策略

服务只监听：

```text
127.0.0.1
```

不监听：

```text
0.0.0.0
```

调用外部 API 时可配置开启或关闭：

```text
LLM 总结 API
Embedding API
```

如果关闭，则相关功能不可用，但本地管理和全文搜索仍可用。

---

## 7. 知识库目录设计

### 7.1 用户知识库示例

```text
D:\Knowledge\
├── podcasts\
│   ├── episode-001.mp3
│   ├── episode-001.txt
│   ├── episode-001.summary.md
│   └── episode-001.notes.md
│
├── videos\
│   ├── talk-001.mp4
│   └── talk-001.txt
│
├── documents\
│   ├── paper.pdf
│   ├── note.md
│   └── note.summary.md
│
└── .knowledge\
```

---

### 7.2 应用数据目录

```text
.knowledge\
├── config.toml
├── db.sqlite
├── vector\
│   └── lancedb\
├── cache\
│   └── embeddings.sqlite
├── backups\
├── logs\
└── tasks\
```

说明：

```text
config.toml          应用配置
db.sqlite            资产、产物、任务、全文索引元数据
vector/lancedb       LanceDB 向量数据
cache/embeddings.sqlite  embedding 缓存，减少 API 重复消耗
backups              覆盖总结前的备份
logs                 日志
tasks                可选任务日志或临时输出
```

---

## 8. 文件类型支持

### 8.1 音频

第一阶段支持：

```text
.mp3
.m4a
.wav
.flac
.aac
.ogg
.opus
```

---

### 8.2 视频

第一阶段支持：

```text
.mp4
.mkv
.mov
.webm
.avi
```

---

### 8.3 文档

第一阶段支持作为 Asset 管理：

```text
.pdf
.docx
.doc
.md
.txt
.html
.htm
.epub
```

但内容解析能力分阶段：

```text
第一阶段可直接内容索引：
.md
.txt
.html / .htm，可选简单提取

第一阶段暂不解析（后续里程碑解决）：
.pdf / .docx / .doc —— m9 起经 MinerU 解析（见 §15）
.epub —— m10 起经内置本地解析器解析（见 §15）
```

这些文件第一阶段仍可：

```text
列表管理
文件名搜索
打开文件位置
用外部程序打开
```

但在对应解析里程碑接入前，不会进入全文搜索、向量搜索和 AI 总结。

---

## 9. 派生文件规则

### 9.1 当前阶段规则

采用同目录同名 sidecar 文件。

原始文件：

```text
episode-001.mp3
```

可识别派生文件：

```text
episode-001.txt                  转录文本，兼容现有 CLI
episode-001.transcript.txt       转录文本，QVoice 默认输出
episode-001.transcript.json      JSON 转录，QVoice -f json 输出（含全文 text + 带时间戳/说话人的 segments）
episode-001.summary.md           AI 总结
episode-001.notes.md             用户笔记
episode-001.parsed.md            文档解析结果，后续使用
episode-001.meta.json            元数据，后续使用
```

m11 起同时识别 sidecar 目录形态 `episode-001.mp3.kb\`（见 §9.4），两种形态可并存。

---

### 9.2 识别优先级

转录文本识别顺序：

```text
1. {stem}.transcript.json
2. {stem}.transcript.txt
3. {stem}.txt
```

如果同时存在，优先：

```text
{stem}.transcript.json
```

`.transcript.json` 是结构化转录（QVoice `-f json` 产物），读取时提取纯文本：
优先顶层 `text` 字段，为空则按行拼接 `segments[].text`。时间轴 / 说话人字段
第一阶段仅保留在原文件中，不做字幕跳转。

但第一阶段也可以多个都识别为 transcript artifact，并在 UI 中提示存在多个转录文件。

---

### 9.3 歧义处理

如果同目录存在：

```text
episode-001.mp3
episode-001.mp4
episode-001.txt
```

则 `episode-001.txt` 无法明确属于哪个 Asset。

第一阶段处理：

```text
标记为 ambiguous artifact
不自动绑定
在 UI 中提示
```

后续可通过：

```text
sidecar 目录（m11 已支持，见 §9.4 —— 目录名含扩展名，天然无歧义）
CLI 指定输出路径（{output} 变量已预留）
更明确命名
```

解决。

---

### 9.4 sidecar 目录（m11 已实现）

派生文件的目录归集形态：

```text
episode-001.mp3.kb\
├── transcript.json
├── transcript.txt
├── summary.md
├── notes.md
├── parsed.md
└── meta.json
```

规则：

```text
目录名 = 原始文件完整文件名 + .kb（含扩展名），按 relative_path 精确绑定资产，
无 stem 歧义；资产不存在时目录内容计入孤儿，不入库，资产恢复后刷新重新绑定
内部固定文件名映射 kind：transcript.json / transcript.txt → transcript、
summary.md → summary、notes.md → note、parsed.md → parsed、meta.json → meta；
未识别命名与隐藏文件忽略，不递归子目录
写入策略 = 跟随现状（opt-in）：资产旁已存在 .kb\ 目录时，应用生成的总结 /
解析产物写入目录内（文件名无 stem 前缀）；否则维持平铺。手动建目录即启用
转录产物维持平铺（QVoice 输出路径能力未确认）；{output} 变量已预留进命令
模板替换，CLI 后产物查找候选包含 .kb 内位置
不做归集 / 迁移工具：旧平铺产物永久识别，手动移动 + 刷新即完成迁移
.kb\ 目录内容永不产生资产记录
```

---

## 10. 文件扫描与同步

### 10.1 启动扫描

优先级：P0

应用启动并打开知识库后，应进行一次扫描。

扫描内容：

```text
发现新增 Asset
发现新增 Artifact
更新已有文件状态
移除已删除文件记录
```

---

### 10.2 手动刷新

优先级：P0

第一阶段不做实时文件监听。

UI 需要提供：

```text
刷新
重新扫描
```

手动刷新后同步文件变化。

---

### 10.3 文件识别依据

第一阶段使用：

```text
relative_path
size
mtime
```

可选开启：

```text
file_hash
```

默认不建议对所有大文件立即 hash，避免扫描慢。

---

### 10.4 删除处理

当文件被删除：

```text
删除 Asset 或 Artifact 数据库记录
删除全文索引
删除向量索引
```

不恢复文件，不操作回收站。

---

### 10.5 移动/重命名

用户要求不允许应用移动或重命名文件。

如果用户自己在资源管理器中移动或重命名：

第一阶段处理：

```text
视为旧文件删除，新文件新增
```

后续可通过 hash 识别同一文件并迁移记录。

---

### 10.6 忽略目录

默认忽略：

```text
.knowledge/
.git/
__pycache__/
node_modules/
.trash/
.venv/
venv/
$RECYCLE.BIN/
System Volume Information/
```

可配置。

---

## 11. 资产管理功能

### 11.1 资产列表

优先级：P0

展示字段：

```text
标题
类型
相对路径
大小
修改时间
转录状态
总结状态
笔记状态
索引状态
```

支持：

```text
按类型过滤：音频 / 视频 / 文档
按目录过滤
按名称排序
按修改时间排序
关键词过滤
```

---

### 11.2 资产详情页

优先级：P0

详情页显示：

```text
标题
类型
路径
大小
修改时间
转录状态
总结状态
笔记状态
任务状态
```

操作按钮：

```text
打开文件
打开所在文件夹
生成转录
生成总结
刷新当前资产
重新索引当前资产
```

音频/视频详情页：

```text
播放器，第一阶段可使用浏览器原生 audio/video
转录内容预览
总结内容预览
笔记内容预览
```

文档详情页：

```text
文本内容预览，仅限可读取文本
总结内容预览
笔记内容预览
```

---

### 11.3 外部打开

优先级：P0

Windows 下支持：

```text
用默认程序打开文件
打开文件所在文件夹
```

实现建议使用：

```python
os.startfile(path)
```

打开文件夹可使用：

```text
explorer /select,"path"
```

---

## 12. 转录功能

### 12.1 CLI 现状

外部转录 CLI（QVoice）：

```bash
qvoice transcribe input.mp3              # 输出 <stem>.transcript.txt（纯文本）
qvoice transcribe input.mp3 -f json      # 输出 <stem>.transcript.json（结构化）
```

JSON 结构：

```text
{generated_at, tool, file, provider, success, text,
 language?, duration?, speakers?, segments: [{start, end, text, speaker?}]}
```

第一阶段只提取其中的纯文本（`text` 优先，回退 `segments[].text`）用于索引、
总结与预览；不做时间轴、字幕、点击跳转。

---

### 12.2 转录命令配置

优先级：P0

默认命令（新库）：

```toml
[cli]
transcribe_command = ["uv", "run", "qvoice", "transcribe", "{input}", "-f", "json"]
```

支持变量：

```text
{input}    原始音视频绝对路径
```

默认输出：

```text
与原始文件同目录同名的 .transcript.json
```

例如：

```text
D:\Knowledge\podcasts\episode-001.mp3
```

输出：

```text
D:\Knowledge\podcasts\episode-001.transcript.json
```

CLI 成功后按以下优先级查找产物（兼容 `-f txt` 或不带 `-f` 的自定义模板）：

```text
1. {stem}.transcript.json
2. {stem}.transcript.txt
3. {stem}.txt
```

---

### 12.3 手动触发转录

优先级：P0

用户在音频或视频详情页点击：

```text
生成转录
```

流程：

```text
1. 创建 transcription task
2. 检查是否已有 transcript artifact
3. 如已存在，提示用户确认是否覆盖
4. 调用 CLI
5. 等待 CLI 结束
6. 按候选优先级检查转录产物是否存在（.transcript.json → .transcript.txt → .txt）
7. 写入 artifact 记录
8. 建立全文索引
9. 建立向量索引
10. 更新 UI 状态
```

---

### 12.4 已有转录文件处理

优先级：P0

如果已有：

```text
episode-001.txt
```

点击转录时提示：

```text
已存在转录文件，是否覆盖？
```

策略：

```text
默认跳过
用户确认后才覆盖
覆盖前可备份到 .knowledge/backups/
```

---

### 12.5 外部 CLI 生成文件

优先级：P0

用户手动运行：

```bash
mytool transcribe episode-001.mp3
```

生成：

```text
episode-001.txt
```

由于第一阶段没有实时监听，用户需要点击：

```text
刷新
```

或重新扫描。

应用识别后：

```text
绑定到对应 Asset
标记 source = external
建立索引
```

---

### 12.6 自动转录

优先级：P2

第一阶段不做自动转录。

后续可配置：

```text
新增音视频后自动转录
```

---

## 13. AI 总结功能

### 13.1 总结方式

根据你的选择，第一阶段没有总结 CLI。

因此总结由主应用直接调用：

```text
OpenAI 兼容 API
```

---

### 13.2 总结输入

优先级：P0

不同 Asset 的总结输入不同。

#### 音频/视频

必须存在转录文本：

```text
{stem}.transcript.json
或
{stem}.transcript.txt
或
{stem}.txt
```

如果没有转录：

```text
禁用生成总结按钮
提示先生成转录
```

#### 文档

第一阶段可总结：

```text
.md
.txt
.html / .htm，若实现文本提取
```

解析后可总结（m9 起，epub 自 m10 起）：

```text
.pdf
.docx
.doc
.pptx
.ppt
.xlsx
.xls
.epub（m10，内置本地解析器）
```

白名单文档解析生成 `{stem}.parsed.md` 后，总结输入改为：

```text
{stem}.parsed.md
```

---

### 13.3 总结输出

输出文件：

```text
{stem}.summary.md
```

例如：

```text
episode-001.summary.md
```

文件内容建议包含 frontmatter：

```markdown
---
type: summary
source: episode-001.mp3
source_hash: 
generator: openai_compatible
model: gpt-4o-mini
created_at: 2026-08-16T12:00:00+08:00
---

# episode-001 总结

## 核心内容

...

## 关键点

...

## 可能值得后续关注

...
```

第一阶段即使模型输出没有 frontmatter，应用也应自动补充基础 frontmatter。

---

### 13.4 总结覆盖策略

优先级：P0

如果已有：

```text
episode-001.summary.md
```

重新生成时：

```text
提示已存在总结
用户确认后才覆盖
覆盖前备份到 .knowledge/backups/
```

备份命名建议：

```text
episode-001.summary.20260816-120000.md
```

---

### 13.5 长文本总结策略

优先级：P0

播客和视频时长大多在：

```text
30 分钟 - 2 小时
```

转录文本可能超过模型上下文限制。

第一阶段采用简单分层总结：

```text
1. 将转录文本按段落切块
2. 对每个块生成局部摘要
3. 将局部摘要合并生成最终总结
```

如果 API 调用失败，可降级为：

```text
截取前 N 个字符生成总结
```

并在总结 frontmatter 或任务日志中记录：

```text
summary_mode: truncated
```

---

### 13.6 总结 Prompt

配置中应支持 Prompt 模板。

默认模板示例：

```text
你是一个知识管理助手。
请根据下面内容生成中文总结。

要求：
1. 先给出 3-5 句核心总结。
2. 再列出 5-15 个关键点。
3. 如果内容包含行动项，请单独列出。
4. 不要编造不存在的信息。
5. 使用 Markdown 格式。

内容：
{content}
```

分段摘要模板示例：

```text
请总结下面这段内容，保留关键信息，输出简洁中文摘要。

内容：
{chunk}
```

合并摘要模板示例：

```text
下面是一篇长内容的多段摘要。
请根据这些摘要生成最终中文总结。

要求：
1. 先给出核心总结。
2. 再列出关键点。
3. 不要编造不存在的信息。

分段摘要：
{partial_summaries}
```

---

### 13.7 总结任务状态

优先级：P0

总结任务需要记录：

```text
task_id
asset_id
type = summarization
status
input_artifact_id
model
api_base_url
error
created_at
started_at
finished_at
output_path
```

---

## 14. 笔记功能

根据你的选择，第一阶段笔记以管理和预览为主，不做复杂编辑。

---

### 14.1 笔记文件

优先级：P0

笔记文件：

```text
{stem}.notes.md
```

例如：

```text
episode-001.notes.md
```

---

### 14.2 笔记识别

优先级：P0

扫描时如果发现：

```text
episode-001.notes.md
```

则识别为：

```text
episode-001.mp3 的 note artifact
```

如果没有 notes 文件，不自动创建。

---

### 14.3 笔记展示

优先级：P0

详情页提供笔记 tab：

```text
只读预览 Markdown
显示文件路径
显示修改时间
```

---

### 14.4 外部编辑

优先级：P0

提供按钮：

```text
用外部编辑器打开
```

Windows 下使用默认程序打开：

```text
episode-001.notes.md
```

用户外部保存后，由于第一阶段无监听，需要点击刷新重新索引。

---

### 14.5 应用内编辑

优先级：P2

第一阶段不做应用内编辑，且已移入暂缓（见 §31）：笔记长期维持「外部编辑器打开 + 手动刷新重新索引」形态（§14.4）。

若未来实现，可加：

```text
简单 Markdown 编辑
保存
自动索引
```

---

### 14.6 笔记保护

优先级：P0

任何自动任务不得覆盖：

```text
{stem}.notes.md
```

AI 总结只写：

```text
{stem}.summary.md
```

后续 AI 笔记草稿只写：

```text
{stem}.ai-notes.md
```

---

## 15. 文档解析策略

你当前文档解析 CLI：

```text
尚未实现，计划做
```

因此第一阶段采取保守策略。

---

### 15.1 第一阶段支持

可直接读取并索引：

```text
.md
.txt
```

可选支持：

```text
.html / .htm
```

这些文件可以：

```text
全文搜索
向量搜索
生成总结
```

---

### 15.2 解析策略（m9 起，m10 扩展 epub）

m9 起白名单文档（.pdf/.docx/.doc/.pptx/.ppt/.xlsx/.xls）可在资产详情页发起
MinerU 解析，生成 `{stem}.parsed.md` 后进入全文/向量索引并可用于 AI 总结。

m10 起 `.epub` 一并纳入白名单：固定路由到内置本地解析器（标准库解
zip + OPF spine，无需远端服务与 token，秒级完成），产物同为
`{stem}.parsed.md`，后续链路与 MinerU 完全一致。

解析前这些文件只能：

```text
作为 Asset 管理
文件名搜索
外部打开
查看详情
```

UI 显示：

```text
待解析（pdf/office/epub 白名单，均可发起解析）
```

---

### 15.3 解析器抽象（m9，m10 扩展）

文档解析走 provider 抽象（`app/services/parsers/`），不再使用 CLI 命令模板：

```text
DocumentParser 接口：submit（提交+上传/校验）→ poll（轮询）→ fetch（取回产物）
                    → to_markdown（产物字节 → markdown 文本）
注册表 PARSERS = {"mineru": MineruParser, "epub": EpubParser}，
[parse].provider 切换（管 pdf/office）
新增解析器实现同一接口并注册即可（doc2x / Textin / 本地 CLI 均可）
```

m10 起按扩展名路由（`get_parser_for_extension`）：

```text
.epub → 内置 EpubParser（本地解析：submit=结构校验、poll=查源文件、
        fetch=现算 markdown；无状态，重启后重算即恢复）
其余白名单后缀 → [parse].provider（现 mineru）
```

产物留档：MinerU 结果 zip 留档 backups/（PRODUCT_BACKUP_SUFFIX=".zip"）；
epub 产物即 markdown 文本，不留档（覆盖重解析有 .bak.md）。

输出：

```text
{stem}.parsed.md
```

一旦 parsed.md 生成：

```text
全文索引
向量索引
AI 总结
```

都基于 parsed.md。

---

## 16. 搜索功能

### 16.1 搜索入口

优先级：P0

全局搜索框。

搜索模式：

```text
文件名
全文
语义
```

第一阶段可以做成三个 tab。

---

### 16.2 文件名搜索

优先级：P0

搜索范围：

```text
Asset 标题
Asset 相对路径
Artifact 相对路径
```

实现：

```sql
LIKE
```

后续可优化为 SQLite FTS。

---

### 16.3 全文搜索

优先级：P0

使用 SQLite FTS5。

索引内容：

```text
转录文本
总结文本
笔记文本
Markdown 文档
TXT 文档
HTML 提取文本，若实现
```

不索引：

```text
未解析 PDF/DOCX 二进制内容
```

搜索结果展示：

```text
资产标题
命中文件路径
命中来源：transcript / summary / note / document
命中片段
```

---

### 16.4 向量搜索

优先级：P0

使用 LanceDB。

搜索流程：

```text
1. 用户输入查询文本
2. 调用 Embedding API 生成 query vector
3. 在 LanceDB 中检索 top_k chunks
4. 根据 chunk 关联 asset/artifact
5. 返回结果
```

结果展示：

```text
资产标题
命中内容片段
来源类型
相对路径
相似度分数，可选
```

---

### 16.5 向量索引范围

第一阶段索引：

```text
transcript
summary
note
document text，仅限可读文本
```

暂不索引：

```text
未解析 PDF/DOCX
二进制文件
```

---

### 16.6 搜索过滤

优先级：P1

支持：

```text
按类型过滤：audio / video / document
按来源过滤：transcript / summary / note / document
```

---

### 16.7 综合搜索

优先级：P2

第一阶段不做复杂混合排序。

后续可以做：

```text
全文结果 + 向量结果融合
Reciprocal Rank Fusion
```

---

## 17. LanceDB 向量索引设计

### 17.1 存储路径

```text
.knowledge/vector/lancedb
```

---

### 17.2 表名

```text
chunks
```

---

### 17.3 字段设计

```text
id
asset_id
artifact_id
artifact_kind
asset_type
relative_path
chunk_index
content
content_hash
embedding_model
updated_at
vector
```

示例：

```json
{
  "id": "chunk_20260816_000001",
  "asset_id": "asset_0001",
  "artifact_id": "artifact_0001",
  "artifact_kind": "transcript",
  "asset_type": "audio",
  "relative_path": "podcasts/episode-001.mp3",
  "chunk_index": 3,
  "content": "这里是一段转录文本……",
  "content_hash": "sha256:xxxx",
  "embedding_model": "text-embedding-3-small",
  "updated_at": "2026-08-16T12:00:00+08:00",
  "vector": [0.012, -0.034, 0.056]
}
```

---

### 17.4 分块策略

第一阶段建议：

```text
max_chunk_chars = 800
chunk_overlap = 100
```

切块顺序：

```text
优先按段落
段落过长按句子
句子过长按字符
```

---

### 17.5 Embedding API

使用 OpenAI 兼容 API。

配置项：

```toml
[embedding]
enabled = true
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "text-embedding-3-small"
dimension = 1536
batch_size = 32
timeout = 120
```

注意：

```text
dimension 必须和模型实际输出一致
模型或维度变化后需要重建向量索引
```

---

### 17.6 Embedding 缓存

为了减少 API 重复调用，需要缓存 embedding。

缓存数据库：

```text
.knowledge/cache/embeddings.sqlite
```

表结构：

```sql
CREATE TABLE embedding_cache (
  content_hash TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  vector BLOB NOT NULL,
  dimension INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

逻辑：

```text
1. 对 chunk 内容计算 content_hash
2. 查询缓存
3. 命中则直接使用
4. 未命中则调用 API
5. 写入缓存
```

如果模型变化：

```text
旧缓存不复用
```

---

### 17.7 向量更新

当 Artifact 变化：

```text
删除该 artifact_id 的旧向量
重新分块
重新 embedding
写入 LanceDB
```

当 Asset 删除：

```text
删除该 asset_id 的所有向量
```

---

### 17.8 向量重建

设置页提供：

```text
重建向量索引
```

重建时：

```text
清空 LanceDB chunks 表
重新扫描所有可索引 artifact
重新分块
重新 embedding
```

需要注意 API 成本。

---

## 18. 全文索引设计

### 18.1 chunks 表

```sql
CREATE TABLE chunks (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  artifact_id TEXT,
  kind TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT,
  created_at TEXT NOT NULL
);
```

---

### 18.2 FTS5 表

```sql
CREATE VIRTUAL TABLE chunks_fts USING fts5(
  content,
  content='chunks',
  content_rowid='rowid'
);
```

---

### 18.3 索引范围

```text
transcript
summary
note
document_text
```

---

### 18.4 搜索片段

使用：

```sql
snippet(chunks_fts, 0, '<b>', '</b>', '...', 20)
```

前端需要注意 HTML 转义或安全渲染。

---

## 19. 数据模型定稿

### 19.1 assets

```sql
CREATE TABLE assets (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  type TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  absolute_path TEXT NOT NULL,
  mime_type TEXT,
  size INTEGER,
  mtime INTEGER,
  file_hash TEXT,
  duration_seconds REAL,
  parse_status TEXT DEFAULT 'unknown',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

`parse_status`：

```text
unknown
not_required
pending
parsed
failed
```

---

### 19.2 artifacts

```sql
CREATE TABLE artifacts (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  absolute_path TEXT NOT NULL,
  file_hash TEXT,
  mtime INTEGER,
  source TEXT,
  generator TEXT,
  model TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

`kind`：

```text
transcript
summary
note
parsed
meta
```

`source`：

```text
app
cli
external
```

`status`：

```text
active
stale
ambiguous
orphan
```

---

### 19.3 tasks

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  asset_id TEXT,
  type TEXT NOT NULL,
  status TEXT NOT NULL,
  command TEXT,
  params_json TEXT,
  output_path TEXT,
  error TEXT,
  pid INTEGER,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT
);
```

---

### 19.4 chunks

见全文索引部分。

---

### 19.5 embedding_cache

```sql
CREATE TABLE embedding_cache (
  content_hash TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  vector BLOB NOT NULL,
  dimension INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

---

## 20. 配置设计

配置文件：

```text
.knowledge/config.toml
```

示例：

```toml
[app]
host = "127.0.0.1"
port = 8765
open_browser = true
log_level = "INFO"

[library]
watch_enabled = false
scan_on_startup = true
ignore = [
  ".knowledge",
  ".git",
  "__pycache__",
  "node_modules",
  ".venv",
  "venv",
  "$RECYCLE.BIN",
  "System Volume Information"
]

[task]
max_workers = 1
task_timeout_seconds = 7200

[cli]
transcribe_command = 'mytool transcribe "{input}" --output "{output}"'

[parse]
# provider 只管 pdf/office；.epub 固定路由到内置本地解析器（无需 token）
enabled = false
provider = "mineru"

[parse.mineru]
base_url = "https://mineru.net"
token_env = "MINERU_API_TOKEN"
model_version = "vlm"
timeout_seconds = 1800
poll_interval_seconds = 10

[llm.summary]
enabled = true
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o-mini"
temperature = 0.2
max_tokens = 2000
timeout = 180
max_input_chars = 24000
chunk_chars = 6000

[embedding]
enabled = true
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "text-embedding-3-small"
dimension = 1536
batch_size = 32
timeout = 120

[index]
chunk_max_chars = 800
chunk_overlap = 100
rebuild_batch_size = 100
```

说明：

```text
api_key_env 表示密钥名称，应用按「环境变量 → .knowledge/secrets.toml → config.toml 明文（不推荐）」顺序读取。
也可以支持 api_key，但不推荐。
```

---

### 20.2 UI 与配置的交互原则（File as Source of Truth）

坚守“不把数据锁进私有数据库”的原则，**严禁将配置持久化到 SQLite**。

1. **读写链路**：`UI 表单保存` -> `后端校验 Dict` -> `序列化覆盖写入 .knowledge/config.toml` -> `触发热重载内存 State`。
2. **渐进式部分支持**：
   - **UI 表单层（高频、易错项）**：基础开关（enabled）、连接参数（base_url, model）、性能切片参数（batch_size, chunk_chars）。
   - **极客直编层（低频、复杂项）**：CLI 转录命令数组、底层超时控制。UI 仅做只读展示，并提供 `[在编辑器中打开]` 按钮调用系统默认编辑器。
3. **环境变量安全底线**：UI **绝不**提供明文输入 API Key 的输入框，防止密钥被意外提交或截屏泄露。

---

## 21. 技术架构

### 21.1 总体架构

```text
浏览器
  ↓
NiceGUI UI
  ↓
FastAPI / Service Layer
  ↓
SQLite / LanceDB / File System
  ↓
Task Worker
  ↓
CLI Runner / OpenAI Compatible API
```

---

### 21.2 模块划分

```text
app/
├── main.py
├── config.py
├── dependencies.py
│
├── domain/
│   ├── models.py
│   ├── enums.py
│   └── rules.py
│
├── services/
│   ├── library_service.py
│   ├── scanner_service.py
│   ├── artifact_service.py
│   ├── sync_service.py
│   ├── task_service.py
│   ├── transcription_service.py
│   ├── summarization_service.py
│   ├── parse_service.py
│   ├── parsers/
│   │   ├── base.py
│   │   ├── mineru_parser.py
│   │   └── epub_parser.py
│   ├── note_service.py
│   ├── search_service.py
│   ├── fts_service.py
│   ├── vector_service.py
│   ├── embedding_service.py
│   ├── llm_client.py
│   └── cli_runner.py
│
├── repositories/
│   ├── sqlite_repository.py
│   ├── asset_repository.py
│   ├── artifact_repository.py
│   ├── task_repository.py
│   ├── chunk_repository.py
│   └── lancedb_repository.py
│
├── api/
│   ├── router.py
│   ├── library.py
│   ├── assets.py
│   ├── tasks.py
│   ├── search.py
│   └── settings.py
│
├── ui/
│   ├── layout.py
│   ├── pages/
│   │   ├── home.py
│   │   ├── assets.py
│   │   ├── asset_detail.py
│   │   ├── search.py
│   │   ├── tasks.py
│   │   └── settings.py
│   └── components/
│       ├── asset_table.py
│       ├── search_box.py
│       ├── task_status.py
│       ├── markdown_viewer.py
│       └── status_badge.py
│
└── workers/
    └── task_worker.py
```

---

## 22. UI 页面设计

### 22.1 首页 / 知识库选择页

功能：

```text
打开知识库
新建知识库
显示最近知识库，P1
```

第一阶段可以简化为：

```text
输入/选择本地目录
打开
```

---

### 22.2 资产列表页

顶部：

```text
搜索框
类型过滤
目录过滤
刷新按钮
新建/打开库
```

主体：

```text
资产表格
```

每行操作：

```text
详情
打开文件
打开目录
生成转录
生成总结
```

状态徽章：

```text
已转录
未转录
已总结
未总结
有笔记
无笔记
歧义文件
未解析
```

---

### 22.3 资产详情页

顶部：

```text
标题
类型
路径
状态
操作按钮
```

Tabs：

```text
概览
转录
总结
笔记
文件信息
任务记录
```

音频/视频概览：

```text
播放器
```

转录 tab：

```text
只读 Markdown / 文本预览
```

总结 tab：

```text
Markdown 预览
生成总结按钮
```

笔记 tab：

```text
Markdown 只读预览
外部编辑器打开按钮
```

文件信息 tab：

```text
路径
大小
mtime
hash，可选
关联 artifacts
```

任务记录 tab：

```text
该资产相关任务
```

---

### 22.4 搜索页

```text
搜索框
模式切换：文件名 / 全文 / 语义
过滤器：类型、来源
结果列表
```

结果项：

```text
资产标题
相对路径
命中来源
命中片段
打开详情
```

---

### 22.5 任务中心页

```text
任务列表
状态过滤
重试
取消，P1
查看错误
打开输出文件
```

---

### 22.6 设置页（Config UI）

设置页采用**渐进式分层设计**，作为 TOML 的可视化编辑器：

1. **高频表单区（UI 强管控）**：
   - **基础开关**：Toggle 开关控制 LLM / Embedding 启用状态。
   - **连接参数**：Input 框输入 `base_url`，支持手动输入或下拉选择 `model`。
   - **性能参数**：Number Input 限制 Min/Max（如 `chunk_chars`）。

2. **极客直编区（UI 弱管控）**：
   - 针对 `[cli]` 命令模板等复杂配置，UI 仅只读展示，并提供 `[在编辑器中打开]` 按钮，直接调用系统默认文本编辑器打开 `config.toml`。

3. **环境变量状态指示（Env Inspector）**：
   - 在 `api_key_env` 字段旁显示状态灯。
   - 🟢 **就绪**：已从进程环境变量或 `.knowledge/secrets.toml` 读取到该密钥。
   - 🔴 **缺失**：未找到密钥，点击弹出“如何配置环境变量或 secrets.toml”的指引。

4. **连通性测试（Test Connection）**：
   - 在 LLM / Embedding 卡片提供 `[测试 API]` 按钮。
   - 后端结合表单数据与系统环境变量，发送极短 Ping 请求，直接在 UI 弹窗返回 HTTP 状态码及连通结果。

5. **危险操作拦截**：
   - 当用户修改 `dimension`（向量维度）或 `embedding.model` 时，触发阻断性警告：“修改维度 / 模型将导致现有向量索引失效，是否确认保存并清空当前知识库的向量数据？”

---

## 23. API 设计

虽然第一阶段 UI 使用 NiceGUI，但为了长期维护，建议提前定义 API。

---

### 23.1 Library API

```text
POST /api/library/open
POST /api/library/scan
GET  /api/library/status
```

---

### 23.2 Assets API

```text
GET /api/assets
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/artifacts
POST /api/assets/{asset_id}/transcribe
POST /api/assets/{asset_id}/summarize
POST /api/assets/{asset_id}/reindex
```

---

### 23.3 Search API

```text
GET /api/search?q=keyword&mode=filename
GET /api/search?q=keyword&mode=fulltext
GET /api/search?q=keyword&mode=vector
```

---

### 23.4 Tasks API

```text
GET /api/tasks
GET /api/tasks/{task_id}
POST /api/tasks/{task_id}/cancel
POST /api/tasks/{task_id}/retry
```

---

### 23.5 Settings API

```text
GET  /api/settings
PUT  /api/settings
POST /api/settings/test-connection
POST /api/index/rebuild-fts
POST /api/index/rebuild-vector
```

---

## 24. 任务系统设计

### 24.1 任务队列

第一阶段使用简单本地任务队列：

```text
SQLite tasks 表
+
后台 worker
```

默认：

```text
max_workers = 1
```

避免多个转录任务同时占用资源。

---

### 24.2 任务执行

CLI 类任务：

```text
asyncio.create_subprocess_exec
```

Windows 注意：

```text
不要使用 shell=True
命令解析为 list
路径使用绝对路径
```

API 类任务：

```text
httpx AsyncClient
```

---

### 24.3 超时

默认任务超时：

```text
7200 秒
```

可配置。

总结 API 单次请求超时：

```text
120 - 180 秒
```

---

### 24.4 错误处理

任务失败时记录：

```text
error message
stdout/stderr 摘要
API response status
API error body 摘要
```

UI 显示友好提示：

```text
转录失败，请查看任务详情
总结失败：API 超时
向量索引失败：embedding 配置无效
```

---

## 25. Windows 特别注意事项

### 25.1 路径

使用：

```python
pathlib.Path
```

避免手动拼接字符串。

---

### 25.2 长路径

Windows 可能存在长路径问题。

建议：

```text
知识库目录不要过深
文件路径过长时记录错误
```

---

### 25.3 编码

文本文件默认尝试：

```text
utf-8
utf-8-sig
gbk，仅作为 fallback
```

转录 txt 建议要求 CLI 输出 UTF-8。

---

### 25.4 命令执行

命令模板不要直接 `shell=True`。

建议：

```text
解析命令模板为 argv list
替换 {input} / {output}
使用 subprocess/exec 调用
```

---

## 26. 隐私与安全

### 26.1 本地服务

```text
只监听 127.0.0.1
```

---

### 26.2 API Key

优先通过环境变量或知识库目录下的本地密钥文件 `.knowledge/secrets.toml` 提供（`api_key_env` 指向密钥名称，不写真实密钥）：

```text
OPENAI_API_KEY
```

本地密钥文件 `.knowledge/secrets.toml` 示例：

```toml
[keys]
OPENAI_API_KEY = "sk-xxx"
```

配置中只写密钥名称：

```toml
api_key_env = "OPENAI_API_KEY"
```

如果用户坚持写入配置文件，需要提示风险。

---

### 26.3 远程 API 提示

当调用总结或 embedding API 时，应提示：

```text
部分内容将发送到配置的 API 服务
```

如果用户关闭远程 API：

```text
总结不可用
向量搜索不可用
本地全文搜索仍可用
```

---

## 27. 性能目标

以下为第一阶段目标。

### 27.1 扫描

```text
1,000 文件：全量扫描 < 5 秒
10,000 文件：全量扫描 < 30 秒
手动增量刷新 < 3 秒，小量变化
```

---

### 27.2 搜索

```text
文件名搜索 < 0.5 秒
全文搜索 < 1 秒
向量搜索 < 2 秒，50,000 chunks 内
```

向量搜索依赖 embedding API 查询延迟。

---

### 27.3 UI

```text
页面切换 < 1 秒
列表页加载 < 1 秒
详情页加载 < 1 秒，不含大文本渲染
```

---

## 28. 里程碑计划

### M0：项目骨架

目标：

```text
FastAPI + NiceGUI 启动
配置加载
日志初始化
首页可访问
```

完成标志：

```text
python -m app.main 可运行
浏览器打开 127.0.0.1:8765
```

---

### M1：知识库与扫描

目标：

```text
选择目录
创建 .knowledge
初始化 SQLite
扫描文件
展示资产列表
```

完成标志：

```text
能显示音频、视频、文档列表
能手动刷新
能打开文件位置
```

---

### M2：派生文件识别

目标：

```text
识别 transcript / summary / note
显示资产状态
处理歧义文件
```

完成标志：

```text
已有 episode.mp3 + episode.txt 时显示已转录
已有 summary.md / notes.md 时显示状态
```

---

### M3：转录任务

目标：

```text
点击生成转录
调用 CLI
任务状态
识别输出 txt
建立索引
```

完成标志：

```text
可通过 UI 生成转录
CLI 失败会显示错误
外部 CLI 生成后刷新可识别
```

---

### M4：全文搜索

目标：

```text
建立 chunks
建立 FTS5
文件名搜索
全文搜索
```

完成标志：

```text
可以搜索转录、总结、笔记、md/txt 内容
```

---

### M5：Embedding 与 LanceDB 向量搜索

目标：

```text
配置 OpenAI compatible embedding
chunk embedding
LanceDB 写入
向量搜索
embedding cache
```

完成标志：

```text
语义搜索可用
重复 chunk 不重复调用 API
模型变化可重建索引
```

---

### M6：AI 总结

目标：

```text
配置 OpenAI compatible LLM
基于转录/文本生成总结
长文本分段总结
写入 summary.md
任务状态
覆盖备份
```

完成标志：

```text
音频有转录后可生成总结
已有总结可提示覆盖
总结进入搜索索引
```

---

### M7：设置、任务中心与索引重建

目标：

```text
实现设置页的“渐进式 UI 表单化”
环境变量状态检测
API 连通性测试
任务中心
支持 FTS 和 LanceDB 索引重建
```

完成标志：

```text
可通过 UI 表单修改核心 API 配置并成功写回 TOML
环境变量缺失时 UI 有明确提示
API 测试功能可用
修改向量维度时能触发重建警告
```

---

### M8：体验优化

目标：

```text
状态徽章
搜索高亮
大文本分页/折叠
错误提示优化
Windows 路径兼容性优化
```

完成标志（已全部完成）：

```text
状态徽章 / 搜索高亮 / 大文本折叠 / 错误提示 / 排序分页 / 统一导航 均已落地
新增「最近打开的 5 个知识库」（首页快捷切换，JSON 持久化）
新增「向量索引状态卡片」（设置页：健康状态 / 模型 / 维度 / 覆盖度 / 最后重建，支持全量重建与清空缓存）
```

---

### M9：文档解析接入（MinerU）

目标：

```text
解析器 provider 抽象（submit / poll / fetch 三阶段 + 注册表）
MinerU 精准解析 API v4：批量上传接口提交本地文件（batch-of-1）
任务粒度一资产一任务，batch_id 持久化，应用重启恢复轮询
产物 {stem}.parsed.md（zip 留档 .knowledge/backups/），自动进入索引
白名单文档解析后 AI 总结输入切换为 parsed.md
设置页解析配置卡（token_env 红绿灯 / 免额度测试 API）
```

完成标志：

```text
pdf / office 白名单文档可在详情页发起解析，任务中心可查进度与重试
解析产物进入全文索引与搜索；已解析文档可生成总结
失败原因（err_msg / 超时 / token 缺失 / 200MB 超限）中文可读
明文 token 绝不出现在 UI 与 TOML
```

---

### M10：EPUB 内容索引（内置本地解析器）

目标：

```text
内置 EpubParser（标准库 only：zipfile + ElementTree + html.parser，零新增依赖）
接口扩展：DocumentParser 增加 to_markdown；按扩展名路由（.epub 固定本地）
epub = zip 容器：container.xml → OPF manifest/spine → XHTML 按阅读顺序转 markdown
本地解析形态：submit=结构校验、poll=查源文件、fetch=现算（无状态，重启重算即恢复）
DRM（encryption.xml）与坏 zip 明确报错；200MB 上限只属于 MinerU，本地不设限
.epub 并入可解析白名单与总结输入切换；UI 文案区分本地（秒级）/远端（分钟级）
```

完成标志：

```text
.epub 资产可在详情页发起解析（无需 MinerU token），数秒完成任务成功
{stem}.parsed.md 生成并进入全文/向量索引；AI 总结输入为解析结果
覆盖重解析旧结果自动备份（.bak.md）；epub 不产生 zip 留档
DRM / 损坏 epub 失败原因中文可读，任务可重试
```

---

### M11：sidecar 目录 .kb

目标：

```text
识别 <原始文件名>.kb/ sidecar 目录：内部固定文件名映射 kind，按目录名
（含扩展名）精确绑定资产，天然无歧义；目录内容不产生资产记录
写入跟随现状（opt-in）：资产旁已存在 .kb/ 目录时，总结 / 解析产物写入
其中（无 stem 前缀原名）；否则维持平铺，旧库行为零变化
转录产物维持平铺；{output} 变量预留进命令模板替换，产物查找候选含 .kb 位置
不做归集工具：旧平铺产物永久识别，手动移动 + 刷新即完成迁移
```

完成标志：

```text
手动创建 .kb 目录放入 summary.md / transcript.txt 等文件，刷新后精确绑定且
不产生多余资产；同 stem 的 mp3 / mp4 各自 .kb 目录互不干扰
存在 .kb 目录的资产：新生成的总结 / 解析写入目录内；无目录资产维持平铺
.kb 内产物进入全文 / 向量索引与搜索；AI 总结输入可读取 .kb 内转录 / 解析
无 .kb 目录的库，转录 / 总结 / 解析行为与之前完全一致
```

---

## 29. 验收标准

### 29.1 知识库

验收：

```text
可以选择 Windows 目录作为知识库
自动创建 .knowledge
可以初始化数据库和 LanceDB 目录
删除 .knowledge 后重新扫描可恢复 Asset/Artifact 关系
```

---

### 29.2 扫描

验收：

```text
放入 mp3 / mp4 / md / txt / pdf 后，手动刷新能显示
pdf 显示为未解析
md/txt 可进入全文索引
删除文件后手动刷新，记录移除
```

---

### 29.3 转录

验收：

```text
已有 episode.mp3 + episode.txt 时，显示已转录
点击生成转录可调用 mytool
支持输出到同名 txt
外部 CLI 生成 txt 后，手动刷新能识别
转录文本可全文搜索
```

---

### 29.4 总结

验收：

```text
没有转录的音视频不能生成总结
有转录的音视频可以调用 API 生成 summary.md
summary.md 可预览
summary.md 可进入全文搜索和向量搜索
已有 summary.md 时覆盖前提示并备份
```

---

### 29.5 笔记

验收：

```text
notes.md 可识别
详情页可只读预览
可用外部编辑器打开
外部修改后手动刷新能重新索引
AI 总结不会覆盖 notes.md
```

---

### 29.6 搜索

验收：

```text
文件名搜索能命中
转录内容关键词能全文命中
语义相近查询能通过 LanceDB 命中
搜索结果能跳转到资产详情
```

---

### 29.7 配置

验收：

```text
可通过 UI 表单修改 LLM / Embedding 的 base_url、model、分块参数，保存后 .knowledge/config.toml 文件内容正确更新
高级 CLI 配置可通过“在编辑器中打开”按钮直接编辑
界面能正确检测密钥来源（环境变量或 secrets.toml）是否存在，并给出红绿灯提示
点击“测试 API”能正确返回连通成功或 401 / 404 等错误信息
在 UI 中修改 Embedding 维度并保存时，能弹出警告提示需要重建向量索引
绝不在 UI 界面和 TOML 文件中出现明文的 API Key
```

---

### 29.8 最近打开的 5 个知识库

验收：

```text
首页展示最近打开的 5 个知识库，点击可直接打开
打开新库后自动记录，去重并置顶，最多保留 5 条
已删除/不存在的目录在展示时自动剔除
```

### 29.9 向量索引状态卡片

验收：

```text
设置页展示向量索引健康状态徽章（无库/无索引/模型不符/不一致/过期/正常）
展示向量总数、磁盘占用、缓存条目、模型、维度、覆盖度、最后重建时间
「全量重建」调用 Embedding API 重建并写入最后重建时间；「清空缓存」清空 embedding_cache
重建或清空后统计自动刷新
```

### 29.10 文档解析（m9 起，m10 扩展 epub）

验收：

```text
pdf / office 白名单文档可在详情页发起解析，任务中心可查进度
解析成功后 {stem}.parsed.md 出现在源文件旁，zip 留档 .knowledge/backups/
解析产物自动进入全文索引，搜索可命中
已解析文档可生成 AI 总结（输入为 parsed.md）
重复解析有覆盖确认，旧产物自动备份
失败（err_msg / 超时 / token 缺失 / 200MB 超限）在任务中心或提交时给出中文原因
应用重启后未完结的解析任务恢复轮询，不产生孤儿任务
设置页可编辑解析配置，token 来源红绿灯与测试 API 可用（不消耗额度）
明文 token 绝不出现在 UI 与 TOML 中
```

m10 增补（epub）：

```text
.epub 可在详情页发起解析（无需 MinerU token），本地解析数秒完成
{stem}.parsed.md 进入索引与搜索；AI 总结输入为解析结果
epub 不产生 zip 留档；覆盖重解析旧结果备份为 .bak.md
DRM（加密书）与损坏 epub 给出中文失败原因，任务可重试
```

---

### 29.11 sidecar 目录（m11）

验收：

```text
手动创建 episode-001.mp3.kb\ 并放入 summary.md / transcript.txt，手动刷新后
绑定到 episode-001.mp3（无歧义标记），且不产生多余资产记录
资产旁存在 .kb\ 目录时，生成的总结 / 解析产物写入目录内（原名，无 stem 前缀）；
无目录的资产行为不变（平铺）
.kb 内产物进入全文索引与搜索；AI 总结输入可读取 .kb 内转录 / 解析结果
资产删除后 .kb 目录内容不再绑定（孤儿）；恢复文件名后刷新重新绑定
覆盖重解析 / 重总结的备份留档命名基于资产名，不因写入位置改变
```

---

## 30. 风险与应对

### 30.1 API 成本

风险：

```text
长播客总结和大库 embedding 会消耗 API token
```

应对：

```text
embedding cache
总结前提示
重建向量前提示预计规模
可关闭远程 API
```

---

### 30.2 长文本总结失败

风险：

```text
2 小时播客转录很长，API 可能失败
```

应对：

```text
分段摘要
合并摘要
失败降级截断
任务日志记录
```

---

### 30.3 Embedding 模型变化

风险：

```text
模型或维度变化导致旧向量不可用
```

应对：

```text
记录 embedding_model 和 dimension
检测维度不匹配
提示重建 LanceDB
```

---

### 30.4 同名文件歧义

风险：

```text
同 stem 多个媒体文件导致 txt 无法绑定
```

应对：

```text
标记 ambiguous
UI 提示
后续支持 sidecar 目录
```

---

### 30.5 Windows 路径和编码

风险：

```text
中文路径、空格路径、长路径、GBK 编码
```

应对：

```text
pathlib
subprocess argv
UTF-8 优先
错误日志记录具体路径
```

---

## 31. 后续阶段规划

第一阶段（M0-M8）完成后，后续阶段按顺序推进。文档解析已由 M9（MinerU）、
EPUB 索引已由 M10（内置本地解析器）、sidecar 目录已由 M11（跟随现状策略）
完成，剩余：

```text
1. transcript JSON segments
2. 音频字幕级跳转
3. TTS 模块接入
4. 混合搜索排序
5. 标签系统
6. 收藏与稍后处理
7. 批量任务
```

### 待实现（暂缓）

- watchdog 文件监听自动同步：当前使用场景不强需求，暂缓，不排入上述顺序；配置模板已预留 `watch_enabled` 开关（默认 false），需要时再实现。
- 应用内笔记编辑：长时间内不做，移出任务顺序；笔记继续走「外部编辑器打开 + 手动刷新重新索引」（§14.4），需要时再实现。

---

## 32. 第一阶段开发任务拆解

下面是可以直接开始的任务列表。

---

### 32.1 后端基础

```text
1. 创建项目结构
2. 加载 config.toml
3. 初始化日志
4. 初始化 FastAPI + NiceGUI
5. 提供本地服务，只监听 127.0.0.1
```

---

### 32.2 数据库

```text
1. 初始化 SQLite
2. 创建 assets 表
3. 创建 artifacts 表
4. 创建 tasks 表
5. 创建 chunks 表
6. 创建 FTS5 表
7. 创建 embedding cache 表
```

---

### 32.3 库管理

```text
1. 打开目录
2. 创建 .knowledge
3. 初始化配置
4. 获取库状态
5. 手动扫描入口
```

---

### 32.4 扫描器

```text
1. 遍历目录
2. 识别音频/视频/文档
3. 识别派生文件
4. 写入 assets/artifacts
5. 删除已失效记录
6. 处理歧义 artifact
```

---

### 32.5 CLI Runner

```text
1. 解析命令模板
2. 替换 {input}/{output}
3. 启动子进程
4. 捕获 stdout/stderr
5. 超时处理
6. 返回结果
```

---

### 32.6 转录任务

```text
1. 创建任务
2. 调用转录 CLI
3. 检查输出
4. 更新 artifact
5. 触发索引
```

---

### 32.7 全文索引

```text
1. 读取 txt/md/summary/notes
2. 分块
3. 写入 chunks
4. 同步 FTS5
5. 删除旧 chunks
```

---

### 32.8 LanceDB 向量索引

```text
1. 初始化 LanceDB
2. 创建 chunks 表
3. 分块
4. 计算 content_hash
5. 查询 embedding cache
6. 调用 embedding API
7. 写入 LanceDB
8. 删除旧向量
```

---

### 32.9 LLM 总结

```text
1. OpenAI compatible client
2. Prompt 模板
3. 长文本分段
4. partial summary
5. merge summary
6. 写入 summary.md
7. frontmatter 生成
8. 备份旧总结
```

---

### 32.10 UI

```text
1. 首页/打开库
2. 资产列表页
3. 资产详情页
4. 搜索页
5. 任务中心页
6. 设置页
```

---

## 33. 仍需你后续提供的配置信息

开发时不需要立刻确定，但运行前需要配置：

```text
1. OpenAI 兼容 API base_url
2. LLM model 名称
3. Embedding model 名称
4. Embedding dimension
5. API Key 环境变量名
6. mytool 是否已加入 PATH
7. mytool transcribe --output 的实际参数格式
```

例如需要确认实际命令是：

```bash
mytool transcribe input.mp3 --output output.txt
```

还是：

```bash
mytool transcribe input.mp3 -o output.txt
```

---

## 34. 最终确认版范围摘要

第一阶段将实现：

```text
Windows 本地源码运行
浏览器访问 127.0.0.1
单知识库管理
不移动、不重命名文件
扫描音频/视频/文档
同目录派生文件识别
手动刷新，不做实时监听
手动触发转录，不做自动转录
转录 CLI 调用
OpenAI 兼容 API 生成总结
OpenAI 兼容 API 生成 embedding
LanceDB 向量搜索
SQLite FTS5 全文搜索
文件名搜索
笔记只读预览和外部编辑
任务中心
配置页
索引重建
```

第一阶段不实现：

```text
文件监听
自动转录
应用内笔记编辑
PDF/DOCX 内容解析
JSON segments 字幕跳转
TTS
标签系统
混合搜索排序
sidecar 目录
打包 exe
```

---

## 35. 结论

这版 PRD 已经可以作为第一阶段开发依据。

当前最合理的开发顺序是：

```text
M0 项目骨架
→ M1 扫描和资产列表
→ M2 派生文件识别
→ M3 转录任务
→ M4 全文搜索
→ M5 LanceDB 向量搜索
→ M6 OpenAI 兼容 API 总结
→ M7 设置和任务中心
→ M8 体验优化
→ M9 文档解析接入（MinerU）
→ M10 EPUB 内容索引（内置本地解析器）
→ M11 sidecar 目录 .kb
```
