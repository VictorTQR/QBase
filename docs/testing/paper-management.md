# 论文管理功能测试计划

## 测试概述

本文档提供论文管理功能的完整测试步骤。根据项目测试哲学，测试由开发人员手动进行，本文档仅提供测试步骤和预期结果。

**测试环境要求：**
- Python 3.10+ 和 uv（后端）
- Node.js 18+ 和 npm（前端）
- SQLite3 数据库

**测试前置准备：**
1. 确保代码仓库最新
2. 安装所有依赖项
3. 准备测试用的搜索关键词

---

## 测试步骤

### 步骤 1: 启动后端服务

**操作步骤：**

```bash
cd "F:/Code/00Code/GitBank/QBase/backend"
uv run python main.py
```

**预期结果：**
- 服务启动成功，无错误日志
- 控制台输出包含："论文管理路由已注册"
- 服务监听在 http://127.0.0.1:8000
- API 文档可访问：http://127.0.0.1:8000/docs

**故障排查：**
- 如果端口被占用，修改 `backend/config.py` 中的 `API_PORT`
- 如果依赖缺失，运行 `uv sync` 重新安装
- 检查 Python 版本是否符合要求（3.10+）

---

### 步骤 2: 启动前端服务

**操作步骤：**

打开新的终端窗口：

```bash
cd "F:/Code/00Code/GitBank/QBase/app"
npm run dev
```

**预期结果：**
- Vite 开发服务器启动成功
- 控制台显示访问地址（通常是 http://localhost:5173）
- 无编译错误或警告

**故障排查：**
- 如果端口 5173 被占用，Vite 会自动选择其他端口，注意查看控制台输出
- 如果依赖缺失，运行 `npm install` 重新安装
- 检查 Node.js 版本是否符合要求（18+）

---

### 步骤 3: 测试论文搜索功能

**操作步骤：**

1. 打开浏览器，访问 `http://localhost:5173/papers`
2. 点击页面上的"搜索论文"按钮
3. 在搜索框中输入关键词（例如："machine learning"）
4. 点击"搜索"按钮或按回车键

**预期结果：**
- 搜索请求成功发送到后端 API
- 页面显示搜索结果列表
- 每个结果显示：
  - 论文标题
  - 作者列表
  - 发表年份
  - 引用数
  - "保存"按钮
- 如果无结果，显示友好的提示信息

**故障排查：**
- 如果搜索失败，检查后端服务是否正常运行
- 查看浏览器控制台是否有错误信息
- 验证 Semantic Scholar API 是否可访问
- 检查网络连接

**验证命令：**

```bash
# 直接测试后端 API
curl "http://127.0.0.1:8000/api/papers/search?query=machine%20learning&limit=10"
```

---

### 步骤 4: 测试论文保存功能

**操作步骤：**

1. 在搜索结果页面，点击"保存全部到数据库"按钮
2. 等待保存操作完成
3. 刷新浏览器页面
4. 查看论文列表是否包含刚保存的论文

**预期结果：**
- 显示保存成功的提示消息
- 提示消息显示保存的论文数量
- 刷新后，论文列表中显示已保存的论文
- 统计卡片中的"总论文数"增加

**故障排查：**
- 如果保存失败，检查数据库文件权限
- 查看后端控制台是否有错误日志
- 验证数据库连接是否正常
- 检查论文数据格式是否正确

**验证命令：**

```bash
# 查询数据库中的论文数量
cd "F:/Code/00Code/GitBank/QBase/backend"
sqlite3 storage/papers.db "SELECT COUNT(*) FROM papers;"

# 查看最近保存的论文
sqlite3 storage/papers.db "SELECT title, authors, year FROM papers ORDER BY saved_at DESC LIMIT 5;"
```

---

### 步骤 5: 测试论文列表显示

**操作步骤：**

1. 在论文管理页面，浏览论文列表
2. 测试分页功能（如果超过每页显示数量）
3. 点击任意论文的"查看 PDF"链接
4. 测试排序和筛选功能（如果已实现）

**预期结果：**
- 论文列表正确显示所有已保存的论文
- 每个论文条目显示：
  - 论文标题（可点击）
  - 作者列表
  - 发表年份和来源
  - 引用数
  - 保存时间
  - "查看 PDF"按钮
  - "删除"按钮（如果已实现）
