# 向量管理页面：必要性分析

## 先看现状：用户目前对向量的"可见性"

| 已有能力 | 位置 |
|---------|------|
| 查看 Embedding 配置（模型/维度/是否启用） | 设置页 |
| 一键重建向量索引 | 设置页按钮 |
| 重建后看到统计（总片段/缓存命中/新调用） | 设置页 notify |
| 使用语义搜索 | 搜索页按钮 |

| 盲区（用户看不到） | 影响 |
|-------------------|------|
| 当前向量索引有多少条、占多少空间 | 不知道"家底" |
| 哪些资产已向量化、哪些没有 | 不知道覆盖范围 |
| embedding 缓存命中率 | 不知道重建要花多少钱 |
| 向量索引 vs chunks 表是否一致 | 不知道有没有"脏数据" |
| 模型/维度是否匹配当前配置 | 换模型后旧向量可能无效 |
| 最后重建时间 | 不知道索引是否过期 |

---

## 我的判断：**不需要独立页面，但需要状态可见**

理由：

**1. 项目哲学决定了向量是"可丢弃的缓存"**

> 文件系统是唯一数据源，数据库只是可重建的索引缓存。

向量索引随时可以删掉重建，不存在"不可恢复的状态"。管理页面的核心价值（保护数据、修复不一致）在这里不成立。

**2. 个人知识库规模有限**

几百个资产、几千个 chunk，不存在"需要分批管理"的场景。一个"全量重建"按钮就够了。

**3. 但"盲盒"体验确实不好**

用户点"重建向量索引"时完全不知道：
- 会调多少次 API？（费用）
- 缓存能命中多少？（省钱）
- 当前索引是不是已经是最新的？（是否值得重建）

---

## 推荐方案：设置页内嵌"向量索引状态"卡片

不新增页面，在现有设置页的"索引管理"区域增加一个状态卡片：

```python
# ── 向量索引状态 ──（设置页新增卡片）
with ui.card().classes("w-full p-4 mt-4"):
    ui.label("向量索引状态").classes("text-lg font-semibold")
    
    # 从 LanceDB 和 embedding_cache 聚合
    vector_stats = get_vector_stats()  # 新增工具函数
    
    with ui.grid(columns=3).classes("w-full gap-2 mt-2"):
        ui.label(f"向量总数：{vector_stats['total_vectors']}")
        ui.label(f"磁盘占用：{vector_stats['disk_size_mb']} MB")
        ui.label(f"缓存条目：{vector_stats['cache_count']}")
        ui.label(f"缓存命中率：{vector_stats['cache_hit_rate']}%")
        ui.label(f"模型：{vector_stats['model']}")
        ui.label(f"维度：{vector_stats['dimension']}")
    
    # 覆盖度：多少资产有向量 vs 总资产数
    ui.label(
        f"覆盖度：{vector_stats['indexed_assets']} / {vector_stats['total_assets']} 个资产"
    ).classes("text-sm text-gray-600 mt-2")
    
    # 最后重建时间
    ui.label(
        f"最后重建：{vector_stats['last_rebuilt'] or '从未'}"
    ).classes("text-sm text-gray-600")
    
    # 操作按钮
    with ui.row().classes("gap-3 mt-3"):
        ui.button("增量更新").props("outline")  # 只处理新增 chunks
        ui.button("全量重建").props("color=red outline")  # 已有，移到这里
        ui.button("清空缓存").props("outline color=orange")  # 清 embedding_cache
```

### 需要新增的工具函数

`app/services/vector_service.py` 中增加：

```python
def get_vector_stats() -> dict:
    """聚合向量索引状态，供设置页展示"""
    stats = {
        "total_vectors": 0,
        "disk_size_mb": 0,
        "cache_count": 0,
        "cache_hit_rate": 0,
        "model": "",
        "dimension": 0,
        "indexed_assets": 0,
        "total_assets": 0,
        "last_rebuilt": None,
    }
    
    # 1. LanceDB 记录数 + 磁盘占用
    vector_dir = state.library_root / ".knowledge" / "vector" / "lancedb"
    if vector_dir.exists():
        try:
            import lancedb
            db = lancedb.connect(str(vector_dir))
            table_names = db.table_names()
            if table_names:
                table = db.open_table(table_names[0])
                stats["total_vectors"] = table.count_rows()
            # 磁盘占用
            total_size = sum(
                f.stat().st_size for f in vector_dir.rglob("*") if f.is_file()
            )
            stats["disk_size_mb"] = round(total_size / 1024 / 1024, 1)
        except Exception:
            pass
    
    # 2. embedding_cache 统计
    db_path = get_db_path()
    conn = get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM embedding_cache"
        ).fetchone()
        stats["cache_count"] = row["cnt"] if row else 0
        
        row = conn.execute(
            "SELECT model, dimension FROM embedding_cache LIMIT 1"
        ).fetchone()
        if row:
            stats["model"] = row["model"]
            stats["dimension"] = row["dimension"]
    finally:
        conn.close()
    
    # 3. 资产覆盖度
    conn = get_conn(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) as cnt FROM assets").fetchone()
        stats["total_assets"] = total["cnt"] if total else 0
        
        indexed = conn.execute(
            "SELECT COUNT(DISTINCT asset_id) as cnt FROM chunks WHERE kind = 'vector'"
        ).fetchone()
        stats["indexed_assets"] = indexed["cnt"] if indexed else 0
    finally:
        conn.close()
    
    return stats
```

