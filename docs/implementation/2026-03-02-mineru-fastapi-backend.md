# MinerU FastAPI 后端实现计划

> **For Claude:** REQUIRED SUB-SKILL: 使用 superpowers:executing-plans 逐个任务执行此计划。

**目标:** 在 backend 目录下使用 FastAPI 构建后端服务，实现 MinerU 文档解析功能。

**架构:** 
- FastAPI 作为 Web 框架
- 使用批量上传方式处理本地文件
- 轮询方式获取任务状态
- 后端代理下载解析结果并解压
- 纯内存存储任务状态（第一版）
- 前端保留 IPC 方式，新增 HTTP 客户端两者共存

**技术栈:** FastAPI + Uvicorn + Loguru + HTTPX + python-multipart + aiofiles

---

## 任务概览

### 1. 项目初始化与依赖配置
### 2. 配置管理（环境变量、API Key）
### 3. MinerU API 客户端封装
### 4. 任务状态管理（内存存储）
### 5. FastAPI 路由实现
### 6. 文件上传与下载服务
### 7. ZIP 解压与结果处理
### 8. 主应用整合

---

### Task 1: 项目依赖配置

**文件:**
- 修改: `backend/pyproject.toml`

**步骤说明:**
添加必要的依赖包：httpx（HTTP 客户端）、python-multipart（文件上传支持）、aiofiles（异步文件操作）、python-dotenv（环境变量管理）、aiozipstream 或 zipfile（ZIP 处理）

**具体操作:**

1. 更新 `pyproject.toml` 的 dependencies 部分

---

### Task 2: 配置管理模块

**文件:**
- 创建: `backend/src/config.py`
- 创建: `backend/.env.example`

**功能:**
- 管理 MinerU API Key
- 配置文件存储路径
- 任务轮询间隔配置

---

### Task 3: MinerU API 客户端封装

**文件:**
- 创建: `backend/src/mineru/client.py`

**功能:**
- 批量申请上传链接 (`POST /api/v4/file-urls/batch`)
- 文件上传 (PUT 到上传链接)
- 批量查询任务结果 (`GET /api/v4/extract-results/batch/{batch_id}`)
- 下载结果 ZIP

---

### Task 4: 任务状态管理

**文件:**
- 创建: `backend/src/mineru/task_manager.py`

**功能:**
- 内存存储任务状态（后续可扩展到数据库）
- 任务 CRUD 操作
- 异步轮询任务状态更新

---

### Task 5: Pydantic 模型定义

**文件:**
- 创建: `backend/src/models/schemas.py`

**功能:**
- 请求/响应数据模型
- 文件上传请求
- 任务状态响应
- 解析结果响应

---

### Task 6: FastAPI 路由实现

**文件:**
- 创建: `backend/src/api/mineru.py`
- 修改: `backend/main.py`

**API 端点:**
- `POST /api/mineru/parse` - 提交文档解析任务
- `GET /api/mineru/tasks/{task_id}` - 查询任务状态
- `GET /api/mineru/tasks/{task_id}/result` - 获取解析结果
- `GET /api/mineru/tasks/{task_id}/download` - 下载原始 ZIP

---

### Task 7: ZIP 解压与结果处理

**文件:**
- 创建: `backend/src/utils/zip_handler.py`

**功能:**
- 异步解压 ZIP 文件
- 提取 Markdown 内容
- 管理解压后的文件存储

---

### Task 8: 主应用整合与测试

**文件:**
- 修改: `backend/main.py`
- 创建: `backend/README.md`（可选）

**功能:**
- 整合所有路由
- 配置 CORS
- 添加健康检查端点
- 编写启动说明

---

## 执行方式

**计划已保存至 `.opencode/plans/2026-03-02-mineru-fastapi-backend.md`。两个执行选项：**

**1. Subagent-Driven (本会话)** - 我为每个任务派遣新的子代理，任务间审查，快速迭代

**2. Parallel Session (单独会话)** - 打开新会话使用 executing-plans，带检查点的批量执行

**选择哪种方式？**
