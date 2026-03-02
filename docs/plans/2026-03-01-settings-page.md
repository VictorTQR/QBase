# 应用设置页面实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个独立的应用设置页面，将 LLM、PDF 解析、向量存储等配置从对话框迁移到统一的设置界面，并实现可选择的 PDF 解析策略。

**Architecture:** 
1. 新增 `/settings` 路由和 Settings.vue 页面，采用二栏布局（左侧导航 + 右侧内容）
2. 将原 LlmConfigDialog 的配置拆分到三个独立组件：LlmSettings、PdfParseSettings、VectorSettings
3. 在 agent store 中新增 `parseStrategy` 配置项，支持 `local`/`mineru`/`auto` 三种策略
4. 更新 TextExtractor 以支持新的解析策略选择
5. 在首页 Header 添加设置图标按钮入口

**Tech Stack:** Vue 3 + Vue Router + Pinia + Element Plus

---

## 已完成的前期工作

以下文件已在前期创建/修改：
- ✅ `app/src/router/index.js` - 添加 `/settings` 路由
- ✅ `app/src/components/Layout/MainLayout.vue` - 添加设置图标按钮
- ✅ `app/src/components/Layout/SettingsSidebar.vue` - 左侧导航组件
- ✅ `app/src/components/settings/LlmSettings.vue` - LLM 设置模块
- ✅ `app/src/components/settings/PdfParseSettings.vue` - PDF 解析设置模块
- ✅ `app/src/components/settings/VectorSettings.vue` - 向量存储设置模块

---

## 剩余任务

### Task 1: 创建 Settings.vue 主页面

**Files:**
- Create: `app/src/views/Settings.vue`

**Step 1: 创建 Settings.vue 组件**

```vue
<template>
  <div class="settings-page">
    <header class="settings-header">
      <el-button @click="handleBack" link>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="header-title">QBase 设置</div>
      <div></div>
    </header>
    <div class="settings-content">
      <SettingsSidebar v-model="activeTab" />
      <div class="settings-panel">
        <component :is="currentComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import SettingsSidebar from '@/components/Layout/SettingsSidebar.vue'
import LlmSettings from '@/components/settings/LlmSettings.vue'
import PdfParseSettings from '@/components/settings/PdfParseSettings.vue'
import VectorSettings from '@/components/settings/VectorSettings.vue'

const router = useRouter()
const activeTab = ref('llm')

const componentMap = {
  'llm': LlmSettings,
  'pdf-parse': PdfParseSettings,
  'vector': VectorSettings,
}

const currentComponent = computed(() => componentMap[activeTab.value] || LlmSettings)

function handleBack() {
  router.push('/')
}
</script>

<style scoped>
.settings-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.settings-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.settings-panel {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}
</style>
```

---

### Task 2: 修改 agent.js 添加 parseStrategy 配置

**Files:**
- Modify: `app/src/stores/agent.js:42-57`

**Step 1: 更新 llmConfig 初始值**

找到 `llmConfig` 定义部分，添加 `parseStrategy` 字段：

```javascript
const llmConfig = ref({
  type: 'openai',
  baseUrl: 'https://api.openai.com/v1',
  apiKey: '',
  model: 'gpt-3.5-turbo',
  parseStrategy: 'mineru',
  mineru: {
    apiKey: '',
    baseUrl: 'https://mineru.net',
  },
  siliconflow: {
    apiKey: '',
    baseUrl: 'https://api.siliconflow.cn',
    embeddingModel: 'BAAI/bge-large-zh-v1.5',
    asrModel: 'FunAudioLLM/SenseVoiceSmall',
  },
})
```

---

### Task 3: 修改 TextExtractor.js 支持新解析策略

**Files:**
- Modify: `app/src/processors/parse/TextExtractor.js:35-52`

**Step 1: 重写 extractPdf 方法**

替换原有的 `extractPdf` 方法：

```javascript
  static async extractPdf(filePath, config = {}) {
    const strategy = config.parseStrategy || 'mineru'

    switch (strategy) {
      case 'local':
        return await this.extractPdfLocal(filePath)

      case 'mineru':
        if (!config.mineru?.apiKey) {
          throw new Error('MinerU API Key 未配置，请在设置中配置')
        }
        return await this.extractWithMinerU(filePath, config.mineru)

      case 'auto':
      default:
        try {
          return await this.extractPdfLocal(filePath)
        } catch (localError) {
          console.warn('本地 PDF 提取失败，尝试云端 MinerU:', localError.message)

          if (config.mineru?.apiKey) {
            try {
              return await this.extractWithMinerU(filePath, config.mineru)
            } catch (mineruError) {
              console.error('MinerU 提取也失败:', mineruError)
              throw new Error(`PDF 提取失败: ${localError.message}`)
            }
          }

          throw new Error(`PDF 提取失败: ${localError.message}`)
        }
    }
  }
```

---

### Task 4: 修改 parse.js 传递 parseStrategy 配置

**Files:**
- Modify: `app/src/stores/parse.js:157-161`

**Step 1: 更新 startParse 中的 config 对象**

找到 `startParse` 函数中的 config 定义，添加 parseStrategy：

```javascript
        const config = {
          parseStrategy: agentStore.llmConfig.parseStrategy,
          mineru: agentStore.llmConfig.mineru,
        }
```

---

### Task 5: 修改 AgentPanel.vue 移除设置按钮

**Files:**
- Modify: `app/src/components/Layout/AgentPanel.vue`

**Step 1: 读取 AgentPanel.vue 文件内容**

先读取文件查看当前结构，然后移除设置按钮相关代码。

---

### Task 6: 删除 LlmConfigDialog.vue 文件

**Files:**
- Delete: `app/src/components/LlmConfigDialog.vue`

**Step 1: 删除文件**

直接删除该文件。

---

### Task 7: 验证代码并运行 lint

**Files:**
- All modified files

**Step 1: 运行 lint 检查**

```bash
cd app
npm run lint
```

**Step 2: 运行 format 格式化**

```bash
npm run format
```

---

## 最终验证清单

- [ ] Settings.vue 页面可通过 `/settings` 路由访问
- [ ] 首页 Header 的设置按钮可跳转到设置页面
- [ ] 设置页面左侧导航可切换三个设置模块
- [ ] 设置页面的「返回」按钮可返回首页
- [ ] LLM 配置、PDF 解析配置、向量存储配置都可正常保存
- [ ] PDF 解析策略选择生效
- [ ] AgentPanel 中不再有设置按钮
- [ ] LlmConfigDialog.vue 已删除
- [ ] npm run lint 通过
- [ ] npm run format 通过

---

Plan complete and saved to `docs/plans/2026-03-01-settings-page.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
