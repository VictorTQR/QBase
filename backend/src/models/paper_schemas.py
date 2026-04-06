from pydantic import BaseModel, Field
from typing import Optional


class PaperSearchRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词", min_length=1)
    max_results: int = Field(100, description="最大结果数", ge=1, le=500)
    sort_by: str = Field(
        "relevance", description="排序方式: relevance 或 submitted_date"
    )


class ImportPaperRequest(BaseModel):
    entry_id: str = Field(..., description="要导入的论文ID")
    folder_path: Optional[str] = Field(None, description="目标文件夹路径")
