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
自动批量转录
文件监听自动更新
自动整理/移动/重命名文件
文档版本历史
总结版本对比
复杂权限管理
在应用内明文存储和输入 API Key（密钥通过环境变量或库级 .knowledge/secrets.toml 提供，不明文存储）
```

其中文档解析、sidecar 目录、转录分段视图与播放器字幕级跳转已实现
（M9-M13）；简单扁平标签已实现（M15，复杂标签体系仍不做），AI 建议
标签已实现（M16，单条建议确认入库），批量总结与批量 AI 打标已实现
（M17，见 §11.1 / §28）；文件监听、笔记编辑与 TTS 暂缓
（见 §31 待实现）。

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
parse（m9）
rebuild_fts
rebuild_vector
scan
tagging（m17，批量 AI 打标）
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
.pptx
.ppt
.xlsx
.xls
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

内容提取未实现（仅文件名搜索，parse_status 为 not_required）：
.html / .htm —— 「可选简单提取」暂缓，2026-08-23 前误标待解析，已纠正

经解析后内容索引：
.pdf / .docx / .doc —— m9 起经 MinerU 解析（见 §15）
.pptx / .ppt / .xlsx / .xls —— 经 MinerU 解析（2026-08-23 起纳入扫描，
  补齐 §15.2 白名单的扫描层缺口）
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
episode-001.analysis.<preset_id>.md
                                 AI 深度分析（m18），<preset_id> 对应
                                 .knowledge/presets/<preset_id>.md 模板
                                 （限 [a-z0-9][a-z0-9_-]*），一个资产 ×
                                 一个模板 = 一份分析
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
m12 起在详情页分段视图展示（§28 M12），m13 起时间戳可点击跳转播放器
（§28 M13）。

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
summary.md → summary、notes.md → note、parsed.md → parsed、meta.json → meta、
analysis.<preset_id>.md → analysis（m18 变长模式，preset_id 反解自文件名）；
未识别命名与隐藏文件忽略，不递归子目录
写入策略 = 跟随现状（opt-in）：资产旁已存在 .kb\ 目录时，应用生成的总结 /
解析产物写入目录内（文件名无 stem 前缀）；否则维持平铺。手动建目录，或在
详情页点「创建 .kb 派生目录」按钮即启用（只建空目录，不移动已有平铺产物）
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
标签（m15，行内徽章，最多 3 个，超出折叠 +N）
```

支持：

```text
按类型过滤：音频 / 视频 / 文档
按目录过滤
按名称排序
按修改时间排序
关键词过滤
按标签过滤（m15，多选，任一命中，可与类型/关键词叠加）
多选与批量操作（m17）：行首勾选 + 全选本页，选择集跨页/跨筛选保留；
批量总结（弹窗可选跳过已有或全部重新生成）、批量 AI 打标（建议自动
追加写库，不删除已有标签）、清除选择；批量入口只做主项目已有能力的
批量版，不含批量转录/解析
按文件夹层级浏览（m19，默认视图，「按文件夹 / 平铺」可切换）：
面包屑（祖先可点击返回）+ 子文件夹行（子树递归资产计数，点击进入，
「打开」定位资源管理器）+ 当前层直接文件表格（隐藏路径列，标题列
加宽）；文件名关键词为全库搜索——忽略当前文件夹、结果平铺带完整
路径列，清空后回到原文件夹；类型/标签筛选在浏览模式作用于当前
文件夹子树（文件夹计数同步变化）、在搜索模式作用于全库结果；
分页仅作用于文件行，排序/多选/批量行为不变
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
标签（m15，基本信息卡内徽章展示 + 多选编辑，可输入新名称；m16 起
「AI 建议标签」按钮生成建议预填编辑器，确认保存才入库）
```

操作按钮：

```text
打开文件
打开所在文件夹
生成转录
生成总结
刷新当前资产
重新索引当前资产
创建 .kb 派生目录（m11，未启用 sidecar 时显示）
```

音频/视频详情页：

```text
播放器，第一阶段可使用浏览器原生 audio/video
转录内容预览
总结内容预览
笔记内容预览
```

播放器 m13 起为详情页「播放」卡片（浏览器原生 audio/video，本地文件由
NiceGUI 自动托管流式播放；§28 M13）。

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

