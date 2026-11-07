from fastapi import FastAPI
from routers import news, users, favorite
from fastapi.middleware.cors import CORSMiddleware
from utils.exception import register_exception_handlers

app = FastAPI()

# 注册异常处理器
register_exception_handlers(app)
# 添加 CORS（跨域资源共享）中间件，允许浏览器从其他来源访问本 API。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的网页访问；部署到生产环境时建议改成可信域名
    allow_credentials=True,  # 允许跨域请求携带 Cookie 等身份凭据
    allow_methods=["*"],  # 允许所有 HTTP 请求方法，例如 GET、POST、PUT、DELETE
    allow_headers=["*"],  # 允许请求携带任意请求头
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


# 挂载注册路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
