from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News


async def add_history(db: AsyncSession, user_id: int, news_id: int) -> History | None:
    # 新闻不存在时不创建浏览记录。
    news = await db.scalar(select(News.id).where(News.id == news_id))
    if news is None:
        return None

    # 按用户和新闻查找已有记录；旧数据可能有重复，取最新的一条。
    history = await db.scalar(
        select(History)
        .where(History.user_id == user_id, History.news_id == news_id)
        .order_by(History.view_time.desc(), History.id.desc())
        .limit(1)
    )
    if history is None:
        # 首次浏览：新增记录，浏览时间由数据库生成。
        history = History(user_id=user_id, news_id=news_id)
        db.add(history)
    else:
        # 再次浏览：保留原记录，使用数据库当前时间更新浏览时间。
        history.view_time = func.current_timestamp()

    # 获取数据库生成的 id 和浏览时间；事务由 get_db 统一提交或回滚。
    await db.flush()
    await db.refresh(history)
    return history


async def get_history_list(db: AsyncSession, user_id: int, page: int, page_size: int):
    # 统计与列表使用相同的连接条件，避免已删除新闻影响总数。
    total = await db.scalar(
        select(func.count()).select_from(History)
        .join(News, News.id == History.news_id)
        .where(History.user_id == user_id)
    )
    statement = (
        select(News, History.view_time, History.id)
        .join(History, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc(), History.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(statement)
    return result.all(), total


async def delete_history(db: AsyncSession, user_id: int, history_id: int) -> bool:
    # 同时限定记录 ID 和用户 ID，避免删除其他用户的浏览记录。
    result = await db.execute(
        delete(History).where(History.id == history_id, History.user_id == user_id)
    )
    return result.rowcount > 0


async def clear_history(db: AsyncSession, user_id: int) -> None:
    # 限定当前用户；没有记录时也视为清空成功。
    await db.execute(delete(History).where(History.user_id == user_id))
