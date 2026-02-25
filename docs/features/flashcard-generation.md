# 智能闪卡生成

**状态**: ✅ 已完成
**版本**: v0.4

---

## 概述

基于 LLM 的智能闪卡生成功能，类似 NotebookLM，可以从当前打开的文档自动生成问答式闪卡，用于学习和记忆。

---

## 功能特性

### 1. 闪卡生成

- 基于当前打开的 Markdown 文档生成
- 支持自定义闪卡数量（5-20 张）
- 自动难度分级（easy/medium/hard）
- 使用 LLM 智能生成问题和答案

### 2. 闪卡查看

- 卡片翻转动画（问题/答案切换）
- 前后翻页导航
- 进度显示（当前/总数）
- 难度标签展示

### 3. 学习管理

- 标记卡片为"已掌握"
- 闪卡集持久化存储
- 闪卡集列表管理
- 创建和删除闪卡集

### 4. UI 集成

- AgentPanel 双模式切换（对话/闪卡）
- 三个标签页：生成闪卡、闪卡列表、学习模式
- 流畅的用户体验

---

## 数据结构

### 闪卡集合 (FlashcardSet)

```javascript
{
  id: string,                    // UUID
  title: string,                 // 标题（基于文档名）
  sourceFile: string,            // 来源文件路径
  createdAt: string,             // ISO 8601
  updatedAt: string,             // ISO 8601
  flashcards: Flashcard[]        // 闪卡数组
}
```

### 闪卡 (Flashcard)

```javascript
{
  id: string,                    // UUID
  front: string,                 // 问题面
  back: string,                  // 答案面
  difficulty: 'easy' | 'medium' | 'hard',
  mastered: boolean,             // 是否已掌握
  lastReviewed: string | null,   // 最后复习时间
  createdAt: string              // ISO 8601
}
```

---

## 组件说明

### FlashcardPanel

闪卡主面板，整合所有闪卡功能。

**位置**: `src/components/flashcards/FlashcardPanel.vue`

**标签页**:
1. **生成闪卡** - 配置并生成新的闪卡集
2. **闪卡列表** - 查看和管理所有闪卡集
3. **学习模式** - 查看和学习闪卡

### FlashcardGenerator

闪卡生成器组件。

**位置**: `src/components/flashcards/FlashcardGenerator.vue`

**功能**:
- 闪卡数量滑块（5-20）
- 生成按钮
- 加载状态显示
- 错误提示

### FlashcardViewer

闪卡查看器组件。

**位置**: `src/components/flashcards/FlashcardViewer.vue`

**功能**:
- 卡片翻转动画
- 前后翻页按钮
- 标记已掌握按钮
- 进度显示

### FlashcardSet

闪卡集列表管理组件。

**位置**: `src/components/flashcards/FlashcardSet.vue`

**功能**:
- 闪卡集列表展示
- 点击选择闪卡集
- 删除闪卡集（带确认）

---

## 使用方法

### 生成闪卡

1. 打开一个 Markdown 文档
2. 在右侧 AgentPanel 切换到"闪卡"标签
3. 点击"生成闪卡"标签
4. 调整闪卡数量（5-20 张）
5. 点击"生成闪卡"按钮
6. 等待生成完成

### 学习闪卡

1. 在"闪卡列表"中选择一个闪卡集
2. 或在生成完成后自动进入"学习模式"
3. 点击卡片查看答案
4. 使用左右按钮或导航键翻页
5. 点击"已掌握"标记卡片

### 管理闪卡集

1. 在"闪卡列表"标签中查看所有闪卡集
2. 点击闪卡集进入学习模式
3. 点击删除按钮删除闪卡集

---

## 提示词设计

**System Prompt**:
```
你是一个专业的学习内容生成助手。请基于以下文档内容生成闪卡。

要求：
1. 生成 {{count}} 个闪卡
2. 问题应该考察对核心概念的理解，而不是简单的事实记忆
3. 答案应该简洁准确，控制在 2-3 句话
4. 输出格式为 JSON 数组，每个元素包含：
   - front: 问题（字符串）
   - back: 答案（字符串）
   - difficulty: 难度（"easy" | "medium" | "hard"）

只返回 JSON，不要其他文字说明。

文档内容：
{{content}}
```

---

## 后续扩展

### 规划中功能

- **艾宾浩斯遗忘曲线复习提醒** - 根据复习间隔自动提醒
- **Anki 格式导出** - 导出为 `.apkg` 格式
- **闪卡编辑功能** - 允许用户修改生成的闪卡
- **闪卡分享功能** - 导出/导入闪卡集
- **批量操作** - 批量标记掌握、批量删除
- **统计功能** - 学习进度统计、掌握率统计

---

## 相关文档

- [实施计划](../plans/2026-02-25-file-format-enhancement.md)
- [实施报告](../implementation/v0.4-complete.md)
