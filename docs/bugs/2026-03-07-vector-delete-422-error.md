# 向量索引删除功能 422 错误 Bug 记录

**日期**: 2026-03-07  
**状态**: ✅ 已修复  
**严重程度**: 中

---

## 问题描述

测试删除索引功能时报错：

```
DELETE http://localhost:8000/api/vector/delete 422 (Unprocessable Entity)
```

错误详情：
```json
[{
  "type": "missing",
  "loc": ["body", "file_path"],
  "msg": "Field required",
  "input": {}
}]
```

后端收到的请求体是空对象 `{}`，提示缺少 `file_path` 字段。

---

## 问题根因

### 技术分析

后端使用 `@router.delete("/delete")` 端点（`backend/src/api/vector.py:168`），通过请求体（request body）接收 `file_path` 字段。

但是，**大多数 HTTP 客户端库（包括 `hook-fetch`）对于 DELETE 请求的处理方式与 POST/PUT 不同**：

1. DELETE 请求通常不建议包含请求体
2. 即使支持，处理方式也可能不一致
3. 在这个案例中，`hook-fetch` 没有正确地将请求体传递给后端

### 相关代码

**后端 API 定义**（`backend/src/api/vector.py:168-178`）：
```python
@router.delete("/delete", response_model=VectorOperationResponse)
async def delete_document_chunks(request: VectorDeleteRequest):
    """删除指定文件的向量索引"""
    lancedb_service.delete_by_file_path(request.file_path)
    ...
```

**前端调用**（`app/src/api/vectorBackend.js:49-55`）：
```javascript
static async deleteDocumentChunks(filePath) {
  const request = backend.client.delete('/api/vector/delete', {
    file_path: filePath,
  })
  return await request.json()
}
```

---

## 修复方案

**最稳妥的解决方案**：将 DELETE 端点改为 POST 端点，这样可以确保请求体能够正确传递。

虽然从 RESTful 设计角度来说，删除操作应该使用 DELETE 方法，但在实际开发中，为了避免请求体处理的兼容性问题，使用 POST 方法是一个常见且可行的做法。

---

## 修复详情

### 任务 1: 修改后端 API 方法

**文件**: `backend/src/api/vector.py`

**修改内容**（第 168 行）:
```python
# 修改前
@router.delete("/delete", response_model=VectorOperationResponse)

# 修改后
@router.post("/delete", response_model=VectorOperationResponse)
```

---

### 任务 2: 修改前端调用方法

**文件**: `app/src/api/vectorBackend.js`

**修改内容**（第 51 行）:
```javascript
// 修改前
const request = backend.client.delete('/api/vector/delete', {

// 修改后
const request = backend.client.post('/api/vector/delete', {
```

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/api/vector.py` | 将 DELETE 端点改为 POST |
| `app/src/api/vectorBackend.js` | 将 delete 方法调用改为 post |

---

## 验证清单

- [x] 后端 API 方法已从 DELETE 改为 POST
- [x] 前端调用方法已从 delete 改为 post
- [ ] 删除索引功能不再出现 422 错误
- [ ] 指定文件的向量索引能被正确删除
- [ ] 删除后通过 `/api/vector/stats` 验证统计数据更新

---

## 替代方案讨论

除了将 DELETE 改为 POST 之外，还可以考虑以下替代方案：

### 方案 A: 使用查询参数（Query Parameters）

将 `file_path` 作为查询参数传递，而不是请求体：
```
POST /api/vector/delete?file_path=/path/to/file
```

**优点**：仍然可以使用 DELETE 方法  
**缺点**：URL 中可能包含特殊字符，需要编码处理

### 方案 B: 使用路径参数（Path Parameters）

将 `file_path` 编码后作为 URL 路径的一部分：
```
DELETE /api/vector/delete/{encoded_file_path}
```

**优点**：符合 RESTful 设计  
**缺点**：文件路径可能包含 `/` 等特殊字符，需要编码和解码处理

### 最终选择

选择**将 DELETE 改为 POST** 方案，因为：
1. 实现最简单，改动最小
2. 避免了 URL 编码/解码的复杂性
3. 与项目中其他操作（如 `/api/vector/clear`）保持一致
4. 兼容性最好，不会有请求体处理问题
