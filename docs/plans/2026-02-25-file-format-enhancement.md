# 文件格式增强与智能内容生成实施计划

**创建日期**: 2026-02-25
**目标版本**: v0.4
**状态**: 📋 已规划

---

## 概述

本次功能扩展分为两个主要部分：
1. **文件格式支持增强** - 增加 PDF、音频、视频格式支持
2. **Agent 能力增强** - 实现闪卡生成功能（类似 NotebookLM）

---

## 一、文件格式支持增强

### 1.1 支持的文件类型

| 类型 | 扩展名 | 查看器 |
|------|--------|--------|
| Markdown | .md | MarkdownViewer（现有） |
| PDF | .pdf | PdfViewer（新增） |
| 音频 | .mp3, .wav, .ogg, .m4a | MediaViewer（新增） |
| 视频 | .mp4, .webm, .mov | MediaViewer（新增） |

### 1.2 技术选型

**PDF 查看器**: pdfjs-dist (Mozilla 官方)
**音视频播放器**: 原生 HTML5 &lt;audio&gt;/&lt;video&gt; + Element Plus 样式

### 1.3 实施步骤

#### Phase 1: 基础设施更新

**1.3.1 安装依赖**
```bash
cd app
npm install pdfjs-dist
```

**1.3.2 更新 Electron IPC**
- `electron/main.js`: 添加 `read-binary-file` handler
- `electron/preload.js`: 暴露 `readBinaryFile` API

**1.3.3 更新文件树过滤**
- `electron/main.js` 的 `read-dir`: 支持新文件类型
- 不再只过滤 `.md`，支持所有目标类型

**1.3.4 更新 Document Store**
- `stores/document.js`: 支持二进制内容存储
- 添加 `contentType` 字段标识文件类型

#### Phase 2: 组件开发

**1.3.5 创建 DocumentViewer 统一分发器**
```
components/DocumentViewer.vue
- 根据文件扩展名选择对应的查看器
- 支持的类型检测逻辑
```

**1.3.6 创建 PdfViewer 组件**
```
components/PdfViewer.vue
- 使用 pdfjs-dist 渲染 PDF
- 基础功能：翻页、缩放
- 预留接口：分页懒加载、文本搜索（后续版本）
```

**1.3.7 创建 MediaViewer 组件**
```
components/MediaViewer.vue
- 音频播放器：播放/暂停、进度条、音量
- 视频播放器：同上 + 全屏支持
- 自动检测媒体类型
```

**1.3.8 更新 ContentPane**
```
components/Layout/ContentPane.vue
- 替换 MarkdownViewer 为 DocumentViewer
- 更新空状态提示文案
```

### 1.4 文件清单

**新增文件**:
```
app/src/components/
├── DocumentViewer.vue       # 统一文档查看器
├── PdfViewer.vue            # PDF 查看器
└── MediaViewer.vue          # 音视频播放器

app/src/repositories/
（预留，后续闪卡功能用）
```

**修改文件**:
```
app/electron/
├── main.js                  # 添加 read-binary-file、更新 read-dir
└── preload.js               # 暴露 readBinaryFile

app/src/stores/
└── document.js              # 支持二进制内容

app/src/components/Layout/
└── ContentPane.vue          # 使用 DocumentViewer
```

---

## 二、Agent 能力增强 - 闪卡生成

### 2.1 功能描述

基于当前打开的文档内容，使用 LLM 智能生成问答式闪卡，用于学习和记忆。

### 2.2 核心特性

- ✅ 基于当前文档生成闪卡
- ✅ 支持自定义闪卡数量（5-20 张）
- ✅ 闪卡查看（前后翻页）
- ✅ 标记掌握状态
- ✅ 闪卡持久化存储
- 🔄 艾宾浩斯复习提醒（后续版本）
- 🔄 导出为 Anki 格式（后续版本）
- ❌ 展示生成过程（不实现）
- ❌ 用户编辑闪卡（暂不实现）

### 2.3 数据结构设计

**闪卡集合 (FlashcardSet)**:
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

**闪卡 (Flashcard)**:
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

