#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Factory Module
统一API管理工厂 - NeuroTrade Nexus (NTN) 核心模块

核心功能：
- API网关服务
- 认证与授权
- 限流与熔断
- 集群管理

技术栈：
- FastAPI + Uvicorn
- SQLite + SQLAlchemy
- Redis + aioredis
- ZeroMQ + pyzmq
- JWT + Passlib
"""

__version__ = "1.0.0"
__author__ = "NTN Development Team"
__email__ = "dev@neurotrade-nexus.com"

# 导出核心组件
from .main import app
from .config.settings import get_settings

__all__ = [
    "app",
    "get_settings",
]