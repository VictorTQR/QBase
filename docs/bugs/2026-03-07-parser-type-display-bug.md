# 音频文件解析器类型显示错误 Bug 记录

**日期**: 2026-03-07  
**状态**: ✅ 已修复  
**严重程度**: 低

---

## 问题描述

音频文件使用硅基流动（SiliconFlow）API 进行解析，但前端显示的解析器类型仍然是 "MinerU"。

---

## 问题根因

### 问题 1: 任务序列化缺失 parser_type 字段

在 `backend/src/mineru/task_manager.py` 的 `_task_to_dict` 方法中，将数据库任务对象转换为字典时，**没有包含 `parser_type` 字段**。

### 前端默认值

前端代码在 `parser_type` 为空时，默认显示为 `'mineru'`：

**文件 1**: `app/src/components/parse/ParseDocumentsView.vue` (第 72 行)
```vue
<span class="parser-type">{{ task.parser_type || 'mineru' }}</span>
```

**文件 2**: `app/src/components/parse/ParseDetailsDrawer.vue` (第 20 行)
```vue
<el-descriptions-item label="解析器">
  {{ task.parser_type || 'mineru' }}
</el-descriptions-item>
```

---

## 修复方案

在 `mineru/task_manager.py` 的 `_task_to_dict` 方法中添加 `"parser_type": task.parser_type` 字段。

---

## 修复详情

### 任务 1: 在 _task_to_dict 方法中添加 parser_type 字段

**文件**: `backend/src/mineru/task_manager.py`

**修改内容**:
- 在 `_task_to_dict` 方法（第 193-210 行）中添加 `"parser_type": task.parser_type`

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/mineru/task_manager.py` | 添加 parser_type 字段序列化 |

---

## 验证清单

- [x] parser_type 字段已添加到 _task_to_dict 方法
- [ ] 音频任务正确显示 "siliconflow_asr" 解析器类型
- [ ] MinerU 任务正确显示 "mineru" 解析器类型
