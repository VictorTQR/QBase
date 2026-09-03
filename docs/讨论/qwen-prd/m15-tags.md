# M15：标签系统（手动打标 + 列表/搜索标签筛选）

2026-08-21 定稿并实施。对应 PRD §31 后续阶段规划第 1 项「标签
系统」。范围 = 标签数据模型（tags / asset_tags 两张表）+ 详情页手动打标 +
资产列表标签列与标签筛选 + 四种搜索模式的标签过滤 + REST 端点。纯手动
打标，不做 AI 建议、层级、颜色与管理页。

---

## 0. 已定决策（讨论结论，不再开放）

1. **数据存放 = 仅 SQLite**：SCHEMA 追加 tags / asset_tags 两表（CREATE
   TABLE IF NOT EXISTS，沿用现有无迁移机制）。扫描、索引重建均不触碰
   标签表；唯一丢失场景 = 手动删除 .knowledge 目录（database.py 模块
   docstring 已明示该目录可删重建，属已知限制，不做 tags.json 双写）。
2. **纯手动打标**：不做 AI 建议标签、不做批量自动打标（后者留待后续
   「批量任务」里程碑合并考虑）。
3. **扁平标签**：无层级、无颜色区分、无独立标签管理页（全局重命名/
   合并/删除不做）。呼应 PRD §3「复杂标签体系不做」——本期只做简单标签。
4. **筛选语义 = 多选、任一命中（OR）**：列表与搜索的标签筛选均为多选
   下拉，资产带任一所选标签即保留；可与类型、文件名筛选叠加。
5. **标签名约束**：trim 后非空、去重（保序）、不含半角逗号（列表页
   tags 列用 group_concat 逗号聚合）、单个 ≤ 30 字符、单资产 ≤ 20 个。
   违规抛 ValueError（中文报错），API 返回 400。
6. **编辑语义 = 整体替换（PUT）**：`PUT /api/assets/{id}/tags` 传全量
   标签列表；不存在的标签名自动创建，移除后零引用的标签自动删除。
7. **向量路的过滤时机**：标签过滤发生在 LanceDB top-K 候选回表之后，
   过滤后结果可能少于 limit（候选集本身有限，属预期行为，docstring
   注明，不算降级）。
8. **范围外（明确不做）**：AI 打标、标签层级/颜色/别名、标签管理页、
   tags.json 导出备份、搜索结果卡展示标签徽章（避免逐结果查询）、
   按标签统计报表。

---

## 1. 现状事实（代码依据）

```text
database.py                      SCHEMA 单串 + IF NOT EXISTS，无迁移机制；
                                 模块 docstring：文件系统是唯一数据源，
                                 .knowledge 删除可重建
asset_repository.py:117          _build_asset_filters 仅 type + keyword
                                 （LIKE title / relative_path）
asset_repository.py:209          delete_missing_assets 只删 assets 行；
                                 全库无外键约束，artifacts/chunks 与资产
                                 仅按 asset_id 值关联，清理靠显式 SQL
ui/pages/assets.py:43-58         工具栏 = 文件名（0.3s 防抖）+ 类型 + 排序；
                                 列表为手搭表格（min-width 900px），
                                 状态列渲染 render_derived_badges
ui/pages/asset_detail.py:307-321 基本信息卡元数据逐行只读展示，无内联
                                 编辑先例；「创建 .kb 目录」按钮（:560
                                 一带）是「调服务 + 就地更新界面」的最近
                                 先例
search_service.py                search_filename / fulltext / vector /
                                 hybrid 均无过滤参数；search_vector 逐
                                 hit 回查 assets（:218-231）
api/library.py:186               GET /api/search 仅 q / mode / limit；
                                 端点模式 = 开库守卫 + conn try/finally +
                                 中文 HTTPException
home.py:17-27                    MILESTONES 仅 M0-M8（M9-M14 均未加入，
                                 本期同样不动）
```

## 2. 实施蓝图

### 2.1 `app/database.py`

