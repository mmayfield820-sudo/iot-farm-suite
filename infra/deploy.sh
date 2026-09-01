#!/usr/bin/env bash
# 智慧农业全栈一键部署脚本（Linux / macOS 服务器用）
# 用法：cd infra && ./deploy.sh
#   ./deploy.sh          # 首次：构建 + 启动
#   ./deploy.sh rebuild  # 更新：重新构建 + 启动
#   ./deploy.sh stop     # 停止
#   ./deploy.sh logs     # 看日志
#   ./deploy.sh status   # 看状态

set -euo pipefail
ENV_FILE="../.env"

# 首次运行前必须存在 .env（在仓库根目录）
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 找不到 $ENV_FILE"
  echo "   请先执行: cp .env.example .env  然后编辑 .env 填入真实密钥"
  exit 1
fi

ACTION="${1:-up}"

case "$ACTION" in
  up|rebuild)
    echo "🔧 正在构建并启动智慧农业全栈..."
    docker compose --env-file "$ENV_FILE" up -d --build
    echo "✅ 启动完成！浏览器访问: http://$(hostname -I 2>/dev/null | awk '{print $1}')  (或服务器公网IP)"
    echo "   5 个服务: emqx / mysql / backend / ai-service / frontend"
    ;;
  stop)
    echo "🛑 正在停止全部服务..."
    docker compose --env-file "$ENV_FILE" down
    ;;
  logs)
    docker compose --env-file "$ENV_FILE" logs -f
    ;;
  status)
    docker compose --env-file "$ENV_FILE" ps
    ;;
  *)
    echo "用法: ./deploy.sh [up|rebuild|stop|logs|status]"
    ;;
esac