索引、总结与预览沿用纯文本提取（`text` 优先，回退 `segments[].text`）；m12 起
详情页对 json 转录增加分段视图（时间戳 / 说话人，§28 M12），m13 起时间戳可
点击跳转播放器（§28 M13）。

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

### 13.8 AI 深度分析（多模板分析产物，m18）

优先级：P1（m18 已实现）

定位：**总结服务快速浏览（短、泛），分析服务深度使用（长、结构化、
带时间锚点）**。总结与打标行为不变，分析不参与打标输入。

**分析模板**：`.knowledge/presets/<preset_id>.md`，frontmatter（name /
description / types，默认 audio, video）+ 正文即提示词模板（占位符
`{title}` 替换为资产标题）。开库自动生成内置「授课分析」（teaching）
与「访谈分析」（interview）模板，已存在一律不覆盖。

**产物**：一个资产 × 一个模板 = 一份分析。有 `.kb/` sidecar 目录写
`analysis.<preset_id>.md`，否则平铺 `{stem}.analysis.<preset_id>.md`；
frontmatter 记 type/preset/preset_name/source/generator/model/
created_at；覆盖前备份 `.knowledge/backups/`；扫描识别 kind=analysis，
进全文索引。

**输入**：active 的 `.transcript.json` segments 构造带时间戳文本
（`[MM:SS] 说话人: 文本`，speaker 缺失由模型推断并注明）；纯文本
转录报错引导 `-f json` 重转录。超长（> max_input_chars）按时间窗
（window_minutes）切块逐窗分析后合并，保留时间戳与模板结构。

**任务**：新任务类型 analysis，params_json 记 preset_id / preset_name；
单条（详情页「AI 分析」卡片选模板）+ 批量（列表多选，跳过已有该模板
分析 / 全部重新生成）+ 重启恢复 + 失败重试，全部复用 M17 设施。

**展示**：详情页派生 tabs「分析·{模板名}」，markdown 渲染（剥
frontmatter，超长分页）；列表「分析」徽章。v1 时间戳仅展示，点击
跳转留后续。

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
（注：.pptx/.ppt/.xlsx/.xls 于 2026-08-23 才补入扫描扩展名——m9 当时仅解析
白名单收录，扫描层不识别这类文件，属实施缺口，现已对齐。）

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
按类型过滤：audio / video / document（未实现）
按来源过滤：transcript / summary / note / document（未实现）
按标签过滤（m15 已实现）：多选，任一命中（OR），四种模式均生效
```

---

### 16.7 综合搜索

优先级：P2

m14 已实现（讨论稿 `docs/讨论/qwen-prdv1/m14-hybrid-search.md`）：

```text
全文结果 + 向量结果融合
Reciprocal Rank Fusion：score = Σ 1/(k + rank)，k=60，两路等权
chunk 级去重：同 chunk 双命中合并为一条并标注来源（全文/语义/双命中）
单路不可用（索引缺失 / Embedding 未启用或失败）时降级为另一路并提示
```

文件名搜索保持独立模式，不参与融合；不做过滤、资产级聚合、权重调参。

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
analysis
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

### 19.6 tags（m15）

```sql
CREATE TABLE tags (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);
```

标签 ID 由名称经 uuid5 稳定生成（同名重建得到同 ID）；仅存 SQLite，
扫描与索引重建不触碰本表。

### 19.7 asset_tags（m15）

```sql
CREATE TABLE asset_tags (
  asset_id TEXT NOT NULL,
  tag_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (asset_id, tag_id)
);
```

不声明外键（与 artifacts/chunks 一致），资产删除时由
`delete_missing_assets` 显式清理绑定并顺带删除零引用标签。

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
# max_workers：批量总结 / 批量 AI 打标的并发数（m17 起被消费），默认 1 串行
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
# 异步对话补全（m20，智谱系专有）：mode=async 走「提交 + 轮询」，
# poll_interval_seconds / max_wait_seconds 仅 async 生效；
# thinking = "enabled"/"disabled" 显式传 {"type":...}，留空不传（默认）
mode = "sync"
thinking = ""
poll_interval_seconds = 5
max_wait_seconds = 1800

[llm.tagging]
# AI 建议标签（m16）：详情页「AI 建议标签」生成建议，确认后保存；
# 可与总结用不同模型（打标输入短、输出小，可用更快/更便宜的模型）
enabled = false
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "gpt-4o-mini"
temperature = 0.1
max_tokens = 300
timeout = 60
max_input_chars = 4000
mode = "sync"
thinking = ""
poll_interval_seconds = 5
max_wait_seconds = 1800

[llm.analysis]
# AI 深度分析（m18）：模板驱动的分析产物（授课分析 / 访谈分析等）。
# 长输入长输出——需要长上下文模型；超过 max_input_chars 时按时间窗
# 切块逐窗分析后合并（window_minutes）；模板见 .knowledge/presets/
# 智谱异步模式（m20）max_tokens 上限 128K，思考型模型不再被截断
enabled = false
provider = "openai_compatible"
base_url = "https://api.example.com/v1"
api_key_env = "OPENAI_API_KEY"
model = "long-context-model"
temperature = 0.3
max_tokens = 6000
timeout = 600
max_input_chars = 100000
window_minutes = 15
mode = "sync"
thinking = ""
poll_interval_seconds = 5
max_wait_seconds = 1800

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
标签过滤（m15，多选，任一命中）
目录过滤
刷新按钮
新建/打开库
批量操作栏（m17）：已选 N 项 + 批量总结 + 批量打标 + 清除选择（N=0 禁用）
```

