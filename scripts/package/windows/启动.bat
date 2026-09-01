@echo off
title 智慧农业平台 · 一键启动
cd /d "%~dp0"

echo.
echo  ==================================================
echo    智慧农业平台  ·  Windows 一键启动
echo  ==================================================
echo.

REM ──────────── 第 1 步：检查 Docker ────────────
docker info >nul 2>&1
if errorlevel 1 (
    echo  [第 1 步失败] Docker 未就绪。
    echo.
    echo  请先安装并打开 Docker Desktop：
    echo    下载地址：https://www.docker.com/products/docker-desktop/
    echo    安装完成后双击打开它，等底部状态变成绿色
    echo    "Engine running"，再双击本文件重试。
    echo.
    pause
    exit /b 1
)
echo  [1/5] Docker 运行正常 [OK]

REM ──────────── 第 2 步：生成配置文件（仅首次）────────────
set "ENV_FILE=iot-farm-suite\.env"
if not exist "%ENV_FILE%" (
    echo  [2/5] 首次运行，自动生成配置文件 ...
    copy /y "iot-farm-suite\.env.example" "%ENV_FILE%" >nul
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Join-Path (Get-Location) 'iot-farm-suite\.env'; $lines=Get-Content $p -Encoding UTF8; $s=-join ((48..57)+(65..90)+(97..122)|Get-Random -Count 64|ForEach-Object{[char]$_}); $lines=$lines|ForEach-Object{if($_ -match '^JWT_SECRET='){'JWT_SECRET='+$s}else{$_}}; [IO.File]::WriteAllLines($p,$lines,(New-Object Text.UTF8Encoding($false)))"
    echo  已生成配置（登录密钥已自动随机生成）[OK]
) else (
    echo  [2/5] 配置文件已存在，跳过 [OK]
)

REM ──────────── 第 3 步：加载平台镜像（仅首次）────────────
docker images smart-farm/frontend:latest >nul 2>&1
if errorlevel 1 (
    echo  [3/5] 首次运行，正在加载平台镜像 ...
    echo        5 个镜像共约 600MB，需要 3~5 分钟，请勿关闭窗口。
    for %%f in (images\*.tar.gz) do (
        echo    正在加载 %%f ...
        docker load -i "%%f"
    )
    echo  镜像加载完成 [OK]
) else (
    echo  [3/5] 平台镜像已就绪，跳过 [OK]
)

REM ──────────── 第 4 步：启动全部服务 ────────────
echo  [4/5] 正在启动 MySQL / EMQX / 后端 / AI / 网页 ...
cd /d "%~dp0iot-farm-suite\infra"
docker compose --env-file ..\.env up -d
if errorlevel 1 (
    echo.
    echo  [启动失败] 请查看上方报错信息。
    echo  常见原因：80 或 1883 端口被占用。
    echo  解决办法见《使用说明.txt》的「常见问题」。
    echo.
    pause
    exit /b 1
)

REM ──────────── 第 5 步：等待就绪并打开浏览器 ────────────
echo  [5/5] 等待平台就绪（首次约 1 分钟）...
set "READY="
for /l %%i in (1,1,30) do (
    curl -s -o nul --max-time 2 http://localhost 2>nul
    if not errorlevel 1 (
        set "READY=1"
        goto ready
    )
    timeout /t 2 /nobreak >nul
)
:ready
if "%READY%"=="1" (
    echo  平台已就绪 [OK]
) else (
    echo  [提示] 尚未等到网页响应，请稍后手动刷新浏览器。
)
start "" http://localhost

echo.
echo  ==================================================
echo    启动成功！浏览器已打开  http://localhost
echo.
echo    演示账号（密码都是 DemoPass123!）：
echo      管理员  demo_admin
echo      农户    demo_farmer
echo      系统    demo_system
echo.
echo    · 本窗口现在可以关闭，平台继续运行。
echo    · 要停止平台，双击「停止.bat」。
echo    · 要完整体验 AI 问答，需填 API Key（见使用说明）。
echo  ==================================================
echo.
pause
