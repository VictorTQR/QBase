# Paper模块P0和P1改进实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 修复Paper模块的P0和P1优先级问题，包括分页统计错误、数据模型统一、响应格式统一、数据库整合、引入Pinia状态管理等。

**架构:** 
- P0问题：修复现有代码中的bug和不一致性
- P1问题：重构架构，整合到主数据库，引入状态管理
- 采用渐进式重构，确保每个步骤都可测试和回滚

**技术栈:** Vue 3 + Pinia + FastAPI + SQLAlchemy (Async) + SQLite

---

## 阶段一：P0立即修复（核心Bug修复）

### Task 1: 修复分页统计错误

**文件:**
- 修改: `backend/src/papers/database.py:212-253`
- 修改: `backend/src/papers/service.py:153-176`

**问题分析:** 当前`list_papers`只返回当前页数据，`get_saved_papers`用`len(papers)`作为total，导致分页失效。

**Step 1: 修改database.py的list_papers方法，同时返回总数**

```python
def list_papers(self, limit: int = 100, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
    """
    列出所有论文（分页）

    Args:
        limit: 每页数量
        offset: 偏移量

    Returns:
        (论文列表, 总数)
    """
    with self.get_session() as session:
        try:
            # 获取总数
            total = session.query(func.count(DBPaper.id)).scalar() or 0
            
            # 获取分页数据
            papers = (
                session.query(DBPaper)
                .order_by(desc(DBPaper.created_at))
                .limit(limit)
                .offset(offset)
                .all()
            )

            result = [
                {
                    "id": p.id,
                    "entry_id": p.entry_id,
                    "title": p.title,
                    "authors": json.loads(p.authors),
                    "summary": p.summary,
                    "published": p.published.isoformat(),
                    "updated": p.updated.isoformat(),
                    "pdf_url": p.pdf_url,
                    "primary_category": p.primary_category,
                    "categories": json.loads(p.categories),
                    "links": json.loads(p.links),
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                }
                for p in papers
            ]
            
            return result, total
        except Exception as e:
            logger.error(f"列出论文时出错: {e}")
            raise
```

**Step 2: 修改service.py的get_saved_papers方法**

```python
def get_saved_papers(
    self, limit: int = 100, offset: int = 0
) -> Dict[str, Any]:
    """
    获取已保存的论文列表

    Args:
        limit: 每页数量
        offset: 偏移量

    Returns:
        论文列表字典
    """
    try:
        papers, total = self.database.list_papers(limit=limit, offset=offset)
        return {
            "papers": papers,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"获取已保存论文时出错: {e}")
        raise
```

**Step 3: 验证修改**

检查数据库导入是否正确，确保`func`已导入。

**Step 4: 提交**

```bash
git add backend/src/papers/database.py backend/src/papers/service.py
git commit -m "fix: 修复论文分页统计错误，返回正确的total"
```

---

### Task 2: 统一数据模型 - 更新Pydantic schemas

**文件:**
- 修改: `backend/src/models/paper_schemas.py`
- 修改: `backend/src/papers/scraper.py` (需要检查)

**问题分析:** 后端使用JSON字符串存储authors/categories/links，前端期望数组；字段名不一致（entry_id vs arxiv_id）。

**Step 1: 更新paper_schemas.py，使用实际列表类型**

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ArxivPaper(BaseModel):
    """arXiv 论文数据模型"""
    entry_id: str = Field(..., description="论文唯一标识")
    arxiv_id: str = Field(..., description="arXiv ID (兼容前端)")
    title: str = Field(..., description="论文标题")
    authors: List[str] = Field(..., description="作者列表")
    summary: str = Field(..., description="论文摘要")
    published: str = Field(..., description="发布时间(ISO字符串)")
    published_date: str = Field(..., description="发布日期(兼容前端)")
    updated: str = Field(..., description="更新时间(ISO字符串)")
    pdf_url: str = Field(..., description="PDF下载链接")
    primary_category: str = Field(..., description="主分类")
    categories: List[str] = Field(..., description="所有分类")
    links: List[Dict[str, Any]] = Field(..., description="相关链接")


