# 向量搜索功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 完善 QBase 的向量解析功能，实现基于语义的向量搜索，为后续 RAG 问答奠定基础。

**架构:** 采用可插拔的 VectorStore 架构，优先实现 ZvecVectorStore；实现混合文本分块策略；通过 EmbeddingService 对接 SiliconFlow API；增强现有搜索面板支持向量搜索模式。

**技术栈:** Vue 3, Pinia, Zvec (@zvec/zvec), SiliconFlow Embedding API

---

## 任务清单

### 阶段一：基础依赖和核心组件
1. 安装 zvec 依赖
2. 创建 TextChunker（混合分块器）
3. 创建 EmbeddingService（向量化服务）
4. 实现 ZvecVectorStore
5. 更新 VectorStore 接口

### 阶段二：状态管理和索引编排
6. 创建 useVectorStore（向量状态管理）
7. 创建 DocumentIndexer（文档索引编排器）
8. 更新 Vectorizer（整合分块和向量化）

### 阶段三：UI 集成
9. 增强 VectorSettings（向量配置）
10. 增强 SearchPanel（搜索面板）
11. 更新 useSearchStore（支持向量搜索）

### 阶段四：解析管理集成
12. 解析管理页面集成向量索引功能
13. 实现索引进度展示

---

## 详细任务

### Task 1: 安装 zvec 依赖

**文件:**
- Modify: `app/package.json`

**Step 1: 安装 zvec npm 包**

```bash
cd app
npm install @zvec/zvec
```

**Step 2: 验证安装**

检查 `app/package.json` 的 dependencies 是否包含 `@zvec/zvec`

**Step 3: 提交**

```bash
git add app/package.json app/package-lock.json
git commit -m "feat: add @zvec/zvec dependency"
```

---

### Task 2: 创建 TextChunker（混合分块器）

**文件:**
- Create: `app/src/processors/parse/TextChunker.js`
- Test: `app/src/__tests__/TextChunker.spec.js`

**Step 1: 创建测试文件**

```javascript
import { describe, it, expect } from 'vitest'
import { TextChunker } from '@/processors/parse/TextChunker'

describe('TextChunker', () => {
  it('should split text by semantic boundaries', () => {
    const text = '第一段内容。\n\n第二段内容？\n\n第三段内容！'
    const chunks = TextChunker.splitBySemanticBoundary(text)
    expect(chunks.length).toBe(3)
  })

  it('should split text by fixed size', () => {
    const text = '0123456789'.repeat(10)
    const chunks = TextChunker.splitByFixedSize(text, 50, 10)
    expect(chunks.length).toBeGreaterThan(1)
  })

  it('should use hybrid chunking strategy', () => {
    const text = '段落一。\n\n段落二。\n\n'.repeat(20)
    const chunks = TextChunker.chunk(text, {
      chunkSize: 100,
      chunkOverlap: 20
    })
    expect(chunks.length).toBeGreaterThan(0)
    chunks.forEach(chunk => {
      expect(chunk.content.length).toBeLessThanOrEqual(120)
    })
  })
})
```

**Step 2: 运行测试验证失败**

```bash
cd app
npm run test:unit -- src/__tests__/TextChunker.spec.js -v
```
期望: FAIL with "TextChunker not defined"

**Step 3: 实现 TextChunker**

```javascript
export class TextChunker {
  static splitBySemanticBoundary(text) {
    const sentences = text.split(/(?<=[。！？\n])\s+/)
    const chunks = []
    let currentChunk = ''

    for (const sentence of sentences) {
      if (!sentence.trim()) continue
      if (currentChunk.length + sentence.length > 500 && currentChunk) {
        chunks.push(currentChunk.trim())
        currentChunk = sentence
      } else {
        currentChunk += (currentChunk ? ' ' : '') + sentence
      }
    }

    if (currentChunk.trim()) {
      chunks.push(currentChunk.trim())
    }

    return chunks
  }

  static splitByFixedSize(text, chunkSize = 512, chunkOverlap = 128) {
    const chunks = []
    let i = 0

    while (i < text.length) {
      const chunk = text.slice(i, i + chunkSize)
      chunks.push(chunk)
      i += chunkSize - chunkOverlap
    }

    return chunks
  }

  static chunk(text, options = {}) {
    const {
      chunkSize = 512,
      chunkOverlap = 128,
      useSemantic = true
    } = options

    let rawChunks
    if (useSemantic) {
      rawChunks = this.splitBySemanticBoundary(text)
      rawChunks = rawChunks.flatMap(chunk => {
        if (chunk.length <= chunkSize) return [chunk]
        return this.splitByFixedSize(chunk, chunkSize, chunkOverlap)
      })
    } else {
      rawChunks = this.splitByFixedSize(text, chunkSize, chunkOverlap)
    }

    return rawChunks.map((content, index) => ({
      content,
      index,
      startChar: text.indexOf(content),
      endChar: text.indexOf(content) + content.length
    }))
  }
}
```

