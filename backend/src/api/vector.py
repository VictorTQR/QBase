from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from loguru import logger
from pydantic import ValidationError
from typing import List, Tuple, Optional, Dict, Any

from vector import (
    lancedb_service,
    TextChunker,
    EmbeddingService,
    VectorIndexRequest,
    VectorIndexResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
    VectorDeleteRequest,
    VectorOperationResponse,
    VectorStatsResponse,
)
from config import settings
from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository

router = APIRouter(prefix="/api/vector", tags=["Vector"])


@router.post("/index", response_model=VectorIndexResponse)
async def index_document(request: Request):
    """索引单个文档"""
    try:
        body = await request.json()
        logger.info(f"[Vector API] 收到索引请求，原始请求体: {body}")
        logger.info(f"[Vector API] file_path: {body.get('file_path')}")
        logger.info(f"[Vector API] file_name: {body.get('file_name')}")
        logger.info(f"[Vector API] task_id: {body.get('task_id')}")
        logger.info(
            f"[Vector API] content 长度: {len(body.get('content', '')) if body.get('content') else 'N/A'}"
        )

        try:
            validated_request = VectorIndexRequest(**body)
            logger.info(f"[Vector API] Pydantic 验证通过")
        except ValidationError as e:
            logger.error(f"[Vector API] Pydantic 验证失败: {e.errors()}")
            raise HTTPException(
                status_code=422,
                detail={"error": "Validation failed", "details": e.errors()},
            )

        # 获取内容：优先从 task_id 获取，其次使用请求中的 content
        content = validated_request.content
        if validated_request.task_id:
            logger.info(
                f"[Vector API] 从数据库获取内容，task_id: {validated_request.task_id}"
            )
            repo, session = AsyncSessionLocal(), None
            try:
                session = AsyncSessionLocal()
                repo = ParseTaskRepository(session)
                task = await repo.get_by_id(validated_request.task_id)
                if task and task.markdown_content:
                    content = task.markdown_content
                    logger.info(
                        f"[Vector API] 从数据库获取内容成功，长度: {len(content)}"
                    )
                else:
                    logger.warning(
                        f"[Vector API] 无法从数据库获取内容，task_id: {validated_request.task_id}"
                    )
            except Exception as e:
                logger.error(f"[Vector API] 从数据库获取内容失败: {e}")
            finally:
                if session:
                    await session.close()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Either content or task_id with valid content is required",
            )

        chunk_size = validated_request.chunk_size or settings.VECTOR_CHUNK_SIZE
        chunk_overlap = validated_request.chunk_overlap or settings.VECTOR_CHUNK_OVERLAP

        logger.info(
            f"[Vector API] 使用 chunk_size={chunk_size}, chunk_overlap={chunk_overlap}"
        )

        chunks = TextChunker.chunk(
            content,
            {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "use_semantic": True,
            },
        )

        logger.info(f"[Vector API] 文本分块完成，共 {len(chunks)} 个分块")

        indexed_chunks = []
        for idx, chunk in enumerate(chunks):
            logger.info(f"[Vector API] 正在处理第 {idx + 1}/{len(chunks)} 个分块")
            embedding = await EmbeddingService.embed_text(
                chunk["content"], settings.SILICONFLOW_EMBEDDING_MODEL
            )

            chunk_id = f"{validated_request.file_path}_chunk_{chunk['index']}"
            indexed_chunks.append(
                {
                    "id": chunk_id,
                    "file_path": validated_request.file_path,
                    "file_name": validated_request.file_name,
                    "workspace_id": validated_request.workspace_id or "",
                    "chunk_index": chunk["index"],
                    "content_type": validated_request.content_type or "text",
                    "content": chunk["content"],
                    "start_char": chunk["start_char"],
                    "end_char": chunk["end_char"],
                    "vector": embedding,
                }
            )

        logger.info(f"[Vector API] 准备删除旧索引: {validated_request.file_path}")
        lancedb_service.delete_by_file_path(validated_request.file_path)
        logger.info(f"[Vector API] 准备添加新索引，共 {len(indexed_chunks)} 个分块")
        lancedb_service.add_chunks(indexed_chunks)
        logger.info(f"[Vector API] 索引添加成功")

        return VectorIndexResponse(
            success=True,
            chunks_indexed=len(indexed_chunks),
            message=f"Successfully indexed {len(indexed_chunks)} chunks",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Vector API] 索引文档时发生异常")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(request: VectorSearchRequest):
    """向量搜索"""
    try:
        query_embedding = await EmbeddingService.embed_text(
            request.query, settings.SILICONFLOW_EMBEDDING_MODEL
        )

        filter_expr = request.filter_expr
        if request.workspace_id:
            workspace_filter = f"workspace_id = '{request.workspace_id}'"
            if filter_expr:
                filter_expr = f"({filter_expr}) AND ({workspace_filter})"
            else:
                filter_expr = workspace_filter

        results = lancedb_service.search(
            query_embedding, top_k=request.top_k or 10, filter_expr=filter_expr
        )

        search_results = [VectorSearchResult(**r) for r in results]

        return VectorSearchResponse(results=search_results, total=len(search_results))
    except Exception as e:
        logger.error(f"Failed to search vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete", response_model=VectorOperationResponse)
async def delete_document_chunks(request: VectorDeleteRequest):
    """删除指定文件的向量索引"""
    try:
        lancedb_service.delete_by_file_path(request.file_path)
        return VectorOperationResponse(
            success=True, message=f"Deleted chunks for file: {request.file_path}"
        )
    except Exception as e:
        logger.error(f"Failed to delete document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=VectorStatsResponse)
async def get_vector_stats():
    """获取向量索引统计"""
    try:
        stats = lancedb_service.get_stats()
        return VectorStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get vector stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=VectorOperationResponse)
async def clear_all_vectors():
    """清空所有向量索引"""
    try:
        lancedb_service.clear_all()
        return VectorOperationResponse(success=True, message="All vector data cleared")
    except Exception as e:
        logger.error(f"Failed to clear vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexed-files", response_model=List[Dict[str, Any]])
async def list_indexed_files():
    """获取所有已索引的文件列表"""
    try:
        files = lancedb_service.list_indexed_files()
        return files
    except Exception as e:
        logger.error(f"Failed to list indexed files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