class PaperSearchRequest(BaseModel):
    """论文搜索请求"""
    keyword: str = Field(..., description="搜索关键词", min_length=1)
    max_results: int = Field(100, description="最大结果数", ge=1, le=500)
    sort_by: str = Field("relevance", description="排序方式: relevance 或 submitted_date")


class PaperSearchResponse(BaseModel):
    """论文搜索响应"""
    success: bool = Field(True, description="是否成功")
    data: Dict[str, Any] = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="消息")


class PaperListResponse(BaseModel):
    """已保存论文列表响应"""
    success: bool = Field(True, description="是否成功")
    data: Dict[str, Any] = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="消息")


class PaperStatsResponse(BaseModel):
    """论文统计响应"""
    success: bool = Field(True, description="是否成功")
    data: Dict[str, Any] = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="消息")


class PaperSaveResponse(BaseModel):
    """论文保存响应"""
    success: bool = Field(True, description="是否成功")
    data: Dict[str, Any] = Field(..., description="响应数据")
    message: Optional[str] = Field(None, description="消息")


class ImportPaperRequest(BaseModel):
    """导入论文到知识库请求"""
    entry_id: str = Field(..., description="要导入的论文ID")
    folder_path: Optional[str] = Field(None, description="目标文件夹路径")
```

**Step 2: 检查并修改scraper.py，确保返回正确格式**

需要查看scraper.py的实现，确认它如何处理数据。

**Step 3: 提交**

```bash
git add backend/src/models/paper_schemas.py
git commit -m "refactor: 统一论文数据模型，使用列表类型和兼容字段"
```

---

### Task 3: 统一API响应格式

**文件:**
- 修改: `backend/src/api/papers.py`

**问题分析:** 后端直接返回Pydantic模型，前端期望`{success, data, message}`格式。

**Step 1: 修改papers.py的所有端点，统一响应格式**

先查看现有papers.py内容，然后修改。

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from loguru import logger

from src.models.paper_schemas import (
    PaperSearchRequest,
    PaperSearchResponse,
    PaperListResponse,
    PaperStatsResponse,
    PaperSaveResponse,
    ImportPaperRequest,
)
from src.papers.service import paper_service

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/search", response_model=PaperSearchResponse)
async def search_papers(request: PaperSearchRequest):
    """搜索arXiv论文"""
    try:
        result = await paper_service.search_papers_only(
            keyword=request.keyword,
            max_results=request.max_results,
            sort_by=request.sort_by,
        )
        return PaperSearchResponse(
            success=True,
            data=result,
            message="搜索成功"
        )
    except Exception as e:
        logger.error(f"搜索论文失败: {e}")
        return PaperSearchResponse(
            success=False,
            data={},
            message=f"搜索失败: {str(e)}"
        )


@router.post("/save", response_model=PaperSaveResponse)
async def save_papers(request: PaperSearchRequest):
    """保存搜索结果"""
    try:
        result = await paper_service.search_and_save(
            keyword=request.keyword,
            max_results=request.max_results,
            sort_by=request.sort_by,
        )
        return PaperSaveResponse(
            success=True,
            data=result,
            message=f"保存成功：新增{result.get('saved', 0)}篇，跳过{result.get('skipped', 0)}篇"
        )
    except Exception as e:
        logger.error(f"保存论文失败: {e}")
        return PaperSaveResponse(
            success=False,
            data={},
            message=f"保存失败: {str(e)}"
        )


@router.get("/list", response_model=PaperListResponse)
async def get_paper_list(offset: int = 0, limit: int = 50):
    """获取已保存论文列表"""
    try:
        result = paper_service.get_saved_papers(limit=limit, offset=offset)
        return PaperListResponse(
            success=True,
            data=result,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        return PaperListResponse(
            success=False,
            data={"papers": [], "total": 0, "offset": offset, "limit": limit},
            message=f"获取失败: {str(e)}"
        )


@router.get("/stats", response_model=PaperStatsResponse)
async def get_paper_stats():
    """获取论文统计信息"""
    try:
        result = paper_service.get_paper_stats()
        return PaperStatsResponse(
            success=True,
            data=result,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return PaperStatsResponse(
            success=False,
            data={"total_papers": 0, "total_keywords": 0, "recent_papers": 0},
            message=f"获取失败: {str(e)}"
        )


@router.post("/import")
async def import_paper(request: ImportPaperRequest):
    """导入单篇论文"""
    try:
        result = await paper_service.import_paper(
            entry_id=request.entry_id,
            keyword="manual_import",
            sort_type="relevance",
        )
        if result:
            return {"success": True, "data": result, "message": "导入成功"}
        else:
            return {"success": False, "data": None, "message": "论文已存在或未找到"}
    except Exception as e:
        logger.error(f"导入论文失败: {e}")
        return {"success": False, "data": None, "message": f"导入失败: {str(e)}"}


@router.get("/paper/{entry_id}")
async def get_paper(entry_id: str):
    """获取单篇论文"""
    try:
        paper = paper_service.get_paper_by_entry_id(entry_id)
        if paper:
            return {"success": True, "data": paper, "message": "获取成功"}
        else:
            return {"success": False, "data": None, "message": "论文未找到"}
    except Exception as e:
        logger.error(f"获取论文失败: {e}")
        return {"success": False, "data": None, "message": f"获取失败: {str(e)}"}


@router.delete("/paper/{entry_id}")
async def delete_paper(entry_id: str):
    """删除论文"""
    try:
        success = paper_service.delete_paper(entry_id)
        if success:
            return {"success": True, "data": None, "message": "删除成功"}
        else:
            return {"success": False, "data": None, "message": "论文未找到"}
    except Exception as e:
        logger.error(f"删除论文失败: {e}")
        return {"success": False, "data": None, "message": f"删除失败: {str(e)}"}
```

