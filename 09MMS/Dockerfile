# 市场微结构仿真引擎(MMS) Docker配置文件
# 多阶段构建，优化镜像大小和安全性

# 构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y --fix-missing -o Acquire::Retries=3 -o Acquire::http::Timeout=30 \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装Python依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --default-timeout=100 --retries 3 --index-url https://pypi.org/simple -r requirements.txt

# 运行阶段
FROM python:3.11-slim as runtime

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# 创建非root用户
RUN groupadd -r mms && useradd -r -g mms mms

# 安装运行时依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置工作目录
WORKDIR /app

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R mms:mms /app

# 复制应用代码
COPY --chown=mms:mms src/ ./src/
COPY --chown=mms:mms scripts/ ./scripts/
COPY --chown=mms:mms config/ ./config/
COPY --chown=mms:mms *.py ./
COPY --chown=mms:mms *.md ./
COPY --chown=mms:mms *.txt ./

# 切换到非root用户
USER mms

# 暴露端口
EXPOSE 8000 5555 5556 5557

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 元数据标签
LABEL maintainer="NeuroTrade Nexus Team" \
      version="1.0.0" \
      description="Market Microstructure Simulation Engine" \
      org.opencontainers.image.title="MMS" \
      org.opencontainers.image.description="Market Microstructure Simulation Engine" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="NeuroTrade Nexus" \
      org.opencontainers.image.licenses="MIT"