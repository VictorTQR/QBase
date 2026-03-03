# 解析功能 Bug 修复与增强实施报告

**日期**: 2026-03-03  
**版本**: v1.0.x  
**状态**: ✅ 已完成

---

## 概述

本次修复主要解决了 QBase 解析功能中的多个问题，包括已索引文档计数错误、API 错误处理缺失、队列管理功能增强、音频解析基础设施完善、Sidebar 右键菜单功能修复等。

---

## 修复的问题清单

### 1. ✅ 已索引文档计数显示错误

**问题描述**: `ParseStatsView.vue` 中 `indexedFilesCount` 计算错误，因为 `indexedFiles` 是对象而非 Map，使用 `.size` 会返回 `undefined`。

**修复方案**:
```javascript
// 修复前
const indexedFilesCount = computed(() => vectorStore.indexedFiles.size)

// 修复后
const indexedFilesCount = computed(() => Object.keys(vectorStore.indexedFiles).length)
```

**修改文件**: `app/src/components/parse/ParseStatsView.vue:155`

**提交**: `7f89bab`

---

### 2. ✅ parseBackend.js 缺少错误处理

**问题描述**: `parseBackend.js` 中的所有 API 方法都没有 try-catch 错误处理，API 调用失败时没有友好的错误提示。

**修复方案**: 为所有 12 个 API 方法添加了完整的错误处理，包括：
- `checkDuplicate()`
- `parseFile()`
- `parseLocalFile()`
- `getTask()`
- `listTasks()`
- `getStats()`
- `getTaskResult()`
- `downloadResult()`
- `clearCompleted()`
- `clearAll()`
- `batchParsePending()`
- `retryFailed()`

每个方法都包含：
- try-catch 包裹
- 错误日志输出
- 友好的中文错误消息

**修改文件**: `app/src/api/parseBackend.js`

**提交**: `87618e2`

---

### 3. ✅ ParseQueueView 缺少批量操作按钮

**问题描述**: 队列管理页面只有"清除已完成"和"清空队列"按钮，缺少"批量解析"和"重试失败"按钮，用户无法在队列管理页面启动任务。

**修复方案**:
1. 添加状态变量：`isBatchParsing`、`isRetrying`
2. 添加处理函数：`handleBatchParse()`、`handleRetryFailed()`
3. 更新按钮区域，添加批量操作按钮和分隔线

**修改文件**: `app/src/components/parse/ParseQueueView.vue`

**提交**: `3ff1d27`

---

### 4. ✅ 缺少音频解析 API 文件

**问题描述**: 只有 `parseBackend.js` 和 `vectorBackend.js`，缺少统一的 `audioBackend.js` API 客户端文件。

**修复方案**: 创建完整的音频解析 API 客户端，包含：
- `transcribeUpload()` - 上传音频转录
- `transcribeLocal()` - 本地音频转录
- `transcribe()` - 向后兼容的转录接口
- `getTask()` - 获取任务状态
- `getTaskResult()` - 获取转录结果
- `listTasks()` - 列出所有任务
- `deleteTask()` - 删除任务

所有方法都包含完整的错误处理。

**新增文件**: `app/src/api/audioBackend.js`

**提交**: `691d521`

---

### 5. ✅ 缺少音频解析 Store

**问题描述**: 没有 `audio.js` store 来管理音频解析任务状态。

**修复方案**: 创建完整的音频解析状态管理 Store，包含：

**状态**:
- `tasks` - 任务列表
- `currentTask` - 当前任务
- `isLoading` - 加载状态
- `error` - 错误信息

**计算属性**:
- `tasksByStatus` - 按状态分组的任务
- `pendingTasks` / `processingTasks` / `completedTasks` / `failedTasks`

**方法**:
- `fetchTasks()` - 获取任务列表
- `fetchTask()` - 获取单个任务
- `transcribeLocalFile()` - 转录本地文件
- `transcribeUploadFile()` - 转录上传文件
- `getTaskResult()` - 获取任务结果
- `deleteTask()` - 删除任务
- `pollTaskUntilDone()` - 轮询任务直到完成

**新增文件**: `app/src/stores/audio.js`

**提交**: `1f0f294`

---

### 6. ✅ ParseSidebar 缺少音频解析导航

**问题描述**: 解析侧边栏只有"队列管理"、"已解析文档"、"解析统计"三个导航项，缺少"音频解析"入口。

**修复方案**:
1. 导入 `Microphone` 图标
2. 在 `navItems` 数组中添加音频解析导航项