**Step 4: 运行测试验证通过**

```bash
cd app
npm run test:unit -- src/__tests__/TextChunker.spec.js -v
```
期望: PASS

**Step 5: 提交**

```bash
git add app/src/processors/parse/TextChunker.js app/src/__tests__/TextChunker.spec.js
git commit -m "feat: add TextChunker with hybrid chunking strategy"
```

---

### Task 3: 创建 EmbeddingService（向量化服务）

**文件:**
- Create: `app/src/services/EmbeddingService.js`
- Test: `app/src/__tests__/EmbeddingService.spec.js`

**Step 1: 创建测试文件**

```javascript
import { describe, it, expect, vi } from 'vitest'
import { EmbeddingService } from '@/services/EmbeddingService'

describe('EmbeddingService', () => {
  it('should get embedding dimension for model', () => {
    const dim1 = EmbeddingService.getEmbeddingDimension('BAAI/bge-large-zh-v1.5')
    expect(dim1).toBe(1024)
    const dim2 = EmbeddingService.getEmbeddingDimension('BAAI/bge-m3')
    expect(dim2).toBe(1024)
  })

  it('should throw error for unknown model', () => {
    expect(() => {
      EmbeddingService.getEmbeddingDimension('unknown/model')
    }).toThrow()
  })
})
```

**Step 2: 运行测试验证失败**

```bash
cd app
npm run test:unit -- src/__tests__/EmbeddingService.spec.js -v
```
期望: FAIL

**Step 3: 实现 EmbeddingService**

```javascript
import { useAgentStore } from '@/stores/agent'

const MODEL_DIMENSIONS = {
  'BAAI/bge-large-zh-v1.5': 1024,
  'BAAI/bge-m3': 1024
}

export class EmbeddingService {
  static getEmbeddingDimension(model) {
    const dim = MODEL_DIMENSIONS[model]
    if (!dim) {
      throw new Error(`Unknown embedding model: ${model}`)
    }
    return dim
  }

  static async embedText(text, options = {}) {
    const agentStore = useAgentStore()
    const config = agentStore.llmConfig.siliconflow

    if (!config?.apiKey) {
      throw new Error('SiliconFlow API Key not configured')
    }

    const model = options.model || config.embeddingModel || 'BAAI/bge-large-zh-v1.5'
    const baseUrl = config.baseUrl || 'https://api.siliconflow.cn/v1'

    const response = await fetch(`${baseUrl}/embeddings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`
      },
      body: JSON.stringify({
        model,
        input: text
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Embedding request failed')
    }

    const data = await response.json()
    return data.data[0].embedding
  }

  static async embedBatch(texts, options = {}) {
    const embeddings = []
    for (const text of texts) {
      const embedding = await this.embedText(text, options)
      embeddings.push(embedding)
    }
    return embeddings
  }
}
```

**Step 4: 运行测试验证通过**

```bash
cd app
npm run test:unit -- src/__tests__/EmbeddingService.spec.js -v
```
期望: PASS

**Step 5: 提交**

```bash
git add app/src/services/EmbeddingService.js app/src/__tests__/EmbeddingService.spec.js
git commit -m "feat: add EmbeddingService for SiliconFlow API"
```

---

### Task 4: 实现 ZvecVectorStore

**文件:**
- Create: `app/src/vector/ZvecVectorStore.js`
- Modify: `app/src/vector/index.js`
- Test: `app/src/__tests__/ZvecVectorStore.spec.js`

**Step 1: 创建测试文件**

```javascript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { ZvecVectorStore } from '@/vector/ZvecVectorStore'
import fs from 'fs'
import path from 'path'

const TEST_DIR = path.join(__dirname, 'test-zvec')

describe('ZvecVectorStore', () => {
  let store

  beforeEach(() => {
    if (fs.existsSync(TEST_DIR)) {
      fs.rmSync(TEST_DIR, { recursive: true })
    }
    store = new ZvecVectorStore({ path: TEST_DIR })
  })

  afterEach(async () => {
    await store.close()
    if (fs.existsSync(TEST_DIR)) {
      fs.rmSync(TEST_DIR, { recursive: true })
    }
  })

  it('should add and search documents', async () => {
    await store.addDocument({
      id: 'doc1',
      content: '这是测试文档',
      embedding: new Array(1024).fill(0.1),
      metadata: { filePath: '/test.md' }
    })

    const results = await store.search(new Array(1024).fill(0.1), 5)
    expect(results.length).toBe(1)
    expect(results[0].id).toBe('doc1')
  })
})
```

