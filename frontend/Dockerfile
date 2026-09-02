# Smart Farm Frontend
# 两阶段构建：node 构建 Vue dist → nginx 托管 + /api 反代后端
# 阶段一：构建
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
# 国内网络：npm 统一走 npmmirror 国内镜像（本机 Docker Desktop 与云服务器均直连可用）
# 注意：不要设 host.docker.internal 代理 —— 那是 Windows Docker Desktop 专属地址，
# 云服务器上不存在，会导致 npm ci 崩溃（Exit handler never called）。
RUN npm config set registry https://registry.npmmirror.com \
 && npm ci
COPY frontend/ ./
# 构建时写入 API 前缀（/api，由 nginx 反代到后端）
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# 阶段二：运行
FROM nginx:latest
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
