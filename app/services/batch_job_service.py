"""Batch 批任务编排（m21）：mode="batch" 时把一批资产任务的请求打包为
厂商 Batch 任务（智谱 / 硅基流动，五折、预计 24 小时内完成）。

与 sync/async 的本质差异：
- 工作单元是「一批请求」而非单次调用：一次提交 = 1 条 type="batch" 任务
  （记录 batch_id / custom_id 映射 / 进度）+ N 条保持 pending 的资产任务，
  结果由轮询线程下载后逐任务回填。
- 提交在调用线程同步完成（上传 + 建 batch 通常数秒），避免「任务已建但
  batch 未提交」的重启竞态；轮询在后台 daemon 线程。
- 重启恢复绝不重新提交（会双倍计费），只续查状态；结果文件厂商保留
  30 天，覆盖正常恢复窗口。

custom_id 规则：{task_id}_{序号}（task_id 为 uuid 不含下划线，反解可靠）。
长文资产贡献多条请求（分段/分窗各一条），合并（merge）在下载后本地
sync 执行——merge 输入仅为分段结果，远小于原文，全价成本占比可忽略。
"""

from __future__ import annotations

import json
import threading
import time

from loguru import logger

from app.database import get_conn
from app.repositories import task_repository
from app.services import config_service, llm_batch
from app.state import get_db_path

_STATUS_LABELS = {
    "completed": "已完成",
    "failed": "失败",
    "expired": "已过期",
    "cancelled": "已取消",
}

# 轮询线程模块级状态（单线程；进程内只有一个 poller 在跑）
_poller_active = False
_poller_lock = threading.Lock()


def is_batch_mode(llm_config: dict) -> bool:
    """该功能的 LLM 配置是否为 batch 模式。"""
    return str(llm_config.get("mode") or "sync").strip().lower() == "batch"


def _feature_config(feature: str) -> dict:
    """按功能读取 LLM 配置。"""
    if feature == "summary":
        return config_service.get_summary_llm_config()

    if feature == "tagging":
        return config_service.get_tagging_llm_config()

    if feature == "analysis":
        return config_service.get_analysis_llm_config()

    raise ValueError(f"未知的 Batch 功能：{feature}")


def _build_one(conn, feature: str, task_id: str) -> dict:
    """构建单个任务的叶子请求，归一化为 {"requests": [...], "window_labels": [...]}。

    惰性导入三个业务服务，避免模块级循环依赖
    （业务服务同样在函数内惰性导入本模块）。
    """
    if feature == "summary":
        from app.services import summarization_service

        return {
            "requests": summarization_service.build_batch_request(conn, task_id),
            "window_labels": [],
        }

    if feature == "tagging":
        from app.services import tag_service

        return {
            "requests": tag_service.build_batch_request(conn, task_id),
            "window_labels": [],
        }

    if feature == "analysis":
        from app.services import analysis_service

        built = analysis_service.build_batch_request(conn, task_id)

        return {
            "requests": built["requests"],
            "window_labels": built.get("window_labels") or [],
        }

    raise ValueError(f"未知的 Batch 功能：{feature}")


def _apply_one(
    conn,
    feature: str,
    task_id: str,
    contents: list[str],
    window_labels: list[str] | None,
    config: dict,
) -> dict:
    """结果落盘并返回合并进任务 params 的附加字段；失败抛异常。"""
    if feature == "summary":
        from app.services import summarization_service

        return summarization_service.apply_batch_results(conn, task_id, contents, config)

    if feature == "tagging":
        from app.services import tag_service

        return tag_service.apply_batch_results(conn, task_id, contents)

    if feature == "analysis":
        from app.services import analysis_service

        return analysis_service.apply_batch_results(
            conn, task_id, contents, window_labels, config
        )

    raise ValueError(f"未知的 Batch 功能：{feature}")


# ──────────────────────────────────────────────────────────────────────────
# 提交
# ──────────────────────────────────────────────────────────────────────────