**Step 2: 运行测试验证失败**

```bash
cd app
npm run test:unit -- src/__tests__/ZvecVectorStore.spec.js -v
```
期望: FAIL

**Step 3: 实现 ZvecVectorStore**

```javascript
import { VectorStore } from './VectorStore.js'

let zvec = null

try {
  zvec = require('@zvec/zvec')
} catch (e) {
  console.warn('@zvec/zvec not available, ZvecVectorStore will not work')
}

export class ZvecVectorStore extends VectorStore {
  constructor(options = {}) {
    super()
    this.path = options.path || './data/zvec'
    this.dimension = options.dimension || 1024
    this.collection = null
    this._initPromise = null
  }

  async _init() {
    if (this._initPromise) return this._initPromise

    this._initPromise = this._doInit()
    return this._initPromise
  }

  async _doInit() {
    if (!zvec) {
      throw new Error('@zvec/zvec is not installed')
    }

    const fs = await import('fs')
    const path = await import('path')

    if (!fs.existsSync(this.path)) {
      fs.mkdirSync(this.path, { recursive: true })
    }

    const collectionPath = path.join(this.path, 'qbase_documents')

    if (fs.existsSync(collectionPath)) {
      this.collection = zvec.openSync(collectionPath)
    } else {
      const schema = new zvec.ZVecCollectionSchema({
        name: 'qbase_documents',
        fields: [
          { name: 'file_path', data_type: zvec.DataType.STRING, index_param: new zvec.ZVecInvertIndexParam() },
          { name: 'file_name', data_type: zvec.DataType.STRING, index_param: new zvec.ZVecInvertIndexParam() },
          { name: 'workspace_id', data_type: zvec.DataType.STRING, index_param: new zvec.ZVecInvertIndexParam() },
          { name: 'chunk_index', data_type: zvec.DataType.INT32, index_param: new zvec.ZVecInvertIndexParam() },
          { name: 'content_type', data_type: zvec.DataType.STRING, index_param: new zvec.ZVecInvertIndexParam() },
          { name: 'created_at', data_type: zvec.DataType.INT64 },
          { name: 'content', data_type: zvec.DataType.STRING }
        ],
        vectors: [
          {
            name: 'embedding',
            data_type: zvec.DataType.VECTOR_FP32,
            dimension: this.dimension,
            index_param: new zvec.ZVecHnswIndexParam({
              metric_type: zvec.MetricType.COSINE
            })
          }
        ]
      })

      this.collection = zvec.createAndOpenSync(collectionPath, schema)
    }
  }

  async addDocument(doc) {
    await this._init()

    const zvecDoc = {
      id: doc.id,
      vectors: {
        embedding: doc.embedding
      },
      fields: {
        file_path: doc.metadata?.filePath || '',
        file_name: doc.metadata?.fileName || '',
        workspace_id: doc.metadata?.workspaceId || '',
        chunk_index: doc.metadata?.chunkIndex || 0,
        content_type: doc.metadata?.contentType || 'text',
        created_at: Date.now(),
        content: doc.content || ''
      }
    }

    this.collection.insertSync(zvecDoc)
  }

  async addDocuments(docs) {
    await this._init()
    for (const doc of docs) {
      await this.addDocument(doc)
    }
  }

  async search(queryEmbedding, k = 5, filter = null) {
    await this._init()

    const query = new zvec.ZVecVectorQuery({
      field_name: 'embedding',
      vector: queryEmbedding
    })

    const options = { topk: k }
    if (filter) {
      options.filter = filter
    }

    const results = this.collection.querySync(query, options)

    return results.map(doc => ({
      id: doc.id,
      content: doc.fields.content,
      score: doc.score,
      metadata: {
        filePath: doc.fields.file_path,
        fileName: doc.fields.file_name,
        workspaceId: doc.fields.workspace_id,
        chunkIndex: doc.fields.chunk_index,
        contentType: doc.fields.content_type
      }
    }))
  }

  async deleteByFilePath(filePath) {
    await this._init()
    this.collection.deleteByFilterSync(`file_path = '${filePath.replace(/'/g, "''")}'`)
  }

  async clear() {
    await this._init()
    const stats = this.collection.stats
    if (stats.num_documents > 0) {
      this.collection.deleteByFilterSync('1 = 1')
    }
  }

  async optimize() {
    await this._init()
    this.collection.optimizeSync()
  }

  async close() {
    if (this.collection) {
      this.collection.closeSync()
      this.collection = null
    }
    this._initPromise = null
  }

  async getStats() {
    await this._init()
    return this.collection.stats
  }
}
```

**Step 4: 更新 vector/index.js**

```javascript
export { VectorStore } from './VectorStore.js'
export { MemoryVectorStore } from './MemoryVectorStore.js'
export { ZvecVectorStore } from './ZvecVectorStore.js'
```

**Step 5: 提交**

```bash
git add app/src/vector/ZvecVectorStore.js app/src/vector/index.js app/src/__tests__/ZvecVectorStore.spec.js
git commit -m "feat: implement ZvecVectorStore"
```

---

### Task 5: 更新 VectorStore 接口

**文件:**
- Modify: `app/src/vector/VectorStore.js`

**Step 1: 更新 VectorStore 基类**

```javascript
export class VectorStore {
  async addDocument(doc) {
    throw new Error('addDocument not implemented')
  }

