from datetime import datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.mysql import INTEGER, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from models.users import Base


class Favorite(Base):
    """用户收藏新闻的 ORM 模型。"""

    __tablename__ = "favorite"
    __table_args__ = (
        # 同一个用户不能重复收藏同一条新闻。
        UniqueConstraint("user_id", "news_id", name="user_news_unique"),
        Index("fk_favorite_user_idx", "user_id"),
        Index("fk_favorite_news_idx", "news_id"),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True, comment="收藏ID"
    )
    user_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("user.id", name="fk_favorite_user", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    news_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("news.id", name="fk_favorite_news", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="新闻ID",
    )
    # 数据库负责填写默认时间，与现有表的 CURRENT_TIMESTAMP 一致。
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False, comment="收藏时间"
    )

    def __repr__(self) -> str:
        return (
            f"<Favorite(id={self.id!r}, user_id={self.user_id!r}, "
            f"news_id={self.news_id!r}, created_at={self.created_at!r})>"
        )
