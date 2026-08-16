# 文档索引

## 权威文档

- [PRD.md](./PRD.md) - 产品需求文档 v1.0（唯一权威 spec：数据模型 / API / UI / 配置 / 里程碑 M0-M8）
- [../CLAUDE.md](../CLAUDE.md) - 开发原则与环境指南

## 里程碑实施记录

每进入一个里程碑，新增一页记录实施决策（只记 PRD 未定的细节与偏差，不重复 PRD 内容）。

- M0 项目骨架 - 已完成（2026-08-16），无偏差，见 PRD §28
  - 备注：NiceGUI `@ui.page` 注册要求包 `__init__.py` 显式导入子模块
- M1 知识库与扫描 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m1.md，已适配 M0 结构
  - 偏差/补充（m1.md 未覆盖、由实施补齐）：
    - `app/database.py`：sqlite3 连接（WAL + Row 工厂）+ assets 建表（DDL 取自 PRD §19.1）
    - `app/services/library_service.py`：open_library / close_library / get_library_status；打开时写默认 `.knowledge/config.toml`（模板取自 PRD §20）
    - `app/api/library.py`：REST 端点（open/close/status/scan/assets），替代 m1.md 的 register_library_api
    - `app/main.py`：未按 m1.md 整体替换，保留 M0 的配置/日志/健康检查，仅追加 API 路由
    - `app/state.py`、`app/rules.py`、`app/utils.py`、`app/repositories/asset_repository.py`、`app/services/scanner_service.py`、`app/ui/pages/assets.py` 按 m1.md 落地（资产页并入 page_frame 导航布局，新增类型过滤）
- M2 派生文件识别 + 资产详情页 - 已完成（2026-08-16）
  - 依据：讨论稿 qwen-prdv1/m2.md，已适配 M1 结构
  - 偏差/补充（m2.md 未覆盖、由实施补齐）：
    - `database.py` 保留 M1 的 WAL/get_conn，SCHEMA 扩至 PRD §19.1 全部 5 表 + artifacts 索引 + chunks_fts（FTS5，M4 搜索用）
    - `list_assets` 保留 M1 的类型过滤参数，叠加 has_transcript/has_summary/note EXISTS 徽章列
    - `assets.py` 保留 page_frame 布局与类型过滤，合并徽章列与详情链接
    - 新增 `GET /api/assets/{asset_id}` 详情端点（含 artifacts）
  - 决策记录：
    - 派生匹配键 = (relative_dir, stem.lower())；转录类只匹配音视频资产，其余 kind 匹配任意资产
    - 同 stem 多候选 -> 歧义不绑定；无候选 -> 孤儿（stats 计数，UI warning 提示）
    - 普通 {stem}.txt 在同目录存在同 stem 音视频时识别为转录，否则仍是文档资产

## 项目文档

- [项目梳理报告.md](./项目梳理报告.md) - 2026-08-16 项目全景梳理（历史演进 / 技术转向 / 架构决策）

## 原始讨论存档（只读，不更新）

- [讨论/](./讨论/) - 与各 AI 模型的设计讨论原始记录，PRD 的推导过程
