# M9：文档解析接入（MinerU）

2026-08-20 与用户讨论定稿。对应 PRD §31 后续阶段规划第 1 项「文档解析接入」
（原表述为「文档解析 CLI 接入」，实施形态调整为 API 解析器 + provider 抽象）。

---

## 0. 已定决策（讨论结论，不再开放）

1. **首个解析器 = MinerU**（精准解析 API v4），通过 provider 抽象预留其他解析器
   （doc2x / Textin / 本地 CLI 等，实现同一接口即可注册接入）。
2. **本地文件走批量上传接口** `POST /api/v4/file-urls/batch`——单文件接口
   `/api/v4/extract/task` 只收 URL 不支持本地上传，批量上传是本地文件唯一入口。
3. **产物只落文本**：从结果 zip 提取 `full.md` 写为源文件旁 `{stem}.parsed.md`
   （平铺 sidecar，扫描层零改动）；原始 zip 留档 `.knowledge/backups/`。
   图片不落盘，markdown 中 `images/` 引用在预览中为断链（搜索/总结不受影响）。
4. **任务粒度 = 一资产一任务**，MinerU 批量接口按 batch-of-1 使用。
   完全复用现有任务中心 / 重试=新建任务 / 并发去重；批量解析体验将来在
   资产列表做多选循环建任务，不在本里程碑。
5. **可解析白名单**：`.pdf/.docx/.doc/.pptx/.ppt/.xlsx/.xls`。
   epub（MinerU 不支持）与图片 OCR 不做，留给未来 provider。
6. **默认模型 `vlm`**，配置可切 `pipeline`。
7. **token 走 `token_env` + secrets.toml 机制**（复用 `get_api_key`），
   明文 token 绝不入 TOML / UI，与 LLM / Embedding 安全约定一致。
8. **PDF 总结输入切换**：解析落地后，AI 总结对白名单文档改读 `{stem}.parsed.md`
   （PRD §13.2 预留项，随本里程碑一并落地）。
9. watchdog 文件监听已移入「待实现（暂缓）」（PRD §31），与本里程碑无关。

---

## 1. MinerU API 要点（事实备查）

文档：<https://mineru.net/apiManage/docs>（精准解析 API v4）

```text
1. 申请上传链接  POST /api/v4/file-urls/batch
   body: { files: [{name}], model_version }
   ≤50 文件/批；响应 data = {batch_id, file_urls}
   （2026-08-21 接真实 API 核对：file_urls 是纯 URL 字符串列表，
    按请求 files 顺序一一对应，不是对象列表）

2. 上传          PUT {upload_url}
   ⚠ 不带 Content-Type 头；上传链接 24h 有效；
   上传完成后系统自动提交解析任务，无需再调提交接口

3. 轮询结果      GET /api/v4/extract-results/batch/{batch_id}
   data.extract_result[] = {file_name, state, full_zip_url, err_msg}
   state: waiting-file / running / done / failed；err_msg 无错时为空串

4. 下载产物      GET {full_zip_url}
   zip 内含 full.md / images/ / 版面中间 json 等
```

限制与注意：

```text
单文件 ≤200MB、≤200 页
每日 1000 页免费高优先级额度（个人库通常无感，需知晓）
认证头 Authorization: Bearer {token}，token 在 MinerU 网站「API 管理」页自建
Agent 轻量解析 API（免 token）仅单文件/50 页/无表格公式，不做主路径
```

零新增依赖：HTTP 用项目已有 `httpx`（llm_service 同款），zip 解压用标准库。

---

## 2. 解析器抽象：`app/services/parsers/`

### 2.1 `app/services/parsers/base.py`

