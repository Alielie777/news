from typing import List
from pydantic import BaseModel, Field,ConfigDict
from schemas.base import NewsItemBase
from datetime import datetime


class FavoriteCheckResponse(BaseModel):
    is_favorite : bool = Field(...,alias="isFavorite")

class AddFavoriteRequest(BaseModel):
    news_id: int = Field(...,alias="newsId")

class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int = Field(...,alias="favoriteId")
    favorite_time: datetime = Field(...,alias="favoriteTime")


# 收藏列表响应模型类
class FavoriteListResponse(BaseModel):
    list: List[FavoriteNewsItemResponse] = Field(...,alias="list")
    count: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