**修改文件**: `app/src/components/Layout/ParseSidebar.vue`

**提交**: `4064d1f`

---

### 7. ✅ 缺少音频解析视图

**问题描述**: 没有音频解析视图组件，点击音频解析导航会找不到对应组件。

**修复方案**:
1. 创建 `AudioParseView.vue` 占位组件
2. 在 `ParseManagement.vue` 中导入和注册该组件
3. 更新 `componentMap` 添加路由映射

**新增文件**: `app/src/components/parse/AudioParseView.vue`

**修改文件**: `app/src/views/ParseManagement.vue`

**提交**: `505d4c6`

---

### 8. ✅ vectorBackend.js searchVectors 缺少错误处理

**问题描述**: `vectorBackend.js` 中只有 `indexDocument()` 有完整的错误处理，`searchVectors()` 方法没有错误处理。

**修复方案**: 为 `searchVectors()` 添加与 `indexDocument()` 相同模式的错误处理，包括：
- try-catch 包裹
- 错误日志输出
- 响应状态码处理
- 错误数据解析
- 友好的错误消息

**修改文件**: `app/src/api/vectorBackend.js:30-34`

**提交**: `d0d58a5`

---

### 9. ✅ Sidebar 右键"添加到解析"功能报错

**问题描述**: `Sidebar.vue:157` 调用 `parseStore.addFile()` 方法，但该方法在 `useParseStore` 中不存在，导致报错：`parseStore.addFile is not a function`。

**修复方案**:
1. 在 `useParseStore` 中实现 `addFile()` 方法
2. 方法根据文件类型分发到相应处理：
   - PDF → 调用 `parseLocalFile()`
   - 音频 → 调用 `audioStore.transcribeLocalFile()`
   - Markdown → 提示无需解析
3. 添加必要的导入：`ElMessage`、`useAudioStore`、`useParseConfigStore`
4. 在 `Sidebar.vue` 中改进错误处理，使用 Promise 链式调用

**修改文件**:
- `app/src/stores/parse.js`
- `app/src/components/Layout/Sidebar.vue`

**提交**: `c708bf0`

---

## 修改文件清单

### 新增文件（3个）
| 文件 | 说明 |
|------|------|
| `app/src/api/audioBackend.js` | 音频解析 API 客户端 |
| `app/src/stores/audio.js` | 音频解析状态管理 Store |
| `app/src/components/parse/AudioParseView.vue` | 音频解析视图占位符 |

### 修改文件（7个）
| 文件 | 说明 |
|------|------|
| `app/src/components/parse/ParseStatsView.vue` | 修复已索引文档计数 |
| `app/src/api/parseBackend.js` | 添加错误处理 |
| `app/src/components/parse/ParseQueueView.vue` | 添加批量操作按钮 |
| `app/src/components/Layout/ParseSidebar.vue` | 添加音频解析导航 |
| `app/src/views/ParseManagement.vue` | 添加音频解析视图路由 |
| `app/src/api/vectorBackend.js` | 为 searchVectors 添加错误处理 |
| `app/src/stores/parse.js` | 添加 addFile 方法 |
| `app/src/components/Layout/Sidebar.vue` | 改进 addFile 调用错误处理 |

---

## 提交记录

```
c708bf0 fix: 修复Sidebar右键添加到解析功能
d0d58a5 fix: 为向量搜索添加错误处理
505d4c6 feat: 添加音频解析视图占位符
4064d1f feat: 在解析侧边栏添加音频解析导航
1f0f294 feat: 创建音频解析状态管理Store
691d521 feat: 创建音频解析API客户端
3ff1d27 feat: 在队列管理页面添加批量解析和重试按钮
87618e2 fix: 为parseBackend添加错误处理
7f89bab fix: 修复已索引文档计数显示错误
```

---

## 功能验证清单

### 已验证功能
- [x] 已索引文档计数正确显示
- [x] parseBackend 所有 API 有错误处理
- [x] 队列管理页面有批量解析和重试按钮
- [x] audioBackend.js 创建完成
- [x] audio.js store 创建完成
- [x] 解析侧边栏有音频解析导航
- [x] 解析管理页面可切换到音频解析视图
- [x] searchVectors 有错误处理
- [x] Sidebar 右键"添加到解析"功能正常工作

---

## 相关文档

- [解析管理功能文档](../features/parse-management.md)
- [WebSocket 实时更新计划](../.opencode/plans/2026-03-03-websocket-realtime-updates.md)
