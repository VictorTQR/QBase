from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger

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

router = APIRouter(prefix="/api/vector", tags=["Vector"])


@router.post("/index", response_model=VectorIndexResponse)
async def index_document(request: VectorIndexRequest):
    """索引单个文档"""
    try:
        chunk_size = request.chunk_size or settings.VECTOR_CHUNK_SIZE
        chunk_overlap = request.chunk_overlap or settings.VECTOR_CHUNK_OVERLAP

        chunks = TextChunker.chunk(
            request.content,
            {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "use_semantic": True,
            },
        )

        indexed_chunks = []
        for chunk in chunks:
            embedding = await EmbeddingService.embed_text(
                chunk["content"], settings.SILICONFLOW_EMBEDDING_MODEL
            )

            chunk_id = f"{request.file_path}_chunk_{chunk['index']}"
            indexed_chunks.append(
                {
                    "id": chunk_id,
                    "file_path": request.file_path,
                    "file_name": request.file_name,
                    "workspace_id": request.workspace_id or "",
                    "chunk_index": chunk["index"],
                    "content_type": request.content_type or "text",
                    "content": chunk["content"],
                    "start_char": chunk["start_char"],
                    "end_char": chunk["end_char"],
                    "vector": embedding,
                }
            )

        lancedb_service.delete_by_file_path(request.file_path)
        lancedb_service.add_chunks(indexed_chunks)

        return VectorIndexResponse(
            success=True,
            chunks_indexed=len(indexed_chunks),
            message=f"Successfully indexed {len(indexed_chunks)} chunks",
        )
    except Exception as e:
        logger.error(f"Failed to index document: {str(e)}")
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