```text
SCHEMA 追加两表（IF NOT EXISTS，老库幂等）：
tags        id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
asset_tags  asset_id TEXT NOT NULL, tag_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (asset_id, tag_id)
索引        idx_asset_tags_tag_id ON asset_tags(tag_id)（反查使用数/清理）
不声明外键  与 artifacts/chunks 现状一致，孤儿清理走显式 SQL
```

### 2.2 新建 `app/repositories/tag_repository.py`

```text
make_tag_id(name)                  uuid5(NAMESPACE_URL, f"tag:{name}")，
                                   同名重建得到同 ID（对齐 make_asset_id）
list_tags(conn)                    全部标签 + 使用数（LEFT JOIN
                                   asset_tags 聚合），使用数降序、名称
                                   升序；返回 [{id, name, usage}]
get_tags_for_asset(conn, asset_id) 该资产标签名列表（名称升序）
set_asset_tags(conn, asset_id,
               tag_names) -> list[str]
                                   全量替换：缺失的 tags 行先建
                                   （make_tag_id），DELETE 该资产
                                   asset_tags 后重插；随后
                                   DELETE FROM tags WHERE id NOT IN
                                   (SELECT tag_id FROM asset_tags)
                                   清零引用；返回最终标签名列表
                                   （调用方负责 commit）
```

### 2.3 `app/repositories/asset_repository.py`

```text
_build_asset_filters               增加 tag_names: list[str] | None，生成
                                   EXISTS(
                                     SELECT 1 FROM asset_tags at
                                     JOIN tags t ON t.id = at.tag_id
                                     WHERE at.asset_id = a.id
                                       AND t.name IN (…)
                                   )，OR 语义
list_assets / count_assets         透传 tag_names
list_assets SELECT                 追加列
                                   (SELECT group_concat(t.name, ',') …
                                    WHERE at.asset_id = a.id) AS tags_csv，
                                   行 dict 拆为 tags: list[str]（空为 []；
                                   展示顺序由 UI 排序，group_concat 不保序）
delete_missing_assets              删 assets 的循环中追加
                                   DELETE FROM asset_tags WHERE asset_id = ?；
                                   收尾清零引用标签（同 2.2 清理 SQL）
```

### 2.4 新建 `app/services/tag_service.py`

```text
normalize_tag_names(names)         trim、去空、去重保序、逐条校验
                                   （决策 5），违规抛 ValueError（中文报错）
get_all_tags() -> list[dict]       自管 conn（get_conn(get_db_path()) 模式）
get_asset_tags(asset_id)           资产不存在抛 ValueError
set_asset_tags(asset_id, names)    校验资产存在 → normalize →
                                   repo.set_asset_tags + commit
```

### 2.5 `app/api/library.py`

```text
GET /api/tags                      → {"items": [{id, name, usage}]}
PUT /api/assets/{asset_id}/tags    body {"tags": [...]}（Pydantic 模型
                                   SetAssetTagsRequest）→ {"tags": [...]}；
                                   400 未开库/校验失败，404 资产不存在
GET /api/assets/{asset_id}         响应增加 "tags": [...]
GET /api/search                    增加可重复查询参数 tag: list[str]
                                   （FastAPI Query），透传 search 系列
```

### 2.6 `app/ui/tokens.py` + `app/ui/pages/assets.py`

```text
tokens.py                          C 增加 TAG = "indigo"（标签徽章专用色）
assets.py 工具栏                    标签多选筛选 ui.select(multiple=True,
                                   clearable, label="标签")，选项页面
                                   加载时 io_bound 取 get_all_tags；
                                   扫描完成后重载选项
assets.py load_assets              读取所选标签（空列表 → None）传
                                   count_assets / list_assets 的 tag_names
assets.py 表格                     表头新增「标签」列（w-40，min-width
                                   900→1040px）；行内最多 3 个
                                   ui.badge(name, color=C.TAG)（text-xs），
                                   超出显示 +N 徽章；无标签留空
筛选联动                            标签筛选变化走既有
                                   handle_filter_or_sort_change（重置页码）
```

### 2.7 `app/ui/pages/asset_detail.py`

