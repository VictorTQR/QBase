# 文档解析管理功能实施计划

&gt; **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 实现文档解析管理功能，包括左侧标签切换、解析状态管理、统计展示等。

**架构：** 
- 左侧区域改造为横向标签切换（文件树/解析管理）
- 使用混合存储方案：LocalStorage（Pinia）存索引，IndexedDB（Dexie.js）存大数据
- 采用 Repository 模式封装数据访问

**技术栈：** Vue 3, Pinia, Dexie.js, Element Plus

---

## 任务清单

### 阶段 1：基础设施

**Task 1.1：安装 Dexie.js 依赖**
- 命令：`cd app && npm install dexie`

**Task 1.2：创建 Dexie.js 数据库封装**
- 创建：`app/src/repositories/IndexedDBRepository.js`

**Task 1.3：创建解析索引仓储**
- 创建：`app/src/repositories/ParseIndexRepository.js`

---

### 阶段 2：状态管理

**Task 2.1：创建 useParseStore**
- 创建：`app/src/stores/parse.js`
- 功能：解析索引、队列、任务、UI 状态

---

### 阶段 3：UI 组件

**Task 3.1：创建 ParseStats 统计组件**
- 创建：`app/src/components/Layout/ParseStats.vue`

**Task 3.2：创建 ParseQueue 队列组件**
- 创建：`app/src/components/Layout/ParseQueue.vue`

**Task 3.3：创建 ParseDocumentList 文档列表组件**
- 创建：`app/src/components/Layout/ParseDocumentList.vue`

**Task 3.4：创建 ParseDetails 详情组件**
- 创建：`app/src/components/Layout/ParseDetails.vue`

**Task 3.5：创建 ParseManager 主组件**
- 创建：`app/src/components/Layout/ParseManager.vue`

**Task 3.6：修改 Sidebar.vue 添加标签切换**
- 修改：`app/src/components/Layout/Sidebar.vue`

---

### 阶段 4：占位处理器（可选，为将来预留）

**Task 4.1：创建占位解析处理器目录**
- 创建：`app/src/processors/parse/` 目录及占位文件

---

## 各任务详细说明

### Task 1.1：安装 Dexie.js 依赖

**文件：**
- 修改：`app/package.json`

**步骤：**
1. 进入 app 目录：`cd app`
2. 安装：`npm install dexie`
3. 验证 package.json 包含 `"dexie": "^x.x.x"`

---

### Task 1.2：创建 Dexie.js 数据库封装

**文件：**
- 创建：`app/src/repositories/IndexedDBRepository.js`

**代码结构：**
```javascript
import Dexie from 'dexie'

class QBaseParseDatabase extends Dexie {
  constructor() {
    super('QBaseParse')
    this.version(1).stores({
      extractedTexts: 'filePath, type, parsedAt',
      vectors: 'filePath',
      transcripts: 'filePath'
    })
  }
}

export const db = new QBaseParseDatabase()

export class IndexedDBRepository {
  async saveExtractedText(filePath, data) { /* ... */ }
  async getExtractedText(filePath) { /* ... */ }
  async deleteExtractedText(filePath) { /* ... */ }
  
  async saveVectors(filePath, vectors) { /* ... */ }
  async getVectors(filePath) { /* ... */ }
  
  async saveTranscript(filePath, transcript) { /* ... */ }
  async getTranscript(filePath) { /* ... */ }
}
```

---

### Task 1.3：创建解析索引仓储

**文件：**
- 创建：`app/src/repositories/ParseIndexRepository.js`

**代码结构：**
```javascript
const STORAGE_KEY = 'qbase-parse-index'

export class LocalStorageParseIndexRepository {
  async getAll() {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : {}
  }

  async save(index) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(index))
  }

  async update(filePath, updates) {
    const index = await this.getAll()
    index[filePath] = { ...index[filePath], ...updates }
    await this.save(index)
  }

  async delete(filePath) {
    const index = await this.getAll()
    delete index[filePath]
    await this.save(index)
  }
}
```

---

### Task 2.1：创建 useParseStore

**文件：**
- 创建：`app/src/stores/parse.js`

**代码结构（参考 agent.js 模式）：**
```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { LocalStorageParseIndexRepository } from '@/repositories/ParseIndexRepository'

export const useParseStore = defineStore(
  'parse',
  () => {
    const repository = new LocalStorageParseIndexRepository()
    
    const parseIndex = ref({})
    const queue = ref([])
    const activeTask = ref(null)
    const selectedFile = ref(null)
    const showDetails = ref(false)
    
    const stats = computed(() => {
      const entries = Object.values(parseIndex.value)
      return {
        total: entries.length,
        completed: entries.filter(e => e.status === 'completed').length,
        pending: entries.filter(e => e.status === 'pending').length,
        parsing: entries.filter(e => e.status === 'parsing').length,
        failed: entries.filter(e => e.status === 'failed').length,
      }
    })
    
    async function loadIndex() {
      parseIndex.value = await repository.getAll()
    }
    
    async function addToQueue(filePath) { /* ... */ }
    async function retryFailed() { /* ... */ }
    async function reparse(filePath) { /* ... */ }
    
    loadIndex()
    
    return {
      parseIndex, queue, activeTask, selectedFile, showDetails,
      stats, loadIndex, addToQueue, retryFailed, reparse
    }
  },
  {
    persist: {
      key: 'qbase-parse',
      paths: ['parseIndex'],
    },
  }
)
```

---

### Task 3.1 - 3.5：创建 UI 组件

这些组件都是 Vue 3 + Element Plus 组件，按需组合即可。

---

### Task 3.6：修改 Sidebar.vue

**修改内容：**
- 将现有内容包装在 `el-tabs` 的第一个标签页中
- 添加第二个标签页「解析管理」，加载 `ParseManager` 组件

**关键代码结构：**
```vue
<template>
  <div class="sidebar">
    <el-tabs v-model="activeTab" class="sidebar-tabs">
      <el-tab-pane label="文件树" name="filetree">
        <div class="workspace-header">
          <!-- 原有工作区头部内容 -->
        </div>
        <el-tree ... >
          <!-- 原有文件树 -->
        </el-tree>
      </el-tab-pane>
      <el-tab-pane label="解析管理" name="parse">
        <ParseManager />
      </el-tab-pane>
    </el-tabs>
    
    <!-- teleported context-menu 保持不变 -->
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ParseManager from './ParseManager.vue'

const activeTab = ref('filetree')

// ... 其余现有代码保持不变
</script>

<style scoped>
.sidebar {
  /* 原有样式 */
  display: flex;
  flex-direction: column;
}
.sidebar-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.sidebar-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.sidebar-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
```

---

## 验收标准

- [ ] Dexie.js 安装成功
- [ ] IndexedDB 仓储可以正常存取
- [ ] ParseStore 可以管理解析状态
- [ ] 左侧标签切换流畅
- [ ] 解析管理界面可以正常展示（即使没有真实解析数据）

---

## 后续迭代（不在本次计划内）

- 真实的文本提取实现
- 音视频转录集成
- 向量化表示功能
