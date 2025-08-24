#!/usr/bin/env python3
"""
ReviewGuard人工审核模组 - FastAPI主应用
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import json
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Dict, Any
import uvicorn
import redis
import json
from datetime import datetime
import uuid

from .models.database import db_manager, StrategyReview, ReviewDecision, User
from .services.review_service import ReviewService
from .services.zmq_service import ZMQService
from .utils.auth import AuthManager
from .utils.config import get_settings

# 配置
settings = get_settings()

# 全局服务实例
review_service = None
zmq_service = None
auth_manager = AuthManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global review_service, zmq_service
    
    # 启动时初始化服务
    print("Starting ReviewGuard services...")
    
    # 初始化Redis连接
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
        redis_client.ping()
        print("Redis connection established")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None
    
    # 初始化服务
    zmq_service = ZMQService(None)  # 先创建ZMQ服务
    review_service = ReviewService(db_manager, redis_client, zmq_service)
    zmq_service.review_service = review_service  # 设置review_service引用
    
    # 启动ZeroMQ服务
    zmq_task = asyncio.create_task(zmq_service.start())
    
    yield
    
    # 关闭时清理资源
    print("Shutting down ReviewGuard services...")
    if zmq_service:
        await zmq_service.stop()
    zmq_task.cancel()
    try:
        await zmq_task
    except asyncio.CancelledError:
        pass


# 创建FastAPI应用
app = FastAPI(
    title="ReviewGuard API",
    description="人工审核模组API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全认证
security = HTTPBearer()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "status_code": 422
        }
    )


@app.exception_handler(json.JSONDecodeError)
async def json_decode_error_handler(request: Request, exc: json.JSONDecodeError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "JSON Decode Error",
            "message": "Invalid JSON format",
            "status_code": 400
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )


# Pydantic模型定义
class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject|defer)$", description="Decision must be one of: approve, reject, defer")
    reason: str = Field(..., min_length=1, description="Reason for the decision is required")
    risk_adjustment: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "decision": "approve",
                "reason": "策略风险可控，历史表现良好",
                "risk_adjustment": {
                    "position_size_limit": 0.8
                }
            }
        }


class LoginRequest(BaseModel):
    username: str
    password: str


class PaginationResponse(BaseModel):
    total: int
    data: List[Dict[str, Any]]
    page_info: Dict[str, Any]


class StrategyDetailResponse(BaseModel):
    strategy_info: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    historical_performance: List[Dict[str, Any]]
    market_conditions: Dict[str, Any]
    review_history: List[Dict[str, Any]]


class ReviewDecisionResponse(BaseModel):
    success: bool
    message: str
    decision_id: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    status: str
    database: str
    zmq_service: str
    timestamp: str


# 依赖注入
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户"""
    try:
        token = credentials.credentials
        user_data = auth_manager.verify_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 从数据库获取用户信息
        user = await db_manager.get_user_by_id(user_data["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "ReviewGuard",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check() -> HealthResponse:
    """健康检查"""
    return HealthResponse(
        status="healthy",
        database="connected",
        zmq_service="running",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """用户登录"""
    try:
        user = await db_manager.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # 生成JWT token
        token = auth_manager.create_access_token(
            data={"user_id": user.id, "username": user.username}
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reviews/pending")
async def get_pending_reviews(
    page: int = 1,
    limit: int = 20,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> PaginationResponse:
    """获取待审核策略列表"""
    try:
        # 构建过滤条件
        filters = {}
        if risk_level:
            filters["risk_level"] = risk_level
        if status:
            filters["status"] = status
        
        # 获取待审核策略
        reviews, total = await review_service.get_pending_reviews(
            page=page,
            limit=limit,
            filters=filters
        )
        
        return PaginationResponse(
            total=total,
            data=[{
                "id": review.id,
                "strategy_id": review.strategy_id,
                "strategy_name": review.strategy_name,
                "risk_level": review.risk_level,
                "status": review.status,
                "created_at": review.created_at.isoformat(),
                "priority": review.priority
            } for review in reviews],
            page_info={
                "current_page": page,
                "total_pages": (total + limit - 1) // limit,
                "page_size": limit,
                "has_next": page * limit < total,
                "has_prev": page > 1
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/detail")
async def get_strategy_detail(
    strategy_id: str,
    current_user: User = Depends(get_current_user)
) -> StrategyDetailResponse:
    """获取策略详细信息"""
    try:
        # 获取策略基本信息
        strategy_info = await review_service.get_strategy_info(strategy_id)
        if not strategy_info:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # 获取风险分析
        risk_analysis = await review_service.get_risk_analysis(strategy_id)
        
        # 获取历史表现
        historical_performance = await review_service.get_historical_performance(strategy_id)
        
        # 获取市场条件
        market_conditions = await review_service.get_market_conditions()
        
        # 获取审核历史
        review_history = await review_service.get_review_history(strategy_id)
        
        return StrategyDetailResponse(
            strategy_info=strategy_info,
            risk_analysis=risk_analysis,
            historical_performance=historical_performance,
            market_conditions=market_conditions,
            review_history=review_history
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reviews/{review_id}/decision")
async def submit_review_decision(
    review_id: str,
    request: ReviewDecisionRequest,
    current_user: User = Depends(get_current_user)
) -> ReviewDecisionResponse:
    """提交审核决策"""
    try:
        # 验证审核记录存在
        review = await db_manager.get_review_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # 检查审核状态
        if review.status != "pending":
            raise HTTPException(
                status_code=400, 
                detail="Review is not in pending status"
            )
        
        # 创建决策记录
        decision_id = str(uuid.uuid4())
        decision = ReviewDecision(
            id=decision_id,
            review_id=review_id,
            reviewer_id=current_user.id,
            decision=request.decision,
            reason=request.reason,
            risk_adjustment=request.risk_adjustment,
            created_at=datetime.now()
        )
        
        # 保存决策
        await db_manager.save_review_decision(decision)
        
        # 更新审核状态
        await db_manager.update_review_status(review_id, request.decision)
        
        # 发送决策结果到其他模组
        await review_service.notify_decision(review_id, decision)
        
        return ReviewDecisionResponse(
            success=True,
            message="Review decision submitted successfully",
            decision_id=decision_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reviews/{review_id}/decisions")
async def get_review_decisions(
    review_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取审核决策历史"""
    try:
        decisions = await db_manager.get_review_decisions(review_id)
        
        return {
            "success": True,
            "data": [{
                "id": decision.id,
                "reviewer_id": decision.reviewer_id,
                "decision": decision.decision,
                "reason": decision.reason,
                "risk_adjustment": decision.risk_adjustment,
                "created_at": decision.created_at.isoformat()
            } for decision in decisions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 审核历史查询
@app.get("/api/reviews/history")
async def get_review_history(
    page: int = 1,
    limit: int = 20,
    reviewer_id: Optional[str] = None,
    decision: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> PaginationResponse:
    """获取审核历史"""
    try:
        # 构建过滤条件
        filters = {}
        if reviewer_id:
            filters["reviewer_id"] = reviewer_id
        if decision:
            filters["decision"] = decision
        
        # 获取审核历史
        decisions, total = await review_service.get_review_history_paginated(
            page=page,
            limit=limit,
            filters=filters
        )
        
        return PaginationResponse(
            total=total,
            data=[{
                "id": decision.id,
                "review_id": decision.review_id,
                "strategy_id": decision.review.strategy_id if decision.review else None,
                "strategy_name": decision.review.strategy_name if decision.review else None,
                "reviewer_id": decision.reviewer_id,
                "decision": decision.decision,
                "reason": decision.reason,
                "risk_adjustment": decision.risk_adjustment,
                "created_at": decision.created_at.isoformat()
            } for decision in decisions],
            page_info={
                "current_page": page,
                "total_pages": (total + limit - 1) // limit,
                "page_size": limit,
                "has_next": page * limit < total,
                "has_prev": page > 1
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 配置管理
@app.get("/api/config/rules")
async def get_audit_rules(
    current_user: User = Depends(get_current_user)
):
    """获取审核规则配置"""
    try:
        rules = await review_service.get_audit_rules()
        return {
            "success": True,
            "data": rules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/status")
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """获取系统状态"""
    try:
        status_info = await review_service.get_system_status()
        
        return {
            "success": True,
            "data": {
                "service_status": "running",
                "database_status": "connected",
                "zmq_status": "active",
                "redis_status": "connected",
                "pending_reviews": status_info.get("pending_reviews", 0),
                "processed_today": status_info.get("processed_today", 0),
                "system_load": status_info.get("system_load", {}),
                "last_update": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 主程序入口
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )