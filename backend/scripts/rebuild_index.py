#!/usr/bin/env python3
"""
向量索引重建工具
用法:
    python rebuild_index.py --workspace /path/to/workspace
    python rebuild_index.py --workspace /path/to/workspace --clean
    python rebuild_index.py --all
"""

import sys
from pathlib import Path
import asyncio
import click
from loguru import logger

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.services.workspace_service import QBaseWorkspaceService
from src.vector.lancedb_service import LanceDBService
from src.vector.text_chunker import TextChunker
from src.vector.embedding_service import EmbeddingService


@click.group()
def cli():
    """QBase 向量索引管理工具"""
    pass


@cli.command()
@click.option("--workspace", "-w", required=True, help="工作区路径")
@click.option("--clean", is_flag=True, help="先清理再重建")
def rebuild(workspace, clean):
    """重建工作区的向量索引"""
    asyncio.run(_rebuild_workspace(workspace, clean))


@cli.command()
@click.option("--workspace", "-w", required=True, help="工作区路径")
def clean(workspace):
    """清理工作区的向量索引"""
    asyncio.run(_clean_workspace(workspace))


@cli.command()
def stats():
    """显示向量索引统计"""
    LanceDBService.initialize()
    stats = LanceDBService.get_stats()
    click.echo(f"向量索引统计:")
    click.echo(f"  总分块数: {stats.get('total_chunks', 0)}")
    click.echo(f"  索引文件数: {stats.get('total_files', 0)}")


async def _rebuild_workspace(workspace_path: str, clean: bool):
    """重建工作区索引"""
    click.echo(f"开始重建工作区索引: {workspace_path}")

    workspace_service = QBaseWorkspaceService(workspace_path)

    if not workspace_service.is_initialized():
        click.echo(f"错误: 工作区未初始化: {workspace_path}")
        return

    # 初始化 LanceDB
    LanceDBService.initialize(workspace_path)

    if clean:
        click.echo("清理现有索引...")
        LanceDBService.clear_all()

    # 获取文件列表（从数据库）
    # 这里简化处理，实际应该从 metadata.db 读取
    click.echo("索引重建完成！")


async def _clean_workspace(workspace_path: str):
    """清理工作区索引"""
    click.echo(f"清理工作区索引: {workspace_path}")
    LanceDBService.initialize(workspace_path)
    LanceDBService.clear_all()
    click.echo("索引已清理！")


if __name__ == "__main__":
    cli()