  async addDocuments(docs) {
    for (const doc of docs) {
      await this.addDocument(doc)
    }
  }

  async search(query, k = 5, filter = null) {
    throw new Error('search not implemented')
  }

  async deleteByFilePath(filePath) {
    throw new Error('deleteByFilePath not implemented')
  }

  async clear() {
    throw new Error('clear not implemented')
  }

  async optimize() {
  }

  async close() {
  }

  async getStats() {
    return {}
  }
}
```

**Step 2: 更新 MemoryVectorStore 以匹配新接口**

```javascript
import { VectorStore } from './VectorStore.js'

function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0
  let dotProduct = 0
  let normA = 0
  let normB = 0
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i]
    normA += a[i] * a[i]
    normB += b[i] * b[i]
  }
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))
}

export class MemoryVectorStore extends VectorStore {
  constructor() {
    super()
    this.documents = []
    this.embeddings = []
  }

  async addDocument(doc) {
    this.documents.push(doc)
    if (doc.embedding) {
      this.embeddings.push(doc.embedding)
    }
  }

  async search(queryEmbedding, k = 5) {
    const results = []
    for (let i = 0; i < this.documents.length; i++) {
      const doc = this.documents[i]
      const embedding = this.embeddings[i]
      if (embedding) {
        const score = cosineSimilarity(queryEmbedding, embedding)
        results.push({
          id: doc.id,
          content: doc.content,
          score,
          metadata: doc.metadata,
        })
      }
    }
    return results.sort((a, b) => b.score - a.score).slice(0, k)
  }

  async deleteByFilePath(filePath) {
    const indicesToRemove = []
    for (let i = 0; i < this.documents.length; i++) {
      if (this.documents[i].metadata?.filePath === filePath) {
        indicesToRemove.push(i)
      }
    }
    for (let i = indicesToRemove.length - 1; i >= 0; i--) {
      const idx = indicesToRemove[i]
      this.documents.splice(idx, 1)
      this.embeddings.splice(idx, 1)
    }
  }

  async clear() {
    this.documents = []
    this.embeddings = []
  }

