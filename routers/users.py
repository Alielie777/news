'''
用户模块路由
'''
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from crud import users
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest
from utils.response import success_response
from utils.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])

@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 验证用户是否存在
    exist = await users.get_user_by_username(db, user_data.username)
    if exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="用户已存在 ")
    # 如果用户不存在，就先创建用户
    user = await users.create_user(db, user_data)
    # 创建完用户紧接着生成token
    token = await users.create_token(db, user.id)

    # return {
    #     "code": "code",
    #     "message": "注册成功",
    #     "data": {
    #         "token": token,
    #         "userInfo": {
    #             "id": user.id,
    #             "username": user.username,
    #             "bio": user.bio,
    #             "avatar": user.avatar
    #         }
    #     }
    # }
    response_data = UserAuthResponse(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功",data=response_data)

# 用户登陆
@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="用户名或密码错误 ")
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功",data=response_data)

# 获取用户信息
@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(message="获取用户信息成功",data=UserInfoResponse.model_validate(user))

# 修改用户信息
# 参数：用户输入 + 验证Token + db
@router.put("/update")
async def update_user_info(user_data: UserUpdateRequest, user: UserRequest = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await users.update_user(db, user.username, user_data)
    return success_response(message="更新用户信息成功",data=UserInfoResponse.model_validate(user))

# 修改密码
@router.put("/password")
async def update_password(user_data: UserChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await users.change_password(db, user, user_data.old_password, user_data.new_password)
    if not result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="修改密码失败")
    return success_response(message="修改密码成功 ")