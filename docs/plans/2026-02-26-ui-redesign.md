# UI 界面重新设计方案

**日期**: 2026-02-26  
**版本**: v0.6  
**状态**: 🔄 设计中

---

## 1. 设计概述

### 1.1 设计目标
解决当前界面功能组织混乱的问题，提供简洁现代的用户体验，同时为未来功能扩展预留空间。

### 1.2 设计原则
- **简洁现代**: 采用 Notion/Linear 风格，大量留白，柔和圆角
- **统一组织**: 所有 AI 功能集中在右侧面板
- **易于扩展**: 导航设计支持未来添加新功能
- **流畅交互**: 平滑过渡动画，清晰的状态反馈

---

## 2. 整体布局设计

### 2.1 三栏布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  Header (48px)                                                    │
├──────────────┬──────────────────────────┬───────────────────────┤
│              │                          │                       │
│   Sidebar    │      ContentPane         │      AgentPanel       │
│  (文件树)    │      (文档预览)          │   (AI 功能面板)       │
│              │                          │                       │
│              │                          │                       │
└──────────────┴──────────────────────────┴───────────────────────┘
```

### 2.2 右侧面板 (AgentPanel) 结构

```
┌─────────────────────────────────────────────────────────────┐
│  Panel Header (48px)                                         │
│  AI 助手                                    [设置] [最小化]  │
├───────────────────────────────────────┬─────────────────────┤
│                                       │                     │
│      Content Area (75%)               │   Nav Sidebar (25%) │
│      (功能内容区域)                    │   (导航侧边栏)      │
│                                       │                     │
│   ┌─────────────────────────────┐   │   💬 对话            │
│   │                             │   │   🎴 闪卡            │
│   │   动态切换的功能内容         │   │   🤖 生成            │
│   │                             │   │   📊 分析            │
│   │                             │   │   📝 笔记            │
│   └─────────────────────────────┘   │   ...                │
│                                       │                     │
└───────────────────────────────────────┴─────────────────────┘
```

---

## 3. 导航侧边栏设计

### 3.1 规格参数
- **位置**: 右侧面板最右侧
- **宽度**: 64px
- **高度**: 100% (除去头部)
- **背景色**: `var(--el-bg-color-page)` 或浅色渐变

### 3.2 导航项设计

#### 视觉样式
```css
.nav-item {
  width: 48px;
  height: 48px;
  margin: 8px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.nav-item:hover {
  background-color: var(--el-bg-color-secondary);
  transform: scale(1.05);
}

.nav-item.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 600;
}

.nav-item .icon {
  font-size: 20px;
}

.nav-item .label {
  font-size: 11px;
  text-align: center;
}
```

#### 导航项数据结构
```javascript
const navItems = [
  { id: 'chat', icon: 'ChatDotRound', label: '对话', component: 'ChatModule' },
  { id: 'flashcard', icon: 'Tickets', label: '闪卡', component: 'FlashcardModule' },
  { id: 'generate', icon: 'MagicStick', label: '生成', component: 'GenerateModule' },
  { id: 'analyze', icon: 'DataAnalysis', label: '分析', component: 'AnalyzeModule' },
  // 未来扩展...
]
```

### 3.3 交互效果
- **悬停**: 背景色变浅，轻微放大
- **选中**: 主色调背景，明显高亮
- **过渡**: 0.2s ease 缓动
- **工具提示**: 鼠标悬停显示完整功能名称

---

## 4. 各功能模块详细设计

### 4.1 对话模块 (ChatModule)

#### 布局结构
```
┌─────────────────────────────────────────────┐
│  会话选择 v  [+新会话] [⚙设置]            │ ← 顶部操作栏
├─────────────────────────────────────────────┤
│                                             │
│   消息列表区域 (flex: 1)                   │
│   ┌─────────────────────────────────────┐  │
│   │  用户消息气泡                       │  │
│   └─────────────────────────────────────┘  │
│   ┌─────────────────────────────────────┐  │
│   │  AI 响应气泡 (流式渲染)             │  │
│   └─────────────────────────────────────┘  │
│                                             │
├─────────────────────────────────────────────┤
│  ☑ 包含当前文档                             │ ← 上下文选项
│  ┌─────────────────────────────────────┐  │
│  │  输入消息...              [发送]    │  │ ← 输入框
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

#### 组件文件
- `src/components/chat/ChatModule.vue` - 对话主模块
- `src/components/chat/MessageList.vue` - 消息列表
- `src/components/chat/MessageBubble.vue` - 消息气泡
- `src/components/chat/InputSender.vue` - 输入发送器

---

### 4.2 闪卡模块 (FlashcardModule)

#### 混合模式设计

**小面板预览模式 (默认)**:
```
┌─────────────────────────────────────────────┐
│  闪卡集 v  [+生成闪卡] [⏏专注模式]        │ ← 顶部操作栏
├─────────────────────────────────────────────┤
│                                             │
│   ┌─────────────────────────────────────┐  │
│   │  Q: 什么是 Vue 3 的 Composition API?│  │ ← 闪卡正面
│   │                                     │  │
│   │  [ 点击查看答案 ]                   │  │
│   └─────────────────────────────────────┘  │
│                                             │
│   [←]  1 / 10  [✓已掌握]  [→]             │ ← 控制栏
│                                             │
│   [ ⏏ 展开专注模式 ]                       │ ← 展开按钮
└─────────────────────────────────────────────┘
```