```python
"""文档解析器抽象：submit → poll → fetch 三阶段。

HTTP API 与本地 CLI 均可实现同一接口：
CLI 解析器的 submit = 起子进程、poll = 查输出文件、fetch = 读产物。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseSubmission:
    """一次解析提交的远端状态。

    持久化进任务 params_json（见 parse_service），应用重启后凭它恢复轮询。
    """

    batch_id: str
    files: list[dict] = field(default_factory=list)


@dataclass
class ParseFileState:
    """单个文件的解析状态。"""

    name: str
    state: str  # waiting_file / running / done / failed
    err_msg: str | None = None
    full_zip_url: str | None = None


class DocumentParser:
    """解析器接口。"""

    name: str = ""

    def submit(self, paths: list[Path]) -> ParseSubmission:
        """提交解析（含文件上传），返回可轮询的远端状态。"""
        raise NotImplementedError

    def poll(self, submission: ParseSubmission) -> list[ParseFileState]:
        """查询各文件状态。结果接口幂等，可反复调用。"""
        raise NotImplementedError

    def fetch(self, state: ParseFileState) -> bytes:
        """取回产物原始字节（MinerU 为 zip 字节流）。"""
        raise NotImplementedError
```

### 2.2 `app/services/parsers/mineru_parser.py`

```python
"""MinerU 精准解析 API v4。本地文件走批量上传接口（见 §1 要点）。"""

from __future__ import annotations

import httpx
from loguru import logger
from pathlib import Path

from app.services.config_service import get_api_key
from app.services.parsers.base import (
    DocumentParser,
    ParseFileState,
    ParseSubmission,
)

DEFAULT_BASE_URL = "https://mineru.net"
MAX_FILE_BYTES = 200 * 1024 * 1024


class MineruParser(DocumentParser):
    name = "mineru"

    def __init__(self, config: dict):
        self.base_url = (config.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
        self.model_version = config.get("model_version") or "vlm"
        self.token_env = config.get("token_env") or "MINERU_API_TOKEN"
        self.timeout = config.get("timeout", 30)
        self.token = get_api_key(self.token_env)

        if not self.token:
            raise ValueError(
                f"未配置 MinerU token：请设置环境变量 {self.token_env}，"
                "或写入 .knowledge/secrets.toml"
            )

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def submit(self, paths: list[Path]) -> ParseSubmission:
        # 1. 申请上传链接（batch-of-1：QBase 一资产一任务，见 §0 决策 4）
        resp = httpx.post(
            f"{self.base_url}/api/v4/file-urls/batch",
            headers=self._headers(),
            json={
                "enable_ocr": True,
                "files": [{"name": p.name} for p in paths],
                "model_version": self.model_version,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get("code") != 0:
            raise ValueError(f"MinerU 申请上传链接失败：{body.get('msg')}")

        data = body["data"]
        files = [
            {"name": item["name"], "upload_url": item["upload_url"]}
            for item in data["file_urls"]
        ]

        # 2. 上传（不能带 Content-Type，见 §1 要点）
        for file_info, path in zip(files, paths):
            up = httpx.put(
                file_info["upload_url"],
                content=path.read_bytes(),
                timeout=600,
            )
            up.raise_for_status()

        # 上传完成即自动提交解析
        return ParseSubmission(batch_id=data["batch_id"], files=files)

    def poll(self, submission: ParseSubmission) -> list[ParseFileState]:
        resp = httpx.get(
            f"{self.base_url}/api/v4/extract-results/batch/{submission.batch_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get("code") != 0:
            raise ValueError(f"MinerU 查询解析结果失败：{body.get('msg')}")

        return [
            ParseFileState(
                name=item.get("file_name", ""),
                state=item.get("state", "running"),
                err_msg=item.get("err_msg"),
                full_zip_url=item.get("full_zip_url"),
            )
            for item in body["data"]["extract_result"]
        ]

    def fetch(self, state: ParseFileState) -> bytes:
        resp = httpx.get(state.full_zip_url, timeout=600, follow_redirects=True)
        resp.raise_for_status()
        return resp.content
```

### 2.3 `app/services/parsers/__init__.py`

```python
"""解析器注册表。[parse] provider 配置值 -> 解析器类。"""

from __future__ import annotations

from app.services.parsers.base import DocumentParser, ParseFileState, ParseSubmission
from app.services.parsers.mineru_parser import MineruParser

PARSERS: dict[str, type[DocumentParser]] = {
    MineruParser.name: MineruParser,
}


def get_parser(config: dict) -> DocumentParser:
    provider = config.get("provider") or "mineru"
    cls = PARSERS.get(provider)

    if cls is None:
        raise ValueError(
            f"未注册的解析器：{provider}（可用：{'、'.join(PARSERS)}）"
        )

    # provider 专属配置挂在同名子表下（如 [parse.mineru]）
    provider_config = dict(config.get(provider) or {})
    return cls(provider_config)
```

