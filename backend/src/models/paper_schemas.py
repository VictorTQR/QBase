from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ArxivPaper(BaseModel):
    """arXiv 论文数据模型"""
    entry_id: str = Field(..., description="论文唯一标识")
    title: str = Field(..., description="论文标题")
    authors: str = Field(..., description="作者列表（JSON字符串）")
    summary: str = Field(..., description="论文摘要")
    published: datetime = Field(..., description="发布时间")
    updated: datetime = Field(..., description="更新时间")
    pdf_url: str = Field(..., description="PDF下载链接")
    primary_category: str = Field(..., description="主分类")
    categories: str = Field(..., description="所有分类（JSON字符串）")
    links: str = Field(..., description="相关链接（JSON字符串）")


class PaperSearchRequest(BaseModel):
    """论文搜索请求"""
    keyword: str = Field(..., description="搜索关键词", min_length=1)
    max_results: int = Field(100, description="最大结果数", ge=1, le=500)
    sort_by: str = Field("relevance", description="排序方式: relevance 或 submitted_date")


class PaperSearchResponse(BaseModel):
    """论文搜索响应"""
    papers: List[ArxivPaper]
    total: int
    keyword: str
    sort_by: str


class ImportPaperRequest(BaseModel):
    """导入论文到知识库请求"""
    entry_id: str = Field(..., description="要导入的论文ID")
    folder_path: Optional[str] = Field(None, description="目标文件夹路径")


class PaperListResponse(BaseModel):
    """已保存论文列表响应"""
    papers: List[ArxivPaper]
    total: int
    offset: int
    limit: int


class PaperStatsResponse(BaseModel):
    """论文统计响应"""
    total_papers: int
    total_keywords: int
    recent_papers: int  # 最近7天


class PaperSaveResponse(BaseModel):
    """论文保存响应"""
    message: str
    total: int
    saved: int
    skipped: int
    keyword: str
    sort_by: str
