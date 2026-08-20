# 修复：向量索引状态卡片永远显示「不一致」，覆盖度恒为 0

- 日期：2026-08-20
- 影响位置：设置页「向量索引状态」卡片（`app/services/vector_service.py` `get_vector_stats`）
- 现象：无论怎么重建，健康状态始终提示「不一致」（chunks 与 LanceDB 行数不相等），资产覆盖度始终 0/N

## 根因

`get_vector_stats` 沿用了讨论稿 [vector-manage.md](../讨论/qwen-prdv1/vector-manage.md) 的统计口径，用 `kind='vector'` 过滤 chunks 表：

```sql
SELECT COUNT(*) FROM chunks WHERE kind='vector'
```

但 chunks 表实际写入的 kind 只有 `transcript / summary / note / parsed / document`（索引来源类型，见 M4 决策），**从不存在 `kind='vector'` 的行**。于是：

- `chunk_rows` 恒为 0，与 LanceDB 实际向量数永不相等 → 一致性判断恒为「不一致」，重建后也不会恢复
- `indexed_assets` 恒为 0 → 覆盖度恒为 0%

统计口径与重建逻辑脱节：`rebuild_vector_index` 实际是对**全部非空白片段**向量化（跳过空白、不限 kind），统计却按一个不存在的 kind 过滤。

## 修复

统计改为与重建逻辑同一口径——统计全部非空白片段，不再按 kind 过滤：

```sql
SELECT COUNT(DISTINCT asset_id) FROM chunks WHERE TRIM(content) <> ''
SELECT COUNT(*) FROM chunks WHERE TRIM(content) <> ''
```

修复后健康状态、一致性、覆盖度均恢复正常。

## 经验

- 讨论稿中的 SQL 只是示意，落地时必须与实际写入路径（重建/索引逻辑）核对口径，本 bug 即「照搬示意 SQL + 表结构演进」叠加产物
- 派生统计（一致性/覆盖度）的过滤条件应与其数据生产方（rebuild）保持同源定义，两处各写一份条件迟早漂移；后续可考虑抽公共常量或由 rebuild 直接维护计数字段
- 该 bug 的症状有辨识度：「重建成功但状态永远不一致」说明不是数据问题而是统计口径问题，优先怀疑过滤条件与写入方不对齐

## 验证

1. 设置页查看向量索引状态卡片：重建后健康状态显示「正常」，不再提示不一致
2. 覆盖度 = 有非空白片段的资产数 / 总资产数，与实际资产数一致
3. 向量总数与缓存条目、磁盘占用显示正常