```text
基本信息卡                         「解析状态」行下新增「标签」行：
                                   ui.badge(name, color=C.TAG) 列表，
                                   无标签显示「暂无标签」
编辑控件                           同卡下方 ui.select(options=全部标签,
                                   multiple=True, with_input=True,
                                   new_value_mode="add-unique",
                                   label="编辑标签")，初值 = 当前标签，
                                   +「保存标签」按钮
保存流程                           run.io_bound(tag_service.set_asset_tags)
                                   → ui.notify 成功 → 标签行 container.clear()
                                   重渲染（沿用 list_container 局部刷新 +
                                   .kb 按钮「调服务后更新界面」模式）
```

### 2.8 `app/services/search_service.py` + `app/ui/pages/search.py`

```text
_tag_filter_sql(alias, tag_names, params)
                                   生成决策 4 的 EXISTS 片段（alias 为
                                   assets 的表别名），各模式复用
search_filename / search_fulltext  WHERE 追加标签条件；fulltext 的 FTS
                                   与 LIKE 兜底两路都要加
search_vector                      回表循环内先按标签过滤（一条
                                   EXISTS/IN 查询判断），未命中跳过
                                   （决策 7 的预期行为）
search_hybrid / search             透传 tag_names；降级逻辑不变
search.py                          按钮行下新增标签多选筛选（同 2.6 控件，
                                   选项 get_all_tags）；四个 handler 与
                                   回车触发均读取并传参
```

### 2.9 零改动确认

scanner_service（仅经 delete_missing_assets 间接获得标签清理）、
index_service、vector_service、转录/总结/解析服务、artifacts/tasks
仓储、FTS5 表、home/settings/tasks 页面均不动；未选标签时，既有筛选
与四种搜索模式的行为和展示完全不变。

## 3. 测试步骤（开发人员手动执行）

```text
1. 详情页添加新标签（如「AI」「播客」）→ 保存后徽章即时刷新，刷新页面
   仍在；「编辑标签」控件可移除既有标签、可输入新名称回车创建
2. 非法输入：空名/纯空格、含半角逗号、>30 字符、单资产 >20 个 → 保存
   报错（UI notify / API 400，中文文案），数据不变
3. 列表页：标签列正常显示（>3 个折叠 +N）；多选两个标签 → 命中任一者
   保留（OR）；叠加类型/文件名筛选；筛选变化页码重置；计数与分页正确
4. 搜索页：四种模式分别带标签过滤各验证一轮；向量模式过滤后条数减少
   属预期；hybrid 降级提示不受标签过滤影响；GET /api/search?…&tag=a&tag=b
   结果与 UI 一致
5. 删除某已打标资产对应的磁盘文件后「扫描 / 刷新」→ 资产与标签绑定一并
   清理；零引用标签从列表/搜索的筛选下拉消失
6. API 直测：GET /api/tags 返回 usage 计数；PUT 整体替换语义（传 []
   清空）；GET /api/assets/{id} 响应含 tags
7. 回归：未打标资产在列表/详情/搜索表现与之前一致；转录/总结/解析/
   播放器不受影响
```

## 4. M15 验收标准

对应 PRD §29.15（新增）：

```text
详情页可查看与编辑资产标签；新标签自动创建，零引用标签自动清理
资产列表展示标签列，并支持多选标签（任一命中）筛选，可与类型/文件名叠加
四种搜索模式（文件名/全文/语义/综合）均支持按标签过滤
标签仅存 SQLite：扫描与索引重建不丢失；删除 .knowledge 目录会丢失（已知限制）
```

## 5. PRD 同步清单（实施完成时）

```text
§3 注记：简单扁平标签已由 m15 实现，「复杂标签体系」仍不做
§11.1 / §11.2 增标签列与标签编辑描述
§16.6 增「按标签过滤（m15）」，注明类型/来源过滤仍未实现
§19 增 19.6 tags / 19.7 asset_tags 表定义
§22.2 / §22.3 / §22.4 UI 设计同步标签控件
§23.2 增 PUT /api/assets/{id}/tags 与 GET /api/tags；§23.3 增 tag 参数
§28 增 M15；§29 增 29.15
§31 移除第 1 项「标签系统」并重排（收藏与稍后处理成为第 1 项）
§34「第一阶段不实现」清单注记标签系统已由 m15 实现
README / CLAUDE.md 功能描述同步
```
