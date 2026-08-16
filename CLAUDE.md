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
├── services/        # 业务层（library/scanner/...）
└── ui/              # NiceGUI 页面（layout.py 框架 + pages/ 各页面）
config.toml          # 应用级默认配置
docs/PRD.md          # 唯一权威 spec
```

## 测试和质量保证

- 你只需要给出测试步骤，而不自动进行测试，测试由开发人员手动进行
- 安装依赖时，你只需要给出命令，而不自动执行

## 当前进度

- [x] M0 项目骨架（2026-08-16 完成）
- [x] M1 知识库与扫描（2026-08-16 完成）
- [x] M2 派生文件识别 + 资产详情页（2026-08-16 完成）
- [x] M3 转录任务（2026-08-16 完成，QVoice CLI 集成）
- [x] M4 全文搜索（2026-08-16 完成，FTS5 + LIKE 兜底 + 文件名搜索 + 转录后自动重建索引）
- [ ] M5 LanceDB 向量搜索 - 下一步
- [ ] M6 AI 总结
- [ ] M7 设置与任务中心
- [ ] M8 体验优化

里程碑详细目标见 [docs/PRD.md](./docs/PRD.md) §28。

## 相关文档

- [docs/PRD.md](./docs/PRD.md) - 权威 spec
- [docs/README.md](./docs/README.md) - 文档索引与里程碑记录
