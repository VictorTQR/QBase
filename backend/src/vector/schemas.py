from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class VectorIndexRequest(BaseModel):
    file_path: str
    file_name: str
    content: str
    workspace_id: Optional[str] = None
    content_type: Optional[str] = "text"
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class VectorIndexResponse(BaseModel):
    success: bool
    chunks_indexed: int
    message: str


class VectorSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10
    workspace_id: Optional[str] = None
    filter_expr: Optional[str] = None


class VectorSearchResult(BaseModel):
    id: str
    file_path: str
    file_name: str
    workspace_id: str
    chunk_index: int
    content: str
    score: float


class VectorSearchResponse(BaseModel):
    results: List[VectorSearchResult]
    total: int


class VectorStatsResponse(BaseModel):
    total_chunks: int
    table_name: str


class VectorDeleteRequest(BaseModel):
    file_path: str


class VectorOperationResponse(BaseModel):
    success: bool
    message: str