def submit_batch_jobs(feature: str, task_ids: list[str]) -> dict:
    """把一批资产任务打包提交为厂商 Batch 任务（mode=batch 分流入口）。

    逐任务构建叶子请求，按单文件上限拆分后上传并创建 batch，同时写入
    type="batch" 任务并在资产任务 params 上登记 batch_task_id（同一事务，
    要么都落库要么都不）。单任务构建失败 / 单批提交失败只影响自身，
    以任务 failed 呈现，不中断其余。
    """
    config = _feature_config(feature)
    conn = get_conn(get_db_path())
    submitted: list[dict] = []
    failed: list[dict] = []

    try:
        requests: list[tuple[str, str, list[dict]]] = []
        request_counts: dict[str, int] = {}
        labels_map: dict[str, list[str]] = {}

        for task_id in task_ids:
            try:
                built = _build_one(conn, feature, task_id)
            except Exception as exc:
                logger.error("Batch 请求构建失败（{}）：{}", task_id, exc)
                _fail_task(conn, task_id, f"Batch 请求构建失败：{exc}")
                failed.append({"task_id": task_id, "reason": str(exc)})
                continue

            request_counts[task_id] = len(built["requests"])

            if built["window_labels"]:
                labels_map[task_id] = built["window_labels"]

            requests.extend(
                (task_id, f"{task_id}_{index}", messages)
                for index, messages in enumerate(built["requests"])
            )

        conn.commit()

        if not requests:
            return {"submitted": 0, "batches": [], "failed": failed}

        for chunk in llm_batch.split_requests_chunks(requests):
            chunk_task_ids = list(dict.fromkeys(owner for owner, _, _ in chunk))

            try:
                jsonl_text = llm_batch.build_jsonl_lines(
                    [(custom_id, messages) for _, custom_id, messages in chunk],
                    config,
                )
                input_file_id = llm_batch.upload_input_file(config, jsonl_text)
                batch = llm_batch.create_batch(
                    config, input_file_id, {"feature": feature}
                )
                batch_task_id = _create_batch_task(
                    conn,
                    feature,
                    batch,
                    input_file_id,
                    chunk_task_ids,
                    request_counts,
                    labels_map,
                    total=len(chunk),
                )

                for owner in chunk_task_ids:
                    _merge_task_params(conn, owner, {"batch_task_id": batch_task_id})

                conn.commit()
            except Exception as exc:
                conn.rollback()
                logger.error("Batch 提交失败：{}", exc)

                for owner in chunk_task_ids:
                    _fail_task(conn, owner, f"Batch 提交失败：{exc}")
                    failed.append({"task_id": owner, "reason": str(exc)})

                conn.commit()
                continue

            submitted.append(
                {"batch_task_id": batch_task_id, "batch_id": batch.get("id")}
            )
            logger.info(
                "Batch 批任务已提交：{} 个请求（feature={}，batch_id={}）",
                len(chunk),
                feature,
                batch.get("id"),
            )
    finally:
        conn.close()

    if submitted:
        _ensure_poller()

    return {"submitted": len(submitted), "batches": submitted, "failed": failed}


def _create_batch_task(
    conn,
    feature: str,
    batch: dict,
    input_file_id: str,
    task_ids: list[str],
    request_counts: dict[str, int],
    labels_map: dict[str, list[str]],
    total: int,
) -> str:
    """写 type="batch" 任务（创建即 running，记录映射与进度）。"""
    params: dict = {
        "feature": feature,
        "batch_id": batch.get("id"),
        "input_file_id": input_file_id,
        "provider_status": batch.get("status"),
        "requests": total,
        "task_ids": task_ids,
        "task_request_counts": {
            task_id: request_counts[task_id] for task_id in task_ids
        },
        "progress": {"completed": 0, "failed": 0, "total": total},
    }

    chunk_labels = {
        task_id: labels_map[task_id] for task_id in task_ids if task_id in labels_map
    }

    if chunk_labels:
        params["window_labels"] = chunk_labels

    batch_task_id = task_repository.create_task(
        conn,
        asset_id=None,
        task_type="batch",
        params=params,
        command=None,
        output_path=None,
    )

    task_repository.update_task(
        conn,
        batch_task_id,
        status="running",
        started_at=task_repository.utcnow_iso(),
    )

    return batch_task_id


# ──────────────────────────────────────────────────────────────────────────
# 轮询与结果回填
# ──────────────────────────────────────────────────────────────────────────


def resume_batch_jobs() -> None:
    """打开知识库时恢复 batch 轮询。

    只续查已提交的批任务，绝不重新提交（避免双倍计费）。
    """
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id FROM tasks
            WHERE type = 'batch' AND status IN ('pending', 'running')
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return

    logger.info("恢复 Batch 批任务轮询：{} 个", len(rows))
    _ensure_poller()


def _ensure_poller() -> None:
    """确保轮询线程在跑（进程内单线程，空闲自退出，有任务再拉起）。"""
    global _poller_active

    with _poller_lock:
        if _poller_active:
            return

        _poller_active = True

    threading.Thread(target=_poll_loop, daemon=True, name="batch-job-poller").start()


