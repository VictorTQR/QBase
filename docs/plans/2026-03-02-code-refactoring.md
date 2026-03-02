# QBase 代码重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 清理 QBase 项目中的冗余代码、重复逻辑和未使用文件，提高代码可维护性，删除约 9 个文件，减少约 500+ 行冗余代码。

**Architecture:** 分四个阶段执行：删除未使用文件 → 移除包装组件 → 提取全局动画 → 统一状态映射。每个阶段包含明确的任务和验证步骤。

**Tech Stack:** Vue 3, Pinia, Element Plus, Electron

---

## 前置检查

在开始前确认：
- [ ] 确认在正确的 Git 分支
- [ ] 运行 `npm run lint` 确认当前代码无错误
- [ ] 备份或提交当前工作

---

## 阶段 1: 删除未使用文件

### Task 1: 删除旧版解析组件（5个文件）

**Files:**
- Delete: `app/src/components/Layout/ParseManager.vue
- Delete: `app/src/components/Layout/ParseQueue.vue
- Delete: `app/src/components/Layout/ParseDetails.vue
- Delete: `app/src/components/Layout/ParseDocumentList.vue
- Delete: `app/src/components/Layout/ParseStats.vue

**Step 1: 确认文件存在

```bash
cd app/src/components/Layout
ls -la Parse*.vue
```

**Step 2: 删除文件

```bash
rm ParseManager.vue ParseQueue.vue ParseDetails.vue ParseDocumentList.vue ParseStats.vue
```

**Step 3: 验证删除成功

```bash
ls -la Parse*.vue
```
Expected: No files found

**Step 4: 提交**

```bash
cd ../../..
git add -u
git commit -m "refactor: 删除未使用的旧版解析组件"
```

---

### Task 2: 删除未使用的 counter store

**Files:**
- Delete: `app/src/stores/counter.js

**Step 1: 确认文件存在

```bash
cd app/src/stores
ls -la counter.js
```

**Step 2: 删除文件

```bash
rm counter.js
```

**Step 3: 验证删除成功

```bash
ls -la counter.js
```
Expected: No such file or directory

**Step 4: 提交**

```bash
cd ../../..
git add -u
git commit -m "refactor: 删除未使用的 counter store"
```

---

## 阶段 2: 移除包装组件

### Task 3: 更新 AgentPanel.vue 移除包装组件引用

**Files:**
- Modify: `app/src/components/Layout/AgentPanel.vue`

**Step 1: 读取当前文件内容

```bash
cd app
cat src/components/Layout/AgentPanel.vue
```

**Step 2: 修改导入语句**

将：
```javascript
import FlashcardModule from '@/components/flashcard/FlashcardModule.vue'
import MindmapModule from '@/components/generate/MindmapModule.vue'
import SummaryModule from '@/components/generate/SummaryModule.vue'
```

替换为：
```javascript
import FlashcardPanel from '@/components/flashcards/FlashcardPanel.vue'
import MindmapGenerator from '@/components/mindmap/MindmapGenerator.vue'
import SummaryGenerator from '@/components/summary/SummaryGenerator.vue'
```

**Step 3: 修改 renderModule 函数**

将：
```javascript
case 'flashcard':
  return FlashcardModule
case 'mindmap':
  return MindmapModule
case 'summary':
  return SummaryModule
```

替换为：
```javascript
case 'flashcard':
  return FlashcardPanel
case 'mindmap':
  return MindmapGenerator
case 'summary':
  return SummaryGenerator
```

**Step 4: 运行 lint 检查

```bash
npm run lint
```

**Step 5: 提交**

```bash
git add src/components/Layout/AgentPanel.vue
git commit -m "refactor: 更新 AgentPanel 使用直接组件引用"
```

---

### Task 4: 为 SummaryGenerator 添加容器样式

**Files:**
- Modify: `app/src/components/summary/SummaryGenerator.vue`

**Step 1: 读取当前样式部分**

```bash
cd app
cat src/components/summary/SummaryGenerator.vue
```

**Step 2: 添加样式**

在 `<style scoped>` 中添加：

```css
.summary-generator {
  height: 100%;
  overflow-y: auto;
}
```

**Step 3: 运行 lint 检查

```bash
npm run lint
```

**Step 4: 提交**

```bash
git add src/components/summary/SummaryGenerator.vue
git commit -m "refactor: 为 SummaryGenerator 添加容器样式"
```

---

### Task 5: 为 MindmapGenerator 添加容器样式

**Files:**
- Modify: `app/src/components/mindmap/MindmapGenerator.vue`

**Step 1: 读取当前样式部分**

```bash
cd app
cat src/components/mindmap/MindmapGenerator.vue
```

**Step 2: 添加样式**

在 `<style scoped>` 中添加：

```css
.mindmap-generator {
  height: 100%;
  overflow-y: auto;
}
```

**Step 3: 运行 lint 检查

```bash
npm run lint
```

**Step 4: 提交**

```bash
git add src/components/mindmap/MindmapGenerator.vue
git commit -m "refactor: 为 MindmapGenerator 添加容器样式"
```

---

### Task 6: 删除包装组件（3个文件）