### 可选：增量更新

```python
def incremental_vector_update() -> dict:
    """只对新增/变更的 chunks 做 embedding，不全量重建"""
    # 找出 chunks 中有 content_hash 但 embedding_cache 中没有的记录
    # 只对这些调 embedding API
    # 返回 {"new_embedded": N, "skipped": M}
```

---

## 向量状态卡片：实现规格（已纳入 M8，已实现 commit 4328a5c）

上面"推荐方案"是草稿，这里给出可直接实现的规格。改动很小（设置页加一个卡片 + `vector_service` 加一个统计函数 + config.toml 增加 `[vector] last_rebuilt`），但对用户决策"要不要花钱重建"很有帮助——尤其是"模型已变更 / 索引不一致 / 已过期"这类健康提示。

### 字段 → 数据来源映射

| 显示字段 | 数据来源 | 备注 |
|---|---|---|
| 向量总数 | LanceDB `table.count_rows()` | 复用 `connect_lancedb()`，单表 `TABLE_NAME` |
| 磁盘占用 | 递归统计 `vector_dir()` 下所有文件 | MB，1 位小数 |
| 缓存条目 | `SELECT COUNT(*) FROM embedding_cache` | |
| 缓存命中率 | 暂无累计字段，先用"上次重建命中数"近似（见下） | M9 再补累计统计 |
| 模型 | `embedding_cache` 采样 / 当前 `get_embedding_config()` | 用于与配置比对 |
| 维度 | `embedding_cache` 采样 / 当前配置 | |
| 覆盖度 | `chunks(kind='vector')` DISTINCT asset_id / `assets` 总数 | |
| 最后重建 | config.toml `[vector] last_rebuilt`（ISO8601） | 重建完成时写入 |
| 健康状态 | 综合判定（见下） | 徽章颜色随之变化 |

> 注意：`embedding_cache` 当前只有 `content_hash/model/vector/dimension/created_at`，**没有命中率累计字段**。单次重建返回的 `cache_hits`（见 `build_embeddings` 返回值）只反映那一次。要做"累计命中率"需给表加 `hits/total` 列或维护统计表——留到 M9。M8 阶段"缓存命中率"先展示"上次重建命中 X 条"或留空。

### 健康状态判定（核心增量价值）

卡片顶部放一个状态徽章，颜色随判定结果变化：

| 状态 `health` | 触发条件 | 颜色 | 说明 |
|---|---|---|---|
| `no_library` | `state.library_root is None` | 灰 | 请先打开知识库 |
| `none` | 向量总数 = 0 | 红 | 索引尚未建立，建议重建 |
| `model_mismatch` | 缓存记录的 `model`/`dimension` ≠ 当前 Embedding 配置 | 红 | 旧向量可能失效，建议重建 |
| `inconsistent` | `chunks(kind='vector')` 行数 ≠ LanceDB `count_rows()`，或表不存在但 chunks 有记录 | 橙 | 索引与数据脱节 |
| `stale` | `last_rebuilt` 早于任一 chunk/artifact 的 `mtime`（粗略） | 橙 | 索引可能过期 |
| `ok` | 以上均不满足 | 绿 | 正常 |

### last_rebuilt 记录机制（当前缺失，需新增）

代码里**没有任何"最后重建时间"的存储**，需补：

- 库级 `config.toml` 增加 `[vector]` 段：`last_rebuilt = "2026-08-16T14:00:00"`（ISO8601 字符串）。
- `build_embeddings`（全量重建 / 增量更新）完成时写入该字段，由 `config_service` 提供 `set_vector_last_rebuilt()`。
- `get_vector_stats` 读取展示；为空显示"从未"。

### 完善版 get_vector_stats

在 `app/services/vector_service.py` 中落地（草稿基础上的增强版，统一用一个 `conn` 跑完所有 SQL，避免原草稿换连接导致一致性检查失效）：

