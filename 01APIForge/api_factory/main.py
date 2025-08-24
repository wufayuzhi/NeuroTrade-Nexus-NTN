#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Factory Module - 主应用入口
核心设计理念：微服务架构、数据隔离、ZeroMQ通信、三环境隔离
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import zmq
import zmq.asyncio
from typing import Dict, Any

from .config.settings import get_settings
from .routers import api_gateway, auth_center, quota_circuit, cluster_management
from .core.zmq_manager import ZMQManager
from .core.redis_manager import RedisManager
from .core.sqlite_manager import SQLiteManager
from .security.auth import AuthManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 全局管理器实例
zmq_manager: ZMQManager = None
redis_manager: RedisManager = None
sqlite_manager: SQLiteManager = None
auth_manager: AuthManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 严格按照全局规范"""
    global zmq_manager, redis_manager, sqlite_manager, auth_manager

    settings = get_settings()
    logger.info(f"启动API Factory Module - 环境: {settings.environment}")

    try:
        # 初始化核心组件 - 按照系统级集成流程
        zmq_manager = ZMQManager(settings.zmq_config)
        await zmq_manager.initialize()

        redis_manager = RedisManager(settings.redis_config)
        await redis_manager.initialize()

        sqlite_manager = SQLiteManager(settings.sqlite_config)
        await sqlite_manager.initialize()

        auth_manager = AuthManager(settings.auth_config)
        await auth_manager.initialize()

        logger.info("所有核心组件初始化完成")

        yield

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    finally:
        # 清理资源
        if zmq_manager:
            await zmq_manager.cleanup()
        if redis_manager:
            await redis_manager.cleanup()
        if sqlite_manager:
            await sqlite_manager.cleanup()
        if auth_manager:
            await auth_manager.cleanup()

        logger.info("API Factory Module 已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="API Factory Module",
    description="统一API管理工厂 - 微服务架构、数据隔离、ZeroMQ通信",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全认证
security = HTTPBearer()

# 注册路由模块 - 四大核心功能
app.include_router(api_gateway.router, prefix="/api/v1/gateway", tags=["API Gateway"])

app.include_router(
    auth_center.router, prefix="/api/v1/auth", tags=["Authentication Center"]
)

app.include_router(
    quota_circuit.router, prefix="/api/v1/quota", tags=["Quota & Circuit Breaker"]
)

app.include_router(
    cluster_management.router, prefix="/api/v1/cluster", tags=["Cluster Management"]
)


@app.get("/")
async def root():
    """根路径 - 系统状态检查"""
    settings = get_settings()
    return {
        "service": "API Factory Module",
        "version": "1.0.0",
        "environment": settings.environment,
        "status": "running",
        "core_modules": [
            "API Gateway",
            "Authentication Center",
            "Quota & Circuit Breaker",
            "Cluster Management",
        ],
    }


@app.get("/health")
async def health_check():
    """健康检查端点 - 测试热重载功能"""
    try:
        # 检查各组件状态
        zmq_status = await zmq_manager.health_check() if zmq_manager else False
        redis_status = await redis_manager.health_check() if redis_manager else False
        sqlite_status = await sqlite_manager.health_check() if sqlite_manager else False

        return {
            "status": "healthy",
            "components": {
                "zmq": zmq_status,
                "redis": redis_status,
                "sqlite": sqlite_status,
            },
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "api_factory.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )