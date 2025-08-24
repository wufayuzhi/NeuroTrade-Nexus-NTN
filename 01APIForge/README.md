# 01APIForge - API统一管理工厂

## 概述

APIForge是NeuroTrade Nexus (NTN)系统的核心模块，负责统一管理和协调所有API接口，提供安全、高效的API网关服务。

## 核心功能

### 1. API网关服务
- 统一API入口点
- 请求路由和负载均衡
- API版本管理
- 请求/响应转换

### 2. 认证与授权
- JWT令牌管理
- 用户身份验证
- 权限控制
- API密钥管理

### 3. 限流与熔断
- 请求频率限制
- 熔断器模式
- 降级策略
- 流量控制

### 4. 监控与日志
- API调用统计
- 性能监控
- 错误追踪
- 审计日志

## 技术架构

### 技术栈
- **框架**: FastAPI 0.104.1
- **异步运行时**: Uvicorn
- **数据库**: SQLite (SQLAlchemy ORM)
- **缓存**: Redis
- **消息队列**: ZeroMQ
- **认证**: JWT + Passlib

### 目录结构
```
api_factory/
├── __init__.py
├── main.py              # 应用入口
├── config/              # 配置管理
├── core/                # 核心业务逻辑
├── routers/             # API路由
└── security/            # 安全模块
```

## 快速开始

### 环境要求
- Python 3.11+
- Redis 7.0+
- Docker (可选)

### 本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件设置必要的配置
```

3. **启动服务**
```bash
python -m api_factory.main
```

### Docker部署

1. **构建镜像**
```bash
docker build -t ntn-api-forge .
```

2. **运行容器**
```bash
docker run -p 8000:8000 -p 5555:5555 -p 5556:5556 ntn-api-forge
```

## API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心端点

### 健康检查
```
GET /health
```

### 认证
```
POST /auth/login
POST /auth/refresh
POST /auth/logout
```

### API管理
```
GET /api/routes
POST /api/register
DELETE /api/unregister
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 运行环境 | `development` |
| `REDIS_HOST` | Redis主机 | `localhost` |
| `REDIS_PASSWORD` | Redis密码 | - |
| `ZMQ_PUBLISHER_PORT` | ZMQ发布端口 | `5555` |
| `ZMQ_SUBSCRIBER_PORT` | ZMQ订阅端口 | `5556` |
| `JWT_SECRET_KEY` | JWT密钥 | 自动生成 |
| `JWT_ALGORITHM` | JWT算法 | `HS256` |
| `JWT_EXPIRE_MINUTES` | JWT过期时间 | `30` |

## 开发指南

### 代码规范
- 遵循PEP 8代码风格
- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用MyPy进行类型检查

### 测试
```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=api_factory

# 运行特定测试
pytest tests/test_auth_center.py
```

### 代码质量检查
```bash
# 代码格式化
black api_factory/

# 导入排序
isort api_factory/

# 代码检查
flake8 api_factory/

# 类型检查
mypy api_factory/
```

## 监控与运维

### 健康检查
服务提供多层次的健康检查：
- HTTP健康检查端点
- Redis连接检查
- 数据库连接检查
- ZMQ连接检查

### 日志管理
- 使用Loguru进行结构化日志
- 支持多种日志级别
- 自动日志轮转
- 集中化日志收集

### 性能监控
- Prometheus指标导出
- API响应时间监控
- 错误率统计
- 资源使用监控

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务状态
   - 验证连接配置
   - 检查网络连通性

2. **ZMQ端口冲突**
   - 检查端口占用情况
   - 修改配置文件中的端口设置
   - 重启相关服务

3. **数据库锁定**
   - 检查SQLite文件权限
   - 确保没有其他进程占用数据库
   - 重启服务

### 日志分析
```bash
# 查看最新日志
tail -f logs/api_factory.log

# 搜索错误日志
grep "ERROR" logs/api_factory.log

# 分析API调用统计
grep "API_CALL" logs/api_factory.log | awk '{print $5}' | sort | uniq -c
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](../LICENSE) 文件。

## 联系方式

- 项目维护者: NTN开发团队
- 邮箱: dev@neurotrade-nexus.com
- 文档: https://docs.neurotrade-nexus.com