**Step 2: 提交**

```bash
git add backend/src/api/papers.py
git commit -m "refactor: 统一论文API响应格式为{success, data, message}"
```

---

### Task 4: 更新前端API客户端适配新格式

**文件:**
- 修改: `app/src/api/papers.js`

**Step 1: 更新papers.js，简化响应处理**

```javascript
import { backendService as backend } from '@/utils/backend'

/**
 * Papers API 客户端
 * 提供与后端论文 API 的交互方法
 */
export class PapersBackendApi {
  /**
   * 搜索 arXiv 论文
   * @param {string} keyword - 搜索关键词
   * @param {number} maxResults - 最大结果数（默认10）
   * @param {string} sortBy - 排序方式：'relevance' | 'lastUpdatedDate' | 'submittedDate'（默认'relevance'）
   * @returns {Promise<Object>} 搜索结果
   */
  static async searchPapers(keyword, maxResults = 10, sortBy = 'relevance') {
    console.log('[PapersBackendApi] searchPapers 调用，参数:', { keyword, maxResults, sortBy })
    try {
      const request = backend.client.post('/api/papers/search', {
        keyword,
        max_results: maxResults,
        sort_by: sortBy,
      })
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] searchPapers 失败:', error)
      throw new Error('搜索论文失败')
    }
  }

  /**
   * 保存搜索结果到数据库
   * @param {string} keyword - 搜索关键词
   * @param {number} maxResults - 最大结果数（默认10）
   * @param {string} sortBy - 排序方式：'relevance' | 'lastUpdatedDate' | 'submittedDate'（默认'relevance'）
   * @returns {Promise<Object>} 保存结果
   */
  static async savePapers(keyword, maxResults = 10, sortBy = 'relevance') {
    console.log('[PapersBackendApi] savePapers 调用，参数:', { keyword, maxResults, sortBy })
    try {
      const request = backend.client.post('/api/papers/save', {
        keyword,
        max_results: maxResults,
        sort_by: sortBy,
      })
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] savePapers 失败:', error)
      throw new Error('保存论文失败')
    }
  }

  /**
   * 获取已保存的论文列表
   * @param {number} offset - 偏移量（默认0）
   * @param {number} limit - 限制数量（默认50）
   * @returns {Promise<Object>} 论文列表
   */
  static async getPaperList(offset = 0, limit = 50) {
    console.log('[PapersBackendApi] getPaperList 调用，参数:', { offset, limit })
    try {
      const request = backend.client.get(`/api/papers/list?offset=${offset}&limit=${limit}`)
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] getPaperList 失败:', error)
      throw new Error('获取论文列表失败')
    }
  }

  /**
   * 获取论文统计信息
   * @returns {Promise<Object>} 统计信息
   */
  static async getPaperStats() {
    console.log('[PapersBackendApi] getPaperStats 调用')
    try {
      const request = backend.client.get('/api/papers/stats')
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] getPaperStats 失败:', error)
      throw new Error('获取论文统计信息失败')
    }
  }

  /**
   * 删除论文
   * @param {string} entryId - 论文entry_id
   * @returns {Promise<Object>} 删除结果
   */
  static async deletePaper(entryId) {
    console.log('[PapersBackendApi] deletePaper 调用，参数:', { entryId })
    try {
      const request = backend.client.delete(`/api/papers/paper/${entryId}`)
      return await request.json()
    } catch (error) {
      console.error('[PapersBackendApi] deletePaper 失败:', error)
      throw new Error('删除论文失败')
    }
  }
}
```