---

## 3. 配置

### 3.1 `DEFAULT_LIBRARY_CONFIG`（library_service.py）

`[cli]` 段删除 `parse_command = []` 占位（CLI 模板思路被 provider 抽象取代，
已有库的该行无害，可留可删），新增：

```toml
[parse]
# 文档解析（m9）。使用前到 https://mineru.net「API 管理」页创建 token，
# 设置环境变量 MINERU_API_TOKEN（或写入 .knowledge/secrets.toml），
# 再把 enabled 改为 true。
enabled = false
provider = "mineru"

[parse.mineru]
base_url = "https://mineru.net"
token_env = "MINERU_API_TOKEN"
# pipeline：经典多模块流水线，更快；vlm：端到端模型，复杂版面/公式/表格更强
model_version = "vlm"
# 单任务整体超时（提交+轮询+下载），秒
timeout_seconds = 1800
poll_interval_seconds = 10
```

仅影响新开的库；已有库手动在 config.toml 补同样段落。

### 3.2 `config_service.get_parse_config()`

与 `get_embedding_config` / `get_summary_llm_config` 并列：

```python
def get_parse_config() -> dict:
    config = load_config()
    parse = dict(config.get("parse") or {})
    provider = parse.get("provider") or "mineru"
    provider_cfg = dict(parse.get(provider) or {})

    return {
        "enabled": bool(parse.get("enabled", False)),
        "provider": provider,
        **provider_cfg,
    }
```

`validate_config` 增补：`[parse] enabled=true` 时 `provider` 必须在
`PARSERS` 注册表内、`model_version ∈ {pipeline, vlm}`（非法值 400 中文报错，
与 dimension 校验同模式）。

`get_key_status` 增补 `parse` 条目：读 `[parse.mineru].token_env` 的
`get_api_key` 结果（复用 llm / embedding 的红绿灯机制）。

`test_connection` 增补 `kind="parse"` 分支 `_test_parse_connection`：

```python
def _test_parse_connection(config: dict) -> dict:
    # 用一个不存在的 batch_id 查结果接口：401 = token 无效，404 = token 有效
    # 不消耗页数额度
    resp = httpx.get(
        f"{base_url}/api/v4/extract-results/batch/qbase-connectivity-test",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    # 401/403 -> "token 无效或已过期"；404 -> "连通成功（token 有效）"
    # 其他 -> 透传状态码与 msg
```

---

## 4. 解析任务服务：`app/services/parse_service.py`

与转录任务的**唯一模型差异**：转录是本机子进程跑完即止；解析是分钟级远程
异步任务，`batch_id` 必须持久化进 `params_json`，应用重启后恢复轮询。

