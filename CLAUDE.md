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
- [x] M9 文档解析接入 MinerU（2026-08-20 代码落地，验收步骤见 docs/讨论/qwen-prdv1/m9-parse.md §8）：解析器 provider 抽象（parsers/）+ 批量上传 batch-of-1 + 重启恢复轮询 + parsed.md 进索引 + PDF 总结输入切换
- [x] M10 EPUB 内容索引（2026-08-21 代码落地，脚本验证已通过，UI 验收步骤见 docs/讨论/qwen-prdv1/m10-epub.md §3）：内置本地 EpubParser（标准库 only）+ to_markdown 接口扩展 + 按扩展名路由（.epub 免 token）+ parsed.md 全链路复用
- [x] M11 sidecar 目录 .kb（2026-08-21 代码落地，验收步骤见 docs/讨论/qwen-prdv1/m11-sidecar.md §3）：<原始文件名>.kb/ 目录识别（目录名精确绑定，无歧义）+ 总结/解析跟随现状写入（有目录才归集）+ 转录平铺不变（{output} 变量预留）；后补：详情页「创建 .kb 派生目录」按钮（service + REST + UI，只建目录不移动文件）
- [x] M12 transcript JSON segments（2026-08-21 代码落地，冒烟验证见讨论稿 m12-segments.md 附录 A，UI 验收步骤见 §3）：详情页 json 转录分段视图（时间戳/说话人/100 段分页）+ 判定统一 is_transcript_json_name（修复 m11 遗留：sidecar transcript.json 此前不命中后缀判定，索引/总结输入读入原始 JSON）
- [x] M13 音频/视频播放器与字幕级跳转（2026-08-21 代码落地，UI 验收步骤见讨论稿 m13-audio-seek.md §3）：详情页「播放」卡片（原生 ui.audio/ui.video，NiceGUI 自动托管本地文件 Range 流式）+ json 转录分段时间戳点击跳转（seek + play）；源文件缺失/无播放器降级纯文本；不做反向同步，API/服务层零改动

里程碑详细目标见 [docs/PRD.md](./docs/PRD.md) §28。

## 相关文档

- [docs/PRD.md](./docs/PRD.md) - 权威 spec
- [docs/README.md](./docs/README.md) - 文档索引与里程碑记录
