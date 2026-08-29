[CmdletBinding()]
param(
    [ValidateSet("All", "Ollama", "Backend", "AI", "Frontend")]
    [string]$Mode = "All",
    [switch]$SkipSimulator,
    [switch]$NoBrowser,
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"
$composeFile = Join-Path $projectRoot "infra\docker-compose.yml"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$ollamaExe = "E:\AI\Ollama\ollama.exe"
$ollamaModels = "E:\AI\OllamaModels"
$javaExe = "E:\bin\java.exe"
$simulatorDirectory = Join-Path $projectRoot "device-simulator\鸿蒙模拟器"
$simulatorJar = Join-Path $simulatorDirectory "javafx-demo-1.0-SNAPSHOT.jar"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-ListeningPort {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-ListeningPort {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-ListeningPort -Port $Port) {
            return $true
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Assert-RequiredFile {
    param([string]$Path, [string]$Description)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Description 不存在：$Path"
    }
}

function Start-ServiceTerminal {
    param(
        [ValidateSet("Ollama", "Backend", "AI", "Frontend")]
        [string]$ServiceMode
    )

    $arguments = "-NoProfile -NoExit -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Mode $ServiceMode"
    Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -WorkingDirectory $projectRoot
}

Assert-RequiredFile -Path $envFile -Description "项目环境配置"
Assert-RequiredFile -Path $composeFile -Description "Docker Compose 配置"
Assert-RequiredFile -Path $pythonExe -Description "Python 虚拟环境"
Assert-RequiredFile -Path $ollamaExe -Description "Ollama 程序"
Assert-RequiredFile -Path $javaExe -Description "JDK 20"
Assert-RequiredFile -Path $simulatorJar -Description "鸿蒙传感器模拟器"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "没有找到 docker 命令，请先安装 Docker Desktop。"
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "没有找到 npm，请先安装 Node.js。"
}
if ($ValidateOnly) {
    Write-Host "一键启动所需文件和命令均已找到。" -ForegroundColor Green
    Write-Host "项目目录：$projectRoot"
    Write-Host "Ollama 模型目录：$ollamaModels"
    exit 0
}

if ($Mode -ne "All") {
    switch ($Mode) {
        "Ollama" {
            $Host.UI.RawUI.WindowTitle = "智慧农业 - Ollama 11434"
            $env:OLLAMA_MODELS = $ollamaModels
            $env:OLLAMA_HOST = "127.0.0.1:11434"
            Set-Location -LiteralPath (Split-Path -Parent $ollamaExe)
            & $ollamaExe serve
        }
        "Backend" {
            $Host.UI.RawUI.WindowTitle = "智慧农业 - 后端 8080"
            Set-Location -LiteralPath $projectRoot
            & $pythonExe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
        }
        "AI" {
            $Host.UI.RawUI.WindowTitle = "智慧农业 - AI 服务 8000"
            Set-Location -LiteralPath (Join-Path $projectRoot "ai-service")
            & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
        }
        "Frontend" {
            $Host.UI.RawUI.WindowTitle = "智慧农业 - 前端 5173"
            Set-Location -LiteralPath (Join-Path $projectRoot "frontend")
            & npm.cmd run dev
        }
    }
    exit $LASTEXITCODE
}

Set-Location -LiteralPath $projectRoot

Write-Step "检查 Docker Desktop"
& docker info *> $null
$dockerReady = ($LASTEXITCODE -eq 0)
if (-not $dockerReady) {
    $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    Assert-RequiredFile -Path $dockerDesktop -Description "Docker Desktop"
    Write-Host "Docker Desktop 尚未运行，正在启动..."
    Start-Process -FilePath $dockerDesktop

    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        Start-Sleep -Seconds 2
        & docker info *> $null
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            break
        }
    }
}
if (-not $dockerReady) {
    throw "Docker Desktop 在 120 秒内没有准备完成。"
}

Write-Step "启动 MySQL 和 EMQX"
& docker compose --env-file $envFile -f $composeFile up -d
if ($LASTEXITCODE -ne 0) {
    throw "Docker 基础服务启动失败。"
}

Write-Step "启动 Ollama"
if (Test-ListeningPort -Port 11434) {
    Write-Host "Ollama 已在 11434 端口运行，跳过重复启动。"
}
else {
    Start-ServiceTerminal -ServiceMode "Ollama"
    if (-not (Wait-ListeningPort -Port 11434 -TimeoutSeconds 60)) {
        throw "Ollama 未能在 60 秒内启动，请查看 Ollama 终端窗口。"
    }
}

Write-Step "启动后端"
if (Test-ListeningPort -Port 8080) {
    Write-Host "后端已在 8080 端口运行，跳过重复启动。"
}
else {
    Start-ServiceTerminal -ServiceMode "Backend"
}

Write-Step "启动 AI 服务"
if (Test-ListeningPort -Port 8000) {
    Write-Host "AI 服务已在 8000 端口运行，跳过重复启动。"
}
else {
    Start-ServiceTerminal -ServiceMode "AI"
}

Write-Step "启动前端"
if (Test-ListeningPort -Port 5173) {
    Write-Host "前端已在 5173 端口运行，跳过重复启动。"
}
else {
    Start-ServiceTerminal -ServiceMode "Frontend"
}

if (-not $SkipSimulator) {
    Write-Step "启动鸿蒙传感器模拟器"
    $simulatorRunning = $false
    try {
        $simulatorRunning = [bool](Get-CimInstance Win32_Process -Filter "Name='java.exe'" |
            Where-Object { $_.CommandLine -like "*$([IO.Path]::GetFileName($simulatorJar))*" })
    }
    catch {
        $simulatorRunning = $false
    }

    if ($simulatorRunning) {
        Write-Host "鸿蒙传感器模拟器已经运行，跳过重复启动。"
    }
    else {
        Start-Process -FilePath $javaExe -ArgumentList @("-jar", $simulatorJar) -WorkingDirectory $simulatorDirectory
    }
}

if (-not $NoBrowser) {
    Write-Step "等待前端并打开浏览器"
    if (Wait-ListeningPort -Port 5173 -TimeoutSeconds 90) {
        Start-Process "http://127.0.0.1:5173"
    }
    else {
        Write-Warning "前端尚未监听 5173，请查看前端终端窗口。"
    }
}

Write-Host "`n所有启动命令均已执行。" -ForegroundColor Green
Write-Host "MySQL 3306 | MQTT 2883 | Ollama 11434 | 后端 8080 | AI 8000 | 前端 5173"