主体：

```text
资产表格（m15 起含标签列：行内徽章，最多 3 个，超出折叠 +N）
行首勾选列 + 表头「全选本页」（m17，选择集跨页/跨筛选保留）
```

每行操作：

```text
详情
打开文件
打开目录
生成转录
生成总结
生成分析（m18 选模板）
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
标签（m15 徽章展示 + 多选编辑保存；m16「AI 建议标签」生成建议预填
编辑器，确认后保存）
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
模式切换：文件名 / 全文 / 语义 / 综合（m14，默认）
过滤器：标签（m15 已实现，多选任一命中，四种模式均生效）；类型、来源（未实现）
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
   - 在 LLM 总结 / AI 打标（m16）/ Embedding / 解析卡片提供 `[测试 API]` 按钮。
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
GET /api/assets/{asset_id}（m15 起响应含 tags）
GET /api/assets/{asset_id}/artifacts
POST /api/assets/{asset_id}/transcribe
POST /api/assets/{asset_id}/summarize
POST /api/assets/{asset_id}/reindex
POST /api/assets/{asset_id}/sidecar-dir（m11，创建 .kb 派生目录）
PUT /api/assets/{asset_id}/tags（m15，整体替换：缺失自动创建、零引用自动清理）
GET /api/tags（m15，全部标签 + 使用数）
POST /api/assets/{asset_id}/suggest-tags（m16，AI 建议标签：只返回建议不写库）
POST /api/assets/batch-summarize（m17，批量总结：body {asset_ids, overwrite}，
  逐资产预检建任务，不合规项 skipped 返回原因）
POST /api/assets/batch-tag（m17，批量 AI 打标：body {asset_ids}，建议清洗后
  自动追加写库，不删除已有标签）
GET /api/analysis-presets（m18，分析模板列表）
POST /api/assets/{asset_id}/analyze（m18，深度分析：body {preset_id}）
POST /api/assets/batch-analyze（m18，批量分析：body {asset_ids,
  preset_id, overwrite}，逐资产预检建任务，不合规项 skipped 返回原因）
```

---

### 23.3 Search API

```text
GET /api/search?q=keyword&mode=filename
GET /api/search?q=keyword&mode=fulltext
GET /api/search?q=keyword&mode=vector
GET /api/search?q=keyword&mode=hybrid（m14，全文+向量 RRF 融合）
GET /api/search?q=…&tag=AI&tag=播客（m15，可重复 tag 参数，多选 OR，四种模式均生效）
```

hybrid 响应额外携带 `degraded_reason` 字段：某一路不可用降级时为原因
文本，两路都参与时为 null。

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
POST /api/settings/test-connection（kind：llm / llm_tagging（m16）/ embedding）
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

避免多个转录任务同时占用资源。m17 起该配置被批量总结 / 批量 AI 打标
消费（batch_runner：≤1 串行逐条，>1 线程池并发；单条入口与重启恢复
同经此路径，in-flight 集合防同任务重复执行）。

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

### M12：transcript JSON segments（结构化转录分段视图）

目标：

