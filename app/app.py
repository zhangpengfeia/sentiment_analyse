from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.routers import config, events, host, report, research
from app.dependencies import get_host_service


# 定义lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_host_service().subscribe_discussion()
        yield  # FASTAPI处理路由
    finally:
        # 应用关闭的时候，清理资源
        get_host_service().unsubscribe_discussion()


app = FastAPI(description="舆情应用的FastAPI实例", lifespan=lifespan)

# app配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由

app.include_router(config.router)

app.include_router(host.router)
app.include_router(report.router)
app.include_router(research.router)
app.include_router(events.router)
