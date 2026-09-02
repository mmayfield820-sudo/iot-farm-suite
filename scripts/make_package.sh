#!/usr/bin/env bash
# =============================================================
# 智慧农业平台 · 部署包打包脚本
#
# 用法（在仓库根目录运行）：
#   bash scripts/make_package.sh
#
# 产出：
#   dist/预构建镜像包/        可直接交付/上传的目录
#   dist/farm-prebuild.tar.gz 压缩包（传给老师/上传服务器用）
#
# 前置：
#   - 本机 Docker + Docker Compose 可用
#   - 建议先 cp .env.example .env 并填写密钥（构建会用默认值，运行才需要密钥）
#
# 每次迭代发布时重跑本脚本即可，会重新构建并打包最新代码。
# =============================================================
set -euo pipefail

# 强制文件名按 UTF-8 进包（否则 Windows/Linux 解压中文文件名会乱码）
export LANG=C.UTF-8 LC_ALL=C.UTF-8

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$DIST_DIR/预构建镜像包"
IMAGES_DIR="$BUILD_DIR/images"
# 包内运行时目录。目录名固定为 iot-farm-suite（启动.bat 与部署文档引用了该路径，勿改）
APP_DIR="$BUILD_DIR/iot-farm-suite"
PACKAGE_WIN_DIR="$PROJECT_ROOT/scripts/package/windows"
DEPLOY_DOC="$PROJECT_ROOT/docs/deployment/部署文档.md"

# 固定镜像名（与 infra/docker-compose.yml 保持一致）
declare -A IMAGES=(
  [emqx]="emqx/emqx:5.8"
  [mysql]="mysql:8.0"
  [backend]="smart-farm/backend:latest"
  [ai-service]="smart-farm/ai-service:latest"
  [frontend]="smart-farm/frontend:latest"
)

# 发布包内"运行时必需文件"白名单（相对仓库根）。
# 交付规范：发布包内不放源码 —— 平台源码（backend/frontend/ai-service 等）单独走 Git 仓库交付，
# 包内只带运行必需文件，避免踩"包内带源码"红线，也让包更小。
# 各文件的用途（启动.bat / docker-compose.yml 直接依赖，缺了老师跑不起来）：
#   - .env.example                             启动.bat 首次运行 copy 成 .env（含 JWT 密钥占位）
#   - infra/docker-compose.yml                 启动.bat cd 进来执行 docker compose up -d
#   - database/schema + seed 的 3 个 .sql      MySQL 容器首次启动自动建库建表 + 预置演示数据（compose 挂载）
#   - device-simulator/鸿蒙模拟器/*            交付的传感器模拟器：jar 成品 + 预置 sensors.dat + 使用文档
RUNTIME_FILES=(
  ".env.example"
  "infra/docker-compose.yml"
  "database/schema/001_schema.sql"
  "database/schema/002_reference_data.sql"
  "database/seed/001_demo_data.sql"
  "device-simulator/鸿蒙模拟器/javafx-demo-1.0-SNAPSHOT.jar"
  "device-simulator/鸿蒙模拟器/sensors.dat"
  "device-simulator/鸿蒙模拟器/使用文档.md"
)

log()  { echo -e "\033[1;36m[打包]\033[0m $*"; }
die()  { echo -e "\033[1;31m[错误]\033[0m $*" >&2; exit 1; }

# ──────────── 0. 前置检查 ────────────
command -v docker >/dev/null 2>&1 || die "未找到 docker，请先安装 Docker"
docker info >/dev/null 2>&1 || die "Docker 未运行（Windows 请先打开 Docker Desktop）"
command -v gzip >/dev/null 2>&1 || die "未找到 gzip"
[ -d "$PACKAGE_WIN_DIR" ] || die "缺少 Windows 启动文件：$PACKAGE_WIN_DIR"
[ -f "$DEPLOY_DOC" ] || die "缺少部署文档：$DEPLOY_DOC"

log "开始打包智慧农业平台 ..."
log "仓库根：$PROJECT_ROOT"

# ──────────── 1. 构建镜像 ────────────
# npm 源默认 npmmirror（云服务器自动部署直连，无需传参）。
# 本机若连 npm 镜像不稳（开着代理/VPN 干扰 Docker 出网，报 ECONNREFUSED），
# 构建 frontend 前请显式传代理出口，例如（Clash 默认 7890）：
#   NPM_REGISTRY=https://registry.npmjs.org NPM_HTTP_PROXY=http://host.docker.internal:7890 \
#   bash scripts/make_package.sh
NPM_REGISTRY="${NPM_REGISTRY:-}"
NPM_HTTP_PROXY="${NPM_HTTP_PROXY:-}"

