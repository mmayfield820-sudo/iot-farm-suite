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
SOURCE_APP_DIR="$BUILD_DIR/iot-farm-suite"
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

# 组装源码时排除的目录/文件（.env 绝不进包！）
SOURCE_EXCLUDES=(
  "--exclude=.git"
  "--exclude=.env"
  "--exclude=node_modules"
  "--exclude=__pycache__"
  "--exclude=dist"
  "--exclude=*.log"
  "--exclude=*.pyc"
  "--exclude=device-simulator"
  "--exclude=农户界面当前演示.mp4"
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
log "第 1/5 步：构建平台镜像（首次约 10 分钟，需联网）..."
cd "$PROJECT_ROOT/infra"
if [ -f "$PROJECT_ROOT/.env" ]; then
  docker compose --env-file "$PROJECT_ROOT/.env" build backend ai-service frontend
else
  log "提示：未找到 .env，构建使用默认配置；运行部署时需填写密钥（见部署文档）"
  docker compose build backend ai-service frontend
fi
docker pull "${IMAGES[emqx]}"
docker pull "${IMAGES[mysql]}"
log "镜像构建完成"

# ──────────── 2. 组装目录 ────────────
log "第 2/5 步：组装部署包目录 ..."
rm -rf "$BUILD_DIR"
mkdir -p "$IMAGES_DIR" "$SOURCE_APP_DIR"

# 复制源码（排除敏感/无用文件）
( cd "$PROJECT_ROOT" && tar "${SOURCE_EXCLUDES[@]}" -cf - . ) \
  | ( cd "$SOURCE_APP_DIR" && tar -xf - )

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
if [ -f "$SOURCE_APP_DIR/.env" ]; then
  die "校验失败：.env 被组装进包了！请检查 SOURCE_EXCLUDES 后重试"
fi
if find "$SOURCE_APP_DIR" -iname "*复盘*" -o -iname "*.key" -o -iname "*.pem" 2>/dev/null | grep -q .; then
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
