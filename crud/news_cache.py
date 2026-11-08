"""
带缓存功能的news
"""
from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category, News
from cache.news_cache import get_cached_categories, set_cached_categories, get_cached_news_list, set_cached_news_list


# 获取新闻类别
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 先尝试从缓存中获取
    cache = await get_cached_categories()
    if cache:
        return cache
    # 缓存中没有，再查库
    statement = select(Category).offset(skip).limit(limit)
    result = await db.execute(statement)
    categories = result.scalars().all() # ORM结果，需要转类型
    # 写入缓存
    if categories:
        categories_cache = jsonable_encoder(categories)
        await set_cached_categories(categories_cache)
    # 返回
    return categories

# 分页获取某类新闻列表
async def get_news_list(
        db: AsyncSession,
        category_id: int,
        page: int = 0,
        page_size: int = 10
):
    # 先尝试从缓存获取新闻列表
    cache = await get_cached_news_list(category_id, page, page_size) # json格式
    if cache:
        # 需要转为 ORM 格式
        return [News(**item) for item in cache]
    # 将页码换算成 SQL OFFSET：第 1 页跳过 0 条，第 2 页跳过 page_size 条。
    # offset：跳过的记录数，limit：返回的记录数
    offset = (page - 1) * page_size
    page_statement = (
        select(News)
        .where(News.category_id == category_id)
        .order_by(News.publish_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    page_result = await db.execute(page_statement)
    news = page_result.scalars().all()
    # 写入缓存
    if news:
        # 先把 ORM 格式转为 JSON 格式
        news_cache = jsonable_encoder(news)
        await set_cached_news_list(category_id,page,page_size,news_cache)
    return news

# 计算某分类下新闻总量
async def get_news_count(db: AsyncSession, category_id: int):
    statement = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(statement)
    # scalar_one: 只能有一个结果，否则报错
    news_count = result.scalar_one()
    return news_count

# 获取新闻详情
async def get_news_detail(db: AsyncSession, news_id: int):
    statement = select(News).where(News.id == news_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

# 增加新闻浏览量
async def increase_news_views(db: AsyncSession, news_id: int):
    statement = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(statement)
    # 检查是否命中结果
    return result.rowcount > 0

# 根据查询相关新闻
async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    statement = select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(News.views.desc(),
               News.publish_time.desc()
    ).limit(limit)
    result = await db.execute(statement)
    related_news = result.scalars().all()
    # 列表推导式推导出新闻的核心数据，再返回
    return [{
            "id" : news_detail.id,
            "title" : news_detail.title,
            "content" : news_detail.content,
            "image" : news_detail.image,
            "author" : news_detail.author,
            "publishTime" : news_detail.publish_time,
            "categoryId" : news_detail.category_id,
            "views" : news_detail.views,
            "relatedNews" : related_news
    } for news_detail in related_news]