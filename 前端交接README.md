# 智慧农业项目前端交接 README

本文档面向继续开发和部署本项目的前端成员，说明当前项目结构、从空环境启动完整系统的方法、主要配置文件以及生产环境部署方式。

> 当前正式 REST API 契约统一以 `contracts/openapi.yaml` 为准。前端不得直接连接 MySQL、发布真实 MQTT 控制指令或保存服务端密钥。

## 1. 项目概览

当前系统由以下部分组成：

```text
Vue 3 前端（5173）
        │ /api
        ▼
FastAPI 业务后端（8080） ────── MySQL（3306）
        │                         ▲
        ├── MQTT ── EMQX（宿主机 2883 / 容器 1883）
        │
        └── HTTP ── AI 服务（8000） ── Ollama（11434）
```

- 浏览器只访问前端和业务后端的 `/api`。
- AI 页面也通过业务后端访问 AI 服务，前端不直接连接 `8000` 端口。
- 设备遥测与控制结果通过 EMQX 进入后端，再由后端写入数据库并提供给前端。
- MySQL、EMQX、AI 服务和 Ollama 均不应直接暴露给公网浏览器。

## 2. 根目录结构

```text
iot-farm-suite/
├─ frontend/                 Vue 3 前端工程
├─ backend/                  FastAPI 业务后端
├─ ai-service/               农业智能问答服务
├─ database/                 当前数据库结构、基础数据和演示数据
├─ contracts/                正式 API、MQTT、事件及字段契约
├─ device-simulator/         Python 与鸿蒙设备模拟器
├─ docs/                     需求、架构、MQTT 和界面资料
├─ infra/                    Docker Compose 基础设施配置
├─ tests/                    后端及跨模块测试
├─ .env.example              根环境变量模板
├─ start-all.ps1             Windows 一键启动脚本
├─ start-all.cmd             一键启动脚本的双击入口
├─ README.md                 项目总说明
└─ 前端交接README.md          本交接文档
```

### 2.1 前端目录

```text
frontend/
├─ public/                   不经过 Vite 打包处理的公共资源
├─ src/
│  ├─ api/                  HTTP 接口封装；统一复用 request.js
│  ├─ assets/               全局样式、作物图片和枝桠底纹
│  ├─ components/           多页面复用的业务组件
│  ├─ layout/               农户、农场管理员、系统管理员布局
│  ├─ mock/                 前端模拟模式数据
│  ├─ router/               页面路由、登录校验和角色守卫
│  ├─ services/             MQTT 协议等前端侧协议定义
│  ├─ stores/               Pinia 状态、数据加载和业务操作
│  ├─ utils/                数据适配、状态转换及通用工具
│  ├─ views/                各角色的完整页面
│  ├─ App.vue               Vue 根组件
│  └─ main.js               前端启动入口
├─ .env.development          本地开发构建变量
├─ .env.production           生产构建变量
├─ index.html                Vite HTML 入口
├─ package.json              依赖与 dev/build/preview 命令
├─ package-lock.json         锁定的 npm 依赖版本
└─ vite.config.js            Vite、路径别名和开发代理
```

前端主要调用链：

```text
views 页面
  → stores 状态与业务逻辑
  → api 接口封装
  → api/request.js
  → /api
  → FastAPI 后端
```

重点文件说明：

| 文件或目录 | 作用 | 修改注意事项 |
| --- | --- | --- |
| `frontend/src/api/request.js` | Axios 实例、Token 注入、401 处理和统一错误提示 | 不要在页面内重复创建 Axios 实例 |
| `frontend/src/router/index.js` | 页面路由、角色权限与懒加载入口 | 新增页面时同步登记路由和侧边栏 |
| `frontend/src/stores/` | 跨页面共享数据和真实/模拟接口切换 | 避免把共享业务状态散落到多个页面 |
| `frontend/src/utils/dataAdapters.js` | 后端字段到页面模型的兼容转换 | 接口字段调整优先集中在这里处理 |
| `frontend/src/assets/main.css` | 全局主题、背景和通用样式 | 修改前检查三种角色页面是否同时受影响 |
| `frontend/.env.*` | Vite 构建变量 | `VITE_` 变量会进入浏览器，禁止写入密钥 |
| `frontend/vite.config.js` | 本地端口与 `/api` 开发代理 | 仅影响开发服务器，不代替生产反向代理 |

### 2.2 后端、数据库和契约目录