**Step 2: 提交**

```bash
git add app/src/api/papers.js
git commit -m "refactor: 更新前端论文API客户端，添加deletePaper方法"
```

---

### Task 5: 更新前端组件适配新数据格式

**文件:**
- 修改: `app/src/components/PaperList.vue`
- 修改: `app/src/views/PapersView.vue`
- 修改: `app/src/components/PaperSearchDialog.vue`

**Step 1: 更新PaperList.vue，简化响应处理**

```javascript
// 修改loadPapers函数
async function loadPapers() {
  try {
    loading.value = true
    const offset = (currentPage.value - 1) * pageSize.value
    const result = await PapersBackendApi.getPaperList(offset, pageSize.value)

    if (result.success) {
      papers.value = result.data?.papers || []
      total.value = result.data?.total || 0
      emit('loaded', {
        count: papers.value.length,
        total: total.value,
      })
    } else {
      ElMessage.error(result.message || '加载论文列表失败')
    }
  } catch (error) {
    console.error('加载论文列表失败:', error)
    ElMessage.error('加载论文列表失败')
  } finally {
    loading.value = false
  }
}

// 添加删除函数
async function deletePaper(paper) {
  try {
    await ElMessageBox.confirm(
      `确定要删除论文"${paper.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    const result = await PapersBackendApi.deletePaper(paper.entry_id)
    if (result.success) {
      ElMessage.success('删除成功')
      loadPapers()
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除论文失败:', error)
      ElMessage.error('删除论文失败')
    }
  }
}
```

同时在模板中添加删除按钮。

**Step 2: 提交**

```bash
git add app/src/components/PaperList.vue
git commit -m "feat: 更新PaperList组件，添加删除功能，适配新响应格式"
```

---

## 阶段二：P1短期改进（架构重构）

### Task 6: 创建Paper数据库模型（整合到主数据库）

**文件:**
- 创建: `backend/src/repositories/paper_repository.py`
- 修改: `backend/src/models/db_models.py` (添加paper表)

**Step 1: 在db_models.py中添加Paper相关模型**

```python
# 在db_models.py末尾添加

class DBPaper(Base):
    """已保存的论文"""

    __tablename__ = "papers"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    entry_id = Column(String, unique=True, nullable=False, index=True)
    arxiv_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    authors = Column(Text, nullable=False)  # JSON数组
    summary = Column(Text, nullable=False)
    published = Column(String, nullable=False)  # ISO字符串
    updated = Column(String, nullable=False)  # ISO字符串
    pdf_url = Column(String, nullable=False)
    primary_category = Column(String, nullable=False)
    categories = Column(Text, nullable=False)  # JSON数组
    links = Column(Text, nullable=False)  # JSON数组
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)


class DBPaperKeyword(Base):
    """论文搜索关键词关联"""

    __tablename__ = "paper_keywords"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String, nullable=False, index=True)
    search_sort_type = Column(String, nullable=False)
    scraped_at = Column(Integer, nullable=True)