```python
"""文档解析任务服务：submit → poll 循环 → 下载 zip → 写 {stem}.parsed.md
→ 自动重扫 + 重建全文索引（对齐转录/总结的成功后动作）。"""

from __future__ import annotations

import io
import json
import threading
import time
import zipfile
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.repositories.asset_repository import get_asset_by_id
from app.services.config_service import get_parse_config
from app.services.index_service import rebuild_fulltext_index
from app.services.parsers import get_parser
from app.services.parsers.base import ParseSubmission
from app.services.scanner_service import scan_current_library
from app.state import get_db_path, get_library_root

# 可解析后缀白名单（见 §0 决策 5；epub/图片留给未来 provider）
PARSEABLE_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls"}
PARSED_SUFFIX = ".parsed.md"
MAX_FILE_BYTES = 200 * 1024 * 1024  # 与 MineruParser 一致

# 正在执行的解析任务守卫（防止 resume 与新任务重复起线程）
_live_task_ids: set[str] = set()
_live_lock = threading.Lock()


def _parsed_path(asset_path: str) -> Path:
    """paper.pdf -> paper.parsed.md（与 ARTIFACT_SUFFIXES 的绑定键一致）。"""
    return Path(asset_path).with_suffix(PARSED_SUFFIX)


def _archive_zip_path(asset_path: str) -> Path:
    root = get_library_root()
    return root / ".knowledge" / "backups" / (_parsed_path(asset_path).name + ".zip")


def _extract_full_md(zip_bytes: bytes) -> str:
    """从 MinerU 结果 zip 提取 full.md 文本；缺失则失败。"""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        target = next((n for n in names if n.endswith("full.md")), None)

        if target is None:
            raise ValueError(f"解析结果 zip 中没有 full.md：{names[:10]}")

        return zf.read(target).decode("utf-8", errors="replace")


def start_parsing(asset_id: str) -> str:
    """创建并启动解析任务（前置校验 + 并发去重，对齐 start_transcription）。"""
    conn = get_conn(get_db_path())

    try:
        asset = get_asset_by_id(conn, asset_id)

        if asset is None:
            raise ValueError("资产不存在")

        ext = Path(asset["absolute_path"]).suffix.lower()

        if ext not in PARSEABLE_EXTENSIONS:
            raise ValueError(f"当前不支持解析 {ext} 文件")

        if Path(asset["absolute_path"]).stat().st_size > MAX_FILE_BYTES:
            raise ValueError("文件超过 MinerU 单文件 200MB 上限，无法解析")

        if task_repository.count_running_tasks(
            conn, asset_id=asset_id, task_type="parse"
        ) > 0:
            raise ValueError("该资产已有解析任务正在运行")

        config = get_parse_config()

        if not config.get("enabled"):
            raise ValueError("文档解析未启用，请在设置页开启 [parse]")

        get_parser(config)  # token 缺失 / provider 未注册在此即抛 ValueError

        parsed = _parsed_path(asset["absolute_path"])
        params = {
            "asset_id": asset_id,
            "input": asset["absolute_path"],
            "provider": config["provider"],
            # submission 字段提交成功后回写（重启恢复轮询的凭据）
        }

        task_id = task_repository.create_task(
            conn,
            asset_id=asset_id,
            task_type="parse",
            params=params,
            command=None,  # API 任务无 CLI 命令，详情对话框显示 provider
            output_path=str(parsed),
        )

        conn.commit()
    finally:
        conn.close()

    _spawn_task_thread(task_id)

    logger.info("解析任务已创建：{} ({})", task_id[:8], asset["title"])

    return task_id


def _spawn_task_thread(task_id: str) -> None:
    with _live_lock:
        if task_id in _live_task_ids:
            return
        _live_task_ids.add(task_id)

    thread = threading.Thread(target=run_parse_task, args=(task_id,), daemon=True)
    thread.start()


def run_parse_task(task_id: str) -> None:
    """后台执行解析任务：提交 → 轮询 → 下载 → 写 parsed.md → 刷新索引。"""
    conn = get_conn(get_db_path())

    try:
        task = task_repository.get_task(conn, task_id)

        if task is None:
            return

        asset = get_asset_by_id(conn, task["asset_id"]) if task["asset_id"] else None

        if asset is None:
            task_repository.update_task(
                conn, task_id,
                status="failed", error="资产不存在",
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
            return

        config = get_parse_config()
        parser = get_parser(config)
        params = json.loads(task["params_json"]) if task["params_json"] else {}

        task_repository.update_task(
            conn, task_id,
            status="running",
            started_at=task_repository.utcnow_iso(),
        )
        conn.commit()

        # ---- 阶段 1：提交（已有 submission 则跳过——重启恢复场景） ----
        submission = None

        if params.get("submission"):
            submission = ParseSubmission(**params["submission"])
        else:
            submission = parser.submit([Path(asset["absolute_path"])])
            params["submission"] = {
                "batch_id": submission.batch_id,
                "files": submission.files,
            }
            task_repository.update_task(
                conn, task_id,
                params_json=json.dumps(params, ensure_ascii=False),
            )
            conn.commit()

        # ---- 阶段 2：轮询（结果接口幂等） ----
        deadline = time.monotonic() + config.get("timeout_seconds", 1800)
        interval = config.get("poll_interval_seconds", 10)
        zip_bytes: bytes | None = None

        while True:
            states = parser.poll(submission)
            state = states[0]  # batch-of-1

            if state.state == "done" and state.full_zip_url:
                break

            if state.state == "failed":
                raise ValueError(f"MinerU 解析失败：{state.err_msg or '未给出原因'}")

            if time.monotonic() > deadline:
                raise ValueError(
                    f"解析超时（超过 {config.get('timeout_seconds', 1800)} 秒），"
                    "可在任务中心重试"
                )

            time.sleep(interval)

        # ---- 阶段 3：下载 + 落盘 ----
        zip_bytes = parser.fetch(state)
        md_text = _extract_full_md(zip_bytes)

        parsed = _parsed_path(asset["absolute_path"])
        archive = _archive_zip_path(asset["absolute_path"])

        if parsed.exists():
            archive_dir = archive.parent
            archive_dir.mkdir(parents=True, exist_ok=True)
            # 覆盖重解析前，旧 parsed.md 一并留档（对齐总结覆盖备份策略）
            backup_md = archive_dir / (
                parsed.name + "." + time.strftime("%Y%m%d-%H%M%S") + ".bak.md"
            )
            backup_md.write_text(parsed.read_text(encoding="utf-8"), encoding="utf-8")

        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(zip_bytes)
        parsed.write_text(md_text, encoding="utf-8")

        # ---- 阶段 4：刷新索引（对齐转录/总结） ----
        warning = None

        try:
            scan_current_library()
            rebuild_fulltext_index()
        except Exception as scan_exc:
            warning = f"解析成功，但刷新索引失败：{scan_exc}"

        task_repository.update_task(
            conn, task_id,
            status="success",
            output_path=str(parsed),
            error=warning,
            finished_at=task_repository.utcnow_iso(),
        )
        conn.commit()
        logger.info("解析任务成功：{}", asset["title"])

    except Exception as exc:
        logger.exception("解析任务异常：{}", task_id)

        try:
            task_repository.update_task(
                conn, task_id,
                status="failed", error=str(exc),
                finished_at=task_repository.utcnow_iso(),
            )
            conn.commit()
        except Exception:
            pass
    finally:
        with _live_lock:
            _live_task_ids.discard(task_id)
        conn.close()


def resume_running_parse_tasks() -> None:
    """应用启动 / 重新打开知识库时，恢复未完结的解析任务。

    - params_json 已含 submission：直接续轮询（幂等）
    - 尚未提交：从 submit 重新开始
    在 library_service.open_library 成功后调用；_live_task_ids 防重复起线程。
    """
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id FROM tasks
            WHERE type = 'parse' AND status IN ('pending', 'running')
            """
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        _spawn_task_thread(row["id"])
        logger.info("恢复未完结的解析任务：{}", row["id"][:8])
```

