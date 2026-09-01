@echo off
title 智慧农业平台 · 停止服务
cd /d "%~dp0"

echo.
echo  正在停止智慧农业平台...
docker compose --env-file "%~dp0iot-farm-suite\.env" -f "%~dp0iot-farm-suite\infra\docker-compose.yml" down
echo.
echo  平台已停止。数据保存在 Docker 里，下次双击「启动.bat」数据还在。
echo.
pause
