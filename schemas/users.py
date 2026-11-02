from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.sql.coercions import cls


class UserRequest(BaseModel):
    username: str
    password: str

class UserInfoBase(BaseModel):
    """用户可编辑的基础信息。"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


# user_info 对应的类：基础类 + info类（ id、用户名）
class UserInfoResponse(UserInfoBase):
    id: int
    username: str

    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM对象中取值
    )

class UserAuthResponse(BaseModel):
    token: str
    user_info  : UserInfoResponse = Field(..., alias="userInfo")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True, # alias和字段名兼容
        from_attributes=True,  # 允许从ORM对象中取值
    )

class UserUpdateRequest (BaseModel):
    nickname: str = None
    avatar: str = None
    gender: str = None
    bio: str = None
    phone: str = None

class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(...,alias="oldPassword" ,description="旧密码")
    new_password: str = Field(...,alias="newPassword",min_length=6,description="新密码")

