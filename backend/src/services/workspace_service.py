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
