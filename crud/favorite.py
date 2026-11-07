from idlelib import delegator

from sqlalchemy import select,delete,func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


# 检查收藏状态: 当前用户是否收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    state = select(Favorite).where(Favorite.user_id == user_id,Favorite.news_id == news_id)
    result = await db.execute(state)
    # 返回布尔值
    return result.scalar_one_or_none() is not None

# 添加收藏
async def add_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    favorite = Favorite(user_id=user_id,news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

# 取消收藏
async def remove_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    state = delete(Favorite).where(Favorite.user_id == user_id,Favorite.news_id == news_id)
    result = await db.execute(state)
    await db.commit()
    return result.rowcount > 0

# 获取某个用户的收藏列表
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 总收藏数
    state = select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    count_result = await db.execute(state)
    count = count_result.scalar_one()

    # 获取收藏列表：连表查询 join() + 分页 + 按收藏时间排序
    # label()：起别名
    state = (select(News,Favorite.created_at.label("favorite_time"),Favorite.id.label("favorite_id"))
     .join(Favorite,Favorite.news_id == News.id)
     .where(Favorite.user_id == user_id)
     .order_by(Favorite.created_at.desc())
     .limit(page_size)
     .offset((page-1) * page_size))
    result = await db.execute(state)
    rows = result.all()
    return rows,count

# 清空收藏列表
async def clear_favorite(
        db: AsyncSession,
        user_id: int
):
    state = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(state)
    await db.commit()
    # 返回删除的数量
    return result.rowcount or 0