`open_library` 末尾（初始化完成、`scan_on_startup` 处理之后）追加：

```python
from app.services.parse_service import resume_running_parse_tasks

resume_running_parse_tasks()
```

---

## 5. API 端点（`app/api/library.py`）

与 transcribe / summarize 完全同构：

```python
@router.post("/assets/{asset_id}/parse")
def api_start_parsing(asset_id: str) -> dict:
    """触发生成文档解析任务。"""
    if get_library_status().get("opened") is not True:
        raise HTTPException(status_code=400, detail="未打开知识库")

    try:
        task_id = start_parsing(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"task_id": task_id, "status": "pending"}
```

任务查询复用既有 `GET /api/tasks`、`GET /api/tasks/{task_id}`，零新增。

---

## 6. UI 改动

### 6.1 资产详情页（`asset_detail.py`）

对 `ext ∈ PARSEABLE_EXTENSIONS` 的文档资产，在转录卡之前新增「文档解析」卡片
（布局/交互对齐转录卡）：

```text
未解析：  [生成解析]  按钮 → POST /api/assets/{id}/parse → notify + disable
          提示文案：调用 MinerU 解析为 Markdown（约需 1-5 分钟）
已解析：  显示 parsed 产物（复用派生文件多 tab 区，kind=parsed 已支持预览）
          [重新解析] 按钮 + 覆盖确认对话框（旧 parsed.md 自动备份，见 §4）
不可用：  enabled=false 或 token 缺失 → 按钮禁用 + hint 文案
          （"文档解析未启用/未配置 token，请前往设置页"，对齐总结卡禁用态）
```

