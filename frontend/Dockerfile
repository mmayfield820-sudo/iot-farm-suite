# Smart Farm Frontend
# 两阶段构建：node 构建 Vue dist → nginx 托管 + /api 反代后端
# 阶段一：构建
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
# npm registry 默认走 npmmirror 国内镜像（云服务器自动部署直连可用）。
# 本机若连 npm 镜像不稳（常见：开着代理/VPN 干扰 Docker 出网导致 ECONNREFUSED），
# 可用 build-arg 覆盖（见 scripts/make_package.sh 顶部说明）：
#   --build-arg NPM_REGISTRY=https://registry.npmjs.org
#   --build-arg http_proxy=http://host.docker.internal:7890
# 注意：代理只在构建时通过 build-arg 临时传入，绝不写死在 Dockerfile 里 ——
# 云服务器上没有 host.docker.internal 这个地址，写死会导致 npm ci 崩溃（Exit handler never called）。
# replace-registry-host always：npm ci 严格按 package-lock.json 的 resolved 字段下载，
# 该配置强制统一走上面的 registry，避免 lock 锁死的镜像源地址连不上。
ARG NPM_REGISTRY=https://registry.npmmirror.com
ARG http_proxy=
ARG https_proxy=
RUN npm config set registry "$NPM_REGISTRY" \
 && npm config set replace-registry-host always \
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