```text
判定统一：文件名 transcript.json（sidecar 固定名）或后缀 .transcript.json
（平铺）均按 QVoice JSON 转录处理——修复 m11 遗留的 sidecar 识别缺口
（索引 / 向量 / 总结输入此前读入原始 JSON、详情页无预览）
utils 新增 load_transcript_segments：归一化 segments[{start,end,text,speaker}]
与 duration / language（缺失项安全降级），按需解析不入库（文件即事实源）
详情页 json 转录 tab 分段视图：[MM:SS] 说话人 文本 每段一行，100 段/页
分页，信息行显示段数 / 时长 / 语言；segments 缺失或解析失败回退纯文本预览
txt 转录、索引分块策略、搜索行为不变；不做播放器与点击跳转（M13）
```

完成标志：

```text
json 转录（平铺与 .kb 内）详情页显示时间戳 / 说话人分段视图，可翻页浏览
.kb 内 json 转录进入索引 / 总结的是提取文本而非 JSON 原文（重建索引后生效）
txt 转录预览行为与之前完全一致；异常 JSON 不白屏
```

---

### M13：音频/视频播放器与字幕级跳转

目标：

```text
详情页新增「播放」卡片（仅音频/视频）：浏览器原生 ui.audio / ui.video，
本地文件由 NiceGUI 自动托管（HTTP Range 流式，可拖动进度条）；源文件缺失
降级为明确提示，不白屏
json 转录分段视图时间戳可点击：跳转播放器到该段时间并自动播放（音频与
视频一致）；无播放器或段 start 缺失时时间戳保持纯文本（m12 行为）
不做反向同步（播放中高亮/滚动当前段）、倍速、字幕文件加载；API / 服务层
零改动
```

完成标志：

```text
音频与视频详情页均可原生播放并拖动进度条；点击分段时间戳跳转播放生效
翻页后点击仍有效；txt 转录 / 文档资产 / 源文件缺失路径行为与之前一致
索引 / 搜索 / 总结与其余页面行为不变
```

---

### M14：混合搜索排序（全文 + 向量 RRF 融合）

目标：

```text
搜索服务新增综合模式：全文 + 向量两路各取 top 50，RRF 融合
（score = Σ 1/(60 + rank)，两路等权），chunk 级去重，双命中条目
合并并标注来源（全文/语义/双命中）
单路不可用（全文索引缺失 / Embedding 未启用或调用失败）时降级为
另一路并提示，不报错
搜索页「综合搜索」为主按钮（回车默认触发）；REST search 端点 mode
增加 hybrid，响应附 degraded_reason
文件名搜索保持独立模式；不做过滤、资产级聚合、权重调参、分页
```

完成标志：

```text
同时命中两路的查询，双命中条目排前且带来源徽章与 rrf_score
停用 Embedding 后综合搜索仍返回全文结果并给出降级提示
文件名 / 全文 / 语义三模式行为与展示不变
```

---

### M15：标签系统（手动打标 + 筛选）

目标：

```text
标签数据模型：tags / asset_tags 两张表（仅 SQLite，随 .knowledge 可删重建，
属已知限制；扫描与索引重建不触碰标签表）
详情页手动打标：徽章展示 + 多选编辑（可输入新名称），PUT 整体替换；
新标签自动创建，零引用标签自动删除
资产列表：标签列（行内徽章，最多 3 个，超出折叠 +N）+ 多选标签筛选
（任一命中），可与类型 / 文件名筛选叠加
四种搜索模式（文件名 / 全文 / 语义 / 综合）均支持标签过滤（OR）；
向量路过滤发生在 top-K 回表之后，结果可能少于 limit（预期行为）
标签名约束：非空、不含半角逗号、单个 ≤30 字符、单资产 ≤20 个
REST：GET /api/tags、PUT /api/assets/{id}/tags、GET /api/search 增 tag 参数
纯手动打标，不做 AI 建议、层级、颜色与标签管理页
```

完成标志：

```text
详情页打标保存后徽章即时刷新，刷新页面仍在
列表与搜索的标签筛选均为多选 OR，可与既有筛选叠加
删除已打标资产对应文件后扫描，绑定一并清理，零引用标签从筛选下拉消失
未打标资产与未选标签时，既有列表 / 搜索行为完全不变
```

---

### M16：AI 建议标签（LLM 打标，M15 增强）

目标：

