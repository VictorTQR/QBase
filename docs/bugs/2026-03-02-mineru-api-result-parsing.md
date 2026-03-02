# Bug 修复: MinerU API 返回结果解析错误

**日期**: 2026-03-02  
**状态**: ✅ 已修复

## 问题描述

使用 Swagger 测试 `/api/mineru/parse` 接口时，出现错误：

```
string indices must be integers, not 'str'
```

## 错误日志

```
2026-03-02 10:23:37.317 | INFO     | mineru.client:batch_apply_upload_urls:47 - 批量申请上传链接成功，batch_id: a40ae63e-7a2a-4ccd-b643-eca1da2dc30b
2026-03-02 10:23:37.319 | ERROR    | api.mineru:parse_document:42 - 解析文档失败: string indices must be integers, not 'str'
INFO:     127.0.0.1:50339 - "POST /api/mineru/parse HTTP/1.1" 500 Internal Server Error
```

## 根本原因

代码对 MinerU API 返回结果的数据结构理解错误。

### 问题 1: file_urls 访问方式

**文件**: `backend/src/api/mineru.py:31`

**错误代码**:
```python
upload_url = apply_result["file_urls"][0]["url"]
```

**问题**: `file_urls` 返回的是字符串数组，不是对象数组。

**官方文档响应示例**:
```json
{
  "code": 0,
  "data": {
    "batch_id": "2bb2f0ec-a336-4a0a-b61a-241afaf9cc87",
    "file_urls": [
      "https://mineru.oss-cn-shanghai.aliyuncs.com/api-upload/***"
    ]
  }
}
```

**修复后代码**:
```python
upload_url = apply_result["file_urls"][0]
```

---

### 问题 2: batch_query_results 结果解析

**文件**: `backend/src/mineru/task_manager.py:62-70`

**错误代码**:
```python
result = await mineru_client.batch_query_results(task["batch_id"])
if result.get("state") == "SUCCESS":
    self.update_task(task_id, state="done", result=result)
```

**问题**: 对返回结果结构理解完全错误。

**官方文档响应示例**:
```json
{
  "code": 0,
  "data": {
    "batch_id": "2bb2f0ec-a336-4a0a-b61a-241afaf9cc87",
    "extract_result": [
      {
        "file_name": "example.pdf",
        "state": "done",
        "full_zip_url": "https://cdn-mineru.openxlab.org.cn/pdf/xxx.zip",
        "err_msg": ""
      }
    ]
  }
}
```

**任务状态值**:
- `done` - 完成
- `pending` - 排队中
- `running` - 正在解析
- `failed` - 解析失败
- `converting` - 格式转换中

**修复后代码**:
```python
result = await mineru_client.batch_query_results(task["batch_id"])

if "extract_result" not in result or len(result["extract_result"]) == 0:
    await asyncio.sleep(settings.TASK_POLL_INTERVAL)
    continue

file_result = result["extract_result"][0]
state = file_result.get("state")

if state == "done":
    self.update_task(task_id, state="done", result=file_result)
elif state == "failed":
    err_msg = file_result.get("err_msg", "任务执行失败")
    self.update_task(task_id, state="failed", error_msg=err_msg)
```

---

### 问题 3: get_parse_result 中的 ZIP URL 访问

**文件**: `backend/src/api/mineru.py:64`

**错误代码**:
```python
zip_url = task["result"]["files"][0]["download_url"]
```

**修复后代码**:
```python
zip_url = task["result"]["full_zip_url"]
```

## 修复的文件

1. `backend/src/api/mineru.py` - 修复问题 1 和 3
2. `backend/src/mineru/task_manager.py` - 修复问题 2

## 测试建议

1. 重启后端服务
2. 使用 Swagger UI (http://localhost:8000/docs) 测试 `/api/mineru/parse`
3. 上传一个 PDF 文件
4. 轮询任务状态直到完成
5. 获取解析结果

## 预防措施

- 仔细阅读官方文档的响应示例
- 在使用 API 前先打印完整响应进行调试
- 添加更完善的错误处理和数据验证