**专注模式 (展开后)**:
- 占据整个内容区域
- 3D 翻转效果
- 沉浸式学习体验
- 可随时退出返回小面板模式

#### 组件文件
- `src/components/flashcard/FlashcardModule.vue` - 闪卡主模块
- `src/components/flashcard/FlashcardPreview.vue` - 小面板预览
- `src/components/flashcard/FlashcardFocus.vue` - 专注模式
- `src/components/flashcard/FlashcardGenerator.vue` - 闪卡生成器

---

### 4.3 智能生成模块 (GenerateModule)

#### 布局结构
```
┌─────────────────────────────────────────────┐
│  [闪卡]  [思维导图]  [摘要]  [分析]        │ ← 顶部标签页
├─────────────────────────────────────────────┤
│                                             │
│   生成配置区域                              │
│   ┌─────────────────────────────────────┐  │
│   │  闪卡数量: [ 5 ●────────── 20 ]    │  │
│   └─────────────────────────────────────┘  │
│                                             │
│   [ 🚀 生成 ]                                │ ← 生成按钮
│                                             │
│   ───────────────────────────────────────   │
│                                             │
│   生成结果区域                              │
│   ┌─────────────────────────────────────┐  │
│   │  文档摘要                            │  │
│   │  ───────────────────────────────    │  │
│   │  这是文档的摘要内容...              │  │
│   └─────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

#### 组件文件
- `src/components/generate/GenerateModule.vue` - 生成主模块
- `src/components/generate/FlashcardTab.vue` - 闪卡生成标签
- `src/components/generate/MindmapTab.vue` - 思维导图标签
- `src/components/generate/SummaryTab.vue` - 摘要生成标签

---

## 5. 视觉设计规范

### 5.1 色彩系统
```css
:root {
  /* 主色调 */
  --primary-color: #409eff;
  --primary-light-9: #ecf5ff;
  
  /* 中性色 */
  --bg-color: #ffffff;
  --bg-color-secondary: #f5f7fa;
  --text-color-primary: #303133;
  --text-color-secondary: #606266;
  --border-color: #dcdfe6;
  
  /* 功能色 */
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
}
```

### 5.2 间距系统
```css
/* 基础间距单位: 4px */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
```

### 5.3 圆角系统
```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
```

### 5.4 阴影系统
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
```

### 5.5 动画系统
```css
--transition-fast: 0.15s ease;
--transition-normal: 0.2s ease;
--transition-slow: 0.3s ease;
```

---

## 6. 组件结构规划

### 6.1 目录结构
```
src/components/
├── Layout/
│   ├── AgentPanel.vue          # 修改：右侧面板主容器
│   └── PanelNavSidebar.vue     # 新增：导航侧边栏
├── chat/
│   ├── ChatModule.vue           # 新增：对话模块
│   ├── MessageList.vue          # 新增：消息列表
│   ├── MessageBubble.vue        # 新增：消息气泡
│   └── InputSender.vue          # 新增：输入发送器
├── flashcard/
│   ├── FlashcardModule.vue      # 重构：闪卡主模块
│   ├── FlashcardPreview.vue     # 新增：小面板预览
│   └── FlashcardFocus.vue       # 新增：专注模式
├── generate/
│   ├── GenerateModule.vue       # 新增：智能生成模块
│   ├── FlashcardTab.vue         # 新增：闪卡生成标签
│   ├── MindmapTab.vue           # 新增：思维导图标签
│   └── SummaryTab.vue           # 新增：摘要生成标签
└── shared/
    ├── PanelHeader.vue           # 新增：面板头部组件
    └── LoadingState.vue          # 新增：加载状态组件
```

### 6.2 状态管理
- 保持现有的 `agent.js` 和 `flashcard.js` store
- 新增 `ui.js` store 管理面板状态、当前选中模块等

---

## 7. 实施步骤

### 阶段一：基础框架
1. 创建新的目录结构
2. 实现 `PanelNavSidebar` 导航组件
3. 重构 `AgentPanel` 主容器
4. 实现模块切换逻辑

### 阶段二：对话模块
1. 拆分现有对话功能到新组件
2. 实现 `ChatModule`
3. 优化消息气泡样式

### 阶段三：闪卡模块
1. 重构闪卡面板
2. 实现混合模式切换
3. 添加专注模式

### 阶段四：生成模块
1. 整合现有生成功能
2. 实现标签页布局
3. 优化结果展示

### 阶段五： polish
1. 添加动画效果
2. 优化响应式布局
3. 统一视觉风格
4. 测试和调优

---

## 8. 兼容性考虑

- 保持现有功能完整可用
- 渐进式迁移，不强制用户立即切换
- 提供回退选项（如需要）

---

## 9. 后续扩展

### 9.1 可添加的新功能
- 📊 文档分析
- 📝 智能笔记
- 🔍 语义搜索
- 📚 知识图谱
- 🎯 学习路径
- 等等...

### 9.2 扩展性保障
- 导航项配置化，无需修改代码即可添加
- 模块组件按需加载
- 标准化的模块接口

---

**文档结束**