```text
独立 [llm.tagging] 配置节（enabled 默认 false；temperature=0.1、
max_tokens=300、timeout=60、输入截断 4000 字符），可与总结用不同模型
详情页「AI 建议标签」按钮：同步调 LLM（按钮禁用防重复），建议合并进
编辑器选中值（不覆盖已选、新标签补进选项），确认保存后才入库
输入 = 标题 + 内容（优先 active 总结，无则取转录/解析/原文，复用总结
来源选择）+ 全库已有标签（引导复用）；输出 = JSON 字符串数组，宽容解析
（剥 fence、截取 [...]），失败中文报错
建议宽松清洗：丢空 / 含半角逗号 / >30 字符，去重保序，截到单资产上限
REST：POST /api/assets/{id}/suggest-tags；test-connection 增 llm_tagging
不做批量打标与总结后自动建议（留待「批量任务」里程碑），AI 结果不写库
```

完成标志：

```text
点「AI 建议标签」后建议预填编辑器且标签行不变（未写库），保存后徽章刷新
未启用时给中文提示；音频无转录沿用「请先生成转录」报错
LLM 返回非 JSON / 含逗号或超长标签时被拒绝或丢弃，不白屏
M15 手动打标与 LLM 总结行为完全不变
```

---

### M17：批量任务（批量总结 + 批量 AI 打标）

目标：

```text
资产列表多选（行首勾选 + 全选本页，选择集跨页/跨筛选保留）+ 批量操作栏
批量总结：弹窗统计已有总结数量，可选「跳过已有」或「全部重新生成
（旧文件自动备份到 .knowledge/backups/）」；逐资产预检，无转录/解析等
不合规项跳过并返回原因
批量 AI 打标：建议清洗后自动追加写库（不删除已有标签），写入内容记入
任务 params_json 的 applied 字段可审计；清洗后为空 → 任务 failed
任务形态 = 每资产一条任务（复用 tasks 表 / 任务中心 / 失败重试 /
同资产同类型去重）；新任务类型 tagging；单条总结与 M16 单条建议不变
并发 = 消费 [task] max_workers（默认 1 串行；串行使先打的标签进入后续
prompt 的已有标签列表，引导收敛）
重启恢复 = open_library 时 pending/running 的 summarization/tagging 任务
重新拉起消费（幂等）；REST：POST /api/assets/batch-summarize、
POST /api/assets/batch-tag
```

完成标志：

```text
批量总结/打标逐资产出现在任务中心并逐个完成，失败可重试
已有标签经批量打标后保留，新标签追加，任务详情可见 applied
重启后未完结任务自动恢复；max_workers>1 时并发生效
单条总结、M16 建议标签、M15 手动打标行为完全不变
```

### M18：深度分析（多模板分析产物）

目标：

```text
新增派生产物类型 analysis：一个资产 × 一个分析模板 = 一份分析文件
（区别于总结：长输出、结构化、带时间锚点；总结/打标行为不变）
模板文件化 .knowledge/presets/<preset_id>.md：frontmatter（name/
description/types）+ 正文即提示词（{title} 占位符）；开库生成内置
授课分析 / 访谈分析两模板，已存在不覆盖——改文件即改提示词、加文件
即加新分析类型
输入带时间戳：transcript.json segments → [MM:SS] 说话人: 文本；
纯文本转录报错引导 -f json 重转录；超长按时间窗切块逐窗分析后合并
独立 [llm.analysis] 配置（长上下文模型、max_tokens 6000、
max_input_chars 100000、window_minutes 15）
任务形态复用 M17：新任务类型 analysis，单条（详情页选模板）+ 批量
（列表多选，跳过已有/全部重新生成）+ 重启恢复 + 失败重试；REST：
GET /api/analysis-presets、POST /api/assets/{id}/analyze、
POST /api/assets/batch-analyze
分析产物 markdown 渲染（详情页 tabs，剥 frontmatter），进全文索引，
列表「分析」徽章；覆盖前自动备份 .knowledge/backups/
```

完成标志：

```text
同一资产可同时持有多个模板的分析，tab 名「分析·{模板名}」
内置两模板开库自动生成，用户修改不被覆盖
分析产物带时间戳、markdown 渲染、可被全文搜索命中
批量/重试/重启恢复正常；总结与打标既有行为完全不变
```

---

### M19：资产列表按文件夹层级浏览

目标：