```python
from app.state import state
from app.database import get_conn, get_db_path
from app.services.config_service import get_embedding_config, get_config
from app.services.vector_service import vector_dir, connect_lancedb, TABLE_NAME, table_exists


def get_vector_stats() -> dict:
    stats = {
        "total_vectors": 0,
        "disk_size_mb": 0.0,
        "cache_count": 0,
        "last_rebuilt": None,
        "model": "",
        "dimension": 0,
        "indexed_assets": 0,
        "total_assets": 0,
        "health": "unknown",
        "health_msg": "",
        "last_run_cache_hits": None,
    }
    if state.library_root is None:
        stats["health"] = "no_library"
        stats["health_msg"] = "请先打开知识库"
        return stats

    # 1. LanceDB 记录数 + 磁盘占用
    vd = vector_dir()
    if vd.exists():
        try:
            db = connect_lancedb()
            if table_exists():
                stats["total_vectors"] = db.open_table(TABLE_NAME).count_rows()
            total = sum(f.stat().st_size for f in vd.rglob("*") if f.is_file())
            stats["disk_size_mb"] = round(total / 1024 / 1024, 1)
        except Exception:
            pass

    # 2. SQLite 统计（统一一个连接）
    conn = get_conn(get_db_path())
    try:
        stats["cache_count"] = conn.execute(
            "SELECT COUNT(*) AS c FROM embedding_cache"
        ).fetchone()["c"]
        row = conn.execute(
            "SELECT model, dimension FROM embedding_cache LIMIT 1"
        ).fetchone()
        if row:
            stats["model"], stats["dimension"] = row["model"], row["dimension"]

        stats["total_assets"] = conn.execute(
            "SELECT COUNT(*) AS c FROM assets"
        ).fetchone()["c"]
        stats["indexed_assets"] = conn.execute(
            "SELECT COUNT(DISTINCT asset_id) AS c FROM chunks WHERE kind='vector'"
        ).fetchone()["c"]

        # 一致性：chunks(kind='vector') 行数 vs LanceDB 行数
        chunk_rows = conn.execute(
            "SELECT COUNT(*) AS c FROM chunks WHERE kind='vector'"
        ).fetchone()["c"]
    finally:
        conn.close()

    # 3. 最后重建时间
    stats["last_rebuilt"] = get_config().get("vector", {}).get("last_rebuilt")

    # 4. 健康判定
    if stats["total_vectors"] == 0:
        stats["health"], stats["health_msg"] = "none", "向量索引尚未建立，建议重建"
    else:
        cfg = get_embedding_config()
        if stats["model"] and (cfg.get("model") != stats["model"]
                               or cfg.get("dimension") != stats["dimension"]):
            stats["health"] = "model_mismatch"
            stats["health_msg"] = "Embedding 模型/维度已变更，旧向量可能失效，建议重建"
        elif chunk_rows != stats["total_vectors"]:
            stats["health"] = "inconsistent"
            stats["health_msg"] = "向量索引与数据不一致，建议重建"
        else:
            stats["health"], stats["health_msg"] = "ok", "正常"

    return stats
```

> 增量更新按钮调用 `incremental_vector_update()`（见"推荐方案"可选草稿）；"全量重建"复用现有 `build_embeddings`；"清空缓存"执行 `DELETE FROM embedding_cache`。

### UI 表现

设置页"索引管理"区新增卡片，自上而下：

1. 标题"向量索引状态" + 右上角**健康状态徽章**（颜色随 `health`）。
2. 3 列 grid：向量总数 / 磁盘占用 / 缓存条目 / 模型 / 维度 / 覆盖度。
3. 小字一行：最后重建时间（无则"从未"）。
4. 小字一行：健康说明 `health_msg`。
5. 按钮行：增量更新（outline）/ 全量重建（红 outline）/ 清空缓存（橙 outline）。

与"全文索引状态"卡片并排在设置页索引管理区，符合 M8"状态可见"的体验优化目标。

> **已实现（commit 4328a5c）**：设置页新增「向量索引状态」卡片；`config_service` 增加 `get/set_vector_last_rebuilt`（写 `config.toml [vector] last_rebuilt`）；`vector_service` 增加 `get_vector_stats`（聚合向量总数/磁盘占用/缓存条目/模型/维度/覆盖度/最后重建/健康状态）与 `clear_embedding_cache`；`rebuild_vector_index` 完成后自动写入 `last_rebuilt`。

---

## 不建议做的

| 功能 | 理由 |
|------|------|
| 独立的 `/vectors` 页面 | 信息量不够撑一个页面，设置页卡片够了 |
| 资产级向量化状态列表 | 个人库规模小，看覆盖度数字就够 |
| 单条向量删除/编辑 | 违背"可重建缓存"哲学，删了重建就行 |
| 向量可视化（t-SNE/UMAP） | 酷但不实用，MVP 不需要 |
| 向量版本管理 | 过度设计 |

---

## 总结

| 决策 | 建议 |
|------|------|
| 独立向量管理页面？ | **不做** |
| 设置页增加向量状态卡片？ | **做**（M8 或 M9 顺手加） |
| 增量更新按钮？ | **M9 再做**（需要先有 chunk 变更检测机制） |
| 全量重建保留在设置页？ | **保留**，移到状态卡片旁边更直觉 |

**决策：向量状态卡片纳入 M8。** 改动很小（设置页加一个卡片 + `vector_service` 加一个 `get_vector_stats` + config.toml 增加 `[vector] last_rebuilt`），但对用户决策"要不要花钱重建"很有帮助——尤其是"模型已变更 / 索引不一致 / 已过期"这类健康状态提示。增量更新按钮与累计命中率留到 M9（依赖 chunk 变更检测与命中率累计字段）。