# aiohttp timeout 参数类型 Bug 记录

**日期**: 2026-03-07  
**状态**: ✅ 已修复  
**严重程度**: 高

---

## 问题描述

向量索引功能在处理音频转录文本时失败，报错提示 aiohttp 的 timeout 参数类型错误。

## 错误日志

```
ValueError: timeout parameter cannot be of <class 'float'> type, please use 'timeout=ClientTimeout(...)'
```

发生在 `backend/src/vector/providers/siliconflow.py:35`。

---

## 问题根因

### 问题 1: aiohttp 新版本 API 变更
- aiohttp 新版本不再接受 float 类型的 timeout 参数
- 必须使用 `aiohttp.ClientTimeout` 对象包装超时时间

### 问题 2: 两个文件存在相同问题
1. `backend/src/vector/providers/siliconflow.py:35` - 使用 `timeout=60.0`
2. `backend/src/audio/providers/siliconflow.py:32` - 使用 `timeout=300.0`（httpx，预防性修复）

---

## 修复方案

1. **vector 提供商**: 将 `timeout=60.0` 改为 `timeout=aiohttp.ClientTimeout(total=60.0)`
2. **audio 提供商**: 将 `timeout=300.0` 改为 `timeout=httpx.Timeout(300.0)`（预防性修复）

---

## 修复详情

### 任务 1: 修复 vector 提供商的 aiohttp timeout

**文件**: `backend/src/vector/providers/siliconflow.py`

**修改内容**:
- 第 35 行：`timeout=60.0` → `timeout=aiohttp.ClientTimeout(total=60.0)`

---

### 任务 2: 预防性修复 audio 提供商的 httpx timeout

**文件**: `backend/src/audio/providers/siliconflow.py`

**修改内容**:
- 第 32 行：`timeout=300.0` → `timeout=httpx.Timeout(300.0)`

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `backend/src/vector/providers/siliconflow.py` | 修复 aiohttp timeout 参数 |
| `backend/src/audio/providers/siliconflow.py` | 预防性修复 httpx timeout 参数 |

---

## 验证清单

- [x] vector 提供商的 aiohttp timeout 已修复
- [x] audio 提供商的 httpx timeout 已预防性修复
- [ ] 向量索引功能正常工作
- [ ] 音频转录功能正常工作