has_parsed 判定复用 `asset_repository.list_assets` 同款 EXISTS 逻辑或详情
接口 artifacts 中 `kind='parsed' AND status='active'`。

### 6.2 设置页（`settings.py`）

新增「文档解析」配置卡（对齐 Embedding / LLM 卡）：

```text
enabled 开关 / provider（当前仅 mineru，只读展示）/ model_version 下拉
（pipeline / vlm）/ base_url / token_env + 密钥来源红绿灯 / 测试 API 按钮
（走 §3.2 的 parse 分支，不消耗页数额度）
```

保存走既有 `save_config` deep-merge patch 机制，`[parse]` 段自动生效；
`model_version` 变更告警不涉及索引重建（解析产物与向量索引解耦，重建索引
按钮已有，无需联动）。

### 6.3 任务中心（`tasks.py`）

- `TYPE_LABELS` 增 `"parse": "解析"`。
- 失败重试按钮增 `parse` 分支（重试=新建任务，对齐既有决策）：

```python
elif task["type"] == "parse" and task["asset_id"]:
    from app.services.parse_service import start_parsing
    start_parsing(task["asset_id"])
```

- 详情对话框 command 为空的 parse 任务显示 `provider: mineru`（params_json
  里已存，替代空白命令区）。

### 6.4 徽章

`parsed`（已解析）/「待解析」徽章 M2/M8 已有（`render_derived_badges` +
`parse_status=pending`），**零改动**。

---

## 7. PDF 总结输入切换（`summarization_service.get_summary_input_text`）

现状：`ext ∈ {.pdf, .docx, ...}` 直接 `raise ValueError("需要文档解析模块")`。

改为（对齐 PRD §13.2 预留）：

```python
# 文档：md/txt 读原文；白名单文档读 {stem}.parsed.md（需先解析）
if ext in PARSEABLE_EXTENSIONS:
    parsed_artifact = 查 artifacts 表 kind='parsed' AND status='active'
    if parsed_artifact is None:
        raise ValueError("该文档尚未解析，请先在详情页生成解析")
    return read_text_for_index(parsed_artifact 绝对路径)
```

详情页总结卡对白名单文档的可用性判断同步改为「已解析即可总结」，
hint 文案对齐音频的"需要先生成转录"模式。

---

## 8. 测试步骤（开发人员手动执行）

沿用 mock 验收模式（零 API 费用/零页数额度）：将附录 A 的 `mock_mineru.py`
保存到测试库 `kb-test/.knowledge/mock_mineru.py`（纯标准库，任意 Python 3.12+
可直接运行，端口 8793；启动方式见附录 A 文件头注释）。

```text
POST /api/v4/file-urls/batch     -> code=0, batch_id=mock-batch-001,
                                   file_urls=[.../upload/{name}]（URL 字符串列表）
PUT  /upload/{name}              -> 200，内容存内存；文件名含「触发失败」标记
GET  /api/v4/extract-results/batch/{batch_id}
      -> 前 2 次返回 running，第 3 次起：
         普通文件 done + full_zip_url=.../result.zip（zip 内 full.md）
         「触发失败」文件 failed + err_msg="mock 解析失败"
GET  /result.zip                 -> 内存拼装 zip（full.md 写入测试文本）
```

步骤：

```text
1. 启动 mock：kb-test/.knowledge 下 python mock_mineru.py
2. config.toml：[parse] enabled=false，base_url=http://127.0.0.1:8793
   → 详情页解析按钮禁用；强行 POST /api/assets/{id}/parse 返回 400「未启用」
3. enabled=true，不设 token → POST 返回 400「未配置 MinerU token」；
   设置页解析卡红绿灯为红
4. 设置 MINERU_API_TOKEN=mock-token → 测试 API 按钮显示连通成功
5. 放入 paper.pdf → 生成解析 → 任务中心 running → 约 20 秒后 success
   → paper.parsed.md 出现于 pdf 旁；.knowledge/backups/paper.parsed.md.zip 留档
   → 搜索 mock 写入的文本（QBASE-MOCK-PARSE-OK）可命中（全文索引已自动重建）
6. 解析完成后详情页「生成总结」按钮可用，输入为 parsed.md 内容
7. 重解析 → 覆盖确认 → 旧 parsed.md 备份 .bak.md 出现
8. 文件名含「触发失败」的 pdf → 任务 failed，err_msg 显示「mock 解析失败」
9. running 期间重启应用 → 重新打开知识库 → 任务自动恢复轮询至 success
10. 放入 note.epub → 解析按钮不出现（白名单外）
11. 放入 >200MB 占位 pdf → 提交返回 400 超限提示
```

