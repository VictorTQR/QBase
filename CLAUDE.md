# QBase 开发原则

本文档定义项目的核心开发原则和规范。

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

## 测试和质量保证

- 你只需要给出测试步骤，而不自动进行测试，测试由开发人员手动进行
- 安装依赖时，你只需要给出命令，而不自动执行
- 前端后端的测试文件分别在 `app/` 和 `backend/` 目录的合适位置

## 项目依赖管理

- 项目使用 uv 管理 Python 虚拟环境

## 文档维护

### 文档目录

项目根目录下的 `docs/` 文件夹：

```
docs/
├── README.md               # 文档入口
├── architecture/           # 架构设计（稳定层）
├── features/               # 功能实现（动态层）
├── plans/                  # 项目规划（演进层）
├── security/               # 安全规范（问题驱动层）
├── testing/                # 测试体系（策略层）
├── deployment/             # 部署运维（运维层）
├── api/                    # 接口文档（API层）
├── roadmap.md              # 项目路线图（项目层）
├── implementation/         # 实施报告（项目层）
└── bugs/                   # 问题记录（项目层）
```

### 更新文档的时机

1. **完成新功能时**：更新对应功能文档的状态
2. **完成阶段时**：更新 roadmap.md 和 README.md
3. **实施重大变更时**：创建实施报告

### 文档命名规范

```
features/<feature-name>.md           # 功能文档
plans/<plan-name>.md                 # 规划文档
implementation/<version>-complete.md # 实施报告
bugs/<date>-<bug-name>.md            # Bug 记录
```

### 状态标记

- ✅ 已完成
- 🔄 进行中
- 📋 已规划
- ⏳ 暂缓

## 相关文档

- [AGENTS.md](./AGENTS.md) - AI 代理开发指南
- [docs/README.md](./docs/README.md) - 文档入口
