# pyarrow.compute.now() 不存在 Bug 记录

**日期**: 2026-03-07  
**状态**: ✅ 已修复  
**严重程度**: 高

---

## 问题描述

向量索引功能在添加文档分块到 LanceDB 时失败，报错提示 pyarrow.compute 模块没有 now() 属性。

## 错误日志

```
AttributeError: module 'pyarrow.compute' has no attribute 'now'
```

发生在 `backend/src/vector/lancedb_service.py:84`。

---

## 问题根因

代码使用了 `pa.compute.now()` 来获取当前时间戳，但这个函数在当前版本的 pyarrow 中不存在。

---

## 修复方案

使用 Python 标准库的 `time.time()` 来替代，这样更简单且兼容性更好。

---

## 修复详情

### 任务 1: 导入 time 模块

**文件**: `backend/src/vector/lancedb_service.py`

**修改内容**:
- 添加 `import time` 到导入语句中

---

### 任务 2: 替换时间戳生成代码

**文件**: `backend/src/vector/lancedb_service.py`

**修改内容**:
- 第 84 行：`int(pa.compute.now().cast(pa.int64()).as_py() / 1000000)` → `int(time.time())`

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/vector/lancedb_service.py` | 替换时间戳生成方式 |

---

## 验证清单

- [x] time 模块已导入
- [x] pa.compute.now() 已替换为 time.time()
- [ ] 向量索引功能正常工作
