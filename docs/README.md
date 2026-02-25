# QBase 项目文档

本地知识库管理系统的完整技术文档。

## 文档导航

### 架构设计
稳定的技术架构文档，描述系统整体设计。

- [系统架构](./architecture/system-architecture.md) - 整体架构设计和技术选型
- [技术栈](./architecture/tech-stack.md) - 核心技术栈说明

### 功能实现
各功能模块的实现细节和使用说明。

- [工作区管理](./features/workspace.md) - 文件夹管理和文件树导航
- [Markdown 预览](./features/markdown-preview.md) - 文档渲染功能
- [AI 助手](./features/ai-assistant.md) - LLM 对话功能

### 项目规划
版本迭代计划和里程碑。

- [项目路线图](./roadmap.md) - 版本规划和开发进度

### 实施报告
各版本完成后的实施总结。

- [v0.1 实施报告](./implementation/v0.1-complete.md) - 核心文件浏览功能
- [v0.2 实施报告](./implementation/v0.2-complete.md) - AI 助手功能
- [v0.3 实施报告](./implementation/v0.3-complete.md) - 增强功能（多会话、测试连接、多轮对话、手动刷新）

### 问题记录
Bug 修复记录和问题追踪。

- [消息 ID 重复 Bug](./bugs/2026-02-25-message-id-duplicate.md) - UUID 生成修复

## 快速链接

| 文档 | 说明 |
|------|------|
| [../README.md](../README.md) | 项目概述和快速开始 |
| [../AGENTS.md](../AGENTS.md) | AI 代理开发指南 |
| [../CLAUDE.md](../CLAUDE.md) | 开发原则和规范 |

## 文档状态标记

- ✅ 已完成
- 🔄 进行中
- 📋 已规划
- ⏳ 暂缓

## 文档维护

### 更新时机

1. **完成新功能时**：更新对应功能文档的状态
2. **完成阶段时**：更新 roadmap.md 和 README.md
3. **实施重大变更时**：创建实施报告
4. **修复 Bug 时**：创建 bugs 记录

### 命名规范

```
features/<feature-name>.md        # 功能文档
implementation/<version>-complete.md  # 实施报告
bugs/<date>-<bug-name>.md         # Bug 记录
```
