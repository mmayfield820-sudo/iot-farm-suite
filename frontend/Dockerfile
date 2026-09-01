# Smart Farm Frontend
# 两阶段构建：node 构建 Vue dist → nginx 托管 + /api 反代后端
# 阶段一：构建
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
# 国内网络：npm 走宿主机代理（Windows Docker Desktop 下 host.docker.internal 指向宿主机）
# 无代理环境会自动跳过（连接失败不致命），改用 npmmirror 镜像兜底
ARG HTTP_PROXY_HOST=host.docker.internal
RUN npm config set registry https://registry.npmmirror.com \
 && npm config set proxy http://${HTTP_PROXY_HOST}:7890 \
 && npm config set https-proxy http://${HTTP_PROXY_HOST}:7890 \
 && npm ci || (npm config delete proxy && npm config delete https-proxy && npm ci)
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
