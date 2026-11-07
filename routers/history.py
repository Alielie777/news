from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud import history
from models.users import User
from schemas.history import HistoryAddRequest, HistoryAddResponse, HistoryListResponse, HistoryNewsItemResponse
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history",tags=["history"])

# 添加浏览记录
@router.post("/add")
async def add_history(
    data: HistoryAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # get_current_user 先验证 Token；未登录时不会进入此处理函数。
    # 已浏览过则更新浏览时间，否则新增记录。
    record = await history.add_history(db, user.id, data.news_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="新闻不存在")
    return success_response(message="添加成功", data=HistoryAddResponse.model_validate(record))


@router.get("/list")
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 只查询当前登录用户的记录，并按最近浏览时间分页。
    rows, total = await history.get_history_list(db, user.id, page, page_size)
    items = []
    for news, view_time, history_id in rows:
        item = HistoryNewsItemResponse.model_validate({**news.__dict__, "view_time": view_time, "history_id": history_id})
        items.append(item)
    data = HistoryListResponse(list=items, total=total, hasMore=page * page_size < total)
    return success_response(data=data)


@router.delete("/delete/{history_id}")
async def delete_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 找不到记录或记录属于其他用户时，统一返回 404。
    if not await history.delete_history(db, user.id, history_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="浏览记录不存在")
    return success_response(message="删除成功")


@router.delete("/clear")
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Token 验证成功后，只清除当前用户的浏览记录。
    await history.clear_history(db, user.id)
    return success_response(message="清空成功")
