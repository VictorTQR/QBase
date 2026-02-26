# 右侧边栏重构实施计划

&gt; **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 将右侧边栏的「生成」聚合组件拆分为独立的「思维导图」和「摘要」标签页，移除重复的闪卡功能，使每个功能职责清晰。

**架构：** 从3个标签页扩展为4个标签页（对话、闪卡、思维导图、摘要），每个功能独立管理，代码结构更模块化。

**技术栈：** Vue 3 + Pinia + Element Plus

---

## 前提条件

- 当前工作目录：`E:\Code\workSpace\GitBank\QBase\app`
- 已安装依赖：运行 `npm install`
- 开发服务器可正常启动：`npm run dev`

---

## 任务清单

### 任务 1：创建思维导图组件

**文件：**
- 创建：`src/components/mindmap/MindmapGenerator.vue`
- 创建：`src/components/generate/MindmapModule.vue`

**步骤 1.1：创建 MindmapGenerator.vue**

从 `AiGeneratorPanel.vue` 中提取思维导图相关代码，创建独立组件。

```vue
<script setup>
import { ref } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useDocumentStore } from '@/stores/document'

const agentStore = useAgentStore()
const documentStore = useDocumentStore()

const isGenerating = ref(false)
const error = ref(null)
const mindmapResult = ref(null)

async function generateMindmap() {
  if (!documentStore.currentFile || !documentStore.content) {
    error.value = '请先打开一个 Markdown 文档'
    return
  }

  isGenerating.value = true
  error.value = null
  mindmapResult.value = null

  try {
    const result = await agentStore.generateMindmap(documentStore.content)
    if (result.success) {
      mindmapResult.value = result.mindmap
    } else {
      error.value = result.error
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isGenerating.value = false
  }
}

function getNodePosition(nodeId) {
  const positions = {
    root: { x: 400, y: 50 },
    node1: { x: 200, y: 150 },
    node2: { x: 600, y: 150 },
    node3: { x: 100, y: 250 },
    node4: { x: 300, y: 250 },
    node5: { x: 500, y: 250 },
    node6: { x: 700, y: 250 },
  }

  return positions[nodeId] || { x: 400, y: 350 }
}
</script>

<template>
  <div class="mindmap-generator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>思维导图生成</span>
        </div>
      </template>

      <div class="content">
        <el-button
          type="primary"
          :loading="isGenerating"
          @click="generateMindmap"
          style="width: 100%"
        >
          {{ isGenerating ? '生成中...' : '生成思维导图' }}
        </el-button>

        <el-alert v-if="error" type="error" :closable="false" style="margin-top: 16px">
          {{ error }}
        </el-alert>

        <div v-if="mindmapResult" class="result-panel">
          <h3>{{ mindmapResult.title }}</h3>
          <div class="mindmap-container">
            <div class="mindmap-svg-container">
              <svg width="100%" height="100%" viewBox="0 0 800 600">
                <template v-for="node in mindmapResult.nodes" :key="node.id">
                  <g v-if="node.parent">
                    <line
                      :x1="getNodePosition(node.parent).x"
                      :y1="getNodePosition(node.parent).y"
                      :x2="getNodePosition(node.id).x"
                      :y2="getNodePosition(node.id).y"
                      stroke="#409eff"
                      stroke-width="2"
                    />
                  </g>
                </template>

                <template v-for="node in mindmapResult.nodes" :key="node.id">
                  <g>
                    <rect
                      :x="getNodePosition(node.id).x - 80"
                      :y="getNodePosition(node.id).y - 20"
                      width="160"
                      height="40"
                      :fill="node.parent ? '#f0f9eb' : '#e6f7ff'"
                      :stroke="node.parent ? '#67c23a' : '#409eff'"
                      stroke-width="2"
                      rx="4"
                    />
                    <text
                      :x="getNodePosition(node.id).x"
                      :y="getNodePosition(node.id).y + 5"
                      text-anchor="middle"
                      fill="#303133"
                      font-size="14"
                    >
                      {{ node.text }}
                    </text>
                  </g>
                </template>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.mindmap-generator {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-panel {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.result-panel h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.mindmap-container {
  position: relative;
  height: 400px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fff;
  overflow: auto;
}

.mindmap-svg-container {
  width: 100%;
  height: 100%;
}

.mindmap-svg-container svg {
  width: 100%;
  height: 100%;
}
</style>
```

