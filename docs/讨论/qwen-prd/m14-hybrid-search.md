# M14：混合搜索排序（全文 + 向量 RRF 融合）

2026-08-21 定稿。对应 PRD §31 后续阶段规划第 1 项「混合搜索排序」，兑现
PRD §16.7 综合搜索「全文结果 + 向量结果融合 / Reciprocal Rank Fusion」。
范围 = 搜索服务新增综合模式（全文 + 向量两路 RRF 融合，chunk 级去重）+
搜索页新增「综合搜索」主入口 + REST search 端点 mode 扩展。文件名搜索
保持独立模式，不参与融合。

---

## 0. 已定决策（讨论结论，不再开放）

1. **融合范围 = 仅全文 + 向量两路**：PRD §16.7 原文即两路；文件名搜索是
   资产级 LIKE 命中，与 chunk 级结果语义不同，保持独立按钮不变。
2. **算法 = Reciprocal Rank Fusion**：score = Σ 1/(k + rank)，k=60（RRF
   论文标准值），rank 从 1 起。每路各取 top 50 候选，融合后按分数降序
   返回 limit 条。不做权重调参（两路等权）、不做分数归一化。
3. **去重粒度 = chunk 级，键为 chunk_id**：全文与向量结果同源于 chunks
   表；同 chunk 双命中合并为一条，条目标注命中来源（全文/语义/双命中），
   双命中天然得分最高、排在前面。
4. **向量不可用时降级为纯全文，不报错**：Embedding 未启用 / 向量索引为
   空 / Embedding API 调用失败，任一情况都只丢掉向量路，返回全文结果，
   UI 黄色提示「向量搜索未参与本次融合（原因）」。全文索引缺失时同理
   反向降级为纯向量 + 提示。
5. **UI 入口 = 「综合搜索」为搜索页主按钮（实心），回车默认触发**：全文
   搜索按钮降为 outline，文件名/语义按钮不变。综合是 M14 的主打能力，
   理应成为默认动作。
6. **结果展示**：每条结果显示命中来源徽章与 rrf_score（4 位小数）；双命中
   条目保留全文片段（带关键词高亮）并附 distance，纯向量条目显示
   distance，纯全文条目保持现有高亮样式。不展示两路各自排名（噪音）。
7. **范围外（明确不做）**：文件名融合、按类型/来源过滤（§16.6 未实现，
   维持现状）、资产级聚合（同资产多 chunk 合并成一条）、分数权重配置化、
   混合结果的分页。

---

## 1. 现状事实（代码依据）

```text
search_service.search_fulltext   chunk 级结果（FTS5 rank + LIKE 兜底），输出
                                 dict 不含 chunk_id；FTS 索引缺失时抛
                                 RuntimeError「请前往设置页重建」
search_service.search_vector     chunk 级结果（LanceDB distance 升序），
                                 输出 dict 不含 chunk_id；Embedding 未启用
                                 时 vector_service 抛 ValueError
vector_service.search_vectors    返回 asset_id/artifact_id/kind/relative_path/
                                 content/distance；LanceDB 记录本身带 id
                                 （= SQLite chunks.id），只是没往外传
search_service.search(query, mode)  统一入口，mode 三选一互斥（filename/
                                 fulltext/vector）
api GET /api/search              mode 校验 filename/fulltext/vector
ui/pages/search.py               三个按钮各自 handler，全文为实心主按钮，
                                 回车触发全文搜索；vector 结果展示
                                 distance，全文/文件名结果做关键词高亮
```

## 2. 实施蓝图

### 2.1 `app/services/vector_service.py`

```text
search_vectors 返回值补 chunk_id    取 LanceDB 记录 id 字段，一行
```

### 2.2 `app/services/search_service.py`

```text
search_fulltext / search_vector    输出 dict 补 chunk_id（融合去重键）
_rrf_fuse(fulltext_results, vector_results, limit)
                                   纯函数：按 chunk_id 合并两路，rank 从 1
                                   起，score = Σ 1/(60+rank)；条目带
                                   rrf_score、sources（fulltext/vector/both）、
                                   snippet/highlight_words 取全文路（有高亮
                                   信息），distance 取向量路；按分数降序截
                                   limit
search_hybrid(conn, query, limit)  两路各自 try/except：全文路 RuntimeError
                                   （索引缺失）→ 丢弃并记原因；向量路任何
                                   异常 → 丢弃并记原因；两路皆空/皆失败时
                                   返回空结果 + 原因。返回 (results,
                                   degraded_reason)，degraded_reason 为
                                   None 表示两路都参与
search(query, mode, limit)         mode 增加 hybrid → search_hybrid
```

### 2.3 `app/api/library.py`

```text
GET /api/search                    mode 校验与 docstring 增加 hybrid；响应
                                   增加 degraded_reason 字段（仅 hybrid 时
                                   可能为非 None）
```

### 2.4 `app/ui/pages/search.py`

```text
按钮区                              「综合搜索」实心主按钮 + 「全文搜索」改
                                   outline + 文件名/语义按钮不变；回车改触
                                   发综合搜索
handle_hybrid                      调 search_hybrid，render_results 前若
                                   degraded_reason 非 None 先在结果区顶部渲染
                                   黄色提示 label
render_results                     支持 sources 徽章（全文/语义/双命中，沿
                                   用 ui.badge + tokens 配色）与 rrf_score
                                   展示（样式对齐现有 distance 行）；hybrid
                                   模式下 snippet 有 highlight_words 时照常
                                   高亮
```

### 2.5 零改动确认

repositories、index_service、rules、utils、其余 UI 页面、其余 API 端点
均不动；三个既有搜索模式的行为与展示不变。

## 3. 测试步骤（开发人员手动执行）

```text
1. 已建全文+向量索引的库，输入同时命中两路的关键词（如转录里的名词）→
   综合搜索出结果；双命中条目排前、带「双命中」徽章与 rrf_score、有高亮
   片段与 distance；纯全文条目高亮无 distance，纯向量条目有 distance
   无高亮
2. 输入仅语义相近、无字面命中的查询（同义改写）→ 向量单路条目正常出现，
   无降级提示
3. 设置中停用 Embedding 后综合搜索 → 返回纯全文结果 + 顶部黄色降级提示，
   不报错；重新启用后恢复两路
4. 重建全文索引前清空 chunks_fts（或新库未建全文索引）→ 综合搜索降级为
   纯向量 + 提示，不白屏
5. 回车键触发综合搜索；文件名/全文/语义三按钮行为与展示不变；
   GET /api/search?q=...&mode=hybrid 返回 items 与 degraded_reason 正常
6. 空关键词综合搜索 → 提示「请输入搜索关键词」，与现有行为一致
7. 回归：列表 / 详情 / 设置 / 任务页不受影响
```

## 4. M14 验收标准

对应 PRD §29.14：

```text
综合搜索返回全文+向量 RRF 融合结果，双命中条目排前并标注来源
同 chunk 双命中合并为一条，展示 rrf_score
向量路不可用时降级为纯全文结果并给出提示，不报错；全文路缺失时同理
回车与主按钮均触发综合搜索；文件名/全文/语义三模式行为不变
```

## 5. PRD 同步清单（实施完成时）

```text
§16.7 注记 m14 已实现并简述 RRF 方案
§28 增 M14；§29 增 29.14
§31 移除第 1 项「混合搜索排序」并重排（标签系统成为第 1 项）
§34「第一阶段不实现」清单移除「混合搜索排序」
```