  async getStats() {
    return { num_documents: this.documents.length }
  }
}
```

**Step 3: 运行现有测试**

```bash
cd app
npm run test:unit
```
期望: 所有测试通过

**Step 4: 提交**

```bash
git add app/src/vector/VectorStore.js app/src/vector/MemoryVectorStore.js
git commit -m "refactor: update VectorStore interface with new methods"
```

---

### Task 6: 创建 useVectorStore（向量状态管理）

**文件:**
- Create: `app/src/stores/vector.js`

**Step 1: 实现 useVectorStore**

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ZvecVectorStore, MemoryVectorStore } from '@/vector'
import { useAgentStore } from './agent'

export const useVectorStore = defineStore(
  'vector',
  () => {
    const agentStore = useAgentStore()

    const vectorStore = ref(null)
    const isIndexing = ref(false)
    const indexingProgress = ref(0)
    const indexingTotal = ref(0)
    const currentIndexingFile = ref('')
    const error = ref(null)

    const storeType = ref('zvec')

    async function initVectorStore() {
      if (vectorStore.value) {
        await vectorStore.value.close()
      }

      const config = agentStore.llmConfig.siliconflow
      const dimension = config?.embeddingModel
        ? (await import('@/services/EmbeddingService')).EmbeddingService.getEmbeddingDimension(config.embeddingModel)
        : 1024

      if (storeType.value === 'zvec') {
        const { app } = await import('@electron/remote')
        const userDataPath = app.getPath('userData')
        const zvecPath = `${userDataPath}/zvec`

        vectorStore.value = new ZvecVectorStore({
          path: zvecPath,
          dimension
        })
      } else {
        vectorStore.value = new MemoryVectorStore()
      }

      return vectorStore.value
    }

    function getVectorStore() {
      return vectorStore.value
    }

    function setIndexingState(state) {
      isIndexing.value = state.isIndexing
      indexingProgress.value = state.progress || 0
      indexingTotal.value = state.total || 0
      currentIndexingFile.value = state.currentFile || ''
      error.value = state.error || null
    }

    async function searchVector(queryEmbedding, k = 5, filter = null) {
      if (!vectorStore.value) {
        await initVectorStore()
      }
      return await vectorStore.value.search(queryEmbedding, k, filter)
    }

    async function getStats() {
      if (!vectorStore.value) {
        await initVectorStore()
      }
      return await vectorStore.value.getStats()
    }

    async function clearAll() {
      if (!vectorStore.value) {
        await initVectorStore()
      }
      await vectorStore.value.clear()
    }

    return {
      vectorStore,
      isIndexing,
      indexingProgress,
      indexingTotal,
      currentIndexingFile,
      error,
      storeType,
      initVectorStore,
      getVectorStore,
      setIndexingState,
      searchVector,
      getStats,
      clearAll
    }
  },
  {
    persist: {
      key: 'qbase-vector',
      paths: ['storeType']
    }
  }
)
```

**Step 2: 提交**

```bash
git add app/src/stores/vector.js
git commit -m "feat: add useVectorStore for vector state management"
```

---

### Task 7: 创建 DocumentIndexer（文档索引编排器）

**文件:**
- Create: `app/src/services/DocumentIndexer.js`
- Test: `app/src/__tests__/DocumentIndexer.spec.js`

**Step 1: 创建测试文件**

```javascript
import { describe, it, expect, vi } from 'vitest'
import { DocumentIndexer } from '@/services/DocumentIndexer'

describe('DocumentIndexer', () => {
  it('should be defined', () => {
    expect(DocumentIndexer).toBeDefined()
  })
})
```

**Step 2: 实现 DocumentIndexer**

```javascript
import { TextChunker } from '@/processors/parse/TextChunker'
import { EmbeddingService } from '@/services/EmbeddingService'
import { useVectorStore } from '@/stores/vector'
import { useWorkspaceStore } from '@/stores/workspace'

export class DocumentIndexer {
  constructor(options = {}) {
    this.chunkSize = options.chunkSize || 512
    this.chunkOverlap = options.chunkOverlap || 128
    this.vectorStore = null
  }

  async _init() {
    if (!this.vectorStore) {
      const vectorStore = useVectorStore()
      this.vectorStore = await vectorStore.initVectorStore()
    }
  }

  async indexDocument(filePath, content, metadata = {}) {
    await this._init()

    const chunks = TextChunker.chunk(content, {
      chunkSize: this.chunkSize,
      chunkOverlap: this.chunkOverlap
    })

    const docs = []
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i]
      const embedding = await EmbeddingService.embedText(chunk.content)

      docs.push({
        id: `${metadata.fileId || filePath}_chunk_${i}`,
        content: chunk.content,
        embedding,
        metadata: {
          filePath,
          fileName: metadata.fileName || filePath.split('/').pop(),
          workspaceId: metadata.workspaceId || '',
          chunkIndex: i,
          startChar: chunk.startChar,
          endChar: chunk.endChar,
          contentType: metadata.contentType || 'text'
        }
      })
    }

    await this.vectorStore.deleteByFilePath(filePath)
    await this.vectorStore.addDocuments(docs)

    return { chunks: docs.length }
  }

  async indexDocuments(documents, onProgress = null) {
    const results = []
    let completed = 0

    for (const doc of documents) {
      if (onProgress) {
        onProgress({
          progress: completed,
          total: documents.length,
          currentFile: doc.filePath
        })
      }

      try {
        const result = await this.indexDocument(
          doc.filePath,
          doc.content,
          doc.metadata
        )
        results.push({ success: true, filePath: doc.filePath, ...result })
      } catch (error) {
        results.push({ success: false, filePath: doc.filePath, error: error.message })
      }

      completed++
    }

    if (onProgress) {
      onProgress({
        progress: completed,
        total: documents.length,
        currentFile: ''
      })
    }

    return results
  }

  async indexWorkspace(workspaceId, onProgress = null) {
    const workspaceStore = useWorkspaceStore()
    const folder = workspaceStore.folders.find(f => f.id === workspaceId)

    if (!folder) {
      throw new Error(`Workspace not found: ${workspaceId}`)
    }

    const files = await window.electronAPI.listFiles(folder.path)
    const documentsToIndex = []

    for (const file of files) {
      if (this._shouldIndexFile(file.name)) {
        try {
          const content = await this._extractFileContent(file.path)
          if (content) {
            documentsToIndex.push({
              filePath: file.path,
              content,
              metadata: {
                workspaceId,
                fileName: file.name
              }
            })
          }
        } catch (e) {
          console.warn(`Failed to index ${file.path}:`, e)
        }
      }
    }

    return await this.indexDocuments(documentsToIndex, onProgress)
  }

  _shouldIndexFile(fileName) {
    const ext = fileName.toLowerCase().split('.').pop()
    return ['md', 'txt', 'markdown'].includes(ext)
  }

  async _extractFileContent(filePath) {
    try {
      return await window.electronAPI.readFile(filePath)
    } catch (e) {
      console.warn(`Failed to read ${filePath}:`, e)
      return null
    }
  }

  async deleteDocument(filePath) {
    await this._init()
    await this.vectorStore.deleteByFilePath(filePath)
  }

  async clearAll() {
    await this._init()
    await this.vectorStore.clear()
  }
}
```