- 分页器正确工作（如果有）
- PDF 链接在新标签页中打开

**故障排查：**
- 如果列表显示不正常，检查前端数据绑定
- 如果分页失败，验证分页参数传递
- 如果 PDF 链接无效，检查 Semantic Scholar 返回的 URL

---

### 步骤 6: 测试统计信息

**操作步骤：**

1. 查看页面顶部的统计卡片
2. 记录当前的统计数据
3. 搜索并保存新的论文
4. 刷新页面，观察统计数据是否更新

**预期结果：**
- 统计卡片显示：
  - 总论文数
  - 本月新增论文数
  - 最近更新时间
- 保存新论文后，统计数据自动更新
- 数据准确无误

**故障排查：**
- 如果统计数据不更新，检查后端统计 API
- 验证数据库查询逻辑
- 检查前端数据刷新机制

**验证命令：**

```bash
# 手动查询统计数据
cd "F:/Code/00Code/GitBank/QBase/backend"
sqlite3 storage/papers.db "
SELECT
  COUNT(*) as total_papers,
  COUNT(CASE WHEN strftime('%Y-%m', saved_at) = strftime('%Y-%m', 'now') THEN 1 END) as this_month
FROM papers;
"
```

---

### 步骤 7: 检查数据库完整性

**操作步骤：**

```bash
cd "F:/Code/00Code/GitBank/QBase/backend"
```

**执行以下验证命令：**

1. 检查数据库文件是否存在：
```bash
ls -lh storage/papers.db
```

2. 检查数据库结构：
```bash
sqlite3 storage/papers.db ".schema papers"
```

3. 检查论文数量：
```bash
sqlite3 storage/papers.db "SELECT COUNT(*) FROM papers;"
```

4. 检查数据完整性：
```bash
sqlite3 storage/papers.db "
SELECT
  COUNT(*) as total,
  COUNT(title) as with_title,
  COUNT(authors) as with_authors,
  COUNT(year) as with_year
FROM papers;
"
```

5. 查看最近添加的论文：
```bash
sqlite3 storage/papers.db "
SELECT title, authors, year, saved_at
FROM papers
ORDER BY saved_at DESC
LIMIT 10;
"
```

**预期结果：**
- 数据库文件存在且大小合理（> 0 KB）
- 表结构包含所有必需字段
- 论文数量与界面显示一致
- 所有记录都有完整的数据（title, authors, year）
- 保存时间戳正确

**故障排查：**
- 如果数据库文件不存在，检查后端是否有写权限
- 如果表结构不完整，重新运行数据库初始化
- 如果数据不完整，检查保存逻辑是否有错误

---

## 完整测试流程示例

以下是一个完整的测试会话示例：

```bash
# 终端 1：启动后端
cd "F:/Code/00Code/GitBank/QBase/backend"
uv run python main.py
# 观察输出：论文管理路由已注册

# 终端 2：启动前端
cd "F:/Code/00Code/GitBank/QBase/app"
npm run dev
# 观察输出：Local: http://localhost:5173/

# 浏览器：访问 http://localhost:5173/papers
# 1. 搜索 "machine learning"
# 2. 保存前 10 篇论文
# 3. 刷新页面，验证列表显示
# 4. 点击 PDF 链接，验证可以打开
# 5. 观察统计卡片数据

# 终端 3：验证数据库
cd "F:/Code/00Code/GitBank/QBase/backend"
sqlite3 storage/papers.db "SELECT COUNT(*) FROM papers;"
# 输出应该显示保存的论文数量
```

---

## 常见问题及解决方案

### 问题 1: 后端启动失败

**症状：** 运行 `uv run python main.py` 时出现错误

**可能原因：**
- 依赖未安装
- Python 版本不兼容
- 端口被占用

**解决方案：**
```bash
# 重新安装依赖
uv sync

# 检查 Python 版本
python --version

# 更改端口
# 编辑 backend/config.py，修改 API_PORT
```

### 问题 2: 前端无法连接后端

**症状：** 浏览器控制台显示 CORS 或连接错误

