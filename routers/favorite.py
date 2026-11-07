from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_config import get_db
from models.users import User
from schemas.favorite import FavoriteCheckResponse, AddFavoriteRequest, FavoriteListResponse
from utils.auth import get_current_user
from utils.response import success_response
from crud import favorite

router = APIRouter(prefix="/api/favorite",tags=["favorite"])

# 检查是否收藏
@router.get("/check")
async def check_favorite(news_id: int=Query(...,alias="newsId",description="新闻id"),
                         user: User=Depends(get_current_user),
                         db: AsyncSession=Depends(get_db)
):
    # 检查是否已经收藏
    is_favorite = await favorite.is_news_favorite(db, user.id, news_id)
    return success_response(message="检查收藏状态成功",data=FavoriteCheckResponse(isFavorite=is_favorite))

@router.post("/add")
async def add_favorite(
        data: AddFavoriteRequest,
        user: User=Depends(get_current_user),
        db: AsyncSession=Depends(get_db)
):
    result = await favorite.add_favorite(db, user.id, data.news_id)

    return success_response(message="添加收藏成功",data=result)

@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(...,alias="newsId"),
        user: User=Depends(get_current_user),
        db: AsyncSession=Depends(get_db)
):
    result = await favorite.remove_favorite(db, user.id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="收藏不存在")
    return success_response(message="删除收藏成功")

@router.get("/list")
async def get_favorite_list(
        page: int = Query(...,ge=1),
        page_size: int = Query(10,ge=1,le=100, alias="pageSize"),
        user: User=Depends(get_current_user),
        db: AsyncSession=Depends(get_db)
):
    rows,count = await favorite.get_favorite_list(db, user.id, page, page_size)
    favorite_list = [{
        **news.__dict__,
        "favorite_time": favorite_time,
        "favorite_id": favorite_id,
    } for news, favorite_time, favorite_id in rows]
    has_more = count > page_size*page
    data = FavoriteListResponse(list=favorite_list,count=count,hasMore=has_more)
    return success_response(message="获取收藏列表成功 ",data=data)

# 清空收藏列表
@router.delete("/clear")
async def clear_favorite(
        user: User=Depends(get_current_user),
        db: AsyncSession=Depends(get_db)
):
    rows = await favorite.clear_favorite(db, user.id)
    return success_response(message=f"清空了{rows}成功")