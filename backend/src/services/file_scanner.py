import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import DBFile
from src.utils.file_hash import compute_file_hash_sync


class FileScanner:
    """文件扫描服务 - 启动时扫描工作区"""

    SUPPORTED_EXTENSIONS = [
        ".md",
        ".pdf",
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
        ".flac",
        ".mp4",
        ".webm",
        ".mov",
        ".mkv",
    ]

    def __init__(self, workspace_root: str, session: AsyncSession):
        self.workspace_root = Path(workspace_root)
        self.session = session

    async def scan_full(self, force_hash: bool = False) -> Dict:
        """
        全量扫描工作区

        Args:
            force_hash: 是否强制重新计算所有文件哈希

        Returns:
            扫描统计信息
        """
        stats = {
            "total_files": 0,
            "new_files": 0,
            "modified_files": 0,
            "unchanged_files": 0,
            "deleted_files": 0,
            "errors": [],
        }

        logger.info(f"开始全量扫描: {self.workspace_root}")
        start_time = time.time()

        try:
            existing_files = await self._get_existing_files()
            logger.debug(f"数据库中现有文件数: {len(existing_files)}")

            current_files = {}
            for file_path in self.workspace_root.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
                ):
                    if ".qbase" in file_path.parts:
                        continue

                    stats["total_files"] += 1
                    rel_path = str(file_path.relative_to(self.workspace_root))
                    current_files[rel_path] = file_path

            for rel_path, file_path in current_files.items():
                try:
                    result = await self._process_file(
                        file_path, rel_path, existing_files.get(rel_path), force_hash
                    )

                    if result == "new":
                        stats["new_files"] += 1
                    elif result == "modified":
                        stats["modified_files"] += 1
                    else:
                        stats["unchanged_files"] += 1

                except Exception as e:
                    error_msg = f"处理文件 {rel_path} 失败: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

            for rel_path, db_file in existing_files.items():
                if rel_path not in current_files:
                    await self._mark_file_missing(db_file)
                    stats["deleted_files"] += 1

            elapsed = time.time() - start_time
            logger.info(f"扫描完成，耗时 {elapsed:.2f}s: {stats}")
            return stats

        except Exception as e:
            logger.error(f"扫描失败: {e}")
            stats["errors"].append(str(e))
            return stats

    async def _get_existing_files(self) -> Dict[str, DBFile]:
        """获取数据库中已有的文件"""
        result = await self.session.execute(select(DBFile))
        files = result.scalars().all()
        return {f.rel_path: f for f in files}

    async def _process_file(
        self,
        file_path: Path,
        rel_path: str,
        existing_file: Optional[DBFile],
        force_hash: bool,
    ) -> str:
        """
        处理单个文件

        Returns:
            "new" | "modified" | "unchanged"
        """
        import time

        stats = file_path.stat()
        mtime = int(stats.st_mtime)
        size = stats.st_size
        file_type = self._get_file_type(file_path)

        if existing_file:
            if (
                not force_hash
                and existing_file.mtime == mtime
                and existing_file.size == size
            ):
                return "unchanged"

            file_hash = compute_file_hash_sync(str(file_path))

            if existing_file.hash == file_hash:
                existing_file.mtime = mtime
                existing_file.size = size
                existing_file.updated_at = int(time.time())
                await self.session.commit()
                return "unchanged"

            existing_file.hash = file_hash
            existing_file.mtime = mtime
            existing_file.size = size
            existing_file.file_type = file_type
            existing_file.status = "pending"
            existing_file.updated_at = int(time.time())
            await self.session.commit()
            return "modified"

        else:
            file_hash = compute_file_hash_sync(str(file_path))
            now = int(time.time())

            db_file = DBFile(
                hash=file_hash,
                rel_path=rel_path,
                file_type=file_type,
                size=size,
                mtime=mtime,
                status="pending",
                created_at=now,
                updated_at=now,
            )

            self.session.add(db_file)
            await self.session.commit()
            return "new"

    async def _mark_file_missing(self, db_file: DBFile):
        """标记文件为缺失"""
        import time

        db_file.status = "missing"
        db_file.updated_at = int(time.time())
        await self.session.commit()
        logger.debug(f"标记文件为缺失: {db_file.rel_path}")

    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型"""
        ext = file_path.suffix.lower()
        if ext == ".md":
            return "markdown"
        elif ext == ".pdf":
            return "pdf"
        elif ext in [".mp3", ".wav", ".ogg", ".m4a", ".flac"]:
            return "audio"
        elif ext in [".mp4", ".webm", ".mov", ".mkv"]:
            return "video"
        return "unknown"