**可能原因：**
- 后端未启动
- 前端配置的后端地址错误
- CORS 配置问题

**解决方案：**
```bash
# 确认后端运行
curl http://127.0.0.1:8000/docs

# 检查前端环境变量
# app/.env.development 中的 VITE_API_URL
```

### 问题 3: 搜索无结果

**症状：** 搜索关键词后返回空列表

**可能原因：**
- 关键词过于具体
- Semantic Scholar API 问题
- 网络连接问题

**解决方案：**
```bash
# 测试 API 直接访问
curl "https://api.semanticscholar.org/graph/v1/paper/search?query=machine+learning&limit=10"

# 尝试更通用的关键词
# 例如：使用 "deep learning" 而不是具体的论文标题
```

### 问题 4: 保存失败

**症状：** 点击保存后出现错误提示

**可能原因：**
- 数据库权限问题
- 数据格式验证失败
- 后端逻辑错误

**解决方案：**
```bash
# 检查数据库文件权限
ls -l backend/storage/papers.db

# 查看后端日志
# 后端控制台应该显示详细错误信息

# 手动测试保存 API
curl -X POST http://127.0.0.1:8000/api/papers/save \
  -H "Content-Type: application/json" \
  -d '{"papers": [...]}'
```

### 问题 5: 统计数据不准确

**症状：** 统计卡片显示的数字与实际不符

**可能原因：**
- 缓存未更新
- 数据库查询错误
- 时区问题

**解决方案：**
```bash
# 强制刷新页面（Ctrl+Shift+R）
# 或清除浏览器缓存

# 直接查询数据库验证
sqlite3 storage/papers.db "SELECT COUNT(*) FROM papers;"

# 检查时区设置
# 确保 Python 和数据库使用相同时区
```

---

## 性能测试（可选）

### 测试大量论文保存

```bash
# 使用脚本测试批量保存
# 创建测试脚本 test_bulk_save.py

import requests
import json

API_URL = "http://127.0.0.1:8000"
SEARCH_QUERY = "artificial intelligence"
LIMIT = 100

# 搜索
response = requests.get(f"{API_URL}/api/papers/search",
                       params={"query": SEARCH_QUERY, "limit": LIMIT})
papers = response.json()

# 保存
save_response = requests.post(f"{API_URL}/api/papers/save",
                             json={"papers": papers})
print(f"保存了 {len(papers)} 篇论文")
print(save_response.json())
```

### 测试数据库查询性能

```bash
# 测试查询性能
cd backend
sqlite3 storage/papers.db "
.timer on
SELECT COUNT(*) FROM papers;
SELECT * FROM papers LIMIT 10;
.timer off
"
```

---

## 测试检查清单

完成测试后，使用此清单确认所有功能正常：

- [ ] 后端服务成功启动
- [ ] 前端服务成功启动
- [ ] 论文搜索功能正常
- [ ] 论文保存功能正常
- [ ] 论文列表显示正常
- [ ] PDF 链接可以访问
- [ ] 统计信息准确显示
- [ ] 数据库数据完整
- [ ] 无控制台错误或警告
- [ ] 响应时间可接受（< 3秒）

---

## 测试报告模板

测试完成后，填写此报告：

```
测试日期：____________________
测试人员：____________________
环境信息：
  - OS: _____________
  - Python: _____________
  - Node.js: _____________

测试结果：
  [ ] 所有测试通过
  [ ] 部分测试失败（说明：___________）
  [ ] 需要进一步测试

发现问题：
1. _____________
2. _____________

建议改进：
1. _____________
2. _____________
```

---

## 附录：相关文件位置

- 后端主文件：`F:/Code/00Code/GitBank/QBase/backend/main.py`
- 前端论文页面：`F:/Code/00Code/GitBank/QBase/app/src/pages/Papers.tsx`
- 数据库文件：`F:/Code/00Code/GitBank/QBase/backend/storage/papers.db`
- API 配置：`F:/Code/00Code/GitBank/QBase/backend/config.py`
- 前端环境变量：`F:/Code/00Code/GitBank/QBase/app/.env.development`

---

**文档版本：** 1.0
**最后更新：** 2026-04-05
**维护者：** QBase 开发团队
