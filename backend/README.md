# QBase Backend

基于 FastAPI 的 MinerU 文档解析后端服务。

## 快速开始

### 前置要求

- Python >= 3.12
- uv (包管理器)

### 安装

```bash
cd backend

# 安装依赖
uv pip install .
```

### 配置

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env，填入你的 MinerU API Key
MINERU_API_KEY=your_api_key_here
```

### 运行

```bash
# 开发模式（自动重载）
uv run python -m uvicorn main:app --reload

# 生产模式
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### API 文档

服务启动后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/mineru/parse` | POST | 提交文档解析任务 |
| `/api/mineru/tasks/{task_id}` | GET | 查询任务状态 |
| `/api/mineru/tasks/{task_id}/result` | GET | 获取解析结果（Markdown） |
| `/api/mineru/tasks/{task_id}/download` | GET | 下载原始 ZIP |

## 项目结构

```
backend/
├── pyproject.toml          # Python 项目配置
├── .env.example            # 环境变量示例
├── main.py                 # FastAPI 主应用
└── src/
    ├── config.py           # 配置管理
    ├── models/
    │   └── schemas.py      # Pydantic 模型
    ├── mineru/
    │   ├── client.py       # MinerU API 客户端
    │   └── task_manager.py # 任务状态管理
    ├── api/
    │   └── mineru.py       # API 路由
    └── utils/
        └── zip_handler.py  # ZIP 处理工具
```

## 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| MINERU_API_KEY | MinerU API Key | "" |
| MINERU_API_BASE_URL | MinerU API 地址 | https://mineru.net |
| STORAGE_DIR | 存储目录 | ./storage |
| TASK_POLL_INTERVAL | 轮询间隔（秒） | 3 |
| MAX_POLL_ATTEMPTS | 最大轮询次数 | 60 |

## 开发

详细文档请参考项目根目录的 `docs/` 文件夹。
