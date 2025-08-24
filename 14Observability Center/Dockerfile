# 多阶段构建
# 阶段1: 构建前端
FROM node:18-bullseye-slim AS frontend-builder

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装所有依赖（包括开发依赖）
RUN npm install

# 复制源代码
COPY . .

# 构建前端
RUN npm run build

# 阶段2: 生产环境
FROM node:18-bullseye-slim AS production

# 安装必要的系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs observability

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装构建工具（用于编译原生模块如bcrypt）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装生产依赖
RUN npm install --only=production && npm cache clean --force

# 复制构建产物
COPY --from=frontend-builder /app/dist ./dist
COPY --from=frontend-builder /app/api ./api

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R observability:nodejs /app && \
    chmod -R 755 /app

# 切换到非root用户
USER observability

# 暴露端口
EXPOSE 3000 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# 使用dumb-init作为PID 1
ENTRYPOINT ["dumb-init", "--"]

# 启动命令
CMD ["node", "api/server.js"]