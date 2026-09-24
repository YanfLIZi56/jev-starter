# =========阶段1：Node构建前端（编译Vue，产出dist）=========
FROM node:22-alpine AS frontend-builder

WORKDIR /build

# 拷贝前端源码
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build
# build完成后，dist在 /build/dist

# =========阶段2：Python运行时（最终镜像，只有python+dist）=========
FROM python:3.11-slim

WORKDIR /app

# 安装python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/main.py .

# 【关键】从上一个构建阶段，把编译好的dist复制进python容器
COPY --from=frontend-builder /build/dist /app/dist

# 启动uvicorn，监听fly要求的 0.0.0.0:8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
