import secrets
from datetime import datetime, timedelta
from idlelib import query
from unittest import result

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security

# 根据用户名查询数据库
async def get_user_by_username(db: AsyncSession , username: str):
    statement = select(User).where(User.username == username)
    result = await db.execute(statement)
    return result.scalar_one_or_none()

# 创建用户
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先对密码加密处理
    hash_pwd = security.get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hash_pwd )
    db.add(user)
    # 先写入当前事务以获得自增ID；由 create_token 统一提交注册和 token。
    await db.flush()
    await db.refresh(user)
    return user

# 生成 Token
async def create_token(db: AsyncSession, user_id: int):
    """为用户创建或轮换唯一 token，7 天后过期。"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=7)

    try:
        # 锁住用户行，避免并发请求同时为同一用户插入多条 token。
        user_result = await db.execute(
            select(User.id).where(User.id == user_id).with_for_update()
        )
        if user_result.scalar_one_or_none() is None:
            raise ValueError(f"用户不存在: {user_id}")

        result = await db.execute(
            select(UserToken)
            .where(UserToken.user_id == user_id)
            .order_by(UserToken.id.desc())
        )
        existing_tokens = result.scalars().all()

        if existing_tokens:
            user_token = existing_tokens[0]
            # 清理旧版本代码可能留下的重复记录，避免旧 token 继续有效。
            for duplicate in existing_tokens[1:]:
                await db.delete(duplicate)
            user_token.token = token
            user_token.expires_at = expires_at
        else:
            db.add(
                UserToken(
                    user_id=user_id,
                    token=token,
                    expires_at=expires_at,
                )
            )

        await db.commit()
        return token
    except Exception:
        await db.rollback()
        raise

# 验证用户
async def authenticate_user(db: AsyncSession, username: str, password: str):
    # 验证用户是否存在
    user = await get_user_by_username(db, username)
    if not user:
        return None
    # 验证密码
    if not security.verify_password(password, user.password):
        return None
    return user

# 根据Token查询用户
async def get_user_by_token(db: AsyncSession, token: str):
    # 查询数据库中的token
    state = select(UserToken).where(UserToken.token == token)
    result = await db.execute(state)
    db_token = result.scalar_one_or_none()
    # token不存在或者过期
    if not db_token or db_token.expires_at < datetime.now():
        return None

    # token存在，则查询用户
    state = select(User).where(User.id == db_token.user_id)
    result = await db.execute(state)
    return result.scalar_one_or_none()

# 更新用户信息
async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    # user_data.model_dump()将Pydantic转字典 **解包(去掉大括号)
    # exclude_unset=True,exclude_none=True 排除未设置值的参数
    state = update(User).where(User.username == username).values(** user_data.model_dump(exclude_unset=True,exclude_none=True))
    result = await db.execute(state)
    await db.commit()
    # 检查是否成功更新
    if result.rowcount == 0 :
        raise HTTPException(status_code=404, detail="用户不存在")
    # 获取更新后的用户信息
    user = await get_user_by_username(db, username)
    return user

# 修改密码
async def change_password(db: AsyncSession, user: User, old_password:str ,new_password: str):
    # 验证密码是否正确
    if not security.verify_password(old_password, user.password):
        return False
    # 新密码加密
    hashed_password = security.get_hash_password(new_password)
    user.password = hashed_password
    # db.add(user) 确保能真正更新，规避Session过期等问题
    db.add(user)
    await db.commit()
    return True