```text
文件管理器式导航：面包屑（祖先可点击返回）+ 子文件夹行（📁 图标 +
名称 + 子树递归资产计数徽章 + 「打开」定位资源管理器）+ 当前层
直接文件表格
「按文件夹 / 平铺」视图切换，默认按文件夹；平铺模式保持原有平铺
列表（完整路径列）
文件名关键词为全库搜索：输入即忽略当前文件夹，结果平铺并保留完整
路径列；清空关键词回到文件夹浏览（记住所在文件夹）
类型/标签筛选：浏览模式作用于当前文件夹子树（文件夹计数同步变化），
搜索模式作用于全库结果
文件夹浏览模式隐藏「路径」列（标题列加宽），平铺/搜索模式保留
数据层：relative_path 前缀匹配（escape_like 转义 %/_/\）+ 直接文件
判定（instr/substr）；list_child_folders 单条 GROUP BY 递归聚合子树
计数；不新增表/列（KISS）
分页仅作用于文件行；排序/多选/全选/批量操作行为不变；扫描后回到
根目录
```

完成标志：

```text
根目录显示顶层文件夹与根层文件，逐层进入与面包屑逐级返回正常
文件夹计数为子树全部资产数（含更深层），类型/标签筛选同步影响计数
关键词搜索跨文件夹命中并展示完整路径；清空后回到原文件夹浏览
「平铺」视图与改造前一致；含 %/_ 等特殊字符的文件夹名正常显示与进入
```

---

### M20：LLM 异步对话补全（智谱）

目标：

```text
chat_completion 按 [llm.*] 的 mode 配置分支：sync（默认，现状不变）/
async（智谱异步对话补全）；三个 LLM 功能（总结/打标/分析）独立开关
async 走「提交 + 轮询」：POST {base_url}/async/chat/completions 返回
任务 id，轮询 GET {base_url}/async-result/{id} 至 SUCCESS/FAIL
（端点从 base_url 推导，不硬编码域名，网关代理同样可用）
提交/轮询均为短请求：timeout 只约束单次 HTTP；总体截止 max_wait_seconds
（默认 1800），轮询间隔 poll_interval_seconds（默认 5）；单次轮询网络
异常或非 200 容忍至截止时间（401/403 密钥问题立即失败）
结果校验与 sync 共用：finish_reason=length 截断检查（含 reasoning_tokens
提示，异步模式 max_tokens 上限 128K 可大幅调大）+ 异步特有 finish_reason
中文报错（sensitive / network_error / model_context_window_exceeded）
提交 404/405 提示「当前提供商不支持异步对话接口，请改回 sync」，不静默降级
thinking 字段（智谱系参数）：显式配置 enabled/disabled 才附带
{"type": ...}，未配置完全不传，兼容所有 OpenAI 兼容端点
设置页 AI 服务三张卡片（总结/打标/分析）加「调用模式」「thinking」下拉，
写回 config.toml；poll/max_wait 走 config.toml 直编
不引入 provider 抽象层：真实差异仅一对端点 + 一个参数，全部提供商均
OpenAI 兼容；config 的 provider 字段 + chat_completion 唯一入口即抽象缝
```

完成标志：