**步骤 1.2：创建 MindmapModule.vue**

```vue
<script setup>
import MindmapGenerator from '@/components/mindmap/MindmapGenerator.vue'
</script>

<template>
  <div class="mindmap-module">
    <MindmapGenerator />
  </div>
</template>

<style scoped>
.mindmap-module {
  height: 100%;
  overflow-y: auto;
}
</style>
```

---

### 任务 2：创建摘要组件

**文件：**
- 创建：`src/components/summary/SummaryGenerator.vue`
- 创建：`src/components/generate/SummaryModule.vue`

**步骤 2.1：创建 SummaryGenerator.vue**

```vue
<script setup>
import { ref } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useDocumentStore } from '@/stores/document'

const agentStore = useAgentStore()
const documentStore = useDocumentStore()

const isGenerating = ref(false)
const error = ref(null)
const summaryResult = ref(null)

async function generateSummary() {
  if (!documentStore.currentFile || !documentStore.content) {
    error.value = '请先打开一个 Markdown 文档'
    return
  }

  isGenerating.value = true
  error.value = null
  summaryResult.value = null

  try {
    const result = await agentStore.generateSummary(documentStore.content)
    if (result.success) {
      summaryResult.value = result.summary
    } else {
      error.value = result.error
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <div class="summary-generator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文档摘要生成</span>
        </div>
      </template>

      <div class="content">
        <el-button
          type="primary"
          :loading="isGenerating"
          @click="generateSummary"
          style="width: 100%"
        >
          {{ isGenerating ? '生成中...' : '生成摘要' }}
        </el-button>

        <el-alert v-if="error" type="error" :closable="false" style="margin-top: 16px">
          {{ error }}
        </el-alert>

        <div v-if="summaryResult" class="result-panel">
          <h3>文档摘要</h3>
          <div class="summary-content">
            {{ summaryResult }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.summary-generator {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-panel {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.result-panel h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.summary-content {
  line-height: 1.6;
  color: var(--el-text-color-regular);
}
</style>
```

**步骤 2.2：创建 SummaryModule.vue**

```vue
<script setup>
import SummaryGenerator from '@/components/summary/SummaryGenerator.vue'
</script>

<template>
  <div class="summary-module">
    <SummaryGenerator />
  </div>
</template>

<style scoped>
.summary-module {
  height: 100%;
  overflow-y: auto;
}
</style>
```

---

### 任务 3：更新导航侧边栏

**文件：**
- 修改：`src/components/Layout/PanelNavSidebar.vue`

**步骤 3.1：更新标签页配置**

将标签页从3个扩展为4个，添加思维导图和摘要的图标。

```vue
<script setup>
import { computed } from 'vue'
import { ChatDotRound, Tickets, Connection, Document } from '@element-plus/icons-vue'

const props = defineProps({
  activeModule: {
    type: String,
    default: 'chat',
  },
})

const emit = defineEmits(['change'])

const navItems = [
  { id: 'chat', icon: ChatDotRound, label: '对话' },
  { id: 'flashcard', icon: Tickets, label: '闪卡' },
  { id: 'mindmap', icon: Connection, label: '思维导图' },
  { id: 'summary', icon: Document, label: '摘要' },
]

const isActive = computed(() => (id) => props.activeModule === id)

const handleClick = (item) => {
  emit('change', item.id)
}
</script>

<template>
  <div class="panel-nav-sidebar">
    <div
      v-for="item in navItems"
      :key="item.id"
      class="nav-item"
      :class="{ active: isActive(item.id) }"
      @click="handleClick(item)"
    >
      <el-icon :size="20">
        <component :is="item.icon" />
      </el-icon>
      <span class="nav-label">{{ item.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.panel-nav-sidebar {
  width: 64px;
  height: 100%;
  background-color: var(--el-bg-color-page);
  border-left: 1px solid var(--el-border-color-lighter);
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  width: 48px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--el-text-color-secondary);
}

.nav-item:hover {
  background-color: var(--el-bg-color-secondary);
  transform: scale(1.05);
}

.nav-item.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.nav-label {
  font-size: 11px;
  text-align: center;
  line-height: 1;
}
</style>
```

---

### 任务 4：更新 AgentPanel 主面板

**文件：**
- 修改：`src/components/Layout/AgentPanel.vue`

**步骤 4.1：更新模块切换逻辑**