| 目录 | 说明 |
| --- | --- |
| `backend/app/main.py` | FastAPI 主入口及部分公共接口 |
| `backend/app/routers/` | 种植、计划、农事、地块时间轴、员工和档案等路由 |
| `backend/app/services/` | 生长阶段、计划、灌溉建议、天气和审计业务逻辑 |
| `backend/app/mqtt.py` | MQTT 订阅、设备配对、状态更新和控制结果处理 |
| `ai-service/app/` | AI 健康检查、知识检索、模型调用及联网搜索 |
| `database/schema/` | 当前最终数据库结构和基础权限数据 |
| `database/seed/` | 当前演示业务数据快照 |
| `database/design/当前数据库说明.docx` | 当前表、字段、关系和数据说明 |
| `contracts/openapi.yaml` | 前后端唯一正式 REST API 契约 |
| `contracts/mqtt-topics.md` | 后端与设备端 MQTT 主题及报文约定 |
| `infra/docker-compose.yml` | MySQL、EMQX 端口、数据卷和空库初始化挂载 |

## 3. 从 0 到 1 启动完整系统

以下步骤以 Windows PowerShell 为例。首次交接建议先走一遍“手工启动”，确认每个服务均正常后再使用一键脚本。

### 3.1 环境依赖

| 依赖 | 建议版本 | 用途 |
| --- | --- | --- |
| Git | 当前稳定版 | 获取和维护代码 |
| Node.js | 20.19+ 或 22.12+ | Vite 7 与前端构建 |
| npm | 随 Node.js 安装 | 安装锁定依赖、启动和构建前端 |
| Python | 3.11+，推荐 3.12 | FastAPI 后端和 AI 服务 |
| Docker Desktop | 当前稳定版，启用 Compose v2 | 运行 MySQL 与 EMQX |
| Ollama | 当前稳定版 | 运行本地 Qwen 模型；不测试 AI 时可暂不安装 |
| JDK/Java | 当前脚本按 JDK 20 配置 | 运行鸿蒙 JAR 模拟器；不测试设备时可不启动 |

安装后检查：

```powershell
git --version
node --version
npm --version
python --version
docker --version
docker compose version
```

### 3.2 获取代码并创建环境配置

进入项目根目录后执行：

```powershell
Copy-Item .env.example .env
```

至少检查并修改 `.env` 中以下内容：

```dotenv
DATABASE_URL=mysql://farm:请修改数据库密码@127.0.0.1:3306/farm
MYSQL_DATABASE=farm
MYSQL_USER=farm
MYSQL_PASSWORD=请修改数据库密码
MYSQL_ROOT_PASSWORD=请修改Root密码

# 使用项目自带 docker-compose.yml 时，宿主机 MQTT 端口是 2883
MQTT_HOST=127.0.0.1
MQTT_PORT=2883

# 必须替换为足够长的随机值
JWT_SECRET=请替换为随机密钥

AI_SERVICE_URL=http://127.0.0.1:8000
AI_MODEL_BASE_URL=http://127.0.0.1:11434/v1
AI_MODEL_API_KEY=ollama
AI_MODEL_NAME=qwen2.5:7b

PUBLIC_REGISTRATION_ENABLED=false
WEATHER_MODE=mock
```

注意：

- `.env` 已被 Git 忽略，不要将真实密码、JWT 密钥或博查密钥提交到仓库。
- `.env.example` 是模板，不应存放生产密钥。
- 如果使用另行安装且直接暴露 `1883` 的 EMQX，可把 `MQTT_PORT` 改为 `1883`；使用本项目 Compose 时应填写 `2883`。
- `PUBLIC_REGISTRATION_ENABLED=false` 表示员工由管理员导入后激活，符合当前业务流程。
- 未配置 `BOCHA_API_KEY` 时，AI 联网搜索会降级，但本地知识问答仍可运行。

### 3.3 安装 Python 依赖

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r ai-service\requirements.txt
```

### 3.4 安装前端依赖

```powershell
Set-Location frontend
npm ci
Set-Location ..
```

优先使用 `npm ci`，它会严格按照 `package-lock.json` 安装，便于不同成员获得一致环境。只有主动升级依赖时才使用 `npm install` 并提交新的锁文件。

### 3.5 启动 MySQL 和 EMQX

确保 Docker Desktop 已启动，然后在项目根目录运行：

```powershell
docker compose --env-file .env -f infra\docker-compose.yml up -d
docker compose --env-file .env -f infra\docker-compose.yml ps
```

首次创建 MySQL 数据卷时会自动按顺序执行：

1. `database/schema/001_schema.sql`
2. `database/schema/002_reference_data.sql`
3. `database/seed/001_demo_data.sql`

这些脚本只会在空数据卷首次初始化时执行。已有数据卷不会因为修改 SQL 文件而自动重建；需要保留数据时禁止直接删除数据卷。

### 3.6 启动 Ollama 和模型（需要 AI 时）

```powershell
ollama pull qwen2.5:7b
ollama serve
```

如果 Ollama 桌面端已经在 `11434` 端口运行，不要重复执行 `ollama serve`。

### 3.7 分别启动三个应用服务

建议打开三个 PowerShell 窗口。

窗口一，业务后端：

```powershell
Set-Location 你的项目根目录
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
```

窗口二，AI 服务：

```powershell
Set-Location 你的项目根目录
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir ai-service
```

窗口三，前端：

```powershell
Set-Location 你的项目根目录\frontend
npm run dev
```

访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端健康检查：`http://127.0.0.1:8080/health`
- 后端 Swagger：`http://127.0.0.1:8080/docs`
- AI 健康检查：`http://127.0.0.1:8000/health`
- EMQX 控制台：`http://127.0.0.1:18083`

