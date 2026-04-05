import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import DBDerivative
from src.repositories.derivative_repository import DerivativeRepository


class DerivativeService:
    """派生数据存储服务 - 管理 AI 生成内容的文件系统存储"""

    DERIVATIVE_TYPES = {
        "raw_text": {"extension": ".md", "filename": "raw_text.md"},
        "transcript": {"extension": ".srt", "filename": "transcript.srt"},
        "notes": {"extension": ".md", "filename": "ai_notes.md"},
        "flashcards": {"extension": ".json", "filename": "flashcards.json"},
        "mindmap": {"extension": ".json", "filename": "mindmap.json"},
        "analysis": {"extension": ".json", "filename": "analysis.json"},
    }

    def __init__(self, workspace_root: str, session: AsyncSession):
        self.workspace_root = Path(workspace_root)
        self.qbase_dir = self.workspace_root / ".qbase"
        self.generated_dir = self.qbase_dir / "generated"
        self.session = session
        self.repository = DerivativeRepository(session)

    def _get_derivative_dir(self, file_hash: str) -> Path:
        """获取指定文件哈希的派生数据目录"""
        short_hash = file_hash[:16]
        dir_path = self.generated_dir / short_hash
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def _get_derivative_path(self, file_hash: str, derivative_type: str) -> Path:
        """获取派生数据文件路径"""
        if derivative_type not in self.DERIVATIVE_TYPES:
            raise ValueError(f"不支持的派生数据类型: {derivative_type}")

        dir_path = self._get_derivative_dir(file_hash)
        config = self.DERIVATIVE_TYPES[derivative_type]
        return dir_path / config["filename"]

    async def save_derivative(
        self,
        file_hash: str,
        derivative_type: str,
        content: Any,
        model_used: Optional[str] = None,
        version: int = 1,
    ) -> DBDerivative:
        """
        保存派生数据到文件系统和数据库

        Args:
            file_hash: 文件哈希
            derivative_type: 派生数据类型
            content: 内容（字符串或字典）
            model_used: 使用的模型
            version: 版本号

        Returns:
            DBDerivative 对象
        """
        import time

        file_path = self._get_derivative_path(file_hash, derivative_type)

        # 写入文件系统
        try:
            if isinstance(content, (dict, list)):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(str(content))

            logger.debug(f"派生数据已写入文件: {file_path}")
        except Exception as e:
            logger.error(f"写入派生数据文件失败: {e}")
            raise

        # 更新或创建数据库记录
        now = int(time.time())

        # 检查是否已存在
        existing = await self.repository.get_by_file_and_type(
            file_hash, derivative_type
        )

        if existing:
            # 更新现有记录
            derivative = await self.repository.update_status(existing.id, "ready")
            derivative.version = version
            derivative.model_used = model_used
            derivative.created_at = now
            await self.session.commit()
            await self.session.refresh(derivative)
        else:
            # 创建新记录
            derivative_data = {
                "file_hash": file_hash[:16],
                "type": derivative_type,
                "version": version,
                "model_used": model_used,
                "status": "ready",
                "created_at": now,
            }
            derivative = await self.repository.create(derivative_data)

        return derivative

    async def load_derivative(
        self,
        file_hash: str,
        derivative_type: str,
    ) -> Optional[Any]:
        """
        加载派生数据（优先从文件系统读取）

        Args:
            file_hash: 文件哈希
            derivative_type: 派生数据类型

        Returns:
            派生数据内容，不存在返回 None
        """
        file_path = self._get_derivative_path(file_hash, derivative_type)

        # 优先从文件系统读取
        if file_path.exists():
            try:
                config = self.DERIVATIVE_TYPES[derivative_type]
                if config["extension"] == ".json":
                    with open(file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
            except Exception as e:
                logger.error(f"读取派生数据文件失败: {e}")

        # 文件系统不存在，返回 None（双写期可以从数据库读取）
        return None

    async def delete_derivative(
        self,
        file_hash: str,
        derivative_type: str,
    ) -> bool:
        """
        删除派生数据

        Args:
            file_hash: 文件哈希
            derivative_type: 派生数据类型

        Returns:
            是否成功
        """
        try:
            # 删除文件
            file_path = self._get_derivative_path(file_hash, derivative_type)
            if file_path.exists():
                file_path.unlink()

            # 删除数据库记录
            existing = await self.repository.get_by_file_and_type(
                file_hash, derivative_type
            )
            if existing:
                await self.session.delete(existing)
                await self.session.commit()

            logger.debug(f"已删除派生数据: {file_hash} - {derivative_type}")
            return True
        except Exception as e:
            logger.error(f"删除派生数据失败: {e}")
            return False

    async def list_derivatives(self, file_hash: str) -> List[Dict]:
        """
        列出文件的所有派生数据

        Args:
            file_hash: 文件哈希

        Returns:
            派生数据列表
        """
        derivatives = await self.repository.list_by_file(file_hash)

        result = []
        for d in derivatives:
            file_path = self._get_derivative_path(file_hash, d.type)
            result.append(
                {
                    "id": d.id,
                    "type": d.type,
                    "version": d.version,
                    "model_used": d.model_used,
                    "status": d.status,
                    "created_at": d.created_at,
                    "file_exists": file_path.exists(),
                }
            )

        return result

    async def mark_outdated(self, file_hash: str) -> int:
        """
        标记文件的所有派生数据为过期

        Args:
            file_hash: 文件哈希

        Returns:
            更新的数量
        """
        derivatives = await self.repository.list_by_file(file_hash)
        count = 0

        for d in derivatives:
            await self.repository.update_status(d.id, "outdated")
            count += 1

        return count
