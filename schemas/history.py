from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from schemas.base import NewsItemBase


class HistoryAddRequest(BaseModel):
    news_id: int = Field(...,alias="newsId")


class HistoryAddResponse(BaseModel):
    id: int
    user_id: int = Field(alias="userId")
    news_id: int = Field(alias="newsId")
    view_time: datetime = Field(alias="viewTime")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HistoryNewsItemResponse(NewsItemBase):
    # 历史列表接口和前端页面使用 publishTime 字段。
    publish_time: datetime | None = Field(None, alias="publishTime")
    view_time: datetime = Field(alias="viewTime")
    history_id: int = Field(alias="historyId")


class HistoryListResponse(BaseModel):
    list: list[HistoryNewsItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(populate_by_name=True)