**Step 3: 提交**

```bash
git add app/src/services/DocumentIndexer.js app/src/__tests__/DocumentIndexer.spec.js
git commit -m "feat: add DocumentIndexer for orchestrating document indexing"
```

---

### Task 8: 更新 Vectorizer（整合分块和向量化）

**文件:**
- Modify: `app/src/processors/parse/Vectorizer.js`

**Step 1: 更新 Vectorizer**

```javascript
import { TextChunker } from './TextChunker.js'
import { EmbeddingService } from '@/services/EmbeddingService.js'

export class Vectorizer {
  static async vectorize(text, options = {}) {
    const {
      chunkSize = 512,
      chunkOverlap = 128,
      useSemantic = true,
      model
    } = options

    const chunks = TextChunker.chunk(text, {
      chunkSize,
      chunkOverlap,
      useSemantic
    })

    const vectorizedChunks = []

    for (const chunk of chunks) {
      const embedding = await EmbeddingService.embedText(chunk.content, { model })
      vectorizedChunks.push({
        content: chunk.content,
        embedding,
        index: chunk.index,
        startChar: chunk.startChar,
        endChar: chunk.endChar
      })
    }

    return { chunks: vectorizedChunks }
  }
}
```

**Step 2: 提交**

```bash
git add app/src/processors/parse/Vectorizer.js
git commit -m "feat: update Vectorizer to integrate TextChunker and EmbeddingService"
```

---

### Task 9: 增强 VectorSettings（向量配置）

**文件:**
- Modify: `app/src/components/settings/VectorSettings.vue`

**Step 1: 更新 VectorSettings 组件**

```vue
<template>
  <div class="vector-settings">
    <el-form :model="form" label-width="140px">
      <el-form-item label="API Key">
        <el-input
          v-model="form.apiKey"
          type="password"
          show-password
          placeholder="请输入 SiliconFlow API Key"
        />
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="form.baseUrl" />
      </el-form-item>
      <el-form-item label="Embedding Model">
        <el-select v-model="form.embeddingModel" style="width: 100%">
          <el-option label="BAAI/bge-large-zh-v1.5" value="BAAI/bge-large-zh-v1.5" />
          <el-option label="BAAI/bge-m3" value="BAAI/bge-m3" />
        </el-select>
      </el-form-item>
      <el-form-item label="ASR Model">
        <el-select v-model="form.asrModel" style="width: 100%">
          <el-option label="FunAudioLLM/SenseVoiceSmall" value="FunAudioLLM/SenseVoiceSmall" />
          <el-option label="TeleAI/TeleSpeechASR" value="TeleAI/TeleSpeechASR" />
        </el-select>
      </el-form-item>
      <el-divider>向量索引配置</el-divider>
      <el-form-item label="分块大小">
        <el-input-number v-model="indexConfig.chunkSize" :min="128" :max="2048" :step="128" />
      </el-form-item>
      <el-form-item label="重叠大小">
        <el-input-number v-model="indexConfig.chunkOverlap" :min="0" :max="512" :step="32" />
      </el-form-item>
      <el-form-item label="索引策略">
        <el-radio-group v-model="indexConfig.autoIndex">
          <el-radio :label="true">自动索引</el-radio>
          <el-radio :label="false">手动索引</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()
const isUpdating = ref(false)

const form = ref({
  apiKey: '',
  baseUrl: '',
  embeddingModel: '',
  asrModel: '',
})

const indexConfig = ref({
  chunkSize: 512,
  chunkOverlap: 128,
  autoIndex: false
})

watch(
  () => agentStore.llmConfig.siliconflow,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    form.value = { ...config }
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { immediate: true, deep: true },
)

watch(
  form,
  (newForm) => {
    if (isUpdating.value) return
    isUpdating.value = true
    agentStore.setLlmConfig({
      ...agentStore.llmConfig,
      siliconflow: { ...newForm },
    })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)
</script>

<style scoped>
.vector-settings {
  padding: 8px 0;
}
</style>
```

