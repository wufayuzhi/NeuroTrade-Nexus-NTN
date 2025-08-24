from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging
import time
from typing import Dict, Any

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting NeuroTrade Nexus AI Strategy Assistant...")

    # 初始化数据库
    try:
        init_db()
        logger.info("Database initialized successfully")

        # 测试异步数据库连接
        from app.core.database import async_engine

        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Async database connection verified")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # 关闭时执行
    logger.info("Shutting down NeuroTrade Nexus AI Strategy Assistant...")
    from app.core.database import async_engine

    await async_engine.dispose()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="AI策略研究助理 - 提供智能交易策略分析和建议",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加可信主机中间件
if settings.ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    response = await call_next(request)

    # 记录响应
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - " f"Time: {process_time:.3f}s")

    return response


# HTTP异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException",
            },
            "timestamp": time.time(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# 通用异常处理器
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "InternalServerError",
            },
            "timestamp": time.time(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# 健康检查端点
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "AI Strategy Assistant",
        "version": "1.0.0",
        "timestamp": time.time(),
    }


# 根路径
@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "NeuroTrade Nexus AI Strategy Assistant",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
    }


# 包含API路由
app.include_router(api_router, prefix="/api/v1")

# 运行应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )