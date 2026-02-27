# YAML Frontmatter 处理实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 实现 YAML frontmatter 的解析、结构化显示和搜索集成。

**架构:**
1. 在 document store 中添加 gray-matter 解析逻辑，分离 frontmatter 数据和正文
2. 创建 FrontmatterCard 组件来结构化显示元数据
3. 修改 MarkdownViewer 集成 frontmatter 显示
4. 更新搜索逻辑，使 frontmatter 参与搜索匹配

**技术栈:** gray-matter (已安装), Element Plus, Vue 3

---

## 任务清单

### 任务 1: 更新 document store 添加 frontmatter 解析

**文件:**
- 修改: `app/src/stores/document.js`

**步骤 1: 修改 document store**

在 `document.js` 中:
1. 导入 gray-matter
2. 添加 `frontmatter` state
3. 修改 `loadFile()` 函数，解析 Markdown 文件时分离 frontmatter 和正文

**预期代码变更:**

```javascript
import matter from 'gray-matter'

// 在 state 中添加
const frontmatter = ref({})

// 修改 loadFile()
if (result.success) {
  if (fileType === 'markdown') {
    const parsed = matter(result.content)
    content.value = parsed.content
    frontmatter.value = parsed.data
  } else {
    content.value = result.content
    frontmatter.value = {}
  }
}

// 在 return 中添加 frontmatter
return { ..., frontmatter, ... }
```

---

### 任务 2: 创建 FrontmatterCard 组件

**文件:**
- 创建: `app/src/components/FrontmatterCard.vue`

**步骤 1: 创建组件文件**

支持的字段：
- `title` - 标题（突出显示）
- `date` - 日期
- `author` - 作者
- `tags` - 标签（数组）
- `description` - 描述
- 其他字段 - 降级显示为键值对

**组件结构:**
```vue
<template>
  <div class="frontmatter-card" v-if="hasData">
    <!-- title -->
    <!-- date, author -->
    <!-- tags -->
    <!-- description -->
    <!-- 其他字段 -->
  </div>
</template>
```

---

### 任务 3: 修改 MarkdownViewer 集成 FrontmatterCard

**文件:**
- 修改: `app/src/components/MarkdownViewer.vue`

**步骤 1: 更新 MarkdownViewer**

1. 从 document store 获取 frontmatter
2. 在 XMarkdown 上方渲染 FrontmatterCard

---

### 任务 4: 更新搜索逻辑使 frontmatter 参与搜索

**文件:**
- 修改: `app/electron/main.js:388-439` (search-files 处理器)

**步骤 1: 在主进程中集成 gray-matter**

1. 在 main.js 顶部导入 gray-matter
2. 修改搜索逻辑，解析 frontmatter 后合并 frontmatter 和正文再搜索

**关键点:**
- 保持当前的文件名优先匹配
- 内容搜索时使用 `frontmatter 字段值 + '\n' + 正文` 进行匹配
- snippet 提取要考虑 frontmatter 的情况

---

### 任务 5: 更新 markdown-preview.md 功能文档

**文件:**
- 修改: `docs/features/markdown-preview.md`

**步骤 1: 更新文档**

添加 YAML frontmatter 处理的相关说明。

---

## 测试步骤

手动测试验证：

1. 准备一个带 frontmatter 的测试文件:
```markdown
---
title: 测试文档
date: 2026-02-27
author: Test Author
tags: [vue, electron, test]
description: 这是一个测试文档
---

# 正文标题

这是正文内容...
```

2. 打开该文件，验证:
   - frontmatter 被正确解析
   - 显示为结构化卡片
   - 正文正常渲染

3. 测试搜索:
   - 搜索 "测试文档" 应能匹配
   - 搜索 "vue" 应能匹配 tags
   - 搜索 "Test Author" 应能匹配

---

## 交付标准

- [ ] document store 正确解析 frontmatter
- [ ] FrontmatterCard 组件美观显示常见字段
- [ ] 不常见字段正确降级显示
- [ ] 搜索功能正常匹配 frontmatter
- [ ] 无回归问题（现有功能正常工作）
