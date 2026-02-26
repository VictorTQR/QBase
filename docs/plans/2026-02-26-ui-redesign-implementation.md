# UI 界面重新设计实施计划

&gt; **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 重构 QBase 的 UI 界面，采用右侧边栏导航 + 统一功能面板的设计

**架构:** 
- 保持现有三栏布局，重构右侧 AgentPanel
- 添加右侧导航侧边栏 (PanelNavSidebar)
- 模块化各功能组件 (对话/闪卡/生成)
- 保持现有 store 逻辑不变

**技术栈:** Vue 3 + Element Plus + Pinia

---

## 前置准备

### 检查现有文件
先阅读以下关键文件了解当前实现：
- `app/src/components/Layout/AgentPanel.vue` - 当前右侧面板
- `app/src/stores/agent.js` - AI 功能状态管理
- `app/src/stores/flashcard.js` - 闪卡状态管理

---

## 阶段一：基础框架

### Task 1: 创建共享组件 PanelHeader

**文件:**
- Create: `app/src/components/shared/PanelHeader.vue`

**Step 1: 创建 PanelHeader 组件**

```vue
&lt;script setup&gt;
defineProps({
  title: {
    type: String,
    default: 'AI 助手'
  }
})

const emit = defineEmits(['settings', 'minimize'])
&lt;/script&gt;

&lt;template&gt;
  &lt;div class="panel-header"&gt;
    &lt;span class="panel-title"&gt;{{ title }}&lt;/span&gt;
    &lt;div class="header-actions"&gt;
      &lt;el-button size="small" circle @click="$emit('settings')"&gt;
        &lt;el-icon&gt;&lt;Setting /&gt;&lt;/el-icon&gt;
      &lt;/el-button&gt;
      &lt;el-button size="small" circle @click="$emit('minimize')"&gt;
        &lt;el-icon&gt;&lt;Minus /&gt;&lt;/el-icon&gt;
      &lt;/el-button&gt;
    &lt;/div&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped&gt;
.panel-header {
  height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.panel-title {
  font-weight: 600;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
}
&lt;/style&gt;
```

**Step 2: 提交**

```bash
cd app
git add src/components/shared/PanelHeader.vue
git commit -m "feat: add PanelHeader shared component"
```

---

### Task 2: 创建导航侧边栏 PanelNavSidebar

**文件:**
- Create: `app/src/components/Layout/PanelNavSidebar.vue`

**Step 1: 创建 PanelNavSidebar 组件**

```vue
&lt;script setup&gt;
import { computed } from 'vue'
import { ChatDotRound, Tickets, MagicStick } from '@element-plus/icons-vue'

const props = defineProps({
  activeModule: {
    type: String,
    default: 'chat'
  }
})

const emit = defineEmits(['change'])

const navItems = [
  { id: 'chat', icon: ChatDotRound, label: '对话' },
  { id: 'flashcard', icon: Tickets, label: '闪卡' },
  { id: 'generate', icon: MagicStick, label: '生成' }
]

const isActive = computed(() =&gt; (id) =&gt; props.activeModule === id)

const handleClick = (item) =&gt; {
  emit('change', item.id)
}
&lt;/script&gt;

&lt;template&gt;
  &lt;div class="panel-nav-sidebar"&gt;
    &lt;div
      v-for="item in navItems"
      :key="item.id"
      class="nav-item"
      :class="{ active: isActive(item.id) }"
      @click="handleClick(item)"
    &gt;
      &lt;el-icon :size="20"&gt;
        &lt;component :is="item.icon" /&gt;
      &lt;/el-icon&gt;
      &lt;span class="nav-label"&gt;{{ item.label }}&lt;/span&gt;
    &lt;/div&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped&gt;
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
&lt;/style&gt;
```

**Step 2: 提交**

```bash
git add src/components/Layout/PanelNavSidebar.vue
git commit -m "feat: add PanelNavSidebar component"
```

---

### Task 3: 创建 UI Store

**文件:**
- Create: `app/src/stores/ui.js`

