# 标签系统实现方案

**创建日期**: 2026-02-25  
**状态**: ⏳ 暂缓  
**版本**: v0.3

---

## 一、需求分析

### 核心功能

1. **标签管理**
   - 创建/删除标签
   - 编辑标签名称和颜色
   - 标签排序

2. **文件标签关联**
   - 为文件添加标签
   - 移除文件标签
   - 批量操作

3. **标签浏览**
   - 按标签筛选文件
   - 标签云展示
   - 标签快速搜索

### 用户交互场景

- 在文件树中右键文件 → 管理标签
- 在侧边栏增加标签面板
- 通过标签快速过滤显示相关文件

---

## 二、数据模型设计

### 方案 A：独立标签表 + 关联表（推荐）

```javascript
// 标签数据模型
{
  id: String,           // UUID
  name: String,         // 标签名称（唯一）
  color: String,        // 标签颜色（如 #409EFF）
  createdAt: ISOString,
  updatedAt: ISOString
}

// 文件-标签关联
{
  fileId: String,       // 文件唯一标识（path）
  tagId: String,        // 标签 ID
  createdAt: ISOString
}
```

**优点**：
- 数据结构清晰，符合数据库设计规范
- 便于后续扩展（如标签分组、层级等）
- 查询效率高

**缺点**：
- 需要维护两个数据集合

---

### 方案 B：文件内嵌标签

```javascript
// 在文件数据中直接嵌入标签
{
  id: String,
  path: String,
  name: String,
  type: 'file',
  tags: [
    {
      id: String,
      name: String,
      color: String
    }
  ]
}
```

**优点**：
- 查询简单，一次获取文件及其标签
- 数据读取快速

**缺点**：
- 标签数据冗余
- 标签重命名需要更新所有关联文件
- 难以统计标签使用情况

---

### 方案 C：混合方案（最佳平衡）

结合方案 A 和 B 的优点：

```javascript
// 标签主数据（独立存储）
tags: [
  { id: 'tag1', name: '重要', color: '#F56C6C', ... }
]

// 文件标签关联（只存 ID）
fileTags: {
  '/path/to/file1.md': ['tag1', 'tag2'],
  '/path/to/file2.md': ['tag1']
}
```

**推荐采用方案 C**，理由：
- 标签元数据集中管理
- 关联数据轻量存储
- 便于实现标签统计和管理
- 符合现有 Repository 模式

---

## 三、存储架构设计

### Repository 层设计

```
repositories/
├── TagRepository.js              # 标签仓储抽象接口
├── LocalStorageTagRepository.js  # localStorage 实现
└── FileTagRepository.js          # 文件标签关联仓储
```

### TagRepository 接口

```javascript
export class TagRepository {
  async getAll() { /* 获取所有标签 */ }
  async getById(id) { /* 根据 ID 获取标签 */ }
  async getByName(name) { /* 根据名称获取标签 */ }
  async create(tag) { /* 创建标签 */ }
  async update(id, updates) { /* 更新标签 */ }
  async delete(id) { /* 删除标签 */ }
}
```

### FileTagRepository 接口

```javascript
export class FileTagRepository {
  async getTagsForFile(filePath) { /* 获取文件的标签 */ }
  async getFilesForTag(tagId) { /* 获取标签下的文件 */ }
  async addTagToFile(filePath, tagId) { /* 为文件添加标签 */ }
  async removeTagFromFile(filePath, tagId) { /* 移除文件标签 */ }
  async getAllFileTags() { /* 获取所有文件标签关联 */ }
}
```

---

## 四、状态管理设计

### Pinia Store: `tag.js`

```javascript
export const useTagStore = defineStore('tag', () => {
  // 状态
  const tags = ref([])           // 所有标签
  const fileTags = ref({})       // 文件-标签映射
  const isLoading = ref(false)
  
  // 方法
  const loadTags = async () => { ... }
  const createTag = async (name, color) => { ... }
  const updateTag = async (id, updates) => { ... }
  const deleteTag = async (id) => { ... }
  const addTagToFile = async (filePath, tagId) => { ... }
  const removeTagFromFile = async (filePath, tagId) => { ... }
  const getFilesByTag = async (tagId) => { ... }
  
  return { tags, fileTags, ... }
}, {
  persist: {
    key: 'qbase-tags',
    paths: ['tags', 'fileTags']  // 持久化标签数据
  }
})
```

---

## 五、UI 组件设计

### 新增组件

```
components/
├── Tag/
│   ├── TagPanel.vue          # 标签面板侧边栏
│   ├── TagManager.vue        # 标签管理对话框
│   ├── TagSelector.vue       # 标签选择器组件
│   ├── TagBadge.vue          # 标签徽章组件
│   └── TagCloud.vue          # 标签云展示
```

### 组件功能说明

1. **TagPanel.vue**
   - 位置：左侧边栏或独立面板
   - 功能：显示所有标签、按标签筛选文件
   - 交互：点击标签 → 过滤文件树

2. **TagSelector.vue**
   - 用途：文件右键菜单、文件详情页
   - 功能：多选标签、创建新标签

3. **TagBadge.vue**
   - 用途：文件树节点、搜索结果
   - 功能：显示文件的标签预览

---

## 六、实现步骤规划

### Phase 1: 数据层基础
1. 创建 TagRepository 接口和 LocalStorage 实现
2. 创建 FileTagRepository
3. 实现基础数据 CRUD

### Phase 2: 状态管理层
1. 创建 useTagStore
2. 集成到现有 store 体系
3. 实现持久化

### Phase 3: UI 组件层
1. 创建 TagBadge 组件
2. 创建 TagSelector 组件
3. 创建 TagPanel 侧边栏

### Phase 4: 集成与交互
1. 在文件树中集成标签显示
2. 实现右键菜单标签管理
3. 实现按标签筛选功能

### Phase 5: 增强功能
1. 标签云展示
2. 标签搜索
3. 批量标签操作

---

## 七、技术细节讨论

### 1. 文件标识问题

**问题**：如何唯一标识文件？
- 当前文件树使用 `id`，但可能是临时生成的
- 文件路径是唯一的，但路径可能变化

**方案**：
- 使用文件路径作为主键
- 监听文件重命名事件，更新标签关联

### 2. 预设标签

**建议**：提供默认预设标签
- 重要（红色）
- 待办（橙色）
- 参考（蓝色）
- 已完成（绿色）

### 3. 性能考虑

- 标签数据量不会很大，localStorage 足够
- 文件标签关联采用 Map 结构，O(1) 查询
- 避免频繁的持久化写入

### 4. 与现有功能集成

- 搜索功能：增加标签过滤选项
- AI 助手：可以基于标签提供上下文建议
- 未来扩展：标签组、层级标签等

---

## 八、待确认的设计选择

在开始实施前，需要确认以下设计选择：

1. **标签面板位置**：放在左侧边栏（替换或新增）还是右侧？
2. **文件树展示**：是否在文件名旁边显示标签徽章？
3. **预设标签**：是否需要提供默认预设标签？
4. **布局调整**：当前是三栏布局，标签面板如何集成？
5. **颜色方案**：标签颜色是用户自定义还是使用预设调色板？

---

## 状态说明

本功能当前状态为 **⏳ 暂缓**，待后续版本规划时再决定是否实施。