演示账号、激活状态和数据库恢复说明见 `database/README.md`。

### 3.8 可选：启动设备模拟器

Python 模拟器单次上报：

```powershell
.\.venv\Scripts\python.exe device-simulator\simulator.py --once
```

鸿蒙 JAR 模拟器位于：

```text
device-simulator/鸿蒙模拟器/javafx-demo-1.0-SNAPSHOT.jar
```

模拟器 MQTT 地址、设备 UUID、配对上报和 topic 必须与 `contracts/mqtt-topics.md` 及当前数据库设备记录一致。

## 4. 一键启动方式

完成依赖安装和 `.env` 配置后，可在根目录双击 `start-all.cmd`，或执行：

```powershell
.\start-all.ps1
```

启动前只做检查：

```powershell
.\start-all.ps1 -ValidateOnly
```

只启动某一服务：

```powershell
.\start-all.ps1 -Mode Backend
.\start-all.ps1 -Mode AI
.\start-all.ps1 -Mode Frontend
```

### 一键脚本的本机路径配置

`start-all.ps1` 当前包含原开发机器上的绝对路径：

```powershell
$ollamaExe = "E:\AI\Ollama\ollama.exe"
$ollamaModels = "E:\AI\OllamaModels"
$javaExe = "E:\bin\java.exe"
```

接手成员必须把它们改成自己电脑上的真实路径。一键脚本当前还会在启动前检查 Python 虚拟环境、Ollama、Java 和鸿蒙模拟器 JAR；如果只做普通前端开发，使用下面的前端单独启动方式更简单。

## 5. 只启动前端

### 5.1 连接真实后端

确认 `frontend/.env.development` 为：

```dotenv
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
```

启动后端 `8080` 后执行：

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite 会根据 `frontend/vite.config.js` 把 `/api` 代理到 `http://localhost:8080`。

### 5.2 不启动后端，使用模拟数据

临时把 `frontend/.env.development` 改为：

```dotenv
VITE_API_BASE_URL=/api
VITE_USE_MOCK=true
```

修改环境文件后必须重新启动 `npm run dev`。模拟模式只用于界面开发，不能替代真实接口联调、权限测试、设备控制和数据库验证。

## 6. 配置文件修改说明

| 文件 | 影响范围 | 常见修改 |
| --- | --- | --- |
| `.env` | Docker、后端、AI 服务 | 数据库、MQTT、JWT、AI、天气和联网搜索配置 |
| `.env.example` | 新成员初始化模板 | 新增服务变量时同步提供无密钥示例 |
| `frontend/.env.development` | `npm run dev` | `/api` 地址、是否使用 Mock |
| `frontend/.env.production` | `npm run build` | 生产 API 地址、关闭 Mock |
| `frontend/vite.config.js` | 本地开发服务器 | 5173 端口、`@` 别名、8080 开发代理 |
| `infra/docker-compose.yml` | MySQL、EMQX | 镜像、端口、数据卷和空库初始化脚本 |
| `start-all.ps1` | Windows 一键启动 | Ollama、模型目录、Java 的本机绝对路径 |
| `contracts/openapi.yaml` | 前后端 REST 契约 | 接口路径、参数、响应和枚举变化 |

### Vite 环境变量规则

- 只有以 `VITE_` 开头的变量可在前端代码中通过 `import.meta.env` 读取。
- 所有 `VITE_` 变量都会打进浏览器资源，不能保存数据库密码、JWT 密钥、MQTT 密码或第三方 API 密钥。
- 修改 `.env.production` 后必须重新执行 `npm run build`，已经生成的 `dist` 不会自动更新。
- 当前推荐生产配置为同域 `/api`，可避免额外的跨域配置。

## 7. 生产环境部署

当前仓库没有封装完整的生产镜像或 Nginx 配置，推荐采用“静态前端 + Nginx + 后端进程服务 + Docker 基础设施”的方式部署。

### 7.1 准备生产环境变量

从 `.env.example` 复制出服务器上的 `.env`，至少完成以下调整：