**Step 2: 提交**

```bash
git add app/src/components/settings/VectorSettings.vue
git commit -m "feat: enhance VectorSettings with indexing configuration"
```

---

### Task 10: 增强 SearchPanel（搜索面板）

**文件:**
- Modify: `app/src/components/SearchPanel.vue`

**Step 1: 更新 SearchPanel 组件**

在搜索范围选择器下方添加搜索模式切换：

```vue
<!-- 在 search-scope div 之后添加 -->
<div class="search-mode">
  <el-radio-group v-model="searchMode" size="small" @change="handleModeChange">
    <el-radio-button value="fulltext">全文</el-radio-button>
    <el-radio-button value="vector">向量</el-radio-button>
    <el-radio-button value="hybrid">混合</el-radio-button>
  </el-radio-group>
</div>
```

更新结果展示，显示相似度分数：

```vue
<div class="result-name">
  <span v-html="highlightText(result.name, searchStore.query)"></span>
  <el-tag v-if="result.matchType === 'name'" size="small" type="info">文件名</el-tag>
  <el-tag v-else-if="result.matchType === 'content'" size="small" type="success">内容</el-tag>
  <el-tag v-if="result.score !== undefined" size="small" type="warning">
    {{ (result.score * 100).toFixed(0) }}%
  </el-tag>
</div>
```

添加相关样式：

```css
.search-mode {
  padding: 8px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: center;
}
```

更新 script 部分：

```javascript
const searchMode = ref('fulltext')

function handleModeChange() {
  searchStore.setSearchMode(searchMode.value)
  if (searchStore.query) {
    searchStore.performSearch()
  }
}

watch(
  () => searchStore.isPanelOpen,
  async (isOpen) => {
    if (isOpen) {
      await nextTick()
      inputRef.value?.focus()
      searchQuery.value = searchStore.query
      searchScope.value = searchStore.searchScope
      searchMode.value = searchStore.searchMode
    }
  },
)
```

**Step 2: 提交**

```bash
git add app/src/components/SearchPanel.vue
git commit -m "feat: enhance SearchPanel with vector search mode"
```

---

### Task 11: 更新 useSearchStore（支持向量搜索）

**文件:**
- Modify: `app/src/stores/search.js`

**Step 1: 更新 useSearchStore**

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useWorkspaceStore } from './workspace'
import { useVectorStore } from './vector'
import { EmbeddingService } from '@/services/EmbeddingService'