**Step 1: 创建 ui.js store**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () =&gt; {
  const activeModule = ref('chat')
  const isAgentPanelVisible = ref(true)
  const isFlashcardFocusMode = ref(false)

  function setActiveModule(moduleId) {
    activeModule.value = moduleId
  }

  function toggleAgentPanel() {
    isAgentPanelVisible.value = !isAgentPanelVisible.value
  }

  function toggleFlashcardFocusMode() {
    isFlashcardFocusMode.value = !isFlashcardFocusMode.value
  }

  return {
    activeModule,
    isAgentPanelVisible,
    isFlashcardFocusMode,
    setActiveModule,
    toggleAgentPanel,
    toggleFlashcardFocusMode
  }
})
```

**Step 2: 提交**

```bash
git add src/stores/ui.js
git commit -m "feat: add ui store for panel state management"
```

---

### Task 4: 重构 AgentPanel 主容器

**文件:**
- Modify: `app/src/components/Layout/AgentPanel.vue`

**Step 1: 备份当前 AgentPanel.vue (先读取内容)**

**Step 2: 重写 AgentPanel.vue**

```vue
&lt;script setup&gt;
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import PanelHeader from '@/shared/PanelHeader.vue'
import PanelNavSidebar from './PanelNavSidebar.vue'
import ChatModule from '@/chat/ChatModule.vue'
import FlashcardModule from '@/flashcard/FlashcardModule.vue'
import GenerateModule from '@/generate/GenerateModule.vue'

const uiStore = useUiStore()
const showConfig = ref(false)

const handleModuleChange = (moduleId) =&gt; {
  uiStore.setActiveModule(moduleId)
}

const handleSettings = () =&gt; {
  showConfig.value = true
}

const handleMinimize = () =&gt; {
  uiStore.toggleAgentPanel()
}

const renderModule = () =&gt; {
  switch (uiStore.activeModule) {
    case 'chat':
      return &lt;ChatModule /&gt;
    case 'flashcard':
      return &lt;FlashcardModule /&gt;
    case 'generate':
      return &lt;GenerateModule /&gt;
    default:
      return &lt;ChatModule /&gt;
  }
}
&lt;/script&gt;

&lt;template&gt;
  &lt;div class="agent-panel"&gt;
    &lt;PanelHeader @settings="handleSettings" @minimize="handleMinimize" /&gt;
    &lt;div class="panel-body"&gt;
      &lt;div class="panel-content"&gt;
        &lt;component :is="renderModule()" /&gt;
      &lt;/div&gt;
      &lt;PanelNavSidebar :active-module="uiStore.activeModule" @change="handleModuleChange" /&gt;
    &lt;/div&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped&gt;
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
&lt;/style&gt;
```

**注意:** 此时 ChatModule、FlashcardModule、GenerateModule 还不存在，我们会在后续任务中创建。先注释掉这些组件引用，让基础框架能运行。

**Step 3: 临时调整 - 使用旧内容作为占位**

修改 renderModule 函数暂时显示旧内容，或者创建简单的占位组件。

**Step 4: 提交**

```bash
git add src/components/Layout/AgentPanel.vue
git commit -m "feat: refactor AgentPanel with new layout structure"
```

---

## 阶段二：对话模块

### Task 5: 创建 ChatModule 对话模块

**文件:**
- Create: `app/src/components/chat/ChatModule.vue`
- Create: `app/src/components/chat/MessageList.vue`
- Create: `app/src/components/chat/MessageBubble.vue`
- Create: `app/src/components/chat/InputSender.vue`

**Step 1: 从现有 AgentPanel.vue 提取对话相关代码**

先阅读当前 AgentPanel.vue 的内容，提取：
- BubbleList 的使用
- Sender 的使用
- 会话管理逻辑

**Step 2: 创建 ChatModule.vue**

```vue
&lt;script setup&gt;
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useWorkspaceStore } from '@/stores/workspace'
import BubbleList from '@/BubbleList.vue'
import Sender from '@/Sender.vue'
import SessionSidebar from './SessionSidebar.vue'

const agentStore = useAgentStore()
const workspaceStore = useWorkspaceStore()

const inputValue = ref('')
const includeContext = ref(true)
const maxHeight = ref(0)
const showSessionSidebar = ref(true)
const bubbleListRef = ref(null)

const bubbleList = computed(() =&gt; agentStore.currentSession?.messages || [])

const handleSubmit = async (content) =&gt; {
  if (!content.trim() || agentStore.isLoading) return
  
  const currentFile = workspaceStore.currentFile
  const context = includeContext.value &amp;&amp; currentFile?.content ? currentFile.content : null
  
  await agentStore.sendMessage(content, context)
  inputValue.value = ''
}

const handleClear = () =&gt; {
  agentStore.clearCurrentSession()
}