1. 使用强随机 `JWT_SECRET`。
2. 修改 MySQL 普通用户和 Root 密码。
3. 根据部署网络填写 `DATABASE_URL`、`MQTT_HOST` 和 `MQTT_PORT`。
4. 保持 `PUBLIC_REGISTRATION_ENABLED=false`，除非业务明确要求开放注册。
5. 配置真实 Ollama 地址；需要联网搜索时配置 `BOCHA_API_KEY`。
6. `WEATHER_MODE=api` 时同时配置真实 `WEATHER_API_URL`；未配置前保持 `mock`。

不要把生产 `.env` 放入前端目录、Web 根目录或 Git 仓库。

### 7.2 启动基础设施

```powershell
docker compose --env-file .env -f infra\docker-compose.yml up -d
```

生产环境建议通过防火墙限制 `3306`、`2883`、`18083` 和 `11434`，只允许可信内网访问。

### 7.3 构建前端

确认 `frontend/.env.production` 为：

```dotenv
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
```

执行：

```powershell
Set-Location frontend
npm ci
npm run build
```

产物位于 `frontend/dist/`。`npm run preview` 仅用于本地检查，不应作为正式生产服务器。

### 7.4 运行后端和 AI 服务

生产环境应使用 Windows 服务管理器、NSSM、systemd 或容器编排工具托管进程并设置失败重启，不要依赖一直打开的终端窗口。

业务后端启动命令：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
```

AI 服务启动命令：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir ai-service
```

如果 Nginx 和后端不在同一台机器，应改为内网监听地址，并通过防火墙限制来源。

### 7.5 配置 Nginx

将 `frontend/dist/` 部署到静态目录，并使用类似配置：

```nginx
server {
    listen 80;
    server_name 你的域名;

    root /opt/iot-farm-suite/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
    }
}
```

说明：

- `try_files ... /index.html` 用于支持 Vue Router history 模式，缺少它会导致刷新子页面时返回 404。
- `/api/` 必须代理到业务后端 `8080`，不要直接代理到 AI 服务。
- AI 问答可能耗时较长，因此反向代理读取超时建议不少于 180 秒。
- 正式公网环境应配置 HTTPS，并将 HTTP 重定向到 HTTPS。

### 7.6 上线检查

依次检查：

1. `GET /health` 能返回业务后端和数据库健康状态。
2. `GET /api/chat/health` 能正确反映 AI 服务状态。
3. 登录、员工激活和三种角色权限正常。
4. 前端刷新任意子路由不会出现 404。
5. MQTT 设备在线、遥测配对、告警恢复和灌溉控制结果正常。
6. 农事计划、日历、地块时间轴和计划变更数据来自真实接口。
7. 生产构建中 `VITE_USE_MOCK=false`。
8. 浏览器开发者工具中没有请求到 `localhost` 或开发机地址。

## 8. 常见问题

### 页面能打开，但数据都是模拟的

检查 `frontend/.env.development` 或 `.env.production` 中的 `VITE_USE_MOCK`，改为 `false` 后重新启动或重新构建。

### 前端请求 `/api` 返回 404

- 开发环境：检查后端是否监听 `8080`，以及 `vite.config.js` 代理目标是否正确。
- 生产环境：检查 Nginx 是否把 `/api/` 转发到后端，并确认没有错误地移除 `/api` 前缀。

### Docker 启动后没有重新导入最新 SQL

MySQL 初始化文件只在空数据卷首次启动时执行。不要为了重新导入而直接删除包含有效数据的数据卷；应先备份，再按交付或迁移方案操作。

### 后端启动后设备始终离线

检查 `.env` 中 MQTT 端口。项目 Compose 对宿主机暴露的是 `2883`，不是容器内部的 `1883`。

### AI 页面提示内部错误

依次检查：

1. `http://127.0.0.1:8000/health`；
2. `.env` 中的 `AI_SERVICE_URL`；
3. Ollama 是否监听 `11434`；
4. `qwen2.5:7b` 是否已经下载；
5. 反向代理超时时间是否足够。

## 9. 交接开发约定

- 接口变化先更新 `contracts/openapi.yaml`，再同步后端、前端 API 封装和数据适配。
- 新页面放入对应角色的 `views` 目录，并同步更新路由和布局菜单。
- 共享数据放在 Pinia store，共享显示组件放在 `components`。
- 不在页面中硬编码数据库 ID、账号、密码、服务地址或设备凭据。
- 日期时间由服务端按 UTC 保存，前端统一转换为北京时间显示。
- 提交前至少执行：

```powershell
Set-Location frontend
npm run build
```

涉及后端逻辑时，再执行项目根目录中的单元测试：

```powershell
Set-Location ..
.\.venv\Scripts\python.exe -m unittest discover -s tests\unit -p "test_*.py"
```