---

## 9. M9 验收标准

```text
pdf / docx 等 白名单文档可在详情页发起解析，任务中心可查进度
解析成功后 {stem}.parsed.md 出现在源文件旁，zip 留档 .knowledge/backups/
解析产物自动进入全文索引，搜索可命中
向量索引重建后解析内容可语义搜索（复用既有索引来源，无新逻辑）
已解析文档可生成 AI 总结（输入为 parsed.md）
重复解析有覆盖确认，旧产物自动备份
失败（err_msg / 超时 / token 缺失 / 200MB 超限）在任务中心或提交时给出中文原因
应用重启后未完结的解析任务恢复轮询，不产生孤儿任务
设置页可编辑解析配置，token 来源红绿灯与测试 API 可用
明文 token 绝不出现在 UI 与 TOML 中
```

---

## 10. PRD 同步清单（实施完成时）

```text
§12 / §13.2  总结输入：白名单文档改读 {stem}.parsed.md（去掉"等待文档解析模块"占位）
§15.3        parse_command CLI 模板替换为 provider 抽象描述（含注册表与三阶段接口）
§20          配置模板增 [parse] / [parse.mineru]，[cli] 删 parse_command 占位
§28          增 M9 里程碑小节（目标 / 完成标志）
§29          验收标准增「文档解析」小节（§9 内容落过去）
§31          第 1 项「文档解析 CLI 接入」标记完成，表述改为 MinerU
docs/README.md  增 M9 实施记录（偏差/决策）
CLAUDE.md       当前进度勾 M9
```

---

## 11. 范围外（明确不做）

```text
epub / 图片 OCR（留给未来 provider）
解析产物图片落盘与渲染（断链可接受，zip 留档可恢复）
真批任务（一任务多文件）与资产列表多选批量解析（后续 UI 增强）
页数本地预估（200 页上限交给服务端报错）
每日 1000 页额度用量统计与展示
MinerU Agent 轻量 API 降级通道
watchdog 文件监听（已移入「待实现（暂缓）」）
```

---

## 附录 A：mock_mineru.py（本地测试服务器）

保存到测试库 `kb-test/.knowledge/mock_mineru.py`，运行：

```bash
python mock_mineru.py          # 监听 127.0.0.1:8793
```

知识库 config.toml 把 `[parse.mineru] base_url` 改为
`http://127.0.0.1:8793`，并设置环境变量 `MINERU_API_TOKEN=mock-token`。

行为约定（与 §8 步骤对应）：

```text
token != mock-token            -> 401（token 无效路径 + 设置页测试按钮）
batch_id = qbase-connectivity-test -> 404（连通性测试的正常路径）
每个批次前 2 次轮询返回 running，第 3 次起返回结果
文件名含「触发失败」            -> failed + err_msg
其余文件                        -> done，zip 内 full.md 含可搜索的固定文本
```

