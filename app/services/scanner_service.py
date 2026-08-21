"""目录扫描服务：识别资产与派生文件，写入 assets / artifacts 表。

匹配规则：
- 明确命名的 sidecar（*.transcript.txt / *.summary.md / *.notes.md 等）按后缀识别；
- 同目录存在同 stem 音视频时，普通 {stem}.txt 视为该媒体的转录；
- 同 stem 多个候选资产时标记歧义，不自动绑定；无候选则记为孤儿。
- <原始文件名>.kb/ sidecar 目录（m11）：内部固定文件名按目录名精确绑定原始
  资产（含扩展名，天然无歧义），目录内容不产生资产记录。
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

from loguru import logger

from app.database import get_conn
from app.repositories.artifact_repository import (
    delete_missing_artifacts,
    upsert_artifact,
)
from app.repositories.asset_repository import (
    delete_missing_assets,
    upsert_asset,
)
from app.rules import (
    IGNORE_FILE_NAMES,
    classify_extension,
    explicit_artifact_kind,
    explicit_artifact_stem,
    get_parse_status,
    is_sidecar_dir,
    should_ignore_dir,
    sidecar_asset_filename,
    sidecar_file_kind,
)
from app.state import get_db_path, state


def collect_files(root: Path) -> tuple[list[dict], list[dict]]:
    """收集知识库中的所有候选文件，返回 (普通文件, sidecar 目录内派生文件)。"""
    items: list[dict] = []
    sidecar_items: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]

        # sidecar 目录单独收集且不再向下递归（其内容只可能是派生文件，不是资产）。
        sidecar_dirs = [d for d in dirnames if is_sidecar_dir(d)]

        for dirname in sidecar_dirs:
            sidecar_items.extend(_collect_sidecar_dir(Path(dirpath) / dirname, root))

        dirnames[:] = [d for d in dirnames if not is_sidecar_dir(d)]

        for filename in filenames:
            if filename.startswith("."):
                continue

            if filename.lower() in IGNORE_FILE_NAMES:
                continue

            full_path = Path(dirpath) / filename

            try:
                stat_result = full_path.stat()
            except OSError:
                continue

            ext = full_path.suffix.lower()

            if not ext:
                continue

            relative_path = full_path.relative_to(root).as_posix()
            relative_dir = full_path.parent.relative_to(root).as_posix()

            if relative_dir == ".":
                relative_dir = ""

            items.append(
                {
                    "filename": filename,
                    "stem": full_path.stem,
                    "ext": ext,
                    "full_path": full_path,
                    "relative_path": relative_path,
                    "relative_dir": relative_dir,
                    "size": stat_result.st_size,
                    "mtime": int(stat_result.st_mtime),
                }
            )

    return items, sidecar_items


def _collect_sidecar_dir(sidecar_path: Path, root: Path) -> list[dict]:
    """收集单个 <原始文件名>.kb/ 目录内的派生文件（不递归；未识别命名跳过）。"""
    relative_dir = sidecar_path.parent.relative_to(root).as_posix()

    if relative_dir == ".":
        relative_dir = ""

    asset_filename = sidecar_asset_filename(sidecar_path.name)
    items: list[dict] = []

    try:
        entries = list(sidecar_path.iterdir())
    except OSError:
        return items

    for entry in entries:
        filename = entry.name

        if filename.startswith("."):
            continue

        kind = sidecar_file_kind(filename)

        if kind is None:
            continue

        try:
            stat_result = entry.stat()
        except OSError:
            continue

        items.append(
            {
                "filename": filename,
                "kind": kind,
                "asset_filename": asset_filename,
                "relative_dir": relative_dir,
                "full_path": entry,
                "relative_path": entry.relative_to(root).as_posix(),
                "mtime": int(stat_result.st_mtime),
            }
        )

    return items


def scan_current_library() -> dict:
    """扫描当前知识库：资产 + 派生文件入库，清理失效记录。"""
    if state.library_root is None:
        raise ValueError("未打开知识库")

    root: Path = state.library_root
    db_path = get_db_path()

    file_items, sidecar_items = collect_files(root)

    stats = {
        "assets_added_or_updated": 0,
        "assets_removed": 0,
        "artifacts_added_or_updated": 0,
        "artifacts_removed": 0,
        "ambiguous_artifacts": 0,
        "orphan_artifacts": 0,
        "total_assets": 0,
    }

    # 先找出所有音视频 stem，用于判断普通 txt 是否是转录。
    media_keys: dict[tuple[str, str], list[str]] = defaultdict(list)

    for item in file_items:
        if classify_extension(item["ext"]) in {"audio", "video"}:
            key = (item["relative_dir"], item["stem"].lower())
            media_keys[key].append(item["relative_path"])

    asset_items: list[dict] = []
    artifact_candidates: list[dict] = []

    # .kb 目录内文件全部是派生候选（按目录名精确绑定，见下方绑定阶段）。
    for item in sidecar_items:
        artifact_candidates.append(
            {
                "item": item,
                "kind": item["kind"],
                "sidecar": True,
            }
        )

    for item in file_items:
        filename = item["filename"]

        explicit_kind = explicit_artifact_kind(filename)

        # 明确命名的派生文件。
        if explicit_kind:
            artifact_candidates.append(
                {
                    "item": item,
                    "kind": explicit_kind,
                    "stem": explicit_artifact_stem(filename),
                }
            )
            continue

        asset_type = classify_extension(item["ext"])

        if not asset_type:
            continue

        # 普通 txt：同目录存在同 stem 音视频，则认为是转录文本。
        if item["ext"] == ".txt":
            key = (item["relative_dir"], item["stem"].lower())

            if media_keys.get(key):
                artifact_candidates.append(
                    {
                        "item": item,
                        "kind": "transcript",
                        "stem": item["stem"],
                    }
                )
                continue

        asset_items.append({**item, "asset_type": asset_type})

    conn = get_conn(db_path)

    seen_asset_paths: set[str] = set()
    seen_artifact_paths: set[str] = set()

    all_asset_keys: dict[tuple[str, str], list[str]] = defaultdict(list)
    media_asset_keys: dict[tuple[str, str], list[str]] = defaultdict(list)
    asset_path_ids: dict[str, str] = {}

    try:
        # 写入 assets。
        for item in asset_items:
            asset = {
                "title": item["stem"],
                "type": item["asset_type"],
                "relative_path": item["relative_path"],
                "absolute_path": str(item["full_path"]),
                "mime_type": None,
                "size": item["size"],
                "mtime": item["mtime"],
                "parse_status": get_parse_status(item["asset_type"], item["ext"]),
            }

            asset_id = upsert_asset(conn, asset)
            seen_asset_paths.add(item["relative_path"])
            stats["assets_added_or_updated"] += 1

            key = (item["relative_dir"], item["stem"].lower())
            all_asset_keys[key].append(asset_id)
            asset_path_ids[item["relative_path"].lower()] = asset_id

            if item["asset_type"] in {"audio", "video"}:
                media_asset_keys[key].append(asset_id)

        stats["assets_removed"] = delete_missing_assets(conn, seen_asset_paths)

        # 写入 artifacts。
        for candidate in artifact_candidates:
            item = candidate["item"]
            kind = candidate["kind"]

            if candidate.get("sidecar"):
                # .kb 目录：目录名去掉 .kb 即原始文件完整文件名，精确匹配。
                prefix = f"{item['relative_dir']}/" if item["relative_dir"] else ""
                lookup = f"{prefix}{item['asset_filename']}".lower()
                asset_id = asset_path_ids.get(lookup)
                candidate_asset_ids = [asset_id] if asset_id else []
            else:
                key = (item["relative_dir"], candidate["stem"].lower())

                if kind in {"transcript", "transcript_meta"}:
                    candidate_asset_ids = media_asset_keys.get(key, [])
                else:
                    candidate_asset_ids = all_asset_keys.get(key, [])

            if len(candidate_asset_ids) == 1:
                upsert_artifact(
                    conn,
                    {
                        "asset_id": candidate_asset_ids[0],
                        "kind": kind,
                        "relative_path": item["relative_path"],
                        "absolute_path": str(item["full_path"]),
                        "mtime": item["mtime"],
                        "source": "external",
                        "generator": None,
                        "model": None,
                        "status": "active",
                    },
                )
                seen_artifact_paths.add(item["relative_path"])
                stats["artifacts_added_or_updated"] += 1
            elif len(candidate_asset_ids) > 1:
                stats["ambiguous_artifacts"] += 1
            else:
                stats["orphan_artifacts"] += 1

        stats["artifacts_removed"] = delete_missing_artifacts(
            conn,
            seen_artifact_paths,
        )

        stats["total_assets"] = len(seen_asset_paths)

        conn.commit()
    finally:
        conn.close()

    logger.info("扫描完成：{}", stats)
    return stats