onMounted(() =&gt; {
  updateMaxHeight()
  window.addEventListener('resize', updateMaxHeight)
})

const updateMaxHeight = () =&gt; {
  nextTick(() =&gt; {
    maxHeight.value = 400
  })
}

watch(() =&gt; bubbleList.value.length, () =&gt; {
  nextTick(() =&gt; {
    bubbleListRef.value?.scrollToBottom()
  })
})
&lt;/script&gt;

&lt;template&gt;
  &lt;div class="chat-module"&gt;
    &lt;div class="chat-header"&gt;
      &lt;el-button size="small" text @click="showSessionSidebar = !showSessionSidebar"&gt;
        &lt;el-icon&gt;&lt;List /&gt;&lt;/el-icon&gt;
        会话
      &lt;/el-button&gt;
      &lt;span class="current-session-title"&gt;{{ agentStore.currentSession?.title || 'AI 助手' }}&lt;/span&gt;
      &lt;div class="header-actions"&gt;
        &lt;el-button size="small" circle @click="handleClear"&gt;
          &lt;el-icon&gt;&lt;Delete /&gt;&lt;/el-icon&gt;
        &lt;/el-button&gt;
      &lt;/div&gt;
    &lt;/div&gt;
    
    &lt;div class="chat-body"&gt;
      &lt;SessionSidebar v-if="showSessionSidebar" /&gt;
      &lt;div class="chat-content"&gt;
        &lt;div class="messages-container"&gt;
          &lt;BubbleList :list="bubbleList" :max-height="maxHeight" ref="bubbleListRef" /&gt;
        &lt;/div&gt;
        &lt;div class="chat-footer"&gt;
          &lt;div class="context-toggle"&gt;
            &lt;el-checkbox v-model="includeContext" size="small"&gt;包含当前文档&lt;/el-checkbox&gt;
          &lt;/div&gt;
          &lt;Sender 
            v-model="inputValue" 
            :loading="agentStore.isLoading" 
            placeholder="输入消息..." 
            @submit="handleSubmit" 
          /&gt;
        &lt;/div&gt;
      &lt;/div&gt;
    &lt;/div&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped&gt;
