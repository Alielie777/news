'''
新闻模块路由
'''

from fastapi import APIRouter,Depends, Query, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from crud import news,news_cache

# 创建 APIRouter 实例
# prefix: 路由前缀 tags: 分组
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现流程：
# 1.模块化路由 -> API 接口规范文档
# 2.定义模型类 -> 数据库表
# 3.在crud中封装操作数据库的方法
# 4.在路由处理函数中调用crud中封装好的方法，响应结果

# 创建路由
@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db),skip: int = 0, limit: int = 100):
    categories = await news_cache.get_categories(db, skip, limit)
    return {
        "code": 200,
        "msg": "success",
        "data": categories
    }

# 按分类获取新闻列表
@router.get("/list")
async def get_news_list(
    category_id: int = Query(..., alias="categoryId"),
    page: int = Query(1, alias="page", ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, alias="pageSize",ge=1, le=100, description="每页记录数，最多 100 条"),
    db: AsyncSession = Depends(get_db)
):
    # 获取新闻列表
    news_list = await news_cache.get_news_list(db, category_id, page, page_size)
    # 获取新闻总量
    total = await news_cache.get_news_count(db, category_id)
    # 检查是否还有更多: 总量 > 查到的数量 + 跳过的数量 ?
    has_more = total > (len(news_list) + (page-1)*page_size)
    return {
        "code": 200,
        "msg": "获取新闻列表成功",
        "data": {
            "list" : news_list,
            "total" : total,
            "hasMore" : has_more
        }
    }

# 获取新闻详情
@router.get("/detail")
async def get_news_detail(
        news_id: int = Query(...,alias="id", description="新闻id"),
        db: AsyncSession = Depends(get_db)
):
    # 获取新闻
    news_detail = await news.get_news_detail(db, news_id)
    # 如果新闻不存在，抛出异常
    if not news_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="新闻不存在")
    # 增加新闻浏览量
    views_res = await news.increase_news_views(db, news_id)
    # 如果更新失败
    if not views_res:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="更新新闻浏览量失败")
    # 获取相关新闻
    related_news = await news.get_related_news(db, news_id,news_detail.category_id)

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "id" : news_detail.id,
            "title" : news_detail.title,
            "content" : news_detail.content,
            "image" : news_detail.image,
            "author" : news_detail.author,
            "publishTime" : news_detail.publish_time,
            "categoryId" : news_detail.category_id,
            "views" : news_detail.views,
            "relatedNews" : related_news
        }
    }