def _poll_loop() -> None:
    global _poller_active

    try:
        while True:
            batch_tasks = _list_running_batch_tasks()

            if not batch_tasks:
                break

            intervals = []

            for batch_task in batch_tasks:
                try:
                    intervals.append(_poll_one(batch_task))
                except Exception as exc:
                    logger.error(
                        "Batch 轮询单任务异常（{}）：{}", batch_task.get("id"), exc
                    )

            time.sleep(min(intervals) if intervals else 60)
    finally:
        with _poller_lock:
            _poller_active = False


def _list_running_batch_tasks() -> list[dict]:
    conn = get_conn(get_db_path())

    try:
        rows = conn.execute(
            """
            SELECT id, params_json FROM tasks
            WHERE type = 'batch' AND status IN ('pending', 'running')
            ORDER BY created_at
            """
        ).fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]


def _poll_one(batch_task: dict) -> int:
    """轮询单个批任务：更新进度；终态则下载结果回填。返回下次轮询间隔秒。"""
    try:
        params = json.loads(batch_task["params_json"] or "{}")
    except json.JSONDecodeError:
        params = {}

    feature = str(params.get("feature") or "")
    batch_id = str(params.get("batch_id") or "")

    if not feature or not batch_id:
        conn = get_conn(get_db_path())

        try:
            _fail_batch(conn, batch_task["id"], params, "Batch 任务参数不完整")
            conn.commit()
        finally:
            conn.close()

        return 60

    try:
        config = _feature_config(feature)
    except Exception as exc:
        logger.warning("Batch 轮询读取配置暂失败（{}）：{}", batch_id, exc)
        return 60

    interval = config.get("batch_poll_interval_seconds", 60)

    try:
        info = llm_batch.retrieve_batch(config, batch_id)
    except (llm_batch.BatchAuthError, llm_batch.BatchMissingError) as exc:
        # 密钥失效 / 批任务不存在：继续轮询没有意义，整批置 failed
        conn = get_conn(get_db_path())

        try:
            _fail_all(conn, batch_task["id"], params, str(exc))
            conn.commit()
        finally:
            conn.close()

        return interval
    except llm_batch.BatchError as exc:
        # 网络抖动 / 服务端暂时异常：容忍，下个 tick 再查
        logger.warning("Batch 状态查询暂失败（{}）：{}", batch_id, exc)
        return interval

    status = str(info.get("status") or "").lower()
    counts = info.get("request_counts") or {}

    progress = {
        "completed": int(counts.get("completed") or 0),
        "failed": int(counts.get("failed") or 0),
        "total": int(counts.get("total") or params.get("requests") or 0),
    }

    conn = get_conn(get_db_path())

    try:
        _update_batch_progress(conn, batch_task["id"], params, status, progress)
        conn.commit()

        if status in llm_batch.BATCH_TERMINAL_STATUSES:
            _finish_batch(conn, batch_task["id"], params, feature, config, info, status)
            conn.commit()
    finally:
        conn.close()

    return interval


def _update_batch_progress(
    conn, batch_task_id: str, params: dict, status: str, progress: dict
) -> None:
    """把厂商侧进度合并进 batch 任务 params_json。"""
    params["provider_status"] = status
    params["progress"] = progress

    task_repository.update_task(
        conn,
        batch_task_id,
        params_json=json.dumps(params, ensure_ascii=False),
    )


