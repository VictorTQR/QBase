from pydantic import BaseModel
from typing import Optional, List, Any


class ParseRequest(BaseModel):
    filename: str
    file_content: Optional[bytes] = None
    file_path: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    state: str
    batch_id: str
    file_name: str
    created_at: str
    updated_at: str
    result: Optional[Any] = None
    error_msg: Optional[str] = None


class ParseResult(BaseModel):
    markdown_content: str
    files: List[str]


class ErrorResponse(BaseModel):
    detail: str
