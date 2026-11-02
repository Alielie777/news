# 根据token查询用户，最后返回用户
from fastapi import Header, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud import users


async def get_current_user(authorization: str | None = Header(default=None, alias="Authorization"),
                           db: AsyncSession = Depends(get_db)
):
    # 前端应按标准格式传入：Authorization: Bearer <token>
    # 先验证请求头，避免缺少 token 或格式错误时出现 IndexError（500）。
    parts = authorization.strip().split() if authorization else []
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少有效的 Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1].strip()
    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已经过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
