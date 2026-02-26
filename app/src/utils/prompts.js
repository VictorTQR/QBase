export function generateFlashcardPrompt(content, count) {
  return `你是一个专业的学习内容生成助手。请基于以下文档内容生成闪卡。

要求：
1. 生成 ${count} 个闪卡
2. 问题应该考察对核心概念的理解，而不是简单的事实记忆
3. 答案应该简洁准确，控制在 2-3 句话
4. 输出格式为 JSON 数组，每个元素包含：
   - front: 问题（字符串）
   - back: 答案（字符串）
   - difficulty: 难度（"easy" | "medium" | "hard"）

只返回 JSON，不要其他文字说明。

文档内容：
${content}`
}

export function generateMindmapPrompt(content) {
  return `你是一个专业的知识整理助手。请基于以下文档内容生成思维导图。

要求：
1. 提取文档的核心概念和层级关系
2. 生成一个结构化的思维导图，包含主主题和子主题
3. 每个节点包含简洁的关键词或短语
4. 保持层级清晰，逻辑连贯
5. 输出格式为 JSON 格式，包含：
   - title: 思维导图标题
   - nodes: 节点数组，每个节点包含：
     - id: 节点ID
     - text: 节点文本
     - parent: 父节点ID（根节点为null）
     - children: 子节点ID数组

只返回 JSON，不要其他文字说明。

文档内容：
${content}`
}

export function generateSummaryPrompt(content) {
  return `你是一个专业的内容总结助手。请基于以下文档内容生成摘要。

要求：
1. 提取文档的核心内容和关键信息
2. 生成一个结构清晰的摘要，包含主要观点和结论
3. 保持语言简洁，控制在300-500字
4. 保持原文的逻辑结构和重点
5. 用中文输出

文档内容：
${content}`
}