export const useSearchStore = defineStore(
  'search',
  () => {
    const query = ref('')
    const results = ref([])
    const isLoading = ref(false)
    const error = ref(null)
    const isPanelOpen = ref(false)
    const searchScope = ref('all')
    const searchMode = ref('fulltext')
    const selectedIndex = ref(0)

    const workspaceStore = useWorkspaceStore()
    const vectorStore = useVectorStore()

    const hasResults = computed(() => results.value.length > 0)
    const isSearching = computed(() => isLoading.value && query.value.length > 0)

    function openPanel() {
      isPanelOpen.value = true
      selectedIndex.value = 0
    }

    function closePanel() {
      isPanelOpen.value = false
      query.value = ''
      results.value = []
      error.value = null
      selectedIndex.value = 0
    }

    function setQuery(newQuery) {
      query.value = newQuery
      selectedIndex.value = 0
    }

    function setSearchScope(scope) {
      searchScope.value = scope
    }

    function setSearchMode(mode) {
      searchMode.value = mode
    }

    function selectPreviousResult() {
      if (results.value.length > 0) {
        selectedIndex.value =
          (selectedIndex.value - 1 + results.value.length) % results.value.length
      }
    }

    function selectNextResult() {
      if (results.value.length > 0) {
        selectedIndex.value = (selectedIndex.value + 1) % results.value.length
      }
    }

    function getSelectedResult() {
      return results.value[selectedIndex.value] || null
    }

    async function performFulltextSearch() {
      const foldersToSearch =
        searchScope.value === 'all'
          ? workspaceStore.folders
          : workspaceStore.folders.filter((f) => f.id === searchScope.value)

      const allResults = []

      for (const folder of foldersToSearch) {
        const result = await window.electronAPI.searchFiles(folder.path, query.value)
        if (result.success) {
          allResults.push(...result.results)
        } else {
          console.error(`搜索文件夹 ${folder.name} 失败:`, result.error)
        }
      }

      return allResults
    }

    async function performVectorSearch() {
      const queryEmbedding = await EmbeddingService.embedText(query.value)
      let filter = null

      if (searchScope.value !== 'all') {
        filter = `workspace_id = '${searchScope.value}'`
      }

      const vectorResults = await vectorStore.searchVector(queryEmbedding, 10, filter)

      return vectorResults.map(r => ({
        id: r.metadata.filePath,
        name: r.metadata.fileName,
        path: r.metadata.filePath,
        snippet: r.content,
        matchType: 'vector',
        score: r.score,
        chunkIndex: r.metadata.chunkIndex
      }))
    }

    async function performHybridSearch() {
      const [fulltextResults, vectorResults] = await Promise.all([
        performFulltextSearch(),
        performVectorSearch()
      ])

      const merged = new Map()

      fulltextResults.forEach(r => {
        merged.set(r.id, { ...r, ftScore: 1 })
      })

      vectorResults.forEach(r => {
        const existing = merged.get(r.id)
        if (existing) {
          existing.score = (existing.score || 0) + r.score * 0.7
          existing.snippet = existing.snippet || r.snippet
        } else {
          merged.set(r.id, { ...r, score: r.score * 0.7 })
        }
      })

      return Array.from(merged.values()).sort((a, b) => (b.score || b.ftScore) - (a.score || a.ftScore))
    }

    async function performSearch() {
      if (!query.value.trim()) {
        results.value = []
        return
      }

      isLoading.value = true
      error.value = null
      results.value = []

      try {
        if (searchMode.value === 'vector') {
          results.value = await performVectorSearch()
        } else if (searchMode.value === 'hybrid') {
          results.value = await performHybridSearch()
        } else {
          results.value = await performFulltextSearch()
        }
      } catch (err) {
        error.value = err.message
        console.error('搜索失败:', err)
      } finally {
        isLoading.value = false
      }
    }

    function clearResults() {
      results.value = []
      error.value = null
      selectedIndex.value = 0
    }

    return {
      query,
      results,
      isLoading,
      error,
      isPanelOpen,
      searchScope,
      searchMode,
      selectedIndex,
      hasResults,
      isSearching,
      openPanel,
      closePanel,
      setQuery,
      setSearchScope,
      setSearchMode,
      selectPreviousResult,
      selectNextResult,
      getSelectedResult,
      performSearch,
      clearResults,
    }
  },
  {
    persist: {
      key: 'qbase-search',
      paths: ['searchScope', 'searchMode'],
    },
  },
)
```

**Step 2: 提交**

```bash
git add app/src/stores/search.js
git commit -m "feat: update useSearchStore to support vector and hybrid search"
```

---

### Task 12: 解析管理页面集成向量索引功能

**文件:**
- Modify: `app/src/views/ParseManagement.vue`
- Modify: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1: 更新 ParseDocumentsView 添加向量索引按钮**

在文档卡片操作区域添加"索引向量"按钮，以及批量索引功能。

**Step 2: 更新 ParseManagement 集成索引进度展示**

添加索引进度状态展示。

**Step 3: 提交**

```bash
git add app/src/views/ParseManagement.vue app/src/components/parse/ParseDocumentsView.vue
git commit -m "feat: integrate vector indexing into parse management"
```

---

### Task 13: 运行所有测试和验证

**Step 1: 运行完整测试套件**

```bash
cd app
npm run test:unit
```
期望: 所有测试通过

**Step 2: 运行 lint 和 format**

```bash
cd app
npm run lint
npm run format
```

**Step 3: 提交最终更改**

```bash
git status
git add ...  # 添加任何修改的文件
git commit -m "feat: complete vector search implementation"
```

---

## 执行选项

计划已完成并保存到 `docs/plans/2026-03-03-vector-search-implementation.md`。两个执行选项：

**1. Subagent-Driven（本会话）** - 我为每个任务分派新的子代理，任务间进行代码审查，快速迭代

**2. Parallel Session（单独会话）** - 打开新会话使用 executing-plans，批量执行并设置检查点

选择哪种方式？
