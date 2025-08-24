# 多阶段构建 Dockerfile for API Factory
# Stage 1: 构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: 运行阶段
FROM python:3.11-slim as runtime

# 创建非root用户
RUN groupadd -r apiuser && useradd -r -g apiuser apiuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/apiuser/.local

# 复制应用代码
COPY api_factory/ ./api_factory/
COPY config/ ./config/

# 创建必要的目录
RUN mkdir -p /app/data /app/logs && \
    chown -R apiuser:apiuser /app

# 切换到非root用户
USER apiuser

# 设置环境变量
ENV PATH=/home/apiuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000 5555 5556

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "api_factory.main"]