log "第 1/5 步：构建平台镜像（首次约 10 分钟，需联网）..."
cd "$PROJECT_ROOT/infra"
BUILD_ARGS=()
if [ -n "$NPM_REGISTRY" ]; then BUILD_ARGS+=(--build-arg "NPM_REGISTRY=$NPM_REGISTRY"); fi
if [ -n "$NPM_HTTP_PROXY" ]; then
  BUILD_ARGS+=(--build-arg "http_proxy=$NPM_HTTP_PROXY" --build-arg "https_proxy=$NPM_HTTP_PROXY")
fi
if [ ${#BUILD_ARGS[@]} -gt 0 ]; then
  log "frontend 构建参数：NPM_REGISTRY=${NPM_REGISTRY:-npmmirror}${NPM_HTTP_PROXY:+ 代理=$NPM_HTTP_PROXY}"
fi
if [ -f "$PROJECT_ROOT/.env" ]; then
  docker compose --env-file "$PROJECT_ROOT/.env" build backend ai-service
  docker compose --env-file "$PROJECT_ROOT/.env" build "${BUILD_ARGS[@]}" frontend
else
  log "提示：未找到 .env，构建使用默认配置；运行部署时需填写密钥（见部署文档）"
  docker compose build backend ai-service
  docker compose build "${BUILD_ARGS[@]}" frontend
fi
docker pull "${IMAGES[emqx]}"
docker pull "${IMAGES[mysql]}"
log "镜像构建完成"

# ──────────── 2. 组装目录 ────────────
log "第 2/5 步：组装部署包目录 ..."
rm -rf "$BUILD_DIR"
mkdir -p "$IMAGES_DIR" "$APP_DIR"

# 复制运行时必需文件（白名单，绝不带源码 / .env）
( cd "$PROJECT_ROOT" && tar -cf - "${RUNTIME_FILES[@]}" ) \
  | ( cd "$APP_DIR" && tar -xf - )

# 复制 Windows 一键启动文件 + 部署文档
cp "$PACKAGE_WIN_DIR/启动.bat"  "$BUILD_DIR/"
cp "$PACKAGE_WIN_DIR/停止.bat"  "$BUILD_DIR/"
cp "$PACKAGE_WIN_DIR/使用说明.txt" "$BUILD_DIR/"
cp "$DEPLOY_DOC" "$BUILD_DIR/"

log "目录组装完成：$BUILD_DIR"

# ──────────── 3. 导出镜像 ────────────
log "第 3/5 步：导出 5 个镜像（约 600MB，请耐心等待）..."
for name in emqx mysql backend ai-service frontend; do
  img="${IMAGES[$name]}"
  log "  导出 ${img} ..."
  docker save "$img" | gzip -1 > "$IMAGES_DIR/${name}.tar.gz"
done
log "镜像导出完成：$(du -sh "$IMAGES_DIR" | cut -f1)"

# ──────────── 4. 安全校验 ────────────
log "第 4/5 步：安全校验 ..."
if [ -f "$APP_DIR/.env" ]; then
  die "校验失败：.env 被组装进包了！请检查 RUNTIME_FILES 白名单后重试"
fi
if find "$APP_DIR" -iname "*复盘*" -o -iname "*.key" -o -iname "*.pem" 2>/dev/null | grep -q .; then
  die "校验失败：发现敏感文件（复盘/密钥/证书），请确认后重试"
fi
log "校验通过：无 .env、无敏感文件"

# ──────────── 5. 打包 ────────────
log "第 5/5 步：压缩为 farm-prebuild.tar.gz ..."
cd "$BUILD_DIR"
tar --force-local -czf "$DIST_DIR/farm-prebuild.tar.gz" \
  images iot-farm-suite 启动.bat 停止.bat 使用说明.txt 部署文档.md

# 校验包内中文文件名（应为 UTF-8 可读）
# 注意：先落盘再 grep，避免 "grep -q 匹配即退出 → tar 写管道 SIGPIPE" 导致 pipefail 误判
LIST_FILE="$(mktemp)"
tar --force-local -tzf "$DIST_DIR/farm-prebuild.tar.gz" > "$LIST_FILE" 2>/dev/null || true
if grep -a -q "启动.bat" "$LIST_FILE"; then
  log "包内中文文件名校验通过"
else
  rm -f "$LIST_FILE"
  die "打包异常：包内找不到 启动.bat（编码问题），请检查 LANG 环境变量"
fi
rm -f "$LIST_FILE"

echo
echo "=============================================================="
echo "  打包完成！"
echo "  目录： $BUILD_DIR"
echo "  压缩包： $DIST_DIR/farm-prebuild.tar.gz"
echo "    $(du -sh "$DIST_DIR/farm-prebuild.tar.gz" | cut -f1)"
echo ""
echo "  交付给老师：预构建镜像包/（Windows 双击 启动.bat）"
echo "  上传服务器：farm-prebuild.tar.gz（部署文档 · 方式 B）"
echo "=============================================================="
