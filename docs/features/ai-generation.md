# 智能生成功能

## 功能概述

智能生成功能是 QBase 的核心 AI 能力，允许用户基于当前文档内容快速生成不同类型的学习辅助材料。

## 功能特性

### 闪卡生成

基于文档内容自动生成学习闪卡，帮助用户记忆和理解知识点。

**特性**：
- 可调节生成数量（5-20 张）
- 基于核心概念生成问题
- 每张闪卡包含问题、答案和难度等级
- 支持预览和管理

**提示模板**：
```javascript
generateFlashcardPrompt(content, count)
```

**数据结构**：
```json
{
  "front": "问题文本",
  "back": "答案文本",
  "difficulty": "easy | medium | hard"
}
```

### 思维导图生成

自动提取文档结构和核心概念，生成可视化的思维导图。

**特性**：
- 提取文档层级结构
- 生成结构化的节点关系
- SVG 格式实时预览
- 支持节点和连线展示

**提示模板**：
```javascript
generateMindmapPrompt(content)
```

**数据结构**：
```json
{
  "title": "文档标题",
  "nodes": [
    {
      "id": "node1",
      "text": "节点文本",
      "parent": "父节点ID或null",
      "children": ["子节点ID数组"]
    }
  ]
}
```

### 摘要生成

自动提取文档核心内容，生成简洁的摘要。

**特性**：
- 提取核心观点和结论
- 保持原文逻辑结构
- 控制字数在 300-500 字
- 支持中文输出

**提示模板**：
```javascript
generateSummaryPrompt(content)
```

**数据结构**：
```
字符串格式的摘要内容
```

## 技术实现

### 依赖项

- `hook-fetch`: LLM API 请求
- `@element-plus/icons-vue`: UI 图标

### 核心组件

#### MindmapGenerator.vue

独立的思维导图生成组件。

**功能**：
- 一键生成思维导图
- 生成状态显示
- SVG 格式结果预览
- 错误处理

**文件位置**：`src/components/mindmap/MindmapGenerator.vue`

#### SummaryGenerator.vue

独立的摘要生成组件。

**功能**：
- 一键生成文档摘要
- 生成状态显示
- 摘要文本预览
- 错误处理

**文件位置**：`src/components/summary/SummaryGenerator.vue`

#### 模块容器

- `MindmapModule.vue`: 思维导图标签页容器
- `SummaryModule.vue`: 摘要标签页容器

**文件位置**：`src/components/generate/`

#### Agent Store 扩展

新增三个生成方法：

```javascript
async function generateFlashcards(content, count)
async function generateMindmap(content)
async function generateSummary(content)
```

所有方法都返回统一格式：
```javascript
{
  success: boolean,
  flashcards?: array,
  mindmap?: object,
  summary?: string,
  error?: string
}
```

### Prompt 模板

位于 `app/src/utils/prompts.js`，提供三个生成提示模板函数：

- `generateFlashcardPrompt(content, count)`
- `generateMindmapPrompt(content)`
- `generateSummaryPrompt(content)`

## 使用流程

### 思维导图生成

1. **打开文档**：在文件树中选择并打开一个 Markdown 文档
2. **切换到思维导图**：在 AgentPanel 点击"思维导图"标签
3. **生成思维导图**：点击"生成思维导图"按钮
4. **查看结果**：在面板中预览 SVG 格式的思维导图

### 摘要生成

1. **打开文档**：在文件树中选择并打开一个 Markdown 文档
2. **切换到摘要**：在 AgentPanel 点击"摘要"标签
3. **生成摘要**：点击"生成摘要"按钮
4. **查看结果**：在面板中预览生成的文档摘要

## UI 交互

### 标签页切换

AgentPanel 包含四个模式标签：
- **对话**：AI 助手对话
- **闪卡**：闪卡管理和学习
- **思维导图**：思维导图生成
- **摘要**：文档摘要生成

### 加载状态

生成过程中显示"生成中..."状态，按钮禁用。

### 错误提示

- 无文档时：显示错误提示"请先打开一个 Markdown 文档"
- LLM 调用失败：显示具体错误信息
- 响应解析失败：显示格式错误提示

## 与其他功能的集成

### 与闪卡功能的集成

- 智能生成的闪卡可以直接保存到闪卡集
- 共享 Flashcard Store 状态管理

### 与文档功能的集成

- 自动从 DocumentStore 获取当前文档内容
- 支持实时同步文档变更

### 与 AI 助手的集成

- 共享 LLM 配置
- 使用相同的 API 客户端
- 复用错误处理逻辑

## 性能优化

- 非流式生成（闪卡、思维导图、摘要）
- 响应时间依赖 LLM 模型性能
- 建议文档内容长度在合理范围内（< 5000 字）

## 后续扩展可能性

1. **更多生成类型**：
   - 大纲生成
   - 问题生成
   - 关键词提取

2. **自定义模板**：
   - 用户自定义提示模板
   - 模板保存和管理

3. **导出功能**：
   - 思维导图导出为图片/JSON
   - 摘要导出为 Markdown/文本

4. **多语言支持**：
   - 支持多种语言文档的生成
   - 多语言摘要输出

## 测试要点

- 验证不同类型文档的生成质量
- 测试边界情况（空文档、超大文档）
- 验证错误处理的健壮性
- 测试生成结果的格式正确性

## 相关文档

- [实施报告](../implementation/0.5-ai-generation-enhancement.md)
- [AI 助手功能](./ai-assistant.md)
- [闪卡生成功能](./flashcard-generation.md)