def _finish_batch(
    conn,
    batch_task_id: str,
    params: dict,
    feature: str,
    config: dict,
    info: dict,
    status: str,
) -> None:
    """终态处理：下载输出/错误文件，逐任务落盘回填，batch 任务置终态。

    expired / cancelled / failed 时已完成请求仍在输出文件里，同样回收；
    没拿到结果的资产任务以具体原因置 failed。
    """
    task_ids = params.get("task_ids") or []
    request_counts = params.get("task_request_counts") or {}
    labels_map = params.get("window_labels") or {}
    max_tokens = config.get("max_tokens", 2000)

    results: dict[str, list[tuple[str | None, str | None]]] = {}
    error_reasons: dict[str, list[str]] = {}
    download_warning = None

    output_file_id = info.get("output_file_id")
    error_file_id = info.get("error_file_id")

    if output_file_id:
        try:
            lines = llm_batch.download_results(config, output_file_id)
        except Exception as exc:
            download_warning = str(exc)
        else:
            for line in lines:
                owner = _owner_of(line)

                if owner not in request_counts:
                    continue

                results.setdefault(owner, []).append(
                    llm_batch.extract_result(line, max_tokens)
                )

    if error_file_id:
        try:
            lines = llm_batch.download_results(config, error_file_id)
        except Exception as exc:
            download_warning = download_warning or str(exc)
        else:
            for line in lines:
                owner = _owner_of(line)

                if owner not in request_counts:
                    continue

                _, reason = llm_batch.extract_result(line, max_tokens)

                if reason:
                    error_reasons.setdefault(owner, []).append(reason)

    for task_id in task_ids:
        task = task_repository.get_task(conn, task_id)

        if task is None or task["status"] in ("success", "failed", "cancelled"):
            continue

        entries = results.get(task_id) or []
        contents = [content for content, _ in entries if content]
        reasons = [reason for _, reason in entries if reason]
        reasons.extend(error_reasons.get(task_id, []))

        if download_warning:
            reasons.append(f"结果下载失败：{download_warning}")

        expected = int(request_counts.get(task_id) or len(entries) or 1)

        if len(contents) < expected:
            detail = (
                "；".join(dict.fromkeys(reasons))[:800]
                or f"Batch 任务{_STATUS_LABELS.get(status, status)}，缺少结果"
            )
            _fail_task(
                conn,
                task_id,
                f"Batch 请求未全部成功（{len(contents)}/{expected}）：{detail}",
            )
            continue

        try:
            extra_params = _apply_one(
                conn, feature, task_id, contents, labels_map.get(task_id), config
            )

            merged_params = _parse_params(task)
            merged_params.update(extra_params)

            task_repository.update_task(
                conn,
                task_id,
                status="success",
                output_path=extra_params.get("output_path"),
                params_json=json.dumps(merged_params, ensure_ascii=False),
                finished_at=task_repository.utcnow_iso(),
            )
            logger.info("Batch 结果已回填：{}（feature={}）", task_id, feature)
        except Exception as exc:
            logger.error("Batch 结果落盘失败（{}）：{}", task_id, exc)
            _fail_task(conn, task_id, str(exc))

    # 统计终态并回写 batch 任务
    failed_count = 0

    for task_id in task_ids:
        task = task_repository.get_task(conn, task_id)

        if task is not None and task["status"] == "failed":
            failed_count += 1

    batch_status = "failed" if failed_count else "success"
    error_text = None

    if failed_count:
        error_text = f"{failed_count}/{len(task_ids)} 个任务失败"

    if download_warning:
        warning_text = f"结果下载告警：{download_warning}"
        error_text = (
            f"{error_text}；{warning_text}" if error_text else warning_text
        )

    params["provider_status"] = status
    task_repository.update_task(
        conn,
        batch_task_id,
        status=batch_status,
        error=error_text,
        params_json=json.dumps(params, ensure_ascii=False),
        finished_at=task_repository.utcnow_iso(),
    )

    logger.info(
        "Batch 批任务结束（batch 状态 {}）：{} 个任务，{} 失败",
        status,
        len(task_ids),
        failed_count,
    )


def _fail_all(conn, batch_task_id: str, params: dict, reason: str) -> None:
    """批任务不可恢复（密钥失效 / 任务不存在）：整批置 failed。"""
    for task_id in params.get("task_ids") or []:
        _fail_task(conn, task_id, reason)

    _fail_batch(conn, batch_task_id, params, reason)


def _fail_batch(conn, batch_task_id: str, params: dict, reason: str) -> None:
    """仅 batch 任务本身置 failed（资产任务由调用方决定）。"""
    task_repository.update_task(
        conn,
        batch_task_id,
        status="failed",
        error=reason,
        finished_at=task_repository.utcnow_iso(),
    )


def _owner_of(line: dict) -> str:
    """从结果行 custom_id 反解资产任务 id（{task_id}_{序号}）。"""
    custom_id = str(line.get("custom_id") or "")

    return custom_id.rsplit("_", 1)[0] if custom_id else ""


def _parse_params(task: dict) -> dict:
    try:
        return json.loads(task["params_json"] or "{}")
    except json.JSONDecodeError:
        return {}


def _fail_task(conn, task_id: str, reason: str) -> None:
    """资产任务置 failed（已完结的任务不动）。"""
    task = task_repository.get_task(conn, task_id)

    if task is None or task["status"] in ("success", "failed", "cancelled"):
        return

    task_repository.update_task(
        conn,
        task_id,
        status="failed",
        error=reason,
        started_at=task["started_at"] or task_repository.utcnow_iso(),
        finished_at=task_repository.utcnow_iso(),
    )


def _merge_task_params(conn, task_id: str, extra: dict) -> None:
    """往资产任务 params_json 合并字段（如 batch_task_id 登记）。"""
    task = task_repository.get_task(conn, task_id)

    if task is None:
        return

    params = _parse_params(task)
    params.update(extra)

    task_repository.update_task(
        conn,
        task_id,
        params_json=json.dumps(params, ensure_ascii=False),
    )