```text
默认 sync 路径回归：总结/打标/分析行为不变，payload 不含 thinking
async 模式深度分析：提交→轮询→产物落盘；思考型模型配大 max_tokens 不再截断
不支持异步的提供商误开 async：报错可读并指回 sync
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

### 29.12 transcript JSON segments（m12）

验收：

```text
json 转录（平铺与 .kb 内）详情页显示分段视图：时间戳 / 说话人 / 文本，
长转录分页浏览，信息行显示段数 / 时长 / 语言
sidecar transcript.json 与平铺同待遇：预览 / 索引 / 总结输入均为提取文本
txt 转录预览行为不变；segments 缺失 / 损坏 JSON 回退纯文本或明确提示
```

---

### 29.13 播放器与字幕级跳转（m13）

验收：

```text
音频/视频详情页显示原生播放器，可播放并拖动进度条
json 转录分段视图时间戳可点击，点击后播放器跳转到该段时间并播放
无播放器或时间戳缺失时降级为纯文本；源文件缺失显示明确提示
其余页面与索引 / 搜索 / 总结行为不变
```

---

### 29.14 混合搜索（m14）

验收：

```text
综合搜索返回全文+向量 RRF 融合结果，双命中条目排前并标注来源
同 chunk 双命中合并为一条，展示 rrf_score
向量路不可用时降级为纯全文结果并给出提示，不报错
回车与主按钮均触发综合搜索；文件名/全文/语义三模式行为不变
```

---

### 29.15 标签系统（m15）

验收：

```text
详情页可查看与编辑资产标签；新标签自动创建，零引用标签自动清理
资产列表展示标签列，并支持多选标签（任一命中）筛选，可与类型/文件名叠加
四种搜索模式（文件名/全文/语义/综合）均支持按标签过滤
标签仅存 SQLite：扫描与索引重建不丢失；删除 .knowledge 目录会丢失（已知限制）
```

---

### 29.16 AI 建议标签（m16）

验收：

```text
详情页「AI 建议标签」生成建议并预填编辑器，确认保存后才入库
独立 [llm.tagging] 配置：未启用给中文提示；设置页可编辑并测试连通
建议经宽松清洗（去空/含逗号/超长/去重），不覆盖已选标签
AI 打标不写库、不产生任务与文件；M15 手动打标行为完全不变
```

---

### 29.17 批量任务（m17）

验收：

```text
资产列表可多选（跨页保留），批量总结 / 批量打标按钮在选中数 > 0 时可用
批量总结弹窗展示已有总结统计，支持「跳过已有」与「全部重新生成（自动备份）」
批量打标自动追加写入、不删除已有标签；写入内容可在任务详情审计
批量任务逐资产进入任务中心，支持失败重试与同资产去重；重启后
pending/running 任务恢复
[task] max_workers 生效（默认 1 串行）；单条总结与 M16/M15 既有行为
完全不变
```

---

### 29.18 资产列表按文件夹层级浏览（m19）

验收：

```text
「按文件夹」视图：面包屑 + 子文件夹行（子树递归计数）+ 当前层直接
文件表格（无路径列）
文件名关键词为全库搜索，结果平铺带完整路径列；清空关键词回到原
文件夹浏览
「平铺」视图与原有平铺列表一致；两视图切换记住所在文件夹
类型/标签筛选影响文件列表与文件夹计数；分页/排序/多选/批量不变
扫描后回到根目录；含 %/_ 等特殊字符的文件夹名正常
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
EPUB 索引已由 M10（内置本地解析器）、sidecar 目录已由 M11（跟随现状策略）、
transcript JSON 分段视图已由 M12（详情页分段展示 + 判定统一）、音频/视频
播放器与字幕级跳转已由 M13（原生播放器 + 分段时间戳点击跳转）、混合搜索
排序已由 M14（全文 + 向量 RRF 融合）、标签系统已由 M15（简单扁平标签：
手动打标 + 列表/搜索标签筛选；m16 增 AI 建议标签增强）、批量任务已由
M17（资产列表多选 + 批量总结 + 批量 AI 打标，复用任务系统与既有 LLM
配置）、深度分析已由 M18（多模板分析产物：presets 文件化 + 带时间戳
输入 + [llm.analysis] + 任务复用）、资产列表文件夹层级浏览已由 M19
（文件管理器式导航：面包屑 + 子文件夹递归计数 + 当前层直接文件 +
关键词全库搜索）、LLM 异步对话补全已由 M20（[llm.*] mode 切换 +
智谱提交/轮询 + thinking 显式配置）完成，剩余：

```text
1. 收藏与稍后处理
```

### 待实现（暂缓）

- watchdog 文件监听自动同步：当前使用场景不强需求，暂缓，不排入上述顺序；配置模板已预留 `watch_enabled` 开关（默认 false），需要时再实现。
- 应用内笔记编辑：长时间内不做，移出任务顺序；笔记继续走「外部编辑器打开 + 手动刷新重新索引」（§14.4），需要时再实现。
- TTS 模块接入：暂缓，移出任务顺序；朗读需求当前不强，且已有音频播放能力（M13），需要时再实现。

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
TTS
标签系统
sidecar 目录
打包 exe
```

注记：标签系统（简单扁平版 + AI 建议）已由 M15/M16 实现，PDF 内容解析
已由 M9（MinerU）实现，sidecar 目录已由 M11 实现；其余项维持不做
（DOCX 解析仍未实现）。

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
→ M12 transcript JSON segments
→ M13 音频/视频播放器与字幕级跳转
→ M14 混合搜索排序（全文 + 向量 RRF 融合）
→ M15 标签系统（手动打标 + 筛选）
→ M16 AI 建议标签（LLM 打标，M15 增强）
```