### 2.4 提示词设计

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
```

### 2.5 实施步骤

#### Phase 1: 数据层

**2.5.1 创建 Repository 抽象**
```
repositories/FlashcardRepository.js
- 接口定义：getAll, getById, create, update, delete
```

**2.5.2 创建 LocalStorage 实现**
```
repositories/LocalStorageFlashcardRepository.js
- 基于 localStorage 的存储实现
```

**2.5.3 创建 Flashcard Store**
```
stores/flashcard.js
- 闪卡集合管理
- 当前闪卡集状态
- 生成闪卡（调用 agent store）
```

#### Phase 2: 组件开发

**2.5.4 创建闪卡生成器**
```
components/flashcards/FlashcardGenerator.vue
- 闪卡数量选择（5-20）
- 生成按钮
- 加载状态显示
```

**2.5.5 创建闪卡查看器**
```
components/flashcards/FlashcardViewer.vue
- 单张闪卡展示
- 翻转动画（问题/答案切换）
- 左右翻页
- 标记掌握按钮
- 进度指示器（x/总）
```

**2.5.6 创建闪卡集合管理**
```
components/flashcards/FlashcardSet.vue
- 闪卡集列表
- 删除闪卡集
- 选择闪卡集
```

**2.5.7 创建闪卡面板**
```
components/flashcards/FlashcardPanel.vue
- 整合以上组件
- 可折叠面板
- 切换"生成"和"查看"模式
```

#### Phase 3: 集成

**2.5.8 扩展 Agent Store**
```
stores/agent.js
- 添加 generateFlashcards(content, count) 函数
- 调用 LLM API
- 解析 JSON 响应
```

**2.5.9 创建提示词工具**
```
utils/prompts.js
- 闪卡生成提示词模板
```

**2.5.10 集成到 AgentPanel**
```
components/Layout/AgentPanel.vue
- 添加"闪卡"标签页或按钮
- 嵌入 FlashcardPanel
```

### 2.6 文件清单

**新增文件**:
```
app/src/components/flashcards/
├── FlashcardPanel.vue         # 闪卡主面板
├── FlashcardGenerator.vue     # 闪卡生成器
├── FlashcardViewer.vue        # 闪卡查看器
└── FlashcardSet.vue           # 闪卡集管理

app/src/stores/
└── flashcard.js               # 闪卡状态管理

app/src/repositories/
├── FlashcardRepository.js     # 闪卡仓库抽象
└── LocalStorageFlashcardRepository.js  # 本地存储实现

app/src/utils/
└── prompts.js                 # 提示词模板
```

**修改文件**:
```
app/src/stores/
└── agent.js                   # 添加 generateFlashcards

app/src/components/Layout/
└── AgentPanel.vue             # 集成闪卡面板
```

---

## 三、实施优先级与里程碑

### Milestone 1: 文件格式支持（预计 1-2 天）
- [ ] Electron IPC 更新
- [ ] DocumentStore 更新
- [ ] PdfViewer 组件
- [ ] MediaViewer 组件
- [ ] DocumentViewer 分发器
- [ ] 集成测试

### Milestone 2: 闪卡生成基础（预计 2-3 天）
- [ ] Repository 层
- [ ] FlashcardStore
- [ ] AgentStore 扩展
- [ ] 提示词模板
- [ ] FlashcardGenerator 组件
- [ ] 生成功能测试

### Milestone 3: 闪卡查看与管理（预计 1-2 天）
- [ ] FlashcardViewer 组件
- [ ] FlashcardSet 组件
- [ ] FlashcardPanel 整合
- [ ] 集成到 AgentPanel
- [ ] 完整功能测试

---

## 四、后续扩展预留

### 智能搜索（预留接口）
- PDF 文本提取
- 向量化存储
- 向量检索
- 混合搜索（文本 + 向量）

### 闪卡增强
- 艾宾浩斯遗忘曲线算法
- 复习提醒系统
- Anki 格式导出 (.apkg)
- 闪卡编辑功能

---

## 五、技术风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| PDF.js 包体积较大 | 加载慢 | 使用动态导入，按需加载 |
| LLM 返回格式不稳定 | 解析失败 | 增加容错处理，多次尝试 |
| 大 PDF 渲染性能 | 卡顿 | 预留分页懒加载接口 |
| 音视频格式兼容性 | 无法播放 | 明确列出支持的格式 |

---

## 六、相关文档

- [技术栈](../architecture/tech-stack.md)
- [系统架构](../architecture/system-architecture.md)
- [项目路线图](../roadmap.md)