```python
"""MinerU v4 批量解析接口 mock（纯标准库）。

用法：python mock_mineru.py    # 监听 127.0.0.1:8793
"""

from __future__ import annotations

import io
import json
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

HOST = "127.0.0.1"
PORT = 8793
TOKEN = "mock-token"
FULL_MD_TEXT = "# QBase mock 解析结果\n\n这是 full.md 的正文，包含固定可搜索文本：QBASE-MOCK-PARSE-OK。\n"

# batch_id -> {poll_count, files: {name: uploaded_bytes}}
_batches: dict[str, dict] = {}
_batch_seq = 0


def _json_bytes(payload: dict, status: int = 200) -> tuple[bytes, str, int]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return body, "application/json", status


def _zip_bytes(name: str) -> bytes:
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{name}/full.md", FULL_MD_TEXT)
        zf.writestr(f"{name}/layout.pdf", b"%PDF-mock")

    return buf.getvalue()


class MockMineruHandler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {TOKEN}"

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""

        try:
            return json.loads(raw or b"{}")
        except Exception:
            return {}

    def log_message(self, fmt, *args):  # 安静模式
        pass

    # ── POST /api/v4/file-urls/batch：申请上传链接 ──
    def do_POST(self):
        global _batch_seq

        path = urlparse(self.path).path

        if path != "/api/v4/file-urls/batch":
            self._send(*_json_bytes({"code": 404, "msg": "not found"}, 404))
            return

        if not self._authorized():
            self._send(*_json_bytes({"code": 401, "msg": "Unauthorized"}, 401))
            return

        body = self._read_body()
        names = [str(f.get("name", "")) for f in body.get("files", [])]

        _batch_seq += 1
        batch_id = f"mock-batch-{_batch_seq:03d}"
        _batches[batch_id] = {"poll_count": 0, "files": {}}

        # 与真实 API 一致：file_urls 是纯 URL 字符串列表，按 files 顺序对应
        file_urls = [f"http://{HOST}:{PORT}/upload/{name}" for name in names]

        self._send(
            *_json_bytes(
                {"code": 0, "data": {"batch_id": batch_id, "file_urls": file_urls}}
            )
        )

    # ── PUT /upload/{name}：接收文件（模拟 OSS 直传）──
    def do_PUT(self):
        name = unquote(urlparse(self.path).path.removeprefix("/upload/"))
        length = int(self.headers.get("Content-Length", 0) or 0)
        data = self.rfile.read(length) if length else b""

        latest = max(_batches, key=lambda b: _batches[b]["poll_count"]) if _batches else None

        if latest:
            _batches[latest]["files"][name] = data

        self._send(b"", "application/octet-stream", 200)

    # ── GET /api/v4/extract-results/batch/{batch_id} 与 /result/{batch}.zip ──
    def do_GET(self):
        path = urlparse(self.path).path

        if not self._authorized():
            self._send(*_json_bytes({"code": 401, "msg": "Unauthorized"}, 401))
            return

        if path.startswith("/api/v4/extract-results/batch/"):
            batch_id = path.rsplit("/", 1)[-1]

            if batch_id == "qbase-connectivity-test":
                self._send(*_json_bytes({"code": 404, "msg": "batch not found"}, 404))
                return

            batch = _batches.get(batch_id)

            if batch is None:
                self._send(*_json_bytes({"code": 404, "msg": "batch not found"}, 404))
                return

            batch["poll_count"] += 1

            # 前 2 次返回 running，第 3 次起出结果
            if batch["poll_count"] <= 2:
                state = "running"
                zip_url = None
                err_msg = None
            else:
                state = "done"
                zip_url = f"http://{HOST}:{PORT}/result/{batch_id}.zip"
                err_msg = None

                # 文件名含「触发失败」走失败路径
                for name in batch["files"]:
                    if "触发失败" in name:
                        state = "failed"
                        zip_url = None
                        err_msg = "mock 解析失败（文件名含触发失败）"

            extract_result = [
                {
                    "file_name": name,
                    "state": state,
                    "full_zip_url": zip_url,
                    "err_msg": err_msg,
                }
                for name in batch["files"]
            ]

            self._send(
                *_json_bytes(
                    {"code": 0, "data": {"batch_id": batch_id, "extract_result": extract_result}}
                )
            )
            return

        if path.startswith("/result/") and path.endswith(".zip"):
            batch_id = path.removeprefix("/result/").removesuffix(".zip")
            batch = _batches.get(batch_id)

            if batch is None:
                self._send(b"not found", "text/plain", 404)
                return

            name = next(iter(batch["files"]), "result")
            self._send(_zip_bytes(name), "application/zip", 200)
            return

        self._send(b"not found", "text/plain", 404)


if __name__ == "__main__":
    print(f"mock MinerU listening on http://{HOST}:{PORT} (token: {TOKEN})")
    ThreadingHTTPServer((HOST, PORT), MockMineruHandler).serve_forever()
```
