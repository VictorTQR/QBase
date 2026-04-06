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
- [文件格式支持](./features/file-format-support.md) - PDF、音视频播放
- [AI 助手](./features/ai-assistant.md) - LLM 对话功能
- [智能闪卡生成](./features/flashcard-generation.md) - 基于文档的闪卡生成
- [智能生成功能](./features/ai-generation.md) - 闪卡、思维导图、摘要生成
- [文档解析管理](./features/parse-management.md) - 文本提取、转录、向量化管理
- [搜索增强](./features/search.md) - 全文搜索、向量搜索、混合搜索
- [论文管理](./features/papers.md) - arXiv 论文搜索与本地保存

### 项目规划
版本迭代计划和里程碑。

- [项目路线图](./roadmap.md) - 版本规划和开发进度

### 实施报告
各版本完成后的实施总结。

- [v0.1 实施报告](./implementation/v0.1-complete.md) - 核心文件浏览功能
- [v0.2 实施报告](./implementation/v0.2-complete.md) - AI 助手功能
- [v0.3 实施报告](./implementation/v0.3-complete.md) - 增强功能（多会话、测试连接、多轮对话、手动刷新、搜索增强）
- [v0.4 实施报告](./implementation/v0.4-complete.md) - 文件格式增强与智能闪卡生成
- [v0.5 实施报告](./implementation/0.5-ai-generation-enhancement.md) - 智能生成功能增强
- [v0.6 实施报告](./implementation/v0.6-core-architecture-complete.md) - 智能体能力增强（核心架构）
- [v0.7 设计文档](./plans/2026-02-27-parse-manager-design.md) - 文档解析管理设计
- [v0.7 实施报告](./implementation/v0.7-text-extraction-complete.md) - 文档解析管理与文本提取
- [v0.8 实施报告](./implementation/v0.8-settings-page-complete.md) - 应用设置页面与 PDF 解析策略
- [v0.9 实施报告](./implementation/v0.9-mineru-fastapi-backend.md) - MinerU FastAPI 后端服务
- [v1.0 实施报告](./implementation/v1.0-backend-integration.md) - 后端服务集成（策略模式）
- [解析管理重构报告](./implementation/2026-03-02-parse-management-refactor.md) - 解析管理 UI 重构与增强
- [音频转录功能报告](./implementation/2026-03-02-audio-transcription.md) - 基于硅基流动 API 的音频转录功能
- [解析配置统一报告](./implementation/2026-03-03-parse-config-unification.md) - 解析配置统一重构（后端环境变量管理）
- [音频 API 统一报告](./implementation/2026-03-03-audio-api-unification.md) - 音频 API 统一重构（文件上传/本地路径/结果端点）
- [SQLite 解析存储报告](./implementation/2026-03-03-sqlite-parse-storage.md) - SQLite 解析结果存储与文件去重
- [向量搜索前端报告](./implementation/2026-03-03-vector-search-frontend.md) - 向量搜索前端实现（API 客户端、Store、搜索面板增强）
- [解析功能修复报告](./implementation/2026-03-03-parse-features-bugfixes.md) - 解析功能 Bug 修复与增强（计数错误、错误处理、音频基础设施、右键菜单等）
- [WebSocket实时更新报告](./implementation/2026-03-03-websocket-realtime-updates.md) - WebSocket 实时更新功能实现（后端管理器、前端客户端、任务状态广播）
- [v1.2 架构准备报告](./implementation/2026-04-05-architecture-prep-complete.md) - 新文件管理架构准备阶段（依赖清理、.qbase 目录、SQLite Schema 扩展、文件哈希工具）
- [v1.3 UI/UX 重塑报告](./implementation/2026-04-06-ui-ux-redesign-complete.md) - UI/UX 全面重塑（设计系统、三种布局模式、AI 上下文菜单、命令面板等）
- [论文管理功能](./features/papers.md) - arXiv 论文搜索与本地保存功能
- [搜索增强功能](./features/search.md) - 向量搜索与混合搜索增强

### 问题记录
Bug 修复记录和问题追踪。

- [消息 ID 重复 Bug](./bugs/2026-02-25-message-id-duplicate.md) - UUID 生成修复
- [音频转录接口 Windows 兼容修复](./bugs/2026-03-03-audio-transcription-windows-bugfix.md) - asyncio subprocess、编码转换等多问题修复
- [项目启动错误修复](./bugs/2026-04-06-startup-errors-fix.md) - 后端导入、Electron API、SQLAlchemy 表冲突等问题修复

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