```vue
<script setup>
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import PanelHeader from '@/components/shared/PanelHeader.vue'
import PanelNavSidebar from './PanelNavSidebar.vue'
import ChatModule from '@/components/chat/ChatModule.vue'
import FlashcardModule from '@/components/flashcard/FlashcardModule.vue'
import MindmapModule from '@/components/generate/MindmapModule.vue'
import SummaryModule from '@/components/generate/SummaryModule.vue'
import LlmConfigDialog from '../LlmConfigDialog.vue'

const uiStore = useUiStore()
const showConfig = ref(false)

const handleModuleChange = (moduleId) => {
  uiStore.setActiveModule(moduleId)
}

const handleSettings = () => {
  showConfig.value = true
}

const handleMinimize = () => {
  uiStore.toggleAgentPanel()
}

const renderModule = () => {
  switch (uiStore.activeModule) {
    case 'chat':
      return ChatModule
    case 'flashcard':
      return FlashcardModule
    case 'mindmap':
      return MindmapModule
    case 'summary':
      return SummaryModule
    default:
      return ChatModule
  }
}
</script>

<template>
  <div class="agent-panel">
    <PanelHeader @settings="handleSettings" @minimize="handleMinimize" />
    <div class="panel-body">
      <div class="panel-content">
        <transition name="fade" mode="out-in">
          <component :is="renderModule()" :key="uiStore.activeModule" />
        </transition>
      </div>
      <PanelNavSidebar :active-module="uiStore.activeModule" @change="handleModuleChange" />
    </div>
    <LlmConfigDialog v-model="showConfig" />
  </div>
</template>

<style scoped>
.agent-panel {
  width: 45%;
  min-width: 450px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-lighter);
}

.panel-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.panel-content {
  flex: 1;
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

---

### 任务 5：清理旧代码

**文件：**
- 删除：`src/components/generate/GenerateModule.vue`
- 删除：`src/components/AiGeneratorPanel.vue`

**步骤 5.1：删除旧文件**

删除不再需要的 `GenerateModule.vue` 和 `AiGeneratorPanel.vue`。

---

## 验证步骤

### 测试清单

1. **启动应用**
   - 运行 `npm run dev`
   - 运行 `npm run ele` 或 `npm run start`
   - 确认应用正常启动无错误

2. **检查标签页**
   - 确认右侧边栏有4个标签页：对话、闪卡、思维导图、摘要
   - 确认每个标签页有正确的图标

3. **测试模块切换**
   - 点击各个标签页，确认模块切换正常
   - 确认切换时有淡入淡出动画效果

4. **测试思维导图功能**
   - 打开一个 Markdown 文档
   - 点击「思维导图」标签页
   - 点击「生成思维导图」按钮
   - 确认思维导图正确显示

5. **测试摘要功能**
   - 打开一个 Markdown 文档
   - 点击「摘要」标签页
   - 点击「生成摘要」按钮
   - 确认摘要正确显示

6. **代码质量检查**
   - 运行 `npm run lint` 确认无 lint 错误
   - 运行 `npm run format` 确认代码格式化正确
   - 运行 `npm run test:unit` 确认所有测试通过

---

## 回滚方案

如果重构出现问题，可以按以下步骤回滚：

```bash
# 查看当前修改
git status
git diff

# 如果有提交， revert 最后一次提交
git revert HEAD

# 或者直接恢复未提交的修改
git checkout -- src/components/Layout/PanelNavSidebar.vue
git checkout -- src/components/Layout/AgentPanel.vue

# 删除新建的文件
rm -f src/components/mindmap/MindmapGenerator.vue
rm -f src/components/generate/MindmapModule.vue
rm -f src/components/summary/SummaryGenerator.vue
rm -f src/components/generate/SummaryModule.vue

# 恢复删除的文件（如果需要）
git checkout -- src/components/generate/GenerateModule.vue
git checkout -- src/components/AiGeneratorPanel.vue
```

---

## 总结

本次重构将：
- ✅ 移除重复的闪卡功能入口
- ✅ 将思维导图和摘要独立为单独的标签页
- ✅ 使代码结构更模块化，职责更清晰
- ✅ 提升用户体验，功能入口更直观

**完成标准：**
- 所有4个标签页正常工作
- 思维导图和摘要功能正常
- 无 lint 错误和测试失败
- 用户体验流畅
