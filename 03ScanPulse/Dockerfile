# 扫描器模组 Docker 配置
# 多阶段构建：构建阶段 + 运行阶段

# ===== 构建阶段 =====
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y \
    gcc \
    g++ \
    libzmq3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到临时目录
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --target=/build/deps -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.11-slim as runtime

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app:/app/deps
ENV PYTHONUNBUFFERED=1
ENV SCANNER_ENV=production

# 安装运行时依赖（仅保留必要的库）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y \
    libzmq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制Python依赖
COPY --from=builder /build/deps /app/deps

# 创建非root用户和组
RUN groupadd -r scanner && useradd -r -g scanner -s /bin/false scanner

# 创建必要目录并设置权限
RUN mkdir -p /app/logs /app/config && \
    chown -R scanner:scanner /app

# 复制应用代码
COPY . /app/

# 设置文件权限
RUN chown -R scanner:scanner /app

# 切换到非root用户
USER scanner

# 暴露端口
EXPOSE 5003 5553 5554

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5003/health')" || exit 1

# 启动命令
CMD ["python", "main.py", "start", "--environment", "production"]