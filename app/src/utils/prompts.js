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
