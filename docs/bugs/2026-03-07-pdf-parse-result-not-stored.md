# PDF 解析结果没有存储到数据库 Bug 记录

**日期**: 2026-03-07  
**状态**: ✅ 已修复  
**严重程度**: 高

---

## 问题描述

PDF 文档解析流程能够正常运行：
- 文件上传成功
- MinerU 解析任务创建成功
- 解析进度正常更新
- 任务状态能正确变为 `done`

但是解析完成后，结果没有存储到数据库中：
- `markdown_content` 字段为空
- `result_file_path` 字段为空
- 结果 ZIP 文件没有保存到本地存储

---

## 问题根因

在 `backend/src/mineru/task_manager.py` 的 `poll_task_status` 函数中（第 235-238 行），当任务状态变为 `done` 时存在严重的逻辑缺失。

### 原始代码（有问题）

```python
if state == "done":
    await self.update_task(task_id, state="done")
    logger.info(f"任务 {task_id} 完成")
    return
```

### 缺失的步骤

1. ❌ 没有从 MinerU 下载结果 ZIP 文件
2. ❌ 没有从 ZIP 中提取 markdown 内容
3. ❌ 没有保存 markdown 到数据库的 `markdown_content` 字段
4. ❌ 没有保存结果文件到本地存储
5. ❌ 没有更新 `result_file_path` 和 `result_file_format` 字段

### 正确逻辑的位置

完整的结果处理逻辑已经在 `backend/src/api/mineru.py` 的 `get_parse_result` 端点中实现（第 190-220 行），只是没有在任务完成时自动调用。

---

## 修复方案

将 `api/mineru.py` 中已有的结果处理逻辑提取并整合到 `task_manager.py` 的任务完成处理流程中。

### 修改内容

1. 在 `task_manager.py` 中添加必要的导入：
   - `import os`
   - `from utils.zip_handler import extract_markdown_from_zip`

2. 修改 `poll_task_status` 函数中任务完成的处理逻辑：
   - 当状态为 `done` 时，添加完整的结果处理逻辑
   - 下载 ZIP、提取 markdown、保存文件、更新数据库
   - 添加完整的错误处理

---

## 修复详情

### 任务 1: 添加必要的导入

**文件**: `backend/src/mineru/task_manager.py`

**修改内容**:
- 添加 `import os`（第 3 行）
- 添加 `from utils.zip_handler import extract_markdown_from_zip`（第 15 行）

---

### 任务 2: 修改 poll_task_status 函数中任务完成处理逻辑

**文件**: `backend/src/mineru/task_manager.py`

**修改内容**（第 237-263 行）:

```python
if state == "done":
    try:
        if "full_zip_url" not in file_result:
            raise Exception("MinerU 结果中缺少 full_zip_url")
        
        zip_url = file_result["full_zip_url"]
        zip_content = await mineru_client.download_zip(zip_url)
        
        markdown_content = extract_markdown_from_zip(zip_content)
        
        storage_path = os.path.join(settings.STORAGE_DIR, f"{task_id}.zip")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(zip_content)
        
        await self.update_task(
            task_id,
            state="done",
            markdown_content=markdown_content,
            result_file_path=storage_path,
            result_file_format="zip",
        )
        logger.info(f"任务 {task_id} 完成，结果已保存")
    except Exception as e:
        logger.error(f"任务 {task_id} 结果保存失败: {str(e)}")
        await self.update_task(task_id, state="failed", error_msg=f"结果保存失败: {str(e)}")
    return
```

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/mineru/task_manager.py` | 添加导入、重写任务完成处理逻辑 |

---

## 验证清单

- [x] 必要的导入已添加（os、extract_markdown_from_zip）
- [x] 任务完成时的 ZIP 下载逻辑已添加
- [x] Markdown 提取逻辑已添加
- [x] 结果文件保存逻辑已添加
- [x] 数据库字段更新逻辑已添加（markdown_content、result_file_path、result_file_format）
- [x] 错误处理逻辑已添加
- [ ] PDF 解析完成后，markdown_content 字段已填充
- [ ] PDF 解析完成后，result_file_path 字段已填充
- [ ] 结果 ZIP 文件已保存到本地存储
- [ ] 通过 API 能正确获取解析结果

---

## 日志示例（修复后）

```
2026-03-07 15:34:20.473 | INFO     | mineru.task_manager:poll_task_status:233 - 任务 8077acb4-6c6c-4ba5-95fe-c14b92f16012 状态: done
2026-03-07 15:34:20.565 | INFO     | mineru.client:download_zip:126 - ZIP 文件下载成功
2026-03-07 15:34:20.566 | INFO     | utils.zip_handler:extract_markdown_from_zip:13 - 从 ZIP 中提取 Markdown 成功: document.md
2026-03-07 15:34:20.567 | INFO     | repositories.parse_task_repository:update:49 - 更新任务 8077acb4-6c6c-4ba5-95fe-c14b92f16012: dict_keys(['state', 'markdown_content', 'result_file_path', 'result_file_format', 'updated_at'])
2026-03-07 15:34:20.568 | INFO     | mineru.task_manager:poll_task_status:259 - 任务 8077acb4-6c6c-4ba5-95fe-c14b92f16012 完成，结果已保存
```