**Files:**
- Delete: `app/src/components/flashcard/FlashcardModule.vue
- Delete: `app/src/components/generate/SummaryModule.vue
- Delete: `app/src/components/generate/MindmapModule.vue

**Step 1: 确认文件存在

```bash
cd app/src/components
ls -la flashcard/FlashcardModule.vue
ls -la generate/SummaryModule.vue
ls -la generate/MindmapModule.vue
```

**Step 2: 删除文件

```bash
rm flashcard/FlashcardModule.vue
rm generate/SummaryModule.vue
rm generate/MindmapModule.vue
```

**Step 3: 验证删除成功

```bash
ls -la flashcard/FlashcardModule.vue
ls -la generate/SummaryModule.vue
ls -la generate/MindmapModule.vue
```
Expected: No such file or directory

**Step 4: 提交**

```bash
cd ../../..
git add -u
git commit -m "refactor: 删除多余的包装组件"
```

---

## 阶段 3: 提取全局动画

### Task 7: 创建全局动画样式文件

**Files:**
- Create: `app/src/styles/animations.css`

**Step 1: 创建 styles 目录（如需要）

```bash
cd app/src
mkdir -p styles
```

**Step 2: 创建动画文件

```bash
cat > styles/animations.css << 'EOF'
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
EOF
```

**Step 3: 验证文件内容

```bash
cat styles/animations.css
```

**Step 4: 提交**

```bash
cd ../..
git add app/src/styles/animations.css
git commit -m "refactor: 创建全局动画样式文件"
```

---

### Task 8: 在 main.js 中引入动画样式

**Files:**
- Modify: `app/src/main.js`

**Step 1: 读取当前文件

```bash
cd app
cat src/main.js
```

**Step 2: 添加导入语句**

在导入部分添加：

```javascript
import './styles/animations.css'
```

**Step 3: 运行 lint 检查

```bash
npm run lint
```

**Step 4: 提交**

```bash
git add src/main.js
git commit -m "refactor: 在 main.js 引入全局动画"
```

---

### Task 9: 从 ParseDocumentsView 移除动画定义

**Files:**
- Modify: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1: 读取当前文件**

```bash
cd app
cat src/components/parse/ParseDocumentsView.vue
```

**Step 2: 删除动画定义**

删除以下内容：

```css
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

**Step 3: 运行 lint 检查

```bash
npm run lint
```

**Step 4: 提交**

```bash
git add src/components/parse/ParseDocumentsView.vue
git commit -m "refactor: 从 ParseDocumentsView 移除重复动画"
```

---

## 阶段 4: 统一状态映射

### Task 10: 在 parse store 中添加状态映射函数

**Files:**
- Modify: `app/src/stores/parse.js`

**Step 1: 读取当前文件**

```bash
cd app
cat src/stores/parse.js
```

**Step 2: 添加状态映射函数**

在 store 定义中（在 return 语句之前添加：

```javascript
function getStatusType(status) {
  const map = {
    completed: 'success',
    parsing: 'primary',
    pending: 'warning',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    completed: '已完成',
    parsing: '解析中',
    pending: '待解析',
    failed: '失败',
  }
  return map[status] || status
}
```

**Step 3: 在 return 语句中导出**

在 return 对象中添加：

```javascript
getStatusType,
getStatusLabel,
```

**Step 4: 运行 lint 检查

```bash
npm run lint
```

**Step 5: 提交**

```bash
git add src/stores/parse.js
git commit -m "refactor: 在 parse store 添加状态映射"
```

---

### Task 11: 更新 ParseDocumentsView 使用 store 中的状态映射

**Files:**
- Modify: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1: 读取当前文件**

```bash
cd app
cat src/components/parse/ParseDocumentsView.vue
```

**Step 2: 删除本地函数**

删除以下本地函数定义：
- `getStatusType()`
- `getStatusLabel()`

**Step 3: 使用 store 中的函数**

将所有 `getStatusType()` 替换为 `parseStore.getStatusType()`
将所有 `getStatusLabel()` 替换为 `parseStore.getStatusLabel()`

**Step 4: 运行 lint 检查

```bash
npm run lint
```

**Step 5: 提交**

```bash
git add src/components/parse/ParseDocumentsView.vue
git commit -m "refactor: ParseDocumentsView 使用 store 状态映射"
```

---

### Task 12: 更新 ParseDetailsDrawer 使用 store 中的状态映射

**Files:**
- Modify: `app/src/components/parse/ParseDetailsDrawer.vue`

**Step 1: 读取当前文件**

```bash
cd app
cat src/components/parse/ParseDetailsDrawer.vue
```

**Step 2: 删除本地函数**

删除以下本地函数定义（如果存在）：
- `getStatusType()`
- `getStatusLabel()`

**Step 3: 使用 store 中的函数**

将所有 `getStatusType()` 替换为 `parseStore.getStatusType()`
将所有 `getStatusLabel()` 替换为 `parseStore.getStatusLabel()`

**Step 4: 运行 lint 检查

```bash
npm run lint
```

**Step 5: 提交**

```bash
git add src/components/parse/ParseDetailsDrawer.vue
git commit -m "refactor: ParseDetailsDrawer 使用 store 状态映射"
```

---

## 最终验证

### Task 13: 完整测试验证

**Step 1: 运行 lint 检查

```bash
cd app
npm run lint
```

**Step 2: 运行测试

```bash
npm run test:unit
```

**Step 3: 启动开发服务器验证

```bash
npm run dev
```

手动验证：
- [ ] 应用正常启动
- [ ] 路由导航正常
- [ ] 解析管理页面正常
- [ ] AI 助手面板所有模块正常（聊天、闪卡、思维导图、摘要）
- [ ] 无控制台错误

**Step 4: 查看 git 状态

```bash
git status
git log --oneline -12
```

---

## 总结

本次重构完成后：
- 删除文件：9 个
- 减少代码量：约 500+ 行
- 功能影响：无

---

## 回滚计划

如遇问题可按提交历史回滚：

```bash
git log --oneline
git reset --hard <commit-hash>
```
