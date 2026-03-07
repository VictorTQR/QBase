import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import lancedb
import pyarrow as pa
from loguru import logger

from config import settings


class LanceDBService:
    _instance: Optional["LanceDBService"] = None
    _db: Optional[lancedb.DBConnection] = None
    _table: Optional[lancedb.Table] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls):
        """初始化 LanceDB 连接和表"""
        if cls._db is not None:
            return

        lancedb_dir = Path(settings.STORAGE_DIR) / "lancedb"
        lancedb_dir.mkdir(parents=True, exist_ok=True)

        cls._db = lancedb.connect(str(lancedb_dir))
        logger.info(f"LanceDB connected at: {lancedb_dir}")

        cls._initialize_table()

    @classmethod
    def _initialize_table(cls):
        """初始化或打开文档向量表"""
        table_name = "document_chunks"

        if table_name in cls._db.table_names():
            cls._table = cls._db.open_table(table_name)
            logger.info(f"Opened existing table: {table_name}")
        else:
            schema = pa.schema(
                [
                    pa.field("id", pa.string()),
                    pa.field("file_path", pa.string()),
                    pa.field("file_name", pa.string()),
                    pa.field("workspace_id", pa.string()),
                    pa.field("chunk_index", pa.int32()),
                    pa.field("content_type", pa.string()),
                    pa.field("content", pa.string()),
                    pa.field("start_char", pa.int32()),
                    pa.field("end_char", pa.int32()),
                    pa.field("created_at", pa.int64()),
                    pa.field("vector", pa.list_(pa.float32(), 1024)),
                ]
            )

            cls._table = cls._db.create_table(table_name, schema=schema)
            logger.info(f"Created new table: {table_name}")

    @classmethod
    def add_chunks(cls, chunks: List[Dict[str, Any]]):
        """添加文档分块"""
        if not chunks:
            return

        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append(
                {
                    "id": chunk["id"],
                    "file_path": chunk["file_path"],
                    "file_name": chunk["file_name"],
                    "workspace_id": chunk.get("workspace_id", ""),
                    "chunk_index": chunk["chunk_index"],
                    "content_type": chunk.get("content_type", "text"),
                    "content": chunk["content"],
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", len(chunk["content"])),
                    "created_at": chunk.get(
                        "created_at",
                        int(time.time()),
                    ),
                    "vector": chunk["vector"],
                }
            )

        cls._table.add(formatted_chunks)
        logger.info(f"Added {len(formatted_chunks)} chunks to LanceDB")

    @classmethod
    def search(
        cls,
        query_vector: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        query = cls._table.search(query_vector).limit(top_k)

        if filter_expr:
            query = query.where(filter_expr)

        results = query.to_list()

        return [
            {
                "id": r["id"],
                "file_path": r["file_path"],
                "file_name": r["file_name"],
                "workspace_id": r["workspace_id"],
                "chunk_index": r["chunk_index"],
                "content": r["content"],
                "score": 1.0 - r["_distance"],
                "_distance": r["_distance"],
            }
            for r in results
        ]

    @classmethod
    def delete_by_file_path(cls, file_path: str):
        """删除指定文件的所有分块"""
        cls._table.delete(f"file_path = '{file_path}'")
        logger.info(f"Deleted chunks for file: {file_path}")

    @classmethod
    def clear_all(cls):
        """清空所有数据"""
        if "document_chunks" in cls._db.table_names():
            cls._db.drop_table("document_chunks")
            cls._initialize_table()
            logger.info("Cleared all data from LanceDB")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取统计信息"""
        count = cls._table.count_rows()
        return {"total_chunks": count, "table_name": "document_chunks"}

    @classmethod
    def list_indexed_files(cls) -> List[Dict[str, Any]]:
        """获取所有已索引的文件列表（按文件分组）"""
        if cls._table is None:
            return []
        
        # 获取所有数据
        all_chunks = cls._table.to_pandas()
        
        if all_chunks.empty:
            return []
        
        # 按 file_path 分组
        grouped = all_chunks.groupby('file_path')
        
        indexed_files = []
        for file_path, group in grouped:
            # 获取该文件的信息
            first_chunk = group.iloc[0]
            latest_chunk = group.iloc[-1]
            
            indexed_files.append({
                "file_path": file_path,
                "file_name": first_chunk['file_name'],
                "workspace_id": first_chunk['workspace_id'],
                "created_at": int(latest_chunk['created_at']),
                "chunk_count": len(group),
            })
        
        # 按 created_at 降序排序
        indexed_files.sort(key=lambda x: x['created_at'], reverse=True)
        
        return indexed_files


lancedb_service = LanceDBService()
