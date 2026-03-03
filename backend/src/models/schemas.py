from pydantic import BaseModel
from typing import Optional, List, Any


class ParseRequest(BaseModel):
    filename: str
    file_content: Optional[bytes] = None
    file_path: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    batch_id: str
    file_name: str
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    state: str
    error_msg: Optional[str] = None
    markdown_content: Optional[str] = None
    result_file_path: Optional[str] = None
    result_file_format: Optional[str] = None
    created_at: str
    updated_at: str
    is_duplicate: Optional[bool] = False


class ParseResult(BaseModel):
    markdown_content: str
    files: List[str]


class ErrorResponse(BaseModel):
    detail: str


class DuplicateCheckRequest(BaseModel):
    file_hash: Optional[str] = None
    file_path: Optional[str] = None


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_task: Optional[TaskResponse] = None


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total: int
    pending: int
    running: int
    done: int
    failed: int