.chat-module {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  height: 40px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.current-session-title {
  flex: 1;
  font-weight: 500;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

.chat-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.context-toggle {
  margin-bottom: 8px;
}
&lt;/style&gt;
```

**Step 3: 从 AgentPanel 移动 SessionSidebar 到 chat 目录**

创建 `app/src/components/chat/SessionSidebar.vue`，从原位置移动代码。

**Step 4: 提交**

```bash
git add src/components/chat/
git commit -m "feat: create ChatModule component"
```

---

## 阶段三：闪卡模块

### Task 6: 重构 FlashcardModule

**文件:**
- Modify: `app/src/components/flashcards/FlashcardPanel.vue` -&gt; 重命名并重构
- Create: `app/src/components/flashcard/FlashcardModule.vue`
- Create: `app/src/components/flashcard/FlashcardPreview.vue`
- Create: `app/src/components/flashcard/FlashcardFocus.vue`

**Step 1: 阅读现有 FlashcardPanel.vue**

**Step 2: 创建 FlashcardModule.vue**

```vue
&lt;script setup&gt;
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import FlashcardPreview from './FlashcardPreview.vue'
import FlashcardFocus from './FlashcardFocus.vue'
import FlashcardGenerator from './FlashcardGenerator.vue'

const uiStore = useUiStore()
const activeTab = ref('preview')
&lt;/script&gt;

&lt;template&gt;
  &lt;div class="flashcard-module"&gt;
    &lt;div class="flashcard-header"&gt;
      &lt;el-radio-group v-model="activeTab" size="small"&gt;
        &lt;el-radio-button label="preview"&gt;闪卡列表&lt;/el-radio-button&gt;
        &lt;el-radio-button label="generate"&gt;生成闪卡&lt;/el-radio-button&gt;
      &lt;/el-radio-group&gt;
      &lt;el-button 
        v-if="activeTab === 'preview'" 
        size="small" 
        type="primary" 
        @click="uiStore.toggleFlashcardFocusMode"
      &gt;
        &lt;el-icon&gt;&lt;FullScreen /&gt;&lt;/el-icon&gt;
        专注模式
      &lt;/el-button&gt;
    &lt;/div&gt;
    
    &lt;div class="flashcard-content"&gt;
      &lt;FlashcardFocus v-if="uiStore.isFlashcardFocusMode" /&gt;
      &lt;FlashcardPreview v-else-if="activeTab === 'preview'" /&gt;
      &lt;FlashcardGenerator v-else-if="activeTab === 'generate'" /&gt;
    &lt;/div&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped&gt;
.flashcard-module {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.flashcard-header {
  height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.flashcard-content {
  flex: 1;
  overflow: hidden;
}
&lt;/style&gt;
```

**Step 3: 创建 FlashcardPreview.vue 和 FlashcardFocus.vue**

从现有 FlashcardViewer 提取代码进行拆分。

**Step 4: 提交**

```bash
git add src/components/flashcard/
git commit -m "feat: refactor FlashcardModule with mixed mode"
```

---

## 阶段四：生成模块

### Task 7: 创建 GenerateModule

**文件:**
- Create: `app/src/components/generate/GenerateModule.vue`
- Create: `app/src/components/generate/FlashcardTab.vue`
- Create: `app/src/components/generate/MindmapTab.vue`
- Create: `app/src/components/generate/SummaryTab.vue`

**Step 1: 阅读现有 AiGeneratorPanel.vue**

**Step 2: 创建 GenerateModule.vue**

```vue
&lt;script setup&gt;
import { ref } from 'vue'
import FlashcardTab from './FlashcardTab.vue'
import MindmapTab from './MindmapTab.vue'
import SummaryTab from './SummaryTab.vue'

const activeTab = ref('flashcard')
&lt;/script&gt;

&lt;template&gt;
  &lt;div class="generate-module"&gt;
    &lt;el-tabs v-model="activeTab" type="card" class="generate-tabs"&gt;
      &lt;el-tab-pane label="闪卡" name="flashcard"&gt;
        &lt;FlashcardTab /&gt;
      &lt;/el-tab-pane&gt;
      &lt;el-tab-pane label="思维导图" name="mindmap"&gt;
        &lt;MindmapTab /&gt;
      &lt;/el-tab-pane&gt;
      &lt;el-tab-pane label="摘要" name="summary"&gt;
        &lt;SummaryTab /&gt;
      &lt;/el-tab-pane&gt;
    &lt;/el-tabs&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;style scoped&gt;
.generate-module {
  height: 100%;
  padding: 16px;
  overflow-y: auto;
}

.generate-tabs {
  height: 100%;
}
&lt;/style&gt;
```

**Step 3: 创建各标签页组件**

从 AiGeneratorPanel 提取代码拆分到各标签组件。

**Step 4: 提交**

```bash
git add src/components/generate/
git commit -m "feat: create GenerateModule with tabbed interface"
```

---

## 阶段五：整合与优化

### Task 8: 整合所有模块到 AgentPanel

**文件:**
- Modify: `app/src/components/Layout/AgentPanel.vue`

**Step 1: 取消注释，导入所有模块组件**

**Step 2: 测试完整流程**

**Step 3: 提交**

```bash
git add src/components/Layout/AgentPanel.vue
git commit -m "feat: integrate all modules into AgentPanel"
```

---

### Task 9: 添加动画和过渡效果

**文件:**
- Modify: 相关组件添加 transition

**Step 1: 在 AgentPanel 添加模块切换过渡**
**Step 2: 在导航项添加动画**
**Step 3: 提交**

```bash
git add ...
git commit -m "feat: add smooth transitions and animations"
```

---

### Task 10: 运行测试和代码检查

**Step 1: 运行 lint**

```bash
npm run lint
```

**Step 2: 运行格式化**

```bash
npm run format
```

**Step 3: 运行单元测试**

```bash
npm run test:unit
```

**Step 4: 手动测试**

- 测试导航切换
- 测试各功能模块
- 测试闪卡混合模式
- 测试响应式布局

---

## 测试步骤

### 功能测试清单
1. [ ] 右侧导航栏显示正确
2. [ ] 点击导航可以切换模块
3. [ ] 对话功能正常工作
4. [ ] 闪卡小面板模式正常
5. [ ] 闪卡专注模式可以切换
6. [ ] 生成功能各标签页正常
7. [ ] 响应式布局正常
8. [ ] 动画过渡流畅

---

## 注意事项

1. 保持现有 store 不变，只修改 UI 层
2. 渐进式迁移，确保每一步都能正常运行
3. 保留旧代码作为参考，确认新代码工作正常后再删除
4. 频繁提交，便于回滚

---

**计划完成**
