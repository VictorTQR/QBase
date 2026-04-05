import os
import json
from pathlib import Path
from typing import Optional
from loguru import logger


class QBaseWorkspaceService:
    """.qbase 目录管理服务"""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.qbase_dir = self.workspace_root / ".qbase"
        self.generated_dir = self.qbase_dir / "generated"
        self.indexes_dir = self.qbase_dir / "indexes"
        self.cache_dir = self.qbase_dir / "cache"
        self.config_path = self.qbase_dir / "config.json"
        self.metadata_db_path = self.qbase_dir / "metadata.db"

    def initialize_workspace(self) -> bool:
        """初始化工作区 .qbase 目录结构"""
        try:
            self.qbase_dir.mkdir(exist_ok=True)

            self.generated_dir.mkdir(exist_ok=True)
            self.indexes_dir.mkdir(exist_ok=True)
            self.cache_dir.mkdir(exist_ok=True)

            if not self.config_path.exists():
                self._create_default_config()

            self._create_gitignore()

            # 初始化工作区数据库
            from src.services.database_service import WorkspaceDatabaseService
            import asyncio
            asyncio.create_task(WorkspaceDatabaseService.init_workspace_db(str(self.workspace_root)))

            logger.info(f"工作区 {self.workspace_root} 初始化成功")
            return True
        except Exception as e:
            logger.error(f"工作区初始化失败: {e}")
            return False

    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "version": "1.2",
            "workspace": {"initialized_at": None},
            "ai": {
                "provider": "siliconflow",
                "embedding_model": "BAAI/bge-large-zh-v1.5",
            },
            "sync": {"enabled": False, "conflict_strategy": "newer_wins"},
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

    def _create_gitignore(self):
        """创建 .gitignore 文件"""
        gitignore_content = """# QBase cache
cache/
*.tmp
*.swp
"""
        gitignore_path = self.qbase_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(gitignore_content)

    def get_generated_dir_for_hash(self, file_hash: str) -> Path:
        """获取指定哈希的派生数据目录"""
        dir_path = self.generated_dir / file_hash[:16]
        dir_path.mkdir(exist_ok=True)
        return dir_path

    def load_config(self) -> dict:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_config(self, config: dict):
        """保存配置文件"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def is_initialized(self) -> bool:
        """检查工作区是否已初始化"""
        return self.qbase_dir.exists()

    def scan_workspace(self, force_hash: bool = False) -> dict:
        """
        扫描工作区文件

        Args:
            force_hash: 是否强制重新计算所有文件哈希

        Returns:
            扫描统计信息
        """
        from pathlib import Path
        import time
        from src.utils.file_hash import compute_file_hash

        stats = {
            "total_files": 0,
            "new_files": 0,
            "modified_files": 0,
            "skipped_files": 0,
            "errors": [],
        }

        supported_extensions = [
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

        logger.info(f"开始扫描工作区: {self.workspace_root}")

        try:
            for file_path in self.workspace_root.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in supported_extensions
                ):
                    if ".qbase" in file_path.parts:
                        continue

                    stats["total_files"] += 1

                    try:
                        rel_path = str(file_path.relative_to(self.workspace_root))
                        mtime = int(file_path.stat().st_mtime)
                        size = file_path.stat().st_size
                        file_type = self._get_file_type(file_path)

                        result = self._process_file(
                            file_path, rel_path, mtime, size, file_type, force_hash
                        )

                        if result == "new":
                            stats["new_files"] += 1
                        elif result == "modified":
                            stats["modified_files"] += 1
                        else:
                            stats["skipped_files"] += 1

                    except Exception as e:
                        error_msg = f"处理文件 {file_path} 失败: {e}"
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)

            logger.info(f"扫描完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"扫描工作区失败: {e}")
            stats["errors"].append(str(e))
            return stats

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

     def _process_file(
        self,
        file_path: Path,
        rel_path: str,
        mtime: int,
        size: int,
        file_type: str,
        force_hash: bool,
    ) -> str:
        """
        处理单个文件

        Returns:
            "new" | "modified" | "skipped"
        """
        import time
        from src.utils.file_hash import compute_file_hash
        from src.database import async_session
        from src.repositories.file_repository import FileRepository

        if force_hash:
            file_hash = compute_file_hash(str(file_path))
            logger.debug(f"强制计算哈希: {rel_path} -> {file_hash}")
            return "modified"
        else:
            return "skipped"

    def get_derivative_service(self, session):
        """获取派生数据服务"""
        from src.services.derivative_service import DerivativeService
        return DerivativeService(str(self.workspace_root), session)

    def get_generated_dir(self) -> Path:
        """获取 generated 目录"""
        return self.generated_dir

    def get_derivative_dir(self, file_hash: str) -> Path:
        """获取指定哈希的派生数据目录"""
        dir_path = self.generated_dir / file_hash[:16]
        dir_path.mkdir(exist_ok=True)
        return dir_path