```

**Step 2: 创建paper_repository.py**

```python
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import DBPaper, DBPaperKeyword
from loguru import logger
import json
import time


class PaperRepository:
    """论文数据访问层"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, 
        paper_data: Dict[str, Any], 
        keyword: str, 
        sort_type: str
    ) -> Optional[DBPaper]:
        """创建论文记录"""
        try:
            # 检查是否已存在
            existing = await self.get_by_entry_id(paper_data["entry_id"])
            if existing:
                logger.debug(f"论文已存在: {paper_data['title']}")
                return None

            # 创建论文记录
            db_paper = DBPaper(
                entry_id=paper_data["entry_id"],
                arxiv_id=paper_data.get("arxiv_id", paper_data["entry_id"]),
                title=paper_data["title"],
                authors=json.dumps(paper_data["authors"]),
                summary=paper_data["summary"],
                published=paper_data["published"],
                updated=paper_data["updated"],
                pdf_url=paper_data["pdf_url"],
                primary_category=paper_data["primary_category"],
                categories=json.dumps(paper_data["categories"]),
                links=json.dumps(paper_data["links"]),
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )
            self.session.add(db_paper)
            await self.session.flush()

            # 创建关键词关联
            keyword_assoc = DBPaperKeyword(
                paper_id=db_paper.id,
                keyword=keyword,
                search_sort_type=sort_type,
                scraped_at=int(time.time()),
            )
            self.session.add(keyword_assoc)

            await self.session.commit()
            await self.session.refresh(db_paper)
            logger.info(f"保存论文: {paper_data['title']}")
            return db_paper
        except Exception as e:
            await self.session.rollback()
            logger.error(f"保存论文时出错: {e}")
            raise

    async def get_by_entry_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """通过entry_id获取论文"""
        result = await self.session.execute(
            select(DBPaper).where(DBPaper.entry_id == entry_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return None
        return self._to_dict(paper)

    async def list_papers(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """列出论文（分页）"""
        # 获取总数
        count_result = await self.session.execute(
            select(func.count(DBPaper.id))
        )
        total = count_result.scalar() or 0

        # 获取分页数据
        result = await self.session.execute(
            select(DBPaper)
            .order_by(desc(DBPaper.created_at))
            .limit(limit)
            .offset(offset)
        )
        papers = result.scalars().all()

        return [self._to_dict(p) for p in papers], total

    async def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        # 总论文数
        total_result = await self.session.execute(
            select(func.count(DBPaper.id))
        )
        total_papers = total_result.scalar() or 0

        # 总关键词数
        keyword_result = await self.session.execute(
            select(func.count(DBPaperKeyword.id))
        )
        total_keywords = keyword_result.scalar() or 0

        # 最近7天论文数
        seven_days_ago = int(time.time()) - 7 * 24 * 60 * 60
        recent_result = await self.session.execute(
            select(func.count(DBPaper.id))
            .where(DBPaper.created_at >= seven_days_ago)
        )
        recent_papers = recent_result.scalar() or 0

        return {
            "total_papers": total_papers,
            "total_keywords": total_keywords,
            "recent_papers": recent_papers,
        }

    async def delete(self, entry_id: str) -> bool:
        """删除论文"""
        result = await self.session.execute(
            select(DBPaper).where(DBPaper.entry_id == entry_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return False

        await self.session.delete(paper)
        await self.session.commit()
        logger.info(f"删除论文: {paper.title}")
        return True

    def _to_dict(self, paper: DBPaper) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": paper.id,
            "entry_id": paper.entry_id,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "authors": json.loads(paper.authors),
            "summary": paper.summary,
            "published": paper.published,
            "published_date": paper.published,
            "updated": paper.updated,
            "pdf_url": paper.pdf_url,
            "primary_category": paper.primary_category,
            "categories": json.loads(paper.categories),
            "links": json.loads(paper.links),
            "created_at": paper.created_at,
            "updated_at": paper.updated_at,
        }
```

**Step 3: 提交**

```bash
git add backend/src/models/db_models.py backend/src/repositories/paper_repository.py
git commit -m "feat: 整合paper模型到主数据库，创建repository"
```

---

### Task 7: 创建Pinia Store

**文件:**
- 创建: `app/src/stores/papers.js`

**Step 1: 创建papers store**

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { PapersBackendApi } from '@/api/papers'

export const usePapersStore = defineStore('papers', () => {
  // 状态
  const papers = ref([])
  const stats = ref(null)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const loading = ref(false)
  const searchResults = ref([])
  const searchLoading = ref(false)

  // 计算属性
  const hasPapers = computed(() => papers.value.length > 0)

  // Actions
  async function fetchPapers(page = currentPage.value, size = pageSize.value) {
    try {
      loading.value = true
      currentPage.value = page
      pageSize.value = size
      const offset = (page - 1) * size
      const result = await PapersBackendApi.getPaperList(offset, size)
      
      if (result.success) {
        papers.value = result.data?.papers || []
        total.value = result.data?.total || 0
      }
      return result
    } catch (error) {
      console.error('[PapersStore] fetchPapers failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function searchPapers(keyword, maxResults = 10, sortBy = 'relevance') {
    try {
      searchLoading.value = true
      const result = await PapersBackendApi.searchPapers(keyword, maxResults, sortBy)
      
      if (result.success) {
        searchResults.value = result.data?.papers || []
      }
      return result
    } catch (error) {
      console.error('[PapersStore] searchPapers failed:', error)
      throw error
    } finally {
      searchLoading.value = false
    }
  }

  async function savePapers(keyword, maxResults = 10, sortBy = 'relevance') {
    try {
      const result = await PapersBackendApi.savePapers(keyword, maxResults, sortBy)
      
      if (result.success) {
        await fetchPapers()
        await fetchStats()
      }
      return result
    } catch (error) {
      console.error('[PapersStore] savePapers failed:', error)
      throw error
    }
  }

  async function deletePaper(entryId) {
    try {
      const result = await PapersBackendApi.deletePaper(entryId)
      
      if (result.success) {
        await fetchPapers()
        await fetchStats()
      }
      return result
    } catch (error) {
      console.error('[PapersStore] deletePaper failed:', error)
      throw error
    }
  }

  async function fetchStats() {
    try {
      const result = await PapersBackendApi.getPaperStats()
      
      if (result.success) {
        stats.value = result.data
      }
      return result
    } catch (error) {
      console.error('[PapersStore] fetchStats failed:', error)
      throw error
    }
  }

  function clearSearchResults() {
    searchResults.value = []
  }

  function setCurrentPage(page) {
    currentPage.value = page
  }

  function setPageSize(size) {
    pageSize.value = size
    currentPage.value = 1
  }

  return {
    // 状态
    papers,
    stats,
    currentPage,
    pageSize,
    total,
    loading,
    searchResults,
    searchLoading,
    // 计算属性
    hasPapers,
    // Actions
    fetchPapers,
    searchPapers,
    savePapers,
    deletePaper,
    fetchStats,
    clearSearchResults,
    setCurrentPage,
    setPageSize,
  }
})
```

**Step 2: 提交**

```bash
git add app/src/stores/papers.js
git commit -m "feat: 创建papers Pinia store"
```

---

### Task 8: 更新组件使用Pinia Store

**文件:**
- 修改: `app/src/components/PaperList.vue`
- 修改: `app/src/views/PapersView.vue`
- 修改: `app/src/components/PaperSearchDialog.vue`

**Step 1: 更新PaperList.vue使用store**

```javascript
<script setup>
import { ref, onMounted, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePapersStore } from '@/stores/papers'

const props = defineProps({
  refresh: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['loaded'])

const papersStore = usePapersStore()
const detailsVisible = ref(false)
const currentPaper = ref(null)

const papers = papersStore.papers
const loading = papersStore.loading
const currentPage = papersStore.currentPage
const pageSize = papersStore.pageSize
const total = papersStore.total

async function loadPapers() {
  try {
    const result = await papersStore.fetchPapers()
    if (result.success) {
      emit('loaded', {
        count: papers.value.length,
        total: total.value,
      })
    } else {
      ElMessage.error(result.message || '加载论文列表失败')
    }
  } catch (error) {
    console.error('加载论文列表失败:', error)
    ElMessage.error('加载论文列表失败')
  }
}

function handlePageChange(page) {
  papersStore.setCurrentPage(page)
  loadPapers()
}

function handleSizeChange(size) {
  papersStore.setPageSize(size)
  loadPapers()
}

async function deletePaper(paper) {
  try {
    await ElMessageBox.confirm(
      `确定要删除论文"${paper.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    const result = await papersStore.deletePaper(paper.entry_id)
    if (result.success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除论文失败:', error)
      ElMessage.error('删除论文失败')
    }
  }
}

function openPdf(paper) {
  const pdfUrl = `https://arxiv.org/pdf/${paper.arxiv_id}.pdf`
  window.open(pdfUrl, '_blank')
}

function openArxiv(paper) {
  const arxivUrl = `https://arxiv.org/abs/${paper.arxiv_id}`
  window.open(arxivUrl, '_blank')
}

function showDetails(paper) {
  currentPaper.value = paper
  detailsVisible.value = true
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

watch(
  () => props.refresh,
  (newVal) => {
    if (newVal) {
      loadPapers()
    }
  },
)

onMounted(() => {
  loadPapers()
})

defineExpose({
  loadPapers,
})
</script>
```

**Step 2: 更新PapersView.vue使用store**

**Step 3: 更新PaperSearchDialog.vue使用store**

**Step 4: 提交**

```bash
git add app/src/components/PaperList.vue app/src/views/PapersView.vue app/src/components/PaperSearchDialog.vue
git commit -m "refactor: 更新组件使用Pinia store"
```

---

## 阶段三：测试验证

### Task 9: 测试完整流程

**测试步骤:**

1. **测试分页功能**
   - 添加足够多的测试论文
   - 验证分页显示正确
   - 验证total显示正确总数

2. **测试数据模型一致性**
   - 搜索论文并保存
   - 验证前端显示作者列表正确
   - 验证分类显示正确
   - 验证arxiv_id显示正确

3. **测试响应格式**
   - 验证所有API调用返回{success, data, message}
   - 验证错误情况处理正确

4. **测试删除功能**
   - 添加论文后删除
   - 验证删除后列表刷新正确
   - 验证统计数据更新正确

5. **测试Pinia store**
   - 验证组件间数据共享
   - 验证路由切换后数据保持
   - 验证loading状态正确

---

## 任务总结

| 优先级 | 任务 | 状态 |
|-------|------|------|
| P0 | 修复分页统计错误 | 待执行 |
| P0 | 统一数据模型 | 待执行 |
| P0 | 统一响应格式 | 待执行 |
| P0 | 更新前端API客户端 | 待执行 |
| P0 | 更新前端组件 | 待执行 |
| P1 | 创建主数据库模型 | 待执行 |
| P1 | 创建PaperRepository | 待执行 |
| P1 | 创建Pinia Store | 待执行 |
| P1 | 更新组件使用Store | 待执行 |
| P1 | 完整流程测试 | 待执行 |

---

**相关文件清单:**

后端:
- `backend/src/papers/database.py`
- `backend/src/papers/service.py`
- `backend/src/api/papers.py`
- `backend/src/models/paper_schemas.py`
- `backend/src/models/db_models.py` (新增)
- `backend/src/repositories/paper_repository.py` (新增)

前端:
- `app/src/api/papers.js`
- `app/src/stores/papers.js` (新增)
- `app/src/components/PaperList.vue`
- `app/src/views/PapersView.vue`
- `app/src/components/PaperSearchDialog.vue`

---

计划文档已保存。两个执行选项：

**1. Subagent-Driven (本会话)** - 我为每个任务调度独立子agent，任务间进行代码审查，快速迭代

**2. Parallel Session (独立会话)** - 使用executing-plans技能打开新会话，批量执行带检查点

选择哪种方式？
