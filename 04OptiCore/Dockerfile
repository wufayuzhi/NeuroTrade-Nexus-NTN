# NeuroTrade Nexus (NTN) - 策略优化模组 Docker 配置
# Strategy Optimization Module Dockerfile
# 采用多阶段构建以减小最终镜像体积

# =================================================================
# 构建阶段 (Builder Stage)
# =================================================================
FROM python:3.11-slim AS builder

# 设置构建阶段环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y --fix-missing -o Acquire::Retries=3 -o Acquire::http::Timeout=30 \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libzmq3-dev \
    libhdf5-dev \
    libatlas3-base \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装TA-Lib C库（金融技术分析库）
RUN cd /tmp && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/ta-lib*

# 创建虚拟环境并安装Python依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制requirements文件
COPY requirements.txt .

# 升级pip并安装Python依赖
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy==1.25.2 pandas==2.1.4 scipy==1.11.4 && \
    pip install --no-cache-dir -r requirements.txt

# =================================================================
# 生产阶段 (Production Stage)
# =================================================================
FROM python:3.11-slim AS production

# 设置维护者信息和标签
LABEL maintainer="NeuroTrade Nexus Team" \
      description="Strategy Optimization Module for NeuroTrade Nexus" \
      version="1.0.0" \
      component="opticore"

# 设置生产环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NTN_ENVIRONMENT=production \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends \
    libzmq5 \
    libhdf5-310 \
    libatlas3-base \
    libfreetype6 \
    libpng16-16 \
    libjpeg62-turbo \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境和TA-Lib库
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/lib/libta_lib.* /usr/lib/
COPY --from=builder /usr/include/ta-lib/ /usr/include/ta-lib/

# 创建非root用户
RUN groupadd -r ntn && useradd -r -g ntn -d /app -s /bin/bash ntn

# 创建必要的目录结构
RUN mkdir -p /app/logs \
             /app/data \
             /app/cache \
             /app/temp \
             /app/config \
             /app/tests/logs \
             /app/supabase/migrations && \
    chown -R ntn:ntn /app

# 复制应用代码
COPY --chown=ntn:ntn . .

# 设置权限
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true && \
    chmod 755 /app

# 创建健康检查脚本
RUN echo '#!/bin/bash\n\
curl -f http://localhost:8000/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh && \
    chown ntn:ntn /app/healthcheck.sh

# 暴露端口
EXPOSE 8000 5555 5556

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# 切换到非root用户
USER ntn

# 设置启动命令
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# =================================================================
# Docker构建和运行说明
# =================================================================
# Build: docker build --target production -t ntn-opticore:latest .
# Run: docker run -d -p 8000:8000 -p 5555:5555 -p 5556:5556 \
#      -e NTN_ENVIRONMENT=production \
#      -e DATABASE_PATH=/app/data/opticore.db \
#      -e REDIS_HOST=redis \
#      -e ZMQ_SUBSCRIBER_PORT=5555 \
#      -e ZMQ_PUBLISHER_PORT=5556 \
#      -v /host/data:/app/data \
#      -v /host/logs:/app/logs \
#      --name ntn-opticore \
#      ntn-opticore